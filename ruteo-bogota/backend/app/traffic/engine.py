"""Motor de simulación de tráfico.

Asigna y actualiza dinámicamente el nivel de tráfico de cada arista del grafo.
El tráfico afecta el tiempo de recorrido y, por tanto, el costo de las aristas
para el modo automóvil (y en menor medida bicicleta), lo que cambia las rutas
óptimas que devuelven los algoritmos.

Estrategias de generación:
- ``random``: nivel aleatorio por vía (con sesgo hacia la vía).
- ``time_of_day``: nivel según la hora simulada (0-23) y el tipo de vía.
- ``rush_hour``: intensifica la congestión propia de las horas pico.

Eventos puntuales:
- ``simulate_accident``: eleva el tráfico de una vía a un nivel alto/crítico.
- ``simulate_closure``: marca una vía como cerrada (tráfico crítico + costo
  efectivamente prohibitivo a través del nivel muy alto).
"""

from __future__ import annotations

import random
from collections import Counter

from app.graph.road_graph import RoadGraph
from app.models.enums import TrafficLevel

# Tipos de vía OSM que sufren más congestión (arterias principales).
_ARTERIAL = {"motorway", "trunk", "primary", "secondary", "primary_link", "secondary_link"}

# Franjas horarias y su intensidad base de congestión (0 = libre, 4 = crítico).
# Mañana (6-9) y tarde (16-19) son horas pico en Bogotá.
_HOUR_BASE_LEVEL: dict[int, int] = {
    0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 1,
    6: 2, 7: 4, 8: 4, 9: 3, 10: 2, 11: 2,
    12: 3, 13: 3, 14: 2, 15: 2, 16: 3, 17: 4,
    18: 4, 19: 3, 20: 2, 21: 1, 22: 1, 23: 0,
}


class TrafficEngine:
    """Gestiona el estado de tráfico de un :class:`RoadGraph`.

    Attributes:
        graph: Grafo vial sobre el que opera el motor.
        closed_edges: Conjunto de aristas cerradas ``(u, v)``.
    """

    def __init__(self, graph: RoadGraph, seed: int | None = None) -> None:
        self.graph = graph
        self.closed_edges: set[tuple[int, int]] = set()
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------ #
    # Generación de tráfico
    # ------------------------------------------------------------------ #
    def _arterial_bias(self, highway: str) -> int:
        """Sesgo adicional de congestión para vías arteriales."""
        return 1 if highway in _ARTERIAL else 0

    def _clamp(self, value: int) -> TrafficLevel:
        """Limita un entero al rango válido de niveles de tráfico."""
        return TrafficLevel(max(0, min(4, value)))

    def generate_random(self) -> None:
        """Asigna a cada vía un nivel de tráfico aleatorio (con sesgo arterial)."""
        for u, v, d in self.graph.g.edges(data=True):
            base = self._rng.randint(0, 4)
            level = self._clamp(base + self._arterial_bias(str(d.get("highway", ""))))
            d["traffic"] = int(level.value)
        self._reapply_closures()

    def generate_time_of_day(self, hour: int) -> None:
        """Asigna tráfico según la hora simulada (0-23).

        Combina el nivel base de la franja horaria con el sesgo arterial y una
        pequeña variación aleatoria, de modo que vías similares no queden
        siempre idénticas.
        """
        base = _HOUR_BASE_LEVEL.get(hour % 24, 1)
        for u, v, d in self.graph.g.edges(data=True):
            jitter = self._rng.randint(-1, 1)
            level = self._clamp(base + self._arterial_bias(str(d.get("highway", ""))) + jitter)
            d["traffic"] = int(level.value)
        self._reapply_closures()

    def generate_rush_hour(self) -> None:
        """Simula una hora pico intensa (las arterias se saturan)."""
        for u, v, d in self.graph.g.edges(data=True):
            highway = str(d.get("highway", ""))
            base = 4 if highway in _ARTERIAL else self._rng.randint(2, 3)
            d["traffic"] = int(self._clamp(base).value)
        self._reapply_closures()

    def generate(self, strategy: str = "time_of_day", hour: int | None = None) -> None:
        """Punto de entrada único para generar tráfico según una estrategia."""
        if strategy == "random":
            self.generate_random()
        elif strategy == "rush_hour":
            self.generate_rush_hour()
        else:  # time_of_day por defecto
            self.generate_time_of_day(hour if hour is not None else 8)

    # ------------------------------------------------------------------ #
    # Eventos puntuales
    # ------------------------------------------------------------------ #
    def simulate_accident(self, u: int, v: int) -> None:
        """Eleva el tráfico de la vía ``(u, v)`` a nivel alto por un accidente."""
        if self.graph.g.has_edge(u, v):
            self.graph.set_edge_traffic(u, v, TrafficLevel.HIGH)

    def simulate_closure(self, u: int, v: int) -> None:
        """Cierra la vía ``(u, v)``: tráfico crítico (costo casi prohibitivo)."""
        if self.graph.g.has_edge(u, v):
            self.closed_edges.add((u, v))
            self.graph.set_edge_traffic(u, v, TrafficLevel.VERY_HIGH)

    def reopen(self, u: int, v: int) -> None:
        """Reabre una vía previamente cerrada."""
        self.closed_edges.discard((u, v))

    def _reapply_closures(self) -> None:
        """Reaplica los cierres tras regenerar el tráfico global."""
        for u, v in self.closed_edges:
            if self.graph.g.has_edge(u, v):
                self.graph.set_edge_traffic(u, v, TrafficLevel.VERY_HIGH)

    # ------------------------------------------------------------------ #
    # Consultas / analítica
    # ------------------------------------------------------------------ #
    def distribution(self) -> dict[str, int]:
        """Conteo de aristas por nivel de tráfico (etiquetas en español)."""
        counter: Counter[str] = Counter()
        for _, _, d in self.graph.g.edges(data=True):
            counter[TrafficLevel(int(d.get("traffic", 0))).label_es] += 1
        return dict(counter)
