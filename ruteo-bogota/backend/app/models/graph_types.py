"""Tipos de datos del grafo vial y de los resultados de ruteo.

Se usan ``dataclasses`` para los objetos internos del grafo (ligeros y
rápidos) y modelos Pydantic para lo que viaja por la API (validado y
serializable). Mantener ambos separados evita acoplar la representación de
cómputo con la representación de transporte.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.enums import AlgorithmName, TrafficLevel, TransportMode


@dataclass(slots=True)
class GraphNode:
    """Nodo (intersección) de la red vial.

    Attributes:
        id: Identificador único del nodo (proveniente de OSM o sintético).
        lat: Latitud en grados decimales (WGS84).
        lon: Longitud en grados decimales (WGS84).
    """

    id: int
    lat: float
    lon: float


@dataclass(slots=True)
class GraphEdge:
    """Arista (segmento de vía) entre dos nodos.

    Attributes:
        u: Nodo origen.
        v: Nodo destino.
        length_m: Longitud del segmento en metros.
        highway: Tipo de vía OSM (``primary``, ``residential``, ``cycleway``...).
        speed_kph: Velocidad estimada en flujo libre (km/h).
        base_time_s: Tiempo base de recorrido en segundos (sin tráfico).
        traffic: Nivel de tráfico dinámico actual.
        name: Nombre de la vía (si está disponible).
    """

    u: int
    v: int
    length_m: float
    highway: str
    speed_kph: float
    base_time_s: float
    traffic: TrafficLevel = TrafficLevel.VERY_LOW
    name: str = ""

    @property
    def current_time_s(self) -> float:
        """Tiempo de recorrido afectado por el tráfico actual (segundos)."""
        return self.base_time_s / max(self.traffic.speed_factor, 1e-6)


@dataclass(slots=True)
class RouteResult:
    """Resultado del cálculo de una ruta.

    Attributes:
        algorithm: Algoritmo que produjo la ruta.
        mode: Modo de transporte usado.
        node_path: Secuencia de IDs de nodo desde origen a destino.
        coordinates: Coordenadas ``(lat, lon)`` de cada nodo de la ruta.
        total_distance_m: Distancia total recorrida (metros).
        total_time_s: Tiempo total estimado considerando tráfico (segundos).
        total_cost: Costo total acumulado según el modelo de costos del modo.
        runtime_ms: Tiempo de ejecución del algoritmo (milisegundos).
        iterations: Iteraciones realizadas (relevante para ACO).
        found: ``True`` si se encontró una ruta válida.
        meta: Información adicional específica del algoritmo.
    """

    algorithm: AlgorithmName
    mode: TransportMode
    node_path: list[int]
    coordinates: list[tuple[float, float]]
    total_distance_m: float
    total_time_s: float
    total_cost: float
    runtime_ms: float
    iterations: int = 0
    found: bool = True
    meta: dict = field(default_factory=dict)
