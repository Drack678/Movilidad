"""Optimización por Colonia de Hormigas (Ant Colony Optimization, ACO).

Implementación DESDE CERO del ACO aplicado al problema de ruta mínima entre un
origen y un destino sobre un grafo dirigido con costos por arista.

Idea general
------------
Un conjunto de "hormigas" construye caminos del origen al destino. En cada nodo,
una hormiga elige la siguiente arista de forma estocástica, favoreciendo:

- aristas con mucha FEROMONA ``tau`` (memoria colectiva de buenos caminos), y
- aristas con buena HEURÍSTICA ``eta`` (deseabilidad inmediata, aquí
  ``1 / costo``: cuanto menor el costo, más deseable).

La probabilidad de ir de ``i`` a ``j`` es:

    p(i, j) = (tau_ij^alpha * eta_ij^beta) / sum_k (tau_ik^alpha * eta_ik^beta)

donde la suma recorre los vecinos ``k`` no visitados de ``i``.

Tras cada iteración:
- las feromonas se EVAPORAN: ``tau <- (1 - rho) * tau``;
- cada hormiga DEPOSITA feromona en su camino: ``tau += Q / costo_camino``
  (los caminos más cortos depositan más).

Parámetros configurables
-------------------------
- ``alpha``: influencia de las feromonas.
- ``beta``: influencia de la heurística.
- ``rho``: tasa de evaporación (0-1).
- ``q``: constante de depósito de feromonas.
- ``n_ants``: cantidad de hormigas por iteración.
- ``n_iterations``: cantidad de iteraciones.

Además se registra el historial iteración por iteración (mejor costo, aristas
exploradas y feromonas) para alimentar la visualización educativa del frontend.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from app.algorithms.base import RouteAlgorithm
from app.graph.road_graph import RoadGraph, haversine_m
from app.models.enums import AlgorithmName, TransportMode
from app.models.graph_types import RouteResult


@dataclass(slots=True)
class ACOConfig:
    """Configuración de los parámetros del ACO."""

    alpha: float = 1.0
    beta: float = 3.0
    rho: float = 0.5
    q: float = 100.0
    n_ants: int = 20
    n_iterations: int = 50
    seed: int | None = None
    # Límite de pasos por hormiga para evitar caminos degenerados (en función
    # del tamaño del grafo). Se calcula en tiempo de ejecución si es None.
    max_steps: int | None = None
    # Si True, guarda historial por iteración para la visualización educativa.
    record_history: bool = False
    # Peso del sesgo hacia el destino en la heurística (>0 evita que las
    # hormigas vaguen alejándose de la meta). 0 = ACO "puro" sin guía espacial.
    goal_bias: float = 2.0


class AntColonyOptimizer(RouteAlgorithm):
    """Algoritmo de Optimización por Colonia de Hormigas."""

    name = AlgorithmName.ACO

    def __init__(
        self,
        graph: RoadGraph,
        costs: dict[tuple[int, int], float],
        config: ACOConfig | None = None,
    ) -> None:
        super().__init__(graph, costs)
        self.config = config or ACOConfig()
        self._rng = random.Random(self.config.seed)
        # Feromona por arista; se inicializa de forma perezosa en ``solve``.
        self.pheromone: dict[tuple[int, int], float] = {}
        # Heurística por arista: eta_ij = 1 / costo_ij (precalculada).
        self.eta: dict[tuple[int, int], float] = {}
        # Coordenadas del destino (para el sesgo direccional), fijadas en solve.
        self._dest_lat: float = 0.0
        self._dest_lon: float = 0.0
        # Cache de coordenadas por nodo para acelerar el sesgo direccional.
        self._coords: dict[int, tuple[float, float]] = {}
        # Cache de vecinos por nodo (evita recomputar sucesores).
        self._succ: dict[int, list[int]] = {}

    # ------------------------------------------------------------------ #
    # Inicialización
    # ------------------------------------------------------------------ #
    def _initialize(self) -> None:
        """Inicializa feromonas (valor uniforme) y heurística (1/costo)."""
        tau0 = 1.0  # feromona inicial uniforme en todas las aristas
        self.pheromone = {edge: tau0 for edge in self.costs}
        self.eta = {
            edge: (1.0 / cost if cost > 0 else 1.0) for edge, cost in self.costs.items()
        }

    # ------------------------------------------------------------------ #
    # Construcción de una solución por una hormiga
    # ------------------------------------------------------------------ #
    def _choose_next(self, current: int, dest: int, visited: set[int]) -> int | None:
        """Elige estocásticamente el siguiente nodo desde ``current``.

        Aplica la regla de probabilidad de transición del ACO sobre los vecinos
        no visitados. Devuelve ``None`` si la hormiga queda sin salida.
        """
        clat, clon = self._coords[current]
        dist_cur = haversine_m(clat, clon, self._dest_lat, self._dest_lon)
        alpha, beta, gbias = self.config.alpha, self.config.beta, self.config.goal_bias

        candidates: list[int] = []
        weights: list[float] = []
        for v in self._succ.get(current, ()):  # vecinos cacheados
            if v in visited:
                continue
            edge = (current, v)
            tau = self.pheromone.get(edge, 1e-6)
            eta = self.eta.get(edge, 1e-6)
            weight = (tau**alpha) * (eta**beta)
            # Sesgo direccional: favorecer vecinos que acercan al destino. Esto
            # imita el "olfato" de la hormiga hacia la meta y acelera la
            # convergencia sin alterar la mecánica de feromonas.
            if gbias > 0:
                vlat, vlon = self._coords[v]
                dist_v = haversine_m(vlat, vlon, self._dest_lat, self._dest_lon)
                progress = (dist_cur - dist_v) / (dist_cur + 1.0)  # >0 si acerca
                weight *= (1.0 + max(progress, 0.0)) ** gbias
            candidates.append(v)
            weights.append(weight)

        if not candidates:
            return None

        # Si el destino es alcanzable directamente, sesgar levemente hacia él
        # ya está implícito en eta; aquí solo hacemos selección por ruleta.
        total = sum(weights)
        if total <= 0 or math.isnan(total):
            return self._rng.choice(candidates)

        r = self._rng.random() * total
        acc = 0.0
        for v, w in zip(candidates, weights):
            acc += w
            if acc >= r:
                return v
        return candidates[-1]

    def _construct_path(self, origin: int, dest: int, max_steps: int) -> list[int] | None:
        """Construye un camino origen→destino para una hormiga.

        Returns:
            La lista de nodos si llega al destino, o ``None`` si se atasca o
            excede ``max_steps``.
        """
        path = [origin]
        visited = {origin}
        current = origin
        for _ in range(max_steps):
            if current == dest:
                return path
            nxt = self._choose_next(current, dest, visited)
            if nxt is None:
                return None  # callejón sin salida
            path.append(nxt)
            visited.add(nxt)
            current = nxt
        return path if current == dest else None

    def _path_cost(self, path: list[int]) -> float:
        """Costo total de un camino sumando los costos de sus aristas."""
        return sum(self.costs.get((path[i], path[i + 1]), 0.0) for i in range(len(path) - 1))

    # ------------------------------------------------------------------ #
    # Actualización de feromonas
    # ------------------------------------------------------------------ #
    def _evaporate(self) -> None:
        """Evapora feromona en todas las aristas: ``tau <- (1 - rho) * tau``."""
        keep = 1.0 - self.config.rho
        for edge in self.pheromone:
            self.pheromone[edge] *= keep

    def _deposit(self, paths: list[tuple[list[int], float]]) -> None:
        """Deposita feromona proporcional a la calidad de cada camino.

        Cada hormiga añade ``Q / costo`` a las aristas de su camino: los caminos
        de menor costo refuerzan más sus aristas.
        """
        for path, cost in paths:
            if cost <= 0:
                continue
            contribution = self.config.q / cost
            for i in range(len(path) - 1):
                edge = (path[i], path[i + 1])
                if edge in self.pheromone:
                    self.pheromone[edge] += contribution

    # ------------------------------------------------------------------ #
    # Bucle principal
    # ------------------------------------------------------------------ #
    def solve(self, origin: int, dest: int, mode: TransportMode) -> RouteResult:
        """Ejecuta el ACO y devuelve la mejor ruta encontrada."""
        start = self._now_ms()
        self._initialize()
        # Precalcular coordenadas y vecinos de todos los nodos una sola vez.
        self._coords = {
            nid: (float(d["y"]), float(d["x"]))
            for nid, d in self.graph.g.nodes(data=True)
        }
        self._succ = {nid: list(self.graph.neighbors(nid)) for nid in self._coords}
        self._dest_lat, self._dest_lon = self._coords[dest]

        max_steps = self.config.max_steps or min(max(self.graph.n_nodes, 50), 5000)
        best_path: list[int] | None = None
        best_cost = float("inf")
        history: list[dict] = []

        for it in range(self.config.n_iterations):
            iteration_paths: list[tuple[list[int], float]] = []
            explored_edges: set[tuple[int, int]] = set()

            # Cada hormiga construye un camino.
            for _ in range(self.config.n_ants):
                path = self._construct_path(origin, dest, max_steps)
                if path is None:
                    continue
                cost = self._path_cost(path)
                iteration_paths.append((path, cost))
                for i in range(len(path) - 1):
                    explored_edges.add((path[i], path[i + 1]))
                if cost < best_cost:
                    best_cost = cost
                    best_path = path

            # Actualización de feromonas: evaporación + depósito.
            self._evaporate()
            self._deposit(iteration_paths)

            if self.config.record_history:
                history.append(
                    {
                        "iteration": it,
                        "best_cost": None if best_cost == float("inf") else best_cost,
                        "n_successful_ants": len(iteration_paths),
                        "explored_edges": [list(e) for e in explored_edges],
                        "best_path": list(best_path) if best_path else [],
                    }
                )

        runtime = self._now_ms() - start
        meta: dict = {
            "alpha": self.config.alpha,
            "beta": self.config.beta,
            "rho": self.config.rho,
            "q": self.config.q,
            "n_ants": self.config.n_ants,
            "best_cost": None if best_cost == float("inf") else best_cost,
        }
        if self.config.record_history:
            meta["history"] = history

        return self._build_result(
            best_path or [],
            mode,
            runtime,
            iterations=self.config.n_iterations,
            meta=meta,
        )
