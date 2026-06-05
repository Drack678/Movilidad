"""Punto de entrada de la API REST (FastAPI).

Crea la aplicación, configura CORS, registra los routers por dominio
(salud, ubicaciones, ruteo, tráfico, analítica) e inicializa la base de datos y
el estado en memoria (grafo + tráfico) al arrancar.

Ejecutar en desarrollo:
    uvicorn app.main:app --reload

Documentación interactiva disponible en /docs (Swagger) y /redoc.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, graph, health, locations, routing, traffic
from app.api.state import app_state
from app.core.config import get_settings
from app.database.session import init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ruteo_bogota")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa recursos al arrancar y los libera al apagar.

    - Crea las tablas de la base de datos.
    - Carga el grafo vial y genera el tráfico inicial.

    La variable de entorno ``USE_REAL_GRAPH`` controla si se intenta descargar
    la red real con OSMnx (``1``, por defecto) o se usa el grafo representativo
    (``0``), útil para arranques rápidos y CI.
    """
    init_db()
    prefer_real = os.getenv("USE_REAL_GRAPH", "1") == "1"
    try:
        app_state.initialize(prefer_real=prefer_real)
    except Exception as exc:  # no impedir el arranque de la API
        logger.error("No se pudo inicializar el grafo al arrancar: %s", exc)
    yield


def create_app() -> FastAPI:
    """Construye y configura la instancia de FastAPI."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend de optimización de rutas urbanas para Bogotá. Calcula rutas "
            "con Ant Colony Optimization (ACO), Dijkstra y A* sobre la red vial de "
            "OpenStreetMap, simula tráfico y expone analítica."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_prefix = "/api"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(locations.router, prefix=api_prefix)
    app.include_router(routing.router, prefix=api_prefix)
    app.include_router(traffic.router, prefix=api_prefix)
    app.include_router(analytics.router, prefix=api_prefix)
    app.include_router(graph.router, prefix=api_prefix)

    @app.get("/", tags=["root"])
    def root() -> dict:
        """Mensaje de bienvenida con enlaces a la documentación."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": f"{api_prefix}/health",
        }

    return app


app = create_app()
