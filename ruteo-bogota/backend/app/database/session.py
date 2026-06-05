"""Gestión de la sesión de base de datos (SQLAlchemy).

Crea el motor y la fábrica de sesiones a partir de ``settings.database_url``.
En producción apunta a PostgreSQL + PostGIS; si la conexión no está disponible
(p. ej. en desarrollo o CI sin Postgres), cae con elegancia a una base SQLite
local para que la API siga funcionando.

La función :func:`get_db` es una dependencia de FastAPI que entrega una sesión
y garantiza su cierre.
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATA_DIR, get_settings
from app.database.models import Base

logger = logging.getLogger(__name__)


def _build_engine() -> Engine:
    """Construye el motor SQLAlchemy con respaldo a SQLite."""
    settings = get_settings()
    url = settings.database_url
    try:
        engine = create_engine(url, pool_pre_ping=True, future=True)
        # Probar la conexión; si falla, usar SQLite.
        with engine.connect():
            pass
        logger.info("Conectado a la base de datos: %s", url.split("@")[-1])
        return engine
    except Exception as exc:  # PostgreSQL no disponible
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite:///{DATA_DIR / 'ruteo_bogota.db'}"
        logger.warning(
            "No se pudo conectar a PostgreSQL (%s). Usando SQLite local: %s",
            exc,
            sqlite_url,
        )
        return create_engine(
            sqlite_url, connect_args={"check_same_thread": False}, future=True
        )


engine: Engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Crea las tablas si no existen."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una sesión y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
