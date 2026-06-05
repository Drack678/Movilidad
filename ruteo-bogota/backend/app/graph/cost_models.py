"""Modelos de costo por modo de transporte.

Cada modo (automóvil, bicicleta, peatón) construye un costo diferente para las
aristas del grafo a partir de los mismos atributos físicos (longitud, tipo de
vía, velocidad, tráfico). El costo es la magnitud que TODOS los algoritmos de
ruteo minimizan, de modo que cambiar de modo cambia la ruta "óptima" sin
modificar los algoritmos.

Filosofía de diseño:
- Automóvil: minimiza el TIEMPO de viaje afectado por el tráfico y la velocidad.
- Bicicleta: minimiza distancia ponderada; bonifica ciclorrutas/vías
  secundarias y penaliza autopistas/vías rápidas.
- Peatón: minimiza distancia ponderada; bonifica andenes/senderos y penaliza
  grandes avenidas e intersecciones peligrosas.
"""

from __future__ import annotations

from app.models.enums import TransportMode
from app.models.graph_types import GraphEdge

# Velocidades de referencia (km/h) por modo cuando no hay velocidad explícita.
DEFAULT_SPEED_KPH: dict[TransportMode, float] = {
    TransportMode.CAR: 40.0,
    TransportMode.BIKE: 15.0,
    TransportMode.FOOT: 5.0,
}

# Tipos de vía OSM considerados "rápidos" (autopistas/vías rápidas).
HIGHWAY_FAST = {"motorway", "motorway_link", "trunk", "trunk_link"}
# Tipos de vía OSM considerados ciclables o secundarios cómodos para bici.
HIGHWAY_BIKE_FRIENDLY = {"cycleway", "residential", "living_street", "tertiary", "path"}
# Tipos de vía cómodos/seguros para peatón.
HIGHWAY_FOOT_FRIENDLY = {"footway", "pedestrian", "path", "living_street", "residential", "steps"}
# Grandes avenidas que penalizan al peatón.
HIGHWAY_BIG_AVENUE = {"primary", "primary_link", "secondary", "secondary_link"}


def _car_cost(edge: GraphEdge) -> float:
    """Costo para automóvil: tiempo de recorrido afectado por el tráfico.

    Se favorece la velocidad de la vía y se penaliza la congestión a través de
    :pyattr:`GraphEdge.current_time_s`.
    """
    return edge.current_time_s


def _bike_cost(edge: GraphEdge) -> float:
    """Costo para bicicleta.

    Base: tiempo a velocidad de bici. Se aplican multiplicadores que bonifican
    ciclorrutas/vías secundarias y penalizan fuertemente autopistas.
    """
    speed = DEFAULT_SPEED_KPH[TransportMode.BIKE]
    base_time = edge.length_m / (speed * 1000.0 / 3600.0)  # segundos

    factor = 1.0
    if edge.highway in HIGHWAY_FAST:
        factor *= 5.0  # penalización fuerte: las bicis evitan autopistas
    elif edge.highway in HIGHWAY_BIKE_FRIENDLY:
        factor *= 0.7  # bonificación por comodidad/seguridad
    # El tráfico afecta menos a la bici que al auto, pero algo penaliza.
    factor *= 1.0 + 0.15 * edge.traffic.value
    return base_time * factor


def _foot_cost(edge: GraphEdge) -> float:
    """Costo para peatón.

    Base: tiempo a velocidad de caminata. Bonifica andenes/senderos y penaliza
    grandes avenidas y autopistas (inseguras o intransitables a pie).
    """
    speed = DEFAULT_SPEED_KPH[TransportMode.FOOT]
    base_time = edge.length_m / (speed * 1000.0 / 3600.0)  # segundos

    factor = 1.0
    if edge.highway in HIGHWAY_FAST:
        factor *= 8.0  # prácticamente prohibido caminar por autopistas
    elif edge.highway in HIGHWAY_BIG_AVENUE:
        factor *= 1.6  # cruces e intersecciones peligrosas
    elif edge.highway in HIGHWAY_FOOT_FRIENDLY:
        factor *= 0.8  # bonificación por andenes/senderos
    return base_time * factor


# Despacho por modo: cada función recibe una arista y devuelve su costo.
_COST_FUNCS = {
    TransportMode.CAR: _car_cost,
    TransportMode.BIKE: _bike_cost,
    TransportMode.FOOT: _foot_cost,
}


def edge_cost(edge: GraphEdge, mode: TransportMode) -> float:
    """Calcula el costo de recorrer ``edge`` en el modo dado.

    Args:
        edge: Arista del grafo con sus atributos físicos y de tráfico.
        mode: Modo de transporte.

    Returns:
        Costo escalar positivo a minimizar por los algoritmos.
    """
    return _COST_FUNCS[mode](edge)


def edge_weights_for_mode(
    edges: list[GraphEdge], mode: TransportMode
) -> dict[tuple[int, int], float]:
    """Precalcula un diccionario ``(u, v) -> costo`` para todas las aristas.

    Útil para los algoritmos que recorren el grafo muchas veces (ACO) y evitan
    recalcular el costo en cada paso.
    """
    return {(e.u, e.v): edge_cost(e, mode) for e in edges}
