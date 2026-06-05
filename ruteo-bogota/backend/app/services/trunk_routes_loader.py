"""
Whitelist de rutas troncales TransMilenio.

Carga `RutasDeTransmilenio.txt` (alias `trunk_routes.txt`) y expone el conjunto
de `route_id` que el sistema considera "rutas TransMilenio válidas".
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# Ubicación por defecto del archivo de whitelist dentro del bundle GTFS.
TRUNK_FILE_CANDIDATES = ("trunk_routes.txt", "RutasDeTransmilenio.txt")
BASE_DIR = Path(__file__).resolve().parents[2]
GTFS_DIR = BASE_DIR / "data" / "gtfs"


@dataclass
class TrunkRoute:
    """Una ruta troncal de la whitelist."""

    route_id: str
    short_name: str          # servicio comercial: G45, B10, etc.
    headsign: str            # destino mostrado
    color: str               # hex sin '#', p.ej. 'ff0000'
    text_color: str          # hex sin '#', p.ej. 'ffffff'
    trunk_type: str          # '1' troncal normal, '6' especial/dual
    agency_type: str = "3"   # route_type GTFS (3 = bus)

    @property
    def hex_color(self) -> str:
        return f"#{self.color}"

    @property
    def label(self) -> str:
        return self.short_name or self.route_id


@dataclass
class TrunkRegistry:
    """Índice en memoria de la whitelist troncal."""

    directory: Path = field(default_factory=lambda: GTFS_DIR)
    by_id: dict[str, TrunkRoute] = field(default_factory=dict)
    # Un route_id puede aparecer varias veces (varios servicios comerciales).
    services_by_route: dict[str, set[str]] = field(default_factory=dict)
    _loaded: bool = False

    # ── localización del archivo ────────────────────────────────────
    def _resolve_file(self) -> Path:
        for name in TRUNK_FILE_CANDIDATES:
            p = self.directory / name
            if p.exists():
                return p
        raise FileNotFoundError(
            f"No se encontró la whitelist troncal en {self.directory} "
            f"(buscado: {', '.join(TRUNK_FILE_CANDIDATES)})"
        )

    # ── carga ───────────────────────────────────────────────────────
    def load(self) -> "TrunkRegistry":
        if self._loaded:
            return self

        path = self._resolve_file()
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 5:
                    continue
                trunk_type = row[0].strip()
                color = (row[1] or "ff0000").strip()
                route_id = row[2].strip()
                headsign = row[3].strip()
                short_name = row[4].strip()
                text_color = (row[5].strip() if len(row) > 5 else "ffffff") or "ffffff"
                agency_type = row[6].strip() if len(row) > 6 else "3"

                if not route_id:
                    continue

                self.services_by_route.setdefault(route_id, set())
                if short_name:
                    self.services_by_route[route_id].add(short_name)

                # Conservamos la primera definición como representativa, pero
                # priorizamos una con short_name no numérico (servicio real).
                existing = self.by_id.get(route_id)
                if existing is None or (
                    not existing.short_name.isalpha() and short_name and not short_name.isdigit()
                ):
                    self.by_id[route_id] = TrunkRoute(
                        route_id=route_id,
                        short_name=short_name,
                        headsign=headsign,
                        color=color,
                        text_color=text_color,
                        trunk_type=trunk_type,
                        agency_type=agency_type,
                    )

        self._loaded = True
        return self

    # ── API de consulta ─────────────────────────────────────────────
    @property
    def route_ids(self) -> frozenset[str]:
        self.load()
        return frozenset(self.by_id.keys())

    def is_trunk(self, route_id: str) -> bool:
        """True si el route_id pertenece a la whitelist troncal."""
        self.load()
        return route_id in self.by_id

    def get(self, route_id: str) -> TrunkRoute | None:
        self.load()
        return self.by_id.get(route_id)

    def color(self, route_id: str, default: str = "#e11d48") -> str:
        r = self.get(route_id)
        return r.hex_color if r else default

    def services(self, route_id: str) -> list[str]:
        self.load()
        return sorted(self.services_by_route.get(route_id, set()))

    def __len__(self) -> int:
        self.load()
        return len(self.by_id)


@lru_cache(maxsize=1)
def get_trunk_registry() -> TrunkRegistry:
    """Singleton del registro de rutas troncales."""
    registry = TrunkRegistry(directory=GTFS_DIR)
    registry.load()
    return registry
