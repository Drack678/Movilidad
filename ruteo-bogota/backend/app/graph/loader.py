"""Carga del grafo vial con estrategia de respaldo.

Decide de dónde obtener el grafo siguiendo este orden de preferencia:

1. Red REAL de Bogotá vía OSMnx (cacheada en ``graph_cache_path``).
2. Grafo representativo de Bogotá desde ``fallback_graph_path`` (JSON).

Así el backend siempre puede arrancar: con datos reales si OSMnx está
disponible, o con el grafo sintético en entornos sin la pila geoespacial.
"""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.graph.road_graph import RoadGraph

logger = logging.getLogger(__name__)


def load_road_graph(settings: Settings, prefer_real: bool = True) -> RoadGraph:
    """Carga el grafo vial según la configuración.

    Args:
        settings: Configuración de la aplicación.
        prefer_real: Si ``True`` intenta primero la red real (OSMnx).

    Returns:
        Un :class:`RoadGraph` listo para usar.
    """
    if prefer_real:
        try:
            from app.graph.osm_builder import download_city_graph

            logger.info("Cargando red vial real de %s (OSMnx)...", settings.city_name)
            graph = download_city_graph(settings.city_name, settings.graph_cache_path)
            logger.info(
                "Grafo real cargado: %d nodos, %d aristas.",
                graph.n_nodes,
                graph.n_edges,
            )
            return graph
        except Exception as exc:  # OSMnx ausente o sin red: usar respaldo.
            logger.warning(
                "No se pudo cargar la red real (%s). Usando grafo representativo.",
                exc,
            )

    if settings.fallback_graph_path.exists():
        logger.info("Cargando grafo representativo desde %s", settings.fallback_graph_path)
        graph = RoadGraph.load_json(settings.fallback_graph_path)
        logger.info("Grafo representativo: %d nodos, %d aristas.", graph.n_nodes, graph.n_edges)
        return graph

    raise FileNotFoundError(
        "No hay grafo disponible. Ejecuta 'python -m scripts.build_graph' para "
        "descargar la red real, o 'python -m scripts.generate_sample_graph' para "
        "crear el grafo representativo."
    )
