"""Estado de la aplicación compartido entre peticiones.

Mantiene en memoria el grafo vial y el motor de tráfico, que son costosos de
construir y se reutilizan en todas las peticiones. Se inicializa al arrancar la
aplicación (evento ``startup``) y se expone mediante dependencias de FastAPI.
"""

from __future__ import annotations

import logging

from app.core.config import Settings, get_settings
from app.graph.loader import load_road_graph
from app.graph.road_graph import RoadGraph
from app.traffic.engine import TrafficEngine

logger = logging.getLogger(__name__)


class AppState:
    """Contenedor del estado en memoria de la aplicación."""

    def __init__(self) -> None:
        self.settings: Settings = get_settings()
        self.graph: RoadGraph | None = None
        self.traffic: TrafficEngine | None = None

    def initialize(self, prefer_real: bool = True) -> None:
        """Carga el grafo y genera un estado de tráfico inicial.

        Args:
            prefer_real: Si ``True``, intenta cargar la red real (OSMnx) y cae
                al grafo representativo si no es posible.
        """
        self.graph = load_road_graph(self.settings, prefer_real=prefer_real)
        self.traffic = TrafficEngine(self.graph, seed=42)
        # Estado de tráfico inicial: una mañana típica (hora pico).
        self.traffic.generate(strategy="time_of_day", hour=8)
        logger.info(
            "Estado inicial listo: %d nodos, %d aristas.",
            self.graph.n_nodes,
            self.graph.n_edges,
        )

    @property
    def is_ready(self) -> bool:
        """Indica si el grafo y el tráfico ya están inicializados."""
        return self.graph is not None and self.traffic is not None


# Instancia única del estado de la aplicación.
app_state = AppState()


def get_state() -> AppState:
    """Dependencia de FastAPI que entrega el estado inicializado."""
    if not app_state.is_ready:
        app_state.initialize()
    return app_state
