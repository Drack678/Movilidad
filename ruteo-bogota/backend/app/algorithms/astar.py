"""Algoritmo A* (A-estrella) con heurística geográfica.

Variante informada de Dijkstra: usa una heurística admisible para guiar la
búsqueda hacia el destino y explorar menos nodos. La heurística es el tiempo
mínimo teórico para cubrir en línea recta (Haversine) la distancia al destino a
la velocidad máxima del grafo, lo que NUNCA sobreestima el costo real
(admisibilidad) y por tanto preserva la optimalidad.
"""

from __future__ import annotations

import heapq

from app.algorithms.base import RouteAlgorithm
from app.graph.road_graph import RoadGraph, haversine_m
from app.models.enums import AlgorithmName, TransportMode
from app.models.graph_types import RouteResult


class AStar(RouteAlgorithm):
    """Búsqueda de camino mínimo con A* y heurística de distancia/tiempo."""

    name = AlgorithmName.ASTAR

    def __init__(self, graph: RoadGraph, costs: dict[tuple[int, int], float]) -> None:
        super().__init__(graph, costs)
        # Velocidad máxima del grafo (m/s) para una heurística admisible:
        # el menor tiempo posible es distancia_recta / velocidad_máxima.
        max_kph = 1.0
        for _, _, d in graph.g.edges(data=True):
            max_kph = max(max_kph, float(d.get("speed_kph", 1.0)))
        self._max_mps = max_kph * 1000.0 / 3600.0

    def _heuristic(self, node: int, dest: int) -> float:
        """Estima el costo restante de ``node`` al destino (admisible)."""
        n = self.graph.node(node)
        d = self.graph.node(dest)
        straight_m = haversine_m(n.lat, n.lon, d.lat, d.lon)
        return straight_m / self._max_mps  # tiempo mínimo teórico (segundos)

    def solve(self, origin: int, dest: int, mode: TransportMode) -> RouteResult:
        """Calcula el camino de costo mínimo guiando la búsqueda con la heurística."""
        start = self._now_ms()

        g_score: dict[int, float] = {origin: 0.0}  # costo real desde el origen
        prev: dict[int, int] = {}
        # Cola por f = g + h (costo estimado total del camino que pasa por el nodo).
        heap: list[tuple[float, int]] = [(self._heuristic(origin, dest), origin)]
        visited: set[int] = set()

        while heap:
            _, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            if u == dest:
                break

            for v in self.graph.neighbors(u):
                if v in visited:
                    continue
                w = self.costs.get((u, v))
                if w is None:
                    continue
                tentative = g_score[u] + w
                if tentative < g_score.get(v, float("inf")):
                    g_score[v] = tentative
                    prev[v] = u
                    f = tentative + self._heuristic(v, dest)
                    heapq.heappush(heap, (f, v))

        path = self._reconstruct(prev, origin, dest)
        runtime = self._now_ms() - start
        return self._build_result(
            path, mode, runtime, meta={"visited_nodes": len(visited)}
        )

    @staticmethod
    def _reconstruct(prev: dict[int, int], origin: int, dest: int) -> list[int]:
        """Reconstruye el camino origen→destino desde los predecesores."""
        if dest != origin and dest not in prev:
            return []
        path = [dest]
        node = dest
        while node != origin:
            node = prev[node]
            path.append(node)
        path.reverse()
        return path
