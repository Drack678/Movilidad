"""API endpoints para TransMilenio y transporte público."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.gtfs_service import get_gtfs
from app.services.transmilenio_service import (
    nearby_stations,
    nearby_trunk_routes,
    recommendation_for_trip,
)

router = APIRouter(prefix="/transit", tags=["transit"])


@router.get("/gtfs/network")
async def get_gtfs_network():
    """Devuelve la red troncal de TransMilenio construida desde GTFS."""
    gtfs = get_gtfs()
    return gtfs.build_trunk_network()


@router.get("/gtfs/stops/nearby")
async def get_nearby_stops(
    lat: float = Query(..., description="Latitud del punto de origen"),
    lon: float = Query(..., description="Longitud del punto de origen"),
    limit: int = Query(6, ge=1, le=20),
    max_m: int = Query(2500, ge=100, le=5000),
    trunk_only: bool = Query(False),
):
    """Encuentra paradas/estaciones cercanas a un punto."""
    gtfs = get_gtfs()
    return gtfs.nearest_stops(lat, lon, limit=limit, max_m=max_m, trunk_only=trunk_only)


@router.get("/transmilenio/stations/nearby")
async def get_transmilenio_nearby_stations(
    lat: float = Query(..., description="Latitud del punto de origen"),
    lon: float = Query(..., description="Longitud del punto de origen"),
    radius_m: int = Query(900, ge=100, le=3000),
    limit: int = Query(8, ge=1, le=20),
):
    """Encuentra estaciones de TransMilenio cercanas usando el API oficial de ArcGIS."""
    stations = await nearby_stations(lat, lon, radius_m, limit)
    return {"stations": stations}


@router.get("/transmilenio/routes/nearby")
async def get_transmilenio_nearby_routes(
    lat: float = Query(..., description="Latitud del punto de origen"),
    lon: float = Query(..., description="Longitud del punto de origen"),
    radius_m: int = Query(1000, ge=100, le=3000),
    limit: int = Query(8, ge=1, le=20),
):
    """Encuentra rutas troncales de TransMilenio cercanas usando el API oficial de ArcGIS."""
    routes = await nearby_trunk_routes(lat, lon, radius_m, limit)
    return {"routes": routes}


@router.get("/transmilenio/recommendation")
async def get_transmilenio_recommendation(
    origin_lat: float = Query(...),
    origin_lon: float = Query(...),
    dest_lat: float = Query(...),
    dest_lon: float = Query(...),
):
    """Obtiene una recomendación de viaje en TransMilenio entre dos puntos."""
    return await recommendation_for_trip(origin_lat, origin_lon, dest_lat, dest_lon)
