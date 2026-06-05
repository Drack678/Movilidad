"""Endpoints de cálculo y comparación de rutas."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.algorithms.aco import ACOConfig, AntColonyOptimizer
from app.algorithms.comparison import best_by_cost, compare_algorithms, run_single, _find_connected_nodes
from app.api.state import AppState, get_state
from app.graph.cost_models import edge_weights_for_mode
from app.models.enums import AlgorithmName, TransportMode
from app.models.graph_types import RouteResult
from app.models.schemas import (
    ACOParams,
    AlgorithmComparison,
    CompareResponse,
    RouteRequest,
    RouteResponse,
)

router = APIRouter(prefix="/route", tags=["routing"])


def _aco_config(params: ACOParams | None, record_history: bool = False) -> ACOConfig:
    """Convierte los parámetros de la API en una :class:`ACOConfig`."""
    if params is None:
        return ACOConfig(record_history=record_history)
    return ACOConfig(
        alpha=params.alpha,
        beta=params.beta,
        rho=params.rho,
        q=params.q,
        n_ants=params.n_ants,
        n_iterations=params.n_iterations,
        seed=params.seed,
        record_history=record_history,
    )


def _to_response(result: RouteResult) -> RouteResponse:
    """Convierte un :class:`RouteResult` interno en el esquema de respuesta."""
    return RouteResponse(
        algorithm=result.algorithm,
        mode=result.mode,
        found=result.found,
        node_path=result.node_path,
        coordinates=result.coordinates,
        total_distance_m=result.total_distance_m,
        total_time_s=result.total_time_s,
        total_cost=result.total_cost,
        runtime_ms=result.runtime_ms,
        iterations=result.iterations,
        meta=result.meta,
    )


def _resolve_endpoints(
    state: AppState, req: RouteRequest
) -> tuple[int, int]:
    """Traduce coordenadas de origen/destino a los nodos más cercanos del grafo."""
    assert state.graph is not None
    origin = state.graph.nearest_node(req.origin_lat, req.origin_lon)
    dest = state.graph.nearest_node(req.dest_lat, req.dest_lon)
    return origin, dest


@router.post("", response_model=RouteResponse)
def calculate_route(
    req: RouteRequest, state: AppState = Depends(get_state)
) -> RouteResponse:
    """Calcula una ruta entre origen y destino con el algoritmo elegido."""
    assert state.graph is not None
    origin, dest = _resolve_endpoints(state, req)
    result = run_single(
        state.graph, origin, dest, req.mode, req.algorithm, _aco_config(req.aco_params)
    )
    return _to_response(result)


@router.post("/compare", response_model=CompareResponse)
def compare(
    req: RouteRequest, state: AppState = Depends(get_state)
) -> CompareResponse:
    """Compara ACO, Dijkstra y A* sobre el mismo trayecto y modo."""
    assert state.graph is not None
    origin, dest = _resolve_endpoints(state, req)

    results = compare_algorithms(
        state.graph,
        origin,
        dest,
        req.mode,
        algorithms=[AlgorithmName.ACO, AlgorithmName.DIJKSTRA, AlgorithmName.ASTAR],
        aco_config=_aco_config(req.aco_params),
    )

    best = best_by_cost(results)

    # Si no hay mejor, usar el primer algoritmo que tenga found
    if best is None:
        for algo in [AlgorithmName.ACO, AlgorithmName.DIJKSTRA, AlgorithmName.ASTAR]:
            if results[algo].found:
                best = algo
                break

    # Si aún no hay nada, usar el primero
    if best is None:
        best = AlgorithmName.ACO

    best_cost = results[best].total_cost if results[best].found else 1.0
    comparisons = [
        AlgorithmComparison(
            algorithm=algo,
            found=r.found,
            total_distance_m=r.total_distance_m,
            total_time_s=r.total_time_s,
            total_cost=r.total_cost,
            runtime_ms=r.runtime_ms,
            iterations=r.iterations,
            quality_ratio=(r.total_cost / best_cost) if (r.found and best_cost > 0) else 0.0,
        )
        for algo, r in results.items()
    ]

    return CompareResponse(
        mode=req.mode,
        best_algorithm=best,
        results=comparisons,
        best_route=_to_response(results[best]),
    )


@router.post("/aco/steps", response_model=RouteResponse)
def aco_with_history(
    req: RouteRequest, state: AppState = Depends(get_state)
) -> RouteResponse:
    """Ejecuta el ACO registrando el historial iteración por iteración.

    El historial (en ``meta.history``) alimenta la visualización educativa del
    frontend: aristas exploradas, mejor costo y mejor camino por iteración.
    """
    assert state.graph is not None
    origin, dest = _resolve_endpoints(state, req)

    # Asegurar que origin y dest están conectados
    origin, dest = _find_connected_nodes(state.graph, origin, dest)

    edges = list(state.graph.edges())
    costs = edge_weights_for_mode(edges, req.mode)

    # Intentar ACO primero, si falla, usar A*
    try:
        solver = AntColonyOptimizer(state.graph, costs, _aco_config(req.aco_params, record_history=True))
        result = solver.solve(origin, dest, req.mode)
        if result.found:
            return _to_response(result)
    except Exception as e:
        print(f"Error en ACO con historial: {e}")

    # Fallback a A*
    from app.algorithms.astar import AStar
    solver = AStar(state.graph, costs)
    result = solver.solve(origin, dest, req.mode)
    return _to_response(result)
