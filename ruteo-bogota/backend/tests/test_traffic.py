"""Tests del motor de simulación de tráfico."""

from __future__ import annotations

from app.graph.road_graph import RoadGraph
from app.models.enums import TrafficLevel
from app.traffic.engine import TrafficEngine


def test_generate_random_sets_levels(small_graph: RoadGraph) -> None:
    """Tras generar tráfico aleatorio, todas las aristas tienen un nivel válido."""
    engine = TrafficEngine(small_graph, seed=1)
    engine.generate_random()
    for e in small_graph.edges():
        assert 0 <= e.traffic.value <= 4


def test_rush_hour_congests_arterials(small_graph: RoadGraph) -> None:
    """En hora pico, las vías primarias deben quedar muy congestionadas."""
    engine = TrafficEngine(small_graph, seed=1)
    engine.generate_rush_hour()
    primaries = [e for e in small_graph.edges() if e.highway == "primary"]
    assert primaries
    assert all(e.traffic == TrafficLevel.VERY_HIGH for e in primaries)


def test_closure_marks_edge_critical(small_graph: RoadGraph) -> None:
    """Un cierre debe poner la vía en nivel crítico y registrarla como cerrada."""
    engine = TrafficEngine(small_graph, seed=1)
    engine.simulate_closure(0, 1)
    assert (0, 1) in engine.closed_edges
    assert small_graph.edge(0, 1).traffic == TrafficLevel.VERY_HIGH


def test_closure_persists_after_regeneration(small_graph: RoadGraph) -> None:
    """Una vía cerrada debe seguir cerrada tras regenerar el tráfico global."""
    engine = TrafficEngine(small_graph, seed=1)
    engine.simulate_closure(0, 1)
    engine.generate_time_of_day(3)  # madrugada: poco tráfico
    assert small_graph.edge(0, 1).traffic == TrafficLevel.VERY_HIGH


def test_traffic_affects_travel_time(small_graph: RoadGraph) -> None:
    """Más tráfico debe aumentar el tiempo de recorrido de la arista."""
    edge = small_graph.edge(0, 1)
    free_time = edge.current_time_s
    small_graph.set_edge_traffic(0, 1, TrafficLevel.VERY_HIGH)
    congested_time = small_graph.edge(0, 1).current_time_s
    assert congested_time > free_time


def test_distribution_counts_all_edges(small_graph: RoadGraph) -> None:
    """La distribución de niveles debe sumar el total de aristas."""
    engine = TrafficEngine(small_graph, seed=2)
    engine.generate_time_of_day(8)
    total = sum(engine.distribution().values())
    assert total == small_graph.n_edges
