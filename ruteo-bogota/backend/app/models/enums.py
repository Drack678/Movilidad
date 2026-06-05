"""Enumeraciones del dominio.

Definen los conjuntos cerrados de valores usados por todo el sistema:
modos de transporte, niveles de tráfico y algoritmos disponibles.
"""

from __future__ import annotations

from enum import Enum


class TransportMode(str, Enum):
    """Perfiles de transporte soportados.

    Cada perfil construye costos diferentes para las aristas del grafo
    (ver :mod:`app.graph.cost_models`).
    """

    CAR = "car"  # Automóvil: prioriza tiempo, velocidad y estado del tráfico.
    BIKE = "bike"  # Bicicleta: prioriza ciclorrutas/vías secundarias; penaliza autopistas.
    FOOT = "foot"  # Peatón: prioriza andenes/senderos; penaliza grandes avenidas.


class TrafficLevel(int, Enum):
    """Niveles dinámicos de tráfico de una vía.

    El valor entero ordena los niveles de menor a mayor congestión y se usa
    como índice para multiplicadores de costo y colores del mapa de calor.
    """

    VERY_LOW = 0  # Muy bajo
    LOW = 1  # Bajo
    MEDIUM = 2  # Medio
    HIGH = 3  # Alto
    VERY_HIGH = 4  # Muy alto

    @property
    def label_es(self) -> str:
        """Etiqueta legible en español."""
        return {
            TrafficLevel.VERY_LOW: "Muy bajo",
            TrafficLevel.LOW: "Bajo",
            TrafficLevel.MEDIUM: "Medio",
            TrafficLevel.HIGH: "Alto",
            TrafficLevel.VERY_HIGH: "Muy alto",
        }[self]

    @property
    def color(self) -> str:
        """Color del mapa de calor estilo Google Maps Traffic.

        Verde → amarillo → naranja → rojo → vinotinto (congestión crítica).
        """
        return {
            TrafficLevel.VERY_LOW: "#2ecc71",  # verde
            TrafficLevel.LOW: "#a3e635",  # verde-amarillo
            TrafficLevel.MEDIUM: "#f1c40f",  # amarillo
            TrafficLevel.HIGH: "#e67e22",  # naranja
            TrafficLevel.VERY_HIGH: "#7b1e3a",  # vinotinto (crítico)
        }[self]

    @property
    def speed_factor(self) -> float:
        """Factor por el que se reduce la velocidad libre según la congestión.

        1.0 = circula a velocidad libre; 0.25 = a un cuarto de la velocidad.
        """
        return {
            TrafficLevel.VERY_LOW: 1.0,
            TrafficLevel.LOW: 0.85,
            TrafficLevel.MEDIUM: 0.65,
            TrafficLevel.HIGH: 0.45,
            TrafficLevel.VERY_HIGH: 0.25,
        }[self]


class AlgorithmName(str, Enum):
    """Algoritmos de ruteo disponibles para cálculo y comparación."""

    ACO = "aco"
    DIJKSTRA = "dijkstra"
    ASTAR = "astar"
    BELLMAN_FORD = "bellman_ford"
