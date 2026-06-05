"""Genera un grafo vial REPRESENTATIVO de Bogotá (sin OSMnx).

Crea una malla de calles sobre el área urbana aproximada de Bogotá, con:

- una cuadrícula de calles locales (residenciales),
- algunas "avenidas" (vías primarias/secundarias) en filas y columnas
  seleccionadas, con mayor velocidad,
- aristas en ambos sentidos (grafo dirigido),
- nombres y tipos de vía plausibles.

El resultado se guarda en ``data/bogota_graph.json`` y permite ejecutar la API,
los algoritmos y los tests sin descargar la red real de OpenStreetMap.

Uso:
    python -m scripts.generate_sample_graph
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permitir ejecutar el script directamente (añade backend/ al path).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.graph.road_graph import RoadGraph, haversine_m  # noqa: E402

# Área urbana aproximada de Bogotá (bounding box).
LAT_MIN, LAT_MAX = 4.50, 4.78
LON_MIN, LON_MAX = -74.18, -74.02

# Tamaño de la cuadrícula (filas x columnas de intersecciones).
ROWS = 28
COLS = 18


def _node_id(r: int, c: int) -> int:
    """ID determinístico para la intersección en (fila, columna)."""
    return r * COLS + c


def _highway_for(r: int, c: int) -> tuple[str, float]:
    """Asigna tipo de vía y velocidad (km/h) a una arista de la malla.

    Cada 6 filas/columnas se traza una "avenida" más rápida; algunas filas son
    ciclorrutas para que el modo bicicleta tenga rutas preferentes.
    """
    if r % 6 == 0:
        return "primary", 60.0
    if c % 6 == 0:
        return "secondary", 50.0
    if r % 5 == 0:
        return "cycleway", 18.0
    return "residential", 30.0


def build_sample_graph() -> RoadGraph:
    """Construye el grafo representativo de Bogotá como :class:`RoadGraph`."""
    g = nx.DiGraph()

    # Crear nodos en una malla regular sobre el bounding box.
    lat_step = (LAT_MAX - LAT_MIN) / (ROWS - 1)
    lon_step = (LON_MAX - LON_MIN) / (COLS - 1)
    for r in range(ROWS):
        for c in range(COLS):
            lat = LAT_MIN + r * lat_step
            lon = LON_MIN + c * lon_step
            g.add_node(_node_id(r, c), x=lon, y=lat)

    def add_edge(a: int, b: int, highway: str, speed: float) -> None:
        """Añade una arista dirigida con longitud y tiempo base calculados."""
        ay, ax = g.nodes[a]["y"], g.nodes[a]["x"]
        by, bx = g.nodes[b]["y"], g.nodes[b]["x"]
        length = haversine_m(ay, ax, by, bx)
        base_time = length / (speed * 1000.0 / 3600.0)
        names = {
            "primary": "Avenida principal",
            "secondary": "Avenida",
            "cycleway": "Ciclorruta",
            "residential": "Calle",
        }
        g.add_edge(
            a,
            b,
            length=length,
            highway=highway,
            speed_kph=speed,
            base_time_s=base_time,
            traffic=0,
            name=names.get(highway, "Vía"),
        )

    # Conectar cada intersección con sus vecinas (este-oeste y norte-sur), en
    # ambos sentidos, para obtener un grafo dirigido transitable.
    for r in range(ROWS):
        for c in range(COLS):
            here = _node_id(r, c)
            if c + 1 < COLS:
                right = _node_id(r, c + 1)
                hw, sp = _highway_for(r, c)
                add_edge(here, right, hw, sp)
                add_edge(right, here, hw, sp)
            if r + 1 < ROWS:
                down = _node_id(r + 1, c)
                hw, sp = _highway_for(r, c)
                add_edge(here, down, hw, sp)
                add_edge(down, here, hw, sp)

    return RoadGraph(g)


def main() -> None:
    """Genera y guarda el grafo representativo en disco."""
    settings = get_settings()
    graph = build_sample_graph()
    graph.save_json(settings.fallback_graph_path)
    print(
        f"Grafo representativo de Bogotá generado: {graph.n_nodes} nodos, "
        f"{graph.n_edges} aristas -> {settings.fallback_graph_path}"
    )


if __name__ == "__main__":
    main()
