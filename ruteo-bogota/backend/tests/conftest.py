"""Fixtures compartidas para los tests.

Provee un grafo pequeño y determinístico (independiente de OSMnx y del grafo
representativo grande) sobre el que se prueban los algoritmos y el tráfico.
"""

from __future__ import annotations

import networkx as nx
import pytest

from app.graph.road_graph import RoadGraph, haversine_m


def _add_edge(g: nx.DiGraph, u: int, v: int, highway: str, speed: float) -> None:
    """Añade una arista dirigida con longitud y tiempo base calculados."""
    uy, ux = g.nodes[u]["y"], g.nodes[u]["x"]
    vy, vx = g.nodes[v]["y"], g.nodes[v]["x"]
    length = haversine_m(uy, ux, vy, vx)
    g.add_edge(
        u,
        v,
        length=length,
        highway=highway,
        speed_kph=speed,
        base_time_s=length / (speed * 1000.0 / 3600.0),
        traffic=0,
        name=f"{highway}-{u}-{v}",
    )


@pytest.fixture
def small_graph() -> RoadGraph:
    """Grafo de 5 nodos con un camino directo y un desvío más largo.

    Topología (costos por longitud):
        0 -> 1 -> 4   (camino corto)
        0 -> 2 -> 3 -> 4   (desvío más largo)

    Permite verificar que los algoritmos exactos eligen el camino corto.
    """
    g = nx.DiGraph()
    coords = {
        0: (4.60, -74.10),
        1: (4.61, -74.09),
        2: (4.59, -74.11),
        3: (4.60, -74.12),
        4: (4.62, -74.08),
    }
    for nid, (lat, lon) in coords.items():
        g.add_node(nid, x=lon, y=lat)

    # Camino corto.
    _add_edge(g, 0, 1, "primary", 60)
    _add_edge(g, 1, 4, "primary", 60)
    # Desvío más largo.
    _add_edge(g, 0, 2, "residential", 30)
    _add_edge(g, 2, 3, "residential", 30)
    _add_edge(g, 3, 4, "residential", 30)
    return RoadGraph(g)
