"""Endpoints que exponen la topología del grafo vial.

Útil para el frontend: permite mapear los identificadores de nodo (usados por
los algoritmos y por el historial de iteraciones del ACO) a coordenadas
geográficas para poder dibujarlos sobre el mapa.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.state import AppState, get_state

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/nodes")
def graph_nodes(state: AppState = Depends(get_state)) -> dict:
    """Devuelve un mapa compacto ``{id: [lat, lon]}`` de todos los nodos.

    El frontend lo usa para traducir los caminos de nodos (por ejemplo el
    ``best_path`` y las ``explored_edges`` del historial del ACO) a polilíneas
    geográficas que se pintan sobre el mapa de Leaflet.
    """
    assert state.graph is not None
    graph = state.graph
    nodes: dict[int, list[float]] = {}
    for nid, data in graph.g.nodes(data=True):
        nodes[int(nid)] = [float(data["y"]), float(data["x"])]
    return {"count": len(nodes), "nodes": nodes}
