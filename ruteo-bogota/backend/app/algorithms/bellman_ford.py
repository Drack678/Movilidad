"""Algoritmo de Bellman-Ford (camino de costo mínimo).

Relaja todas las aristas hasta ``|V| - 1`` veces. Es más lento que Dijkstra,
pero se incluye por completitud académica y porque soporta una detección
explícita de mejoras: si tras ``|V| - 1`` pasadas aún hay relajaciones, habría
ciclos negativos (no ocurre aquí, pues los costos son no negativos).

Se implementa una versión optimizada que se detiene en cuanto una pasada
completa no produce cambios.
"""

from __future__ import annotations

from app.algorithms.base import RouteAlgorithm
from app.models.enums import AlgorithmName, TransportMode
from app.models.graph_types import RouteResult


class BellmanFord(RouteAlgorithm):
    """Camino de costo mínimo mediante relajación iterativa de aristas."""

    name = AlgorithmName.BELLMAN_FORD

    def solve(self, origin: int, dest: int, mode: TransportMode) -> RouteResult:
        """Calcula el camino de costo mínimo de ``origin`` a ``dest``."""
        start = self._now_ms()

        dist: dict[int, float] = {origin: 0.0}
        prev: dict[int, int] = {}
        edges = list(self.graph.g.edges())
        n_nodes = self.graph.n_nodes

        passes = 0
        for _ in range(max(n_nodes - 1, 1)):
            passes += 1
            changed = False
            for u, v in edges:
                if u not in dist:
                    continue
                w = self.costs.get((u, v))
                if w is None:
                    continue
                new_cost = dist[u] + w
                if new_cost < dist.get(v, float("inf")):
                    dist[v] = new_cost
                    prev[v] = u
                    changed = True
            if not changed:
                break  # convergió antes de tiempo

        path = self._reconstruct(prev, origin, dest)
        runtime = self._now_ms() - start
        return self._build_result(path, mode, runtime, meta={"passes": passes})

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
