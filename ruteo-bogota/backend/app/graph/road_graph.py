"""Grafo vial dirigido de la ciudad.

:class:`RoadGraph` encapsula un ``networkx.DiGraph`` con la red vial y ofrece:

- Descarga de la red REAL desde OpenStreetMap con OSMnx (cacheada en disco).
- Carga/guardado desde un JSON representativo (para trabajar sin OSMnx).
- Búsqueda del nodo más cercano a una coordenada.
- Acceso a nodos y aristas como objetos del dominio (:class:`GraphNode`,
  :class:`GraphEdge`).

Los algoritmos de ruteo y el motor de tráfico operan sobre esta clase, no
directamente sobre OSMnx, de modo que el resto del sistema es independiente de
si los datos vienen de OSM o de un grafo sintético.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import networkx as nx

from app.models.graph_types import GraphEdge, GraphNode
from app.models.enums import TrafficLevel

# Velocidades por defecto (km/h) según el tipo de vía OSM, usadas cuando OSM no
# reporta ``maxspeed``.
_HIGHWAY_SPEED_KPH: dict[str, float] = {
    "motorway": 90,
    "motorway_link": 60,
    "trunk": 80,
    "trunk_link": 50,
    "primary": 60,
    "primary_link": 40,
    "secondary": 50,
    "secondary_link": 35,
    "tertiary": 40,
    "residential": 30,
    "living_street": 20,
    "unclassified": 30,
    "cycleway": 15,
    "footway": 5,
    "pedestrian": 5,
    "path": 10,
    "steps": 2,
}
_DEFAULT_SPEED_KPH = 30.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos coordenadas (fórmula de Haversine)."""
    r = 6_371_000.0  # radio terrestre en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class RoadGraph:
    """Red vial dirigida de la ciudad.

    Attributes:
        g: Grafo dirigido de NetworkX. Cada nodo tiene atributos ``x`` (lon),
            ``y`` (lat); cada arista tiene ``length``, ``highway``,
            ``speed_kph``, ``base_time_s``, ``traffic``, ``name``.
    """

    def __init__(self, g: nx.DiGraph | None = None) -> None:
        self.g: nx.DiGraph = g if g is not None else nx.DiGraph()
        # Asegurar que solo tengamos la componente fuertemente conexa más grande
        if self.g.number_of_nodes() > 0:
            try:
                largest_component = max(nx.strongly_connected_components(self.g), key=len)
                self.g = self.g.subgraph(largest_component).copy()
            except:
                pass

    # ------------------------------------------------------------------ #
    # Propiedades básicas
    # ------------------------------------------------------------------ #
    @property
    def n_nodes(self) -> int:
        """Número de nodos del grafo."""
        return self.g.number_of_nodes()

    @property
    def n_edges(self) -> int:
        """Número de aristas del grafo."""
        return self.g.number_of_edges()

    def has_node(self, node_id: int) -> bool:
        """Indica si el nodo existe en el grafo."""
        return self.g.has_node(node_id)

    def node(self, node_id: int) -> GraphNode:
        """Devuelve el nodo como objeto del dominio."""
        data = self.g.nodes[node_id]
        return GraphNode(id=node_id, lat=float(data["y"]), lon=float(data["x"]))

    def edge(self, u: int, v: int) -> GraphEdge:
        """Devuelve la arista ``(u, v)`` como objeto del dominio."""
        d = self.g.edges[u, v]
        return GraphEdge(
            u=u,
            v=v,
            length_m=float(d["length"]),
            highway=str(d.get("highway", "unclassified")),
            speed_kph=float(d.get("speed_kph", _DEFAULT_SPEED_KPH)),
            base_time_s=float(d["base_time_s"]),
            traffic=TrafficLevel(int(d.get("traffic", 0))),
            name=str(d.get("name", "")),
        )

    def edges(self) -> Iterable[GraphEdge]:
        """Itera todas las aristas como objetos del dominio."""
        for u, v in self.g.edges():
            yield self.edge(u, v)

    def neighbors(self, node_id: int) -> Iterable[int]:
        """Itera los sucesores (vecinos salientes) de un nodo."""
        return self.g.successors(node_id)

    def set_edge_traffic(self, u: int, v: int, level: TrafficLevel) -> None:
        """Asigna un nivel de tráfico a una arista existente."""
        self.g.edges[u, v]["traffic"] = int(level.value)

    # ------------------------------------------------------------------ #
    # Búsqueda espacial
    # ------------------------------------------------------------------ #
    def nearest_node(self, lat: float, lon: float) -> int:
        """Devuelve el ID del nodo más cercano a la coordenada dada.

        Implementa una búsqueda lineal por Haversine. Para grafos muy grandes
        conviene un índice espacial (KD-Tree); aquí se prioriza la simplicidad
        y la ausencia de dependencias extra.
        """
        best_id = -1
        best_dist = float("inf")
        for nid, data in self.g.nodes(data=True):
            d = haversine_m(lat, lon, float(data["y"]), float(data["x"]))
            if d < best_dist:
                best_dist = d
                best_id = nid
        if best_id == -1:
            raise ValueError("El grafo no tiene nodos.")
        return best_id

    # ------------------------------------------------------------------ #
    # Persistencia en JSON (formato propio, no requiere OSMnx)
    # ------------------------------------------------------------------ #
    def to_json_dict(self) -> dict:
        """Serializa el grafo a un diccionario JSON-compatible."""
        nodes = [
            {"id": nid, "lat": float(d["y"]), "lon": float(d["x"])}
            for nid, d in self.g.nodes(data=True)
        ]
        edges = [
            {
                "u": u,
                "v": v,
                "length": float(d["length"]),
                "highway": str(d.get("highway", "unclassified")),
                "speed_kph": float(d.get("speed_kph", _DEFAULT_SPEED_KPH)),
                "base_time_s": float(d["base_time_s"]),
                "traffic": int(d.get("traffic", 0)),
                "name": str(d.get("name", "")),
            }
            for u, v, d in self.g.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    def save_json(self, path: Path) -> None:
        """Guarda el grafo en un archivo JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json_dict()), encoding="utf-8")

    @classmethod
    def from_json_dict(cls, data: dict) -> "RoadGraph":
        """Reconstruye un :class:`RoadGraph` desde un diccionario JSON."""
        g = nx.DiGraph()
        for n in data["nodes"]:
            g.add_node(int(n["id"]), x=float(n["lon"]), y=float(n["lat"]))
        for e in data["edges"]:
            length = float(e["length"])
            speed = float(e.get("speed_kph", _DEFAULT_SPEED_KPH))
            base_time = e.get("base_time_s")
            if base_time is None:
                base_time = length / (speed * 1000.0 / 3600.0)
            g.add_edge(
                int(e["u"]),
                int(e["v"]),
                length=length,
                highway=str(e.get("highway", "unclassified")),
                speed_kph=speed,
                base_time_s=float(base_time),
                traffic=int(e.get("traffic", 0)),
                name=str(e.get("name", "")),
            )
        return cls(g)

    @classmethod
    def load_json(cls, path: Path) -> "RoadGraph":
        """Carga un :class:`RoadGraph` desde un archivo JSON."""
        return cls.from_json_dict(json.loads(Path(path).read_text(encoding="utf-8")))
