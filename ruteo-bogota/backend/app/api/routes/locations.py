"""Endpoints CRUD de ubicaciones guardadas."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.repository import LocationRepository
from app.database.session import get_db
from app.models.schemas import LocationCreate, LocationRead

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(data: LocationCreate, db: Session = Depends(get_db)) -> LocationRead:
    """Crea una ubicación personalizada (nombre, descripción, lat, lon, categoría)."""
    loc = LocationRepository(db).create(data)
    return LocationRead.model_validate(loc)


@router.get("", response_model=list[LocationRead])
def list_locations(db: Session = Depends(get_db)) -> list[LocationRead]:
    """Lista todas las ubicaciones guardadas."""
    return [LocationRead.model_validate(loc) for loc in LocationRepository(db).list_all()]


@router.get("/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)) -> LocationRead:
    """Obtiene una ubicación por su ID."""
    loc = LocationRepository(db).get(location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada.")
    return LocationRead.model_validate(loc)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: Session = Depends(get_db)) -> Response:
    """Elimina una ubicación por su ID."""
    if not LocationRepository(db).delete(location_id):
        raise HTTPException(status_code=404, detail="Ubicación no encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
