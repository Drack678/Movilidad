"""Modelos de dominio y esquemas de la API.

Se exponen aquí los tipos más usados para facilitar las importaciones.
"""

from app.models.enums import AlgorithmName, TrafficLevel, TransportMode
from app.models.graph_types import GraphEdge, GraphNode, RouteResult

__all__ = [
    "AlgorithmName",
    "TrafficLevel",
    "TransportMode",
    "GraphEdge",
    "GraphNode",
    "RouteResult",
]
