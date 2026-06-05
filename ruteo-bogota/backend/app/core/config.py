"""Configuración central de la aplicación.

Carga parámetros desde variables de entorno (o un archivo ``.env``) usando
``pydantic-settings``. Centralizar la configuración aquí permite cambiar el
comportamiento del backend (ciudad objetivo, base de datos, parámetros por
defecto del ACO) sin tocar el código.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directorio raíz del backend (.../backend) y carpeta de datos.
BASE_DIR: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = BASE_DIR / "data"


class Settings(BaseSettings):
    """Parámetros de configuración de la aplicación.

    Todos los campos pueden sobreescribirse mediante variables de entorno con
    el mismo nombre en mayúsculas (por ejemplo ``CITY_NAME``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Metadatos de la API -------------------------------------------------
    app_name: str = "Ruteo Bogotá API"
    app_version: str = "1.0.0"
    debug: bool = True

    # --- Ciudad y grafo vial -------------------------------------------------
    city_name: str = Field(
        default="Bogotá, Colombia",
        description="Lugar que OSMnx usa para descargar la red vial.",
    )
    # Punto central aproximado de Bogotá (Plaza de Bolívar) usado por el frontend
    # para centrar el mapa y como respaldo en cálculos.
    city_center_lat: float = 4.5981
    city_center_lon: float = -74.0758

    # Ruta donde se cachea el grafo descargado para no volver a pedirlo a OSM.
    graph_cache_path: Path = DATA_DIR / "bogota_graph.graphml"
    # Grafo representativo (JSON) que permite trabajar sin OSMnx instalado.
    fallback_graph_path: Path = DATA_DIR / "bogota_graph.json"

    # --- Base de datos -------------------------------------------------------
    database_url: str = Field(
        default="postgresql+psycopg2://ruteo:ruteo@localhost:5432/ruteo_bogota",
        description="Cadena de conexión SQLAlchemy a PostgreSQL/PostGIS.",
    )

    # --- Parámetros por defecto del ACO -------------------------------------
    aco_alpha: float = 1.0  # influencia de las feromonas
    aco_beta: float = 3.0  # influencia de la heurística
    aco_rho: float = 0.5  # tasa de evaporación
    aco_q: float = 100.0  # constante de depósito de feromonas
    aco_n_ants: int = 20  # cantidad de hormigas por iteración
    aco_n_iterations: int = 50  # cantidad de iteraciones

    # --- CORS ----------------------------------------------------------------
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve una instancia única (cacheada) de :class:`Settings`."""
    return Settings()
