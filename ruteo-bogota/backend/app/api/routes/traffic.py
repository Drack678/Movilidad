"""Endpoints del motor de simulación de tráfico y mapa de calor."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.state import AppState, get_state
from app.models.enums import TrafficLevel
from app.models.schemas import IncidentRequest, TrafficEdge, TrafficGenerateRequest

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.post("/generate")
def generate_traffic(
    req: TrafficGenerateRequest, state: AppState = Depends(get_state)
) -> dict:
    """Regenera el estado de tráfico según la estrategia indicada.

    Estrategias: ``random``, ``time_of_day`` (con ``hour``), ``rush_hour``.
    """
    assert state.traffic is not None
    if req.seed is not None:
        state.traffic = type(state.traffic)(state.graph, seed=req.seed)  # type: ignore[arg-type]
    state.traffic.generate(strategy=req.strategy, hour=req.hour)
    return {
        "strategy": req.strategy,
        "hour": req.hour,
        "distribution": state.traffic.distribution(),
    }


@router.post("/incident")
def add_incident(
    req: IncidentRequest, state: AppState = Depends(get_state)
) -> dict:
    """Simula un accidente o un cierre de vía sobre una arista ``(u, v)``."""
    assert state.traffic is not None
    if req.kind == "closure":
        state.traffic.simulate_closure(req.edge_u, req.edge_v)
    else:
        state.traffic.simulate_accident(req.edge_u, req.edge_v)
    return {"kind": req.kind, "edge": [req.edge_u, req.edge_v], "applied": True}


@router.get("/heatmap", response_model=list[TrafficEdge])
def heatmap(
    limit: int = 2000, state: AppState = Depends(get_state)
) -> list[TrafficEdge]:
    """Devuelve el estado de tráfico por arista para el mapa de calor.

    Cada elemento incluye las coordenadas de la vía, su nivel y el color
    asociado (verde → amarillo → naranja → rojo → vinotinto).
    """
    assert state.graph is not None
    out: list[TrafficEdge] = []
    for i, edge in enumerate(state.graph.edges()):
        if i >= limit:
            break
        level = edge.traffic
        u_node = state.graph.node(edge.u)
        v_node = state.graph.node(edge.v)
        out.append(
            TrafficEdge(
                u=edge.u,
                v=edge.v,
                coordinates=[(u_node.lat, u_node.lon), (v_node.lat, v_node.lon)],
                level=level,
                color=level.color,
                name=edge.name,
            )
        )
    return out


@router.get("/levels")
def traffic_levels() -> list[dict]:
    """Devuelve la leyenda de niveles de tráfico con sus colores."""
    return [
        {"level": lv.value, "label": lv.label_es, "color": lv.color}
        for lv in TrafficLevel
    ]
