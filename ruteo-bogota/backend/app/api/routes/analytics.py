"""Endpoints de analítica del grafo y del tráfico (dashboard)."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends

from app.api.state import AppState, get_state
from app.models.enums import TrafficLevel
from app.models.schemas import GraphStats

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/stats", response_model=GraphStats)
def graph_stats(state: AppState = Depends(get_state)) -> GraphStats:
    """Estadísticas para el dashboard: nodos, aristas, tiempos y congestión."""
    assert state.graph is not None and state.traffic is not None
    graph = state.graph

    edges = list(graph.edges())
    n_edges = len(edges)
    avg_time = (sum(e.current_time_s for e in edges) / n_edges) if n_edges else 0.0

    # Vías más y menos congestionadas (por nivel de tráfico y tiempo actual).
    ranked = sorted(edges, key=lambda e: (e.traffic.value, e.current_time_s), reverse=True)
    most = [
        {
            "u": e.u,
            "v": e.v,
            "name": e.name or "(sin nombre)",
            "level": e.traffic.label_es,
            "time_s": round(e.current_time_s, 1),
        }
        for e in ranked[:10]
    ]
    least = [
        {
            "u": e.u,
            "v": e.v,
            "name": e.name or "(sin nombre)",
            "level": e.traffic.label_es,
            "time_s": round(e.current_time_s, 1),
        }
        for e in ranked[-10:]
    ]

    return GraphStats(
        n_nodes=graph.n_nodes,
        n_edges=n_edges,
        avg_travel_time_s=round(avg_time, 2),
        most_congested=most,
        least_congested=least,
        traffic_distribution=state.traffic.distribution(),
    )


@router.get("/by-hour")
def stats_by_hour(state: AppState = Depends(get_state)) -> list[dict]:
    """Estadística simulada por hora: tiempo medio de viaje a lo largo del día.

    Regenera temporalmente el tráfico para cada hora y calcula el tiempo medio
    de recorrido por arista. Útil para los gráficos del dashboard.
    """
    assert state.graph is not None and state.traffic is not None
    edges = list(state.graph.edges())
    engine = state.traffic
    by_hour: list[dict] = []

    # Guardar el estado actual de tráfico para restaurarlo al final.
    saved = {(e.u, e.v): e.traffic.value for e in edges}

    for hour in range(24):
        engine.generate_time_of_day(hour)
        es = list(state.graph.edges())
        avg = (sum(e.current_time_s for e in es) / len(es)) if es else 0.0
        dist: dict[str, int] = defaultdict(int)
        for e in es:
            dist[e.traffic.label_es] += 1
        by_hour.append({"hour": hour, "avg_travel_time_s": round(avg, 2)})

    # Restaurar el estado de tráfico previo.
    for (u, v), lvl in saved.items():
        state.graph.set_edge_traffic(u, v, TrafficLevel(lvl))

    return by_hour
