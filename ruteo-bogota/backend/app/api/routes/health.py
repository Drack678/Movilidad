"""Endpoints de salud y metadatos del servicio."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.state import AppState, get_state
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Comprobación simple de que el servicio responde."""
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/ready")
def ready(state: AppState = Depends(get_state)) -> dict:
    """Indica si el grafo y el tráfico ya están cargados en memoria."""
    assert state.graph is not None
    return {
        "ready": state.is_ready,
        "n_nodes": state.graph.n_nodes,
        "n_edges": state.graph.n_edges,
        "city": state.settings.city_name,
    }
