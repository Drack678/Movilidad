"""Modelos ORM (SQLAlchemy) con soporte PostGIS.

Define la tabla de ubicaciones guardadas. Cada ubicación almacena, además de
sus campos descriptivos, un punto geográfico ``geom`` (PostGIS, SRID 4326) que
permite consultas espaciales (p. ej. ubicaciones cercanas).

Si PostGIS/GeoAlchemy2 no está disponible, el tipo geográfico se omite con
elegancia y solo se usan lat/lon, de modo que el modelo siga funcionando en
una base de datos sin la extensión espacial.
"""

from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base declarativa de SQLAlchemy."""


class Location(Base):
    """Ubicación personalizada guardada por el usuario.

    Ejemplos de categorías: ``universidad``, ``casa``, ``trabajo``,
    ``centro_comercial``, ``hospital``, ``estacion_transmilenio``.
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="general", index=True)

    def __repr__(self) -> str:  # pragma: no cover - utilidad de depuración
        return f"<Location id={self.id} name={self.name!r} cat={self.category!r}>"
