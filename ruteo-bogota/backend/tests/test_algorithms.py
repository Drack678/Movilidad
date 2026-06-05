"""Tests de los algoritmos de ruteo."""

from __future__ import annotations

from app.algorithms.aco import ACOConfig, AntColonyOptimizer
from app.algorithms.astar import AStar
from app.algorithms.bellman_ford import BellmanFord
from app.algorithms.comparison import best_by_cost, compare_algorithms
from app.algorithms.dijkstra import Dijkstra
from app.graph.cost_models import edge_weights_for_mode
from app.graph.road_graph import RoadGraph
from app.models.enums import AlgorithmName, TransportMode


def _costs(graph: RoadGraph, mode: TransportMode = TransportMode.CAR) -> dict:
    """Atajo: costos de arista para un modo."""
    return edge_weights_for_mode(list(graph.edges()), mode)


def test_dijkstra_finds_shortest_path(small_graph: RoadGraph) -> None:
    """Dijkstra debe elegir el camino corto 0->1->4."""
    costs = _costs(small_graph)
    result = Dijkstra(small_graph, costs).solve(0, 4, TransportMode.CAR)
    assert result.found
    assert result.node_path == [0, 1, 4]


def test_astar_matches_dijkstra(small_graph: RoadGraph) -> None:
    """A* debe encontrar el mismo costo óptimo que Dijkstra."""
    costs = _costs(small_graph)
    d = Dijkstra(small_graph, costs).solve(0, 4, TransportMode.CAR)
    a = AStar(small_graph, costs).solve(0, 4, TransportMode.CAR)
    assert a.found
    assert abs(a.total_cost - d.total_cost) < 1e-6


def test_bellman_ford_matches_dijkstra(small_graph: RoadGraph) -> None:
    """Bellman-Ford debe coincidir en costo con Dijkstra."""
    costs = _costs(small_graph)
    d = Dijkstra(small_graph, costs).solve(0, 4, TransportMode.CAR)
    b = BellmanFord(small_graph, costs).solve(0, 4, TransportMode.CAR)
    assert b.found
    assert abs(b.total_cost - d.total_cost) < 1e-6


def test_no_path_returns_not_found(small_graph: RoadGraph) -> None:
    """Si no hay camino, el resultado debe marcar found=False."""
    costs = _costs(small_graph)
    # El nodo 4 no tiene salidas, así que no hay ruta 4 -> 0.
    result = Dijkstra(small_graph, costs).solve(4, 0, TransportMode.CAR)
    assert not result.found


def test_aco_finds_valid_path(small_graph: RoadGraph) -> None:
    """El ACO debe encontrar un camino válido de origen a destino."""
    costs = _costs(small_graph)
    cfg = ACOConfig(n_ants=10, n_iterations=20, seed=1)
    result = AntColonyOptimizer(small_graph, costs, cfg).solve(0, 4, TransportMode.CAR)
    assert result.found
    assert result.node_path[0] == 0
    assert result.node_path[-1] == 4


def test_aco_is_deterministic_with_seed(small_graph: RoadGraph) -> None:
    """Con la misma semilla, el ACO debe ser reproducible."""
    costs = _costs(small_graph)
    cfg = ACOConfig(n_ants=10, n_iterations=15, seed=42)
    r1 = AntColonyOptimizer(small_graph, costs, cfg).solve(0, 4, TransportMode.CAR)
    r2 = AntColonyOptimizer(small_graph, costs, cfg).solve(0, 4, TransportMode.CAR)
    assert r1.node_path == r2.node_path
    assert abs(r1.total_cost - r2.total_cost) < 1e-9


def test_aco_records_history(small_graph: RoadGraph) -> None:
    """Con record_history se debe poblar meta['history'] por iteración."""
    costs = _costs(small_graph)
    cfg = ACOConfig(n_ants=5, n_iterations=8, seed=3, record_history=True)
    result = AntColonyOptimizer(small_graph, costs, cfg).solve(0, 4, TransportMode.CAR)
    assert "history" in result.meta
    assert len(result.meta["history"]) == 8
    assert result.meta["history"][0]["iteration"] == 0


def test_compare_returns_all_algorithms(small_graph: RoadGraph) -> None:
    """La comparación debe devolver resultados para los tres algoritmos."""
    results = compare_algorithms(
        small_graph,
        0,
        4,
        TransportMode.CAR,
        algorithms=[AlgorithmName.ACO, AlgorithmName.DIJKSTRA, AlgorithmName.ASTAR],
        aco_config=ACOConfig(n_ants=8, n_iterations=10, seed=1),
    )
    assert set(results) == {AlgorithmName.ACO, AlgorithmName.DIJKSTRA, AlgorithmName.ASTAR}
    best = best_by_cost(results)
    # Dijkstra/A* son óptimos, así que el mejor no puede costar más que ellos.
    assert results[best].total_cost <= results[AlgorithmName.DIJKSTRA].total_cost + 1e-6


def test_runtime_is_measured(small_graph: RoadGraph) -> None:
    """Todos los algoritmos deben reportar un tiempo de ejecución no negativo."""
    costs = _costs(small_graph)
    for solver in (Dijkstra(small_graph, costs), AStar(small_graph, costs)):
        r = solver.solve(0, 4, TransportMode.CAR)
        assert r.runtime_ms >= 0
