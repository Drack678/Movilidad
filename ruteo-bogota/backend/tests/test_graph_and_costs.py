"""Tests del grafo vial, costos por modo y persistencia JSON."""

from __future__ import annotations

from pathlib import Path

from app.graph.cost_models import edge_cost
from app.graph.road_graph import RoadGraph, haversine_m
from app.models.enums import TransportMode


def test_haversine_known_distance() -> None:
    """La distancia entre dos puntos a ~1 grado de latitud es ~111 km."""
    d = haversine_m(0.0, 0.0, 1.0, 0.0)
    assert 110_000 < d < 112_000


def test_nearest_node(small_graph: RoadGraph) -> None:
    """nearest_node debe devolver el nodo más próximo a una coordenada."""
    # Coordenada casi idéntica al nodo 0.
    nid = small_graph.nearest_node(4.601, -74.101)
    assert nid == 0


def test_car_cost_increases_with_traffic(small_graph: RoadGraph) -> None:
    """Para automóvil, el costo de la arista crece con el tráfico."""
    e = small_graph.edge(0, 1)
    base = edge_cost(e, TransportMode.CAR)
    small_graph.set_edge_traffic(0, 1, small_graph.edge(0, 1).traffic.VERY_HIGH)
    congested = edge_cost(small_graph.edge(0, 1), TransportMode.CAR)
    assert congested > base


def test_bike_penalizes_fast_roads(small_graph: RoadGraph) -> None:
    """La bici debe penalizar autopistas frente a vías residenciales similares."""
    fast = small_graph.edge(0, 1)  # primary
    calm = small_graph.edge(0, 2)  # residential
    # Normalizar por longitud para comparar de forma justa.
    cost_fast = edge_cost(fast, TransportMode.BIKE) / fast.length_m
    cost_calm = edge_cost(calm, TransportMode.BIKE) / calm.length_m
    assert cost_fast > cost_calm


def test_json_roundtrip(small_graph: RoadGraph, tmp_path: Path) -> None:
    """Guardar y cargar el grafo en JSON debe preservar nodos y aristas."""
    path = tmp_path / "graph.json"
    small_graph.save_json(path)
    loaded = RoadGraph.load_json(path)
    assert loaded.n_nodes == small_graph.n_nodes
    assert loaded.n_edges == small_graph.n_edges
    # Los atributos clave de una arista deben conservarse.
    orig = small_graph.edge(0, 1)
    rt = loaded.edge(0, 1)
    assert abs(orig.length_m - rt.length_m) < 1e-6
    assert orig.highway == rt.highway
