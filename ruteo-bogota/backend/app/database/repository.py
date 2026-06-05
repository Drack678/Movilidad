"""Repositorio de ubicaciones guardadas.

Encapsula las operaciones CRUD sobre la tabla ``locations``, separando el
acceso a datos de la capa de la API.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Location
from app.models.schemas import LocationCreate


class LocationRepository:
    """Operaciones de persistencia para :class:`Location`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: LocationCreate) -> Location:
        """Inserta una nueva ubicación y la devuelve con su ID asignado."""
        loc = Location(
            name=data.name,
            description=data.description,
            lat=data.lat,
            lon=data.lon,
            category=data.category,
        )
        self.db.add(loc)
        self.db.commit()
        self.db.refresh(loc)
        return loc

    def list_all(self) -> list[Location]:
        """Devuelve todas las ubicaciones guardadas."""
        return list(self.db.scalars(select(Location).order_by(Location.id)))

    def get(self, location_id: int) -> Location | None:
        """Devuelve una ubicación por ID, o ``None`` si no existe."""
        return self.db.get(Location, location_id)

    def delete(self, location_id: int) -> bool:
        """Elimina una ubicación. Devuelve ``True`` si existía."""
        loc = self.db.get(Location, location_id)
        if loc is None:
            return False
        self.db.delete(loc)
        self.db.commit()
        return True
