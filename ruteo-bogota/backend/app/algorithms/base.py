"""Interfaz común de los algoritmos de ruteo.

Todos los algoritmos (ACO, Dijkstra, A*, Bellman-Ford) heredan de
:class:`RouteAlgorithm` y exponen un método ``solve`` con la misma firma, lo que
permite intercambiarlos y compararlos sin cambiar el resto del sistema.

Cada algoritmo recibe:
- el grafo vial,
- un mapa de costos por arista ``(u, v) -> costo`` (dependiente del modo),
- nodos de origen y destino,

y devuelve un :class:`RouteResult` con la ruta y sus métricas.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from app.graph.road_graph import RoadGraph
from app.models.enums import AlgorithmName, TransportMode
from app.models.graph_types import RouteResult


class RouteAlgorithm(ABC):
    """Clase base abstracta para los algoritmos de ruteo."""

    name: AlgorithmName

    def __init__(self, graph: RoadGraph, costs: dict[tuple[int, int], float]) -> None:
        """Inicializa el algoritmo.

        Args:
            graph: Grafo vial sobre el que se busca la ruta.
            costs: Costo de cada arista ``(u, v)`` según el modo de transporte.
        """
        self.graph = graph
        self.costs = costs

    @abstractmethod
    def solve(self, origin: int, dest: int, mode: TransportMode) -> RouteResult:
        """Calcula la ruta óptima de ``origin`` a ``dest``.

        Returns:
            Un :class:`RouteResult` (con ``found=False`` si no hay camino).
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Utilidades compartidas
    # ------------------------------------------------------------------ #
    def _build_result(
        self,
        path: list[int],
        mode: TransportMode,
        runtime_ms: float,
        iterations: int = 0,
        meta: dict | None = None,
    ) -> RouteResult:
        """Construye un :class:`RouteResult` a partir de un camino de nodos.

        Calcula distancia total, tiempo total (afectado por tráfico) y costo
        total recorriendo las aristas del camino.
        """
        if not path or len(path) < 2:
            return RouteResult(
                algorithm=self.name,
                mode=mode,
                node_path=path,
                coordinates=[],
                total_distance_m=0.0,
                total_time_s=0.0,
                total_cost=0.0,
                runtime_ms=runtime_ms,
                iterations=iterations,
                found=False,
                meta=meta or {},
            )

        total_distance = 0.0
        total_time = 0.0
        total_cost = 0.0
        coords: list[tuple[float, float]] = []

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self.graph.edge(u, v)
            total_distance += edge.length_m
            total_time += edge.current_time_s
            total_cost += self.costs.get((u, v), edge.current_time_s)

        for nid in path:
            node = self.graph.node(nid)
            coords.append((node.lat, node.lon))

        return RouteResult(
            algorithm=self.name,
            mode=mode,
            node_path=path,
            coordinates=coords,
            total_distance_m=total_distance,
            total_time_s=total_time,
            total_cost=total_cost,
            runtime_ms=runtime_ms,
            iterations=iterations,
            found=True,
            meta=meta or {},
        )

    @staticmethod
    def _now_ms() -> float:
        """Marca de tiempo monotónica en milisegundos."""
        return time.perf_counter() * 1000.0
