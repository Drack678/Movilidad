"""Algoritmo de Dijkstra (camino de costo mínimo).

Implementación propia con cola de prioridad (montículo binario). Encuentra el
camino de menor costo acumulado entre origen y destino sobre el grafo dirigido,
usando los costos por arista del modo de transporte seleccionado.

Sirve como referencia de OPTIMALIDAD para comparar contra el ACO: dado que los
costos son no negativos, Dijkstra garantiza el costo mínimo real.
"""

from __future__ import annotations

import heapq

from app.algorithms.base import RouteAlgorithm
from app.models.enums import AlgorithmName, TransportMode
from app.models.graph_types import RouteResult


class Dijkstra(RouteAlgorithm):
    """Camino de costo mínimo mediante el algoritmo de Dijkstra."""

    name = AlgorithmName.DIJKSTRA

    def solve(self, origin: int, dest: int, mode: TransportMode) -> RouteResult:
        """Calcula el camino de costo mínimo de ``origin`` a ``dest``."""
        start = self._now_ms()

        # Distancia (costo acumulado) mínima conocida a cada nodo.
        dist: dict[int, float] = {origin: 0.0}
        # Predecesor de cada nodo en el mejor camino encontrado.
        prev: dict[int, int] = {}
        # Cola de prioridad de pares (costo_acumulado, nodo).
        heap: list[tuple[float, int]] = [(0.0, origin)]
        visited: set[int] = set()

        while heap:
            cost_u, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            if u == dest:
                break  # ya tenemos el costo mínimo al destino

            for v in self.graph.neighbors(u):
                if v in visited:
                    continue
                w = self.costs.get((u, v))
                if w is None:
                    continue
                new_cost = cost_u + w
                if new_cost < dist.get(v, float("inf")):
                    dist[v] = new_cost
                    prev[v] = u
                    heapq.heappush(heap, (new_cost, v))

        path = self._reconstruct(prev, origin, dest)
        runtime = self._now_ms() - start
        return self._build_result(
            path, mode, runtime, meta={"visited_nodes": len(visited)}
        )

    @staticmethod
    def _reconstruct(prev: dict[int, int], origin: int, dest: int) -> list[int]:
        """Reconstruye el camino origen→destino a partir de los predecesores."""
        if dest != origin and dest not in prev:
            return []
        path = [dest]
        node = dest
        while node != origin:
            node = prev[node]
            path.append(node)
        path.reverse()
        return path
