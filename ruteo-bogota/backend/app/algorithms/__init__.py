"""Algoritmos de optimización de rutas.

Expone una fábrica :func:`get_algorithm` que devuelve la implementación
correspondiente a un :class:`AlgorithmName`, de modo que la API y la
comparación no dependan de las clases concretas.
"""

from app.algorithms.aco import AntColonyOptimizer
from app.algorithms.astar import AStar
from app.algorithms.base import RouteAlgorithm
from app.algorithms.bellman_ford import BellmanFord
from app.algorithms.dijkstra import Dijkstra
from app.models.enums import AlgorithmName

_REGISTRY: dict[AlgorithmName, type[RouteAlgorithm]] = {
    AlgorithmName.ACO: AntColonyOptimizer,
    AlgorithmName.DIJKSTRA: Dijkstra,
    AlgorithmName.ASTAR: AStar,
    AlgorithmName.BELLMAN_FORD: BellmanFord,
}


def get_algorithm(name: AlgorithmName) -> type[RouteAlgorithm]:
    """Devuelve la clase de algoritmo asociada a ``name``."""
    return _REGISTRY[name]


__all__ = [
    "RouteAlgorithm",
    "AntColonyOptimizer",
    "Dijkstra",
    "AStar",
    "BellmanFord",
    "get_algorithm",
]
