"""Esquemas Pydantic de entrada/salida de la API REST.

Estos modelos validan los cuerpos de las peticiones y dan forma a las
respuestas JSON. Están separados de los tipos internos del grafo
(:mod:`app.models.graph_types`) para no acoplar transporte y cómputo.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AlgorithmName, TrafficLevel, TransportMode


# ---------------------------------------------------------------------------
# Ubicaciones guardadas
# ---------------------------------------------------------------------------
class LocationBase(BaseModel):
    """Campos comunes de una ubicación personalizada."""

    name: str = Field(..., min_length=1, max_length=120, description="Nombre de la ubicación.")
    description: str = Field(default="", max_length=500)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    category: str = Field(default="general", max_length=60)


class LocationCreate(LocationBase):
    """Cuerpo para crear una ubicación."""


class LocationRead(LocationBase):
    """Ubicación tal como se devuelve al cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------------------------------------------------------------------------
# Cálculo de rutas
# ---------------------------------------------------------------------------
class ACOParams(BaseModel):
    """Parámetros configurables del algoritmo de colonia de hormigas."""

    alpha: float = Field(default=1.0, ge=0, description="Influencia de las feromonas.")
    beta: float = Field(default=3.0, ge=0, description="Influencia de la heurística.")
    rho: float = Field(default=0.5, ge=0, le=1, description="Tasa de evaporación.")
    q: float = Field(default=100.0, gt=0, description="Constante de depósito de feromonas.")
    n_ants: int = Field(default=20, ge=1, le=500, description="Cantidad de hormigas.")
    n_iterations: int = Field(default=50, ge=1, le=1000, description="Cantidad de iteraciones.")
    seed: int | None = Field(default=None, description="Semilla para reproducibilidad.")


class RouteRequest(BaseModel):
    """Petición de cálculo de ruta entre dos coordenadas."""

    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lon: float = Field(..., ge=-180, le=180)
    dest_lat: float = Field(..., ge=-90, le=90)
    dest_lon: float = Field(..., ge=-180, le=180)
    mode: TransportMode = TransportMode.CAR
    algorithm: AlgorithmName = AlgorithmName.ACO
    aco_params: ACOParams | None = None


class RouteResponse(BaseModel):
    """Respuesta con la ruta calculada."""

    algorithm: AlgorithmName
    mode: TransportMode
    found: bool
    node_path: list[int]
    coordinates: list[tuple[float, float]]
    total_distance_m: float
    total_time_s: float
    total_cost: float
    runtime_ms: float
    iterations: int
    meta: dict


class AlgorithmComparison(BaseModel):
    """Métricas de un algoritmo dentro de una comparación."""

    algorithm: AlgorithmName
    found: bool
    total_distance_m: float
    total_time_s: float
    total_cost: float
    runtime_ms: float
    iterations: int
    # Calidad relativa: razón entre el costo de este algoritmo y el mejor costo
    # encontrado (1.0 = óptimo dentro de la comparación).
    quality_ratio: float


class CompareResponse(BaseModel):
    """Respuesta de la comparación de algoritmos."""

    mode: TransportMode
    best_algorithm: AlgorithmName
    results: list[AlgorithmComparison]
    # Ruta del mejor algoritmo, lista para dibujar en el mapa.
    best_route: RouteResponse


# ---------------------------------------------------------------------------
# Tráfico
# ---------------------------------------------------------------------------
class TrafficGenerateRequest(BaseModel):
    """Configuración para generar/regenerar el estado del tráfico."""

    strategy: str = Field(
        default="time_of_day",
        description="Estrategia: 'random', 'time_of_day', 'rush_hour'.",
    )
    hour: int | None = Field(default=None, ge=0, le=23, description="Hora simulada (0-23).")
    seed: int | None = None


class IncidentRequest(BaseModel):
    """Simulación de un incidente (accidente o cierre) sobre una vía."""

    edge_u: int
    edge_v: int
    kind: str = Field(default="accident", description="'accident' o 'closure'.")


class TrafficEdge(BaseModel):
    """Estado de tráfico de una arista para el mapa de calor."""

    u: int
    v: int
    coordinates: list[tuple[float, float]]
    level: TrafficLevel
    color: str
    name: str


# ---------------------------------------------------------------------------
# Analítica / grafo
# ---------------------------------------------------------------------------
class GraphStats(BaseModel):
    """Estadísticas generales del grafo y del tráfico."""

    n_nodes: int
    n_edges: int
    avg_travel_time_s: float
    most_congested: list[dict]
    least_congested: list[dict]
    traffic_distribution: dict[str, int]
