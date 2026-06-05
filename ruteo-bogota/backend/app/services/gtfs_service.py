"""
Carga GTFS TransMilenio/SITP — infraestructura de transporte oficial.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from app.services.trunk_routes_loader import get_trunk_registry

BASE_DIR = Path(__file__).resolve().parents[2]
GTFS_DIR = BASE_DIR / "data" / "gtfs"

ANTS_PER_ROUTE = 5

# Velocidad comercial promedio troncal TransMilenio (~26-30 km/h con paradas).
TM_COMMERCIAL_SPEED_M_PER_MIN = 500.0  # 500 m/min ≈ 30 km/h


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class GTFSBundle:
    """Índice GTFS en memoria (carga perezosa) consciente de la whitelist troncal."""

    def __init__(self, directory: Path | None = None):
        self.directory = directory or GTFS_DIR
        self.stops: dict[str, dict] = {}
        self.routes: dict[str, dict] = {}
        self.route_shape: dict[str, str] = {}
        self.route_stops: dict[str, list[str]] = {}
        self.stop_routes: dict[str, set[str]] = defaultdict(set)
        self.shapes: dict[str, list[list[float]]] = {}
        self._core_loaded = False
        self._shapes_loaded = False
        # Registro de rutas troncales (whitelist).
        self.trunk = get_trunk_registry()

    def _path(self, name: str) -> Path:
        p = self.directory / name
        if not p.exists():
            raise FileNotFoundError(f"GTFS no encontrado: {p}")
        return p

    # ── carga núcleo ────────────────────────────────────────────────
    def load_core(self) -> None:
        if self._core_loaded:
            return

        with open(self._path("stops.txt"), encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                self.stops[row["stop_id"]] = {
                    "id": row["stop_id"],
                    "name": row["stop_name"],
                    "lat": float(row["stop_lat"]),
                    "lon": float(row["stop_lon"]),
                    "location_type": int(row.get("location_type") or 0),
                    "parent_station": row.get("parent_station") or "",
                }

        # routes.txt puede no incluir todos los troncales; completamos con la
        # whitelist para que cada route_id troncal tenga metadatos (color, etc.).
        try:
            with open(self._path("routes.txt"), encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    rid = row["route_id"]
                    self.routes[rid] = {
                        "id": rid,
                        "short_name": row.get("route_short_name", rid),
                        "long_name": row.get("route_long_name", ""),
                        "color": row.get("route_color", "ff0000"),
                        "type": int(row.get("route_type") or 3),
                        "is_trunk": self.trunk.is_trunk(rid),
                    }
        except FileNotFoundError:
            pass

        # Garantizar metadatos para cada ruta troncal de la whitelist.
        for rid in self.trunk.route_ids:
            tr = self.trunk.get(rid)
            self.routes.setdefault(rid, {
                "id": rid,
                "short_name": tr.short_name if tr else rid,
                "long_name": tr.headsign if tr else "",
                "color": tr.color if tr else "ff0000",
                "type": 3,
                "is_trunk": True,
            })
            self.routes[rid]["is_trunk"] = True
            if tr:
                self.routes[rid]["color"] = tr.color

        # trips → primer trip por ruta + shape asociado.
        route_trip: dict[str, str] = {}
        with open(self._path("trips.txt"), encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                tid, rid = row["trip_id"], row["route_id"]
                if rid not in route_trip:
                    route_trip[rid] = tid
                    if row.get("shape_id"):
                        self.route_shape[rid] = row["shape_id"]

        # stop_times → secuencia de paradas por trip representativo.
        trip_stops: dict[str, list[tuple[int, str]]] = defaultdict(list)
        with open(self._path("stop_times.txt"), encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                trip_stops[row["trip_id"]].append(
                    (int(row["stop_sequence"]), row["stop_id"])
                )

        for rid, tid in route_trip.items():
            seq = [s for _, s in sorted(trip_stops.get(tid, []))]
            if not seq:
                continue
            self.route_stops[rid] = seq
            for sid in seq:
                self.stop_routes[sid].add(rid)

        self._core_loaded = True

    def load_shapes(self) -> None:
        if self._shapes_loaded:
            return
        self.load_core()
        current_id: str | None = None
        current_pts: list[list[float]] = []

        with open(self._path("shapes.txt"), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row["shape_id"]
                if sid != current_id:
                    if current_id and current_pts:
                        self.shapes[current_id] = current_pts
                    current_id = sid
                    current_pts = []
                current_pts.append(
                    [float(row["shape_pt_lat"]), float(row["shape_pt_lon"])]
                )
            if current_id and current_pts:
                self.shapes[current_id] = current_pts

        self._shapes_loaded = True

    # ── helpers whitelist ───────────────────────────────────────────
    def is_trunk_route(self, route_id: str) -> bool:
        return self.trunk.is_trunk(route_id)

    @property
    def trunk_route_ids(self) -> list[str]:
        """route_ids troncales que además tienen paradas cargadas."""
        self.load_core()
        return [rid for rid in self.trunk.route_ids if self.route_stops.get(rid)]

    # ── consultas espaciales ────────────────────────────────────────
    def nearest_stops(
        self,
        lat: float,
        lon: float,
        limit: int = 6,
        max_m: int = 2500,
        trunk_only: bool = False,
    ) -> list[dict]:
        """
        Paradas más cercanas. Con trunk_only=True solo devuelve estaciones
        servidas por al menos una ruta troncal de la whitelist.
        """
        self.load_core()
        ranked = []
        for stop in self.stops.values():
            if trunk_only and not self._stop_has_trunk(stop["id"]):
                continue
            d = _haversine(lat, lon, stop["lat"], stop["lon"])
            if d <= max_m:
                ranked.append({**stop, "distance_m": round(d)})
        ranked.sort(key=lambda s: s["distance_m"])
        return ranked[:limit]

    def _stop_has_trunk(self, stop_id: str) -> bool:
        return any(self.trunk.is_trunk(r) for r in self.stop_routes.get(stop_id, ()))

    # ── geometría ───────────────────────────────────────────────────
    def route_geometry(self, route_id: str) -> list[list[float]]:
        self.load_shapes()
        shape_id = self.route_shape.get(route_id)
        if shape_id and shape_id in self.shapes:
            return self.shapes[shape_id]
        return self._geometry_from_stops(route_id)

    def _geometry_from_stops(self, route_id: str) -> list[list[float]]:
        pts = []
        for sid in self.route_stops.get(route_id, []):
            stop = self.stops.get(sid)
            if stop:
                pts.append([stop["lat"], stop["lon"]])
        return pts

    # ── consultas de rutas (con filtro troncal) ─────────────────────
    def routes_serving_stop(self, stop_id: str, trunk_only: bool = False) -> list[str]:
        self.load_core()
        routes = self.stop_routes.get(stop_id, set())
        if trunk_only:
            return [r for r in routes if self.trunk.is_trunk(r)]
        return list(routes)

    def routes_connecting(
        self, stop_a: str, stop_b: str, trunk_only: bool = False
    ) -> list[str]:
        """Rutas que pasan por A y luego por B (en ese orden)."""
        self.load_core()
        ra = self.stop_routes.get(stop_a, set())
        rb = self.stop_routes.get(stop_b, set())
        direct = ra & rb
        result = []
        for rid in direct:
            if trunk_only and not self.trunk.is_trunk(rid):
                continue
            seq = self.route_stops.get(rid, [])
            if stop_a in seq and stop_b in seq:
                ia, ib = seq.index(stop_a), seq.index(stop_b)
                if ia < ib:
                    result.append(rid)
        return result

    def stop_sequence_segment(
        self, route_id: str, from_stop: str, to_stop: str
    ) -> list[str]:
        seq = self.route_stops.get(route_id, [])
        if from_stop not in seq or to_stop not in seq:
            return []
        i, j = seq.index(from_stop), seq.index(to_stop)
        if i >= j:
            return []
        return seq[i : j + 1]

    def segment_travel_min(self, stop_ids: list[str]) -> float:
        if len(stop_ids) < 2:
            return 0.0
        dist = 0.0
        for a, b in zip(stop_ids[:-1], stop_ids[1:]):
            sa, sb = self.stops[a], self.stops[b]
            dist += _haversine(sa["lat"], sa["lon"], sb["lat"], sb["lon"])
        return max(dist / TM_COMMERCIAL_SPEED_M_PER_MIN, 1.0)

    # ── grafo-mapa troncal (estilo image-5.jpg) ─────────────────────
    def build_trunk_network(self) -> dict[str, dict]:
        """
        Construye el grafo completo de la red troncal.
        """
        self.load_shapes()
        nodes: dict[str, dict] = {}
        adjacency: dict[str, dict] = defaultdict(dict)
        lines: list[dict] = []

        for rid in self.trunk_route_ids:
            seq = self.route_stops.get(rid, [])
            if len(seq) < 2:
                continue
            tr = self.trunk.get(rid)
            color = self.trunk.color(rid)

            for sid in seq:
                stop = self.stops.get(sid)
                if stop and sid not in nodes:
                    nodes[sid] = {
                        "id": sid,
                        "name": stop["name"],
                        "lat": stop["lat"],
                        "lon": stop["lon"],
                    }

            for a, b in zip(seq[:-1], seq[1:]):
                if a not in self.stops or b not in self.stops:
                    continue
                sa, sb = self.stops[a], self.stops[b]
                cost = max(
                    _haversine(sa["lat"], sa["lon"], sb["lat"], sb["lon"])
                    / TM_COMMERCIAL_SPEED_M_PER_MIN,
                    1.0,
                )
                # Conservamos la arista de menor costo si hay varias rutas.
                prev = adjacency[a].get(b)
                if prev is None or cost < prev["cost_min"]:
                    adjacency[a][b] = {
                        "route_id": rid,
                        "cost_min": round(cost, 2),
                        "color": color,
                    }

            lines.append({
                "route_id": rid,
                "short_name": tr.short_name if tr else rid,
                "color": color,
                "stop_sequence": seq,
                "geometry": self.route_geometry(rid),
            })

        return {
            "nodes": nodes,
            "adjacency": {k: dict(v) for k, v in adjacency.items()},
            "lines": lines,
            "stats": {
                "trunk_routes": len(lines),
                "stations": len(nodes),
                "edges": sum(len(v) for v in adjacency.values()),
            },
        }


@lru_cache(maxsize=1)
def get_gtfs() -> GTFSBundle:
    bundle = GTFSBundle(GTFS_DIR)
    bundle.load_core()
    return bundle


# ── hormigas = buses circulando (simulación de tráfico TM) ──────────
def make_ants(route_id: str, count: int = ANTS_PER_ROUTE) -> list[dict]:
    """Buses distribuidos uniformemente sobre una ruta para simulación periódica."""
    return [
        {
            "id": f"{route_id}-bus-{i}",
            "index": i,
            "offset": round(i / count, 4),
            "progress": round(i / count, 4),
        }
        for i in range(count)
    ]


def point_at_progress(
    geometry: list[list[float]], progress: float
) -> list[float] | None:
    if not geometry:
        return None
    if len(geometry) == 1:
        return geometry[0]
    idx = min(int(progress * (len(geometry) - 1)), len(geometry) - 1)
    return geometry[idx]
