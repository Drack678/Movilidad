"""Comparación de algoritmos de ruteo.

Ejecuta varios algoritmos sobre el mismo par origen/destino y modo, y compara
tiempo de ejecución, distancia, tiempo de viaje, costo y calidad relativa de la
solución (qué tan cerca está cada uno del mejor costo encontrado).
"""

from __future__ import annotations

import networkx as nx

from app.algorithms import get_algorithm
from app.algorithms.aco import ACOConfig, AntColonyOptimizer
from app.graph.cost_models import edge_weights_for_mode
from app.graph.road_graph import RoadGraph, haversine_m
from app.models.enums import AlgorithmName, TransportMode
from app.models.graph_types import RouteResult


def _find_connected_nodes(graph: RoadGraph, origin: int, dest: int) -> tuple[int, int]:
    """Encuentra nodos conectados si origin y dest no lo están.

    Si hay un camino entre origin y dest, los devuelve tal cual.
    Si no, busca el par de nodos (u, v) más cercanos a (origin, dest) respectivamente
    que tengan un camino entre sí.
    """
    print(f"Origen: {origin}, Destino: {dest}")
    print(f"Nodos: {graph.n_nodes}, Aristas: {graph.n_edges}")

    # Primero verificar si ya hay un camino
    try:
        has_path = nx.has_path(graph.g, origin, dest)
        print(f"Existe ruta directa: {has_path}")
        if has_path:
            return origin, dest
    except (nx.NodeNotFound, nx.NetworkXNoPath):
        print("Nodo no encontrado o sin ruta directa")

    # Si no hay camino, buscar los nodos más cercanos en la misma componente
    all_nodes = list(graph.g.nodes())
    # Precalcular coordenadas de todos los nodos
    node_coords = {
        nid: (float(graph.g.nodes[nid]["y"]), float(graph.g.nodes[nid]["x"]))
        for nid in all_nodes
    }

    best_u = origin
    best_v = dest
    best_total_dist = float("inf")

    # Buscar el par de nodos con la menor distancia combinada
    for u_candidate in all_nodes:
        u_lat, u_lon = node_coords[u_candidate]
        dist_u = haversine_m(node_coords[origin][0], node_coords[origin][1], u_lat, u_lon)
        for v_candidate in all_nodes:
            try:
                if nx.has_path(graph.g, u_candidate, v_candidate):
                    v_lat, v_lon = node_coords[v_candidate]
                    dist_v = haversine_m(node_coords[dest][0], node_coords[dest][1], v_lat, v_lon)
                    total_dist = dist_u + dist_v
                    if total_dist < best_total_dist:
                        best_total_dist = total_dist
                        best_u = u_candidate
                        best_v = v_candidate
            except:
                continue

    print(f"Usando nodos conectados: {best_u} -> {best_v}")
    return best_u, best_v


def run_single(
    graph: RoadGraph,
    origin: int,
    dest: int,
    mode: TransportMode,
    algorithm: AlgorithmName,
    aco_config: ACOConfig | None = None,
) -> RouteResult:
    """Ejecuta un único algoritmo y devuelve su resultado, con fallback a otros algoritmos."""
    # Orden de fallback: ACO → A* → Dijkstra
    fallback_order = [algorithm, AlgorithmName.ASTAR, AlgorithmName.DIJKSTRA]
    # Eliminar duplicados manteniendo el orden
    fallback_order = list(dict.fromkeys(fallback_order))

    edges = list(graph.edges())
    costs = edge_weights_for_mode(edges, mode)

    # Asegurar que origin y dest estén conectados
    origin, dest = _find_connected_nodes(graph, origin, dest)

    for algo in fallback_order:
        try:
            print(f"Intentando algoritmo: {algo}")
            if algo == AlgorithmName.ACO:
                solver = AntColonyOptimizer(graph, costs, aco_config or ACOConfig())
            else:
                solver = get_algorithm(algo)(graph, costs)
            result = solver.solve(origin, dest, mode)
            if result.found:
                print(f"Algoritmo {algo} encontró una ruta!")
                return result
            else:
                print(f"Algoritmo {algo} no encontró ruta")
        except Exception as e:
            print(f"Error con algoritmo {algo}: {e}")
            continue

    # Si ninguno funciona, devolver un resultado vacío
    return RouteResult(
        algorithm=algorithm,
        mode=mode,
        found=False,
        node_path=[],
        coordinates=[],
        total_distance_m=0.0,
        total_time_s=0.0,
        total_cost=0.0,
        runtime_ms=0.0,
        iterations=0,
        meta={},
    )


def compare_algorithms(
    graph: RoadGraph,
    origin: int,
    dest: int,
    mode: TransportMode,
    algorithms: list[AlgorithmName] | None = None,
    aco_config: ACOConfig | None = None,
) -> dict[AlgorithmName, RouteResult]:
    """Ejecuta varios algoritmos y devuelve sus resultados indexados por nombre.

    Args:
        graph: Grafo vial.
        origin: Nodo origen.
        dest: Nodo destino.
        mode: Modo de transporte (define los costos de arista).
        algorithms: Lista de algoritmos a comparar. Por defecto: ACO, Dijkstra, A*.
        aco_config: Configuración opcional del ACO.

    Returns:
        Diccionario ``algoritmo -> RouteResult``.
    """
    if algorithms is None:
        algorithms = [AlgorithmName.ACO, AlgorithmName.DIJKSTRA, AlgorithmName.ASTAR]

    # Los costos solo dependen del modo, así que se calculan una sola vez.
    edges = list(graph.edges())
    costs = edge_weights_for_mode(edges, mode)

    # Asegurar que origin y dest estén conectados
    origin, dest = _find_connected_nodes(graph, origin, dest)

    results: dict[AlgorithmName, RouteResult] = {}
    for algo in algorithms:
        try:
            print(f"Comparando algoritmo: {algo}")
            if algo == AlgorithmName.ACO:
                solver = AntColonyOptimizer(graph, costs, aco_config or ACOConfig())
            else:
                solver = get_algorithm(algo)(graph, costs)
            results[algo] = solver.solve(origin, dest, mode)
        except Exception as e:
            print(f"Error comparando algoritmo {algo}: {e}")
            results[algo] = RouteResult(
                algorithm=algo,
                mode=mode,
                found=False,
                node_path=[],
                coordinates=[],
                total_distance_m=0.0,
                total_time_s=0.0,
                total_cost=0.0,
                runtime_ms=0.0,
                iterations=0,
                meta={},
            )
    return results


def best_by_cost(results: dict[AlgorithmName, RouteResult]) -> AlgorithmName | None:
    """Devuelve el algoritmo con menor costo total entre los que hallaron ruta."""
    found = {a: r for a, r in results.items() if r.found}
    if not found:
        return None
    return min(found, key=lambda a: found[a].total_cost)
