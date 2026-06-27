from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.modules.measurements.service import get_latest_for_station
from app.modules.stations import service
from app.modules.stations.schemas import StationResponse, StationWithDistance

router = APIRouter(prefix="/stations", tags=["stations"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[StationResponse])
async def list_stations(
    db: DbSession,
    active_only: bool = Query(True),
) -> list[StationResponse]:
    stations = await service.get_stations(db, active_only=active_only)
    return [StationResponse.model_validate(s) for s in stations]


@router.get("/nearest", response_model=list[StationWithDistance])
async def nearest_stations(
    db: DbSession,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    limit: int = Query(5, ge=1, le=20),
) -> list[StationWithDistance]:
    ranked = await service.get_nearest_stations(db, lat, lon, limit)
    return [
        StationWithDistance(**StationResponse.model_validate(s).model_dump(), distance_km=dist)
        for s, dist in ranked
    ]


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(station_id: UUID, db: DbSession) -> StationResponse:
    station = await service.get_station(db, station_id)
    if station is None:
        raise NotFoundError("Station not found")
    return StationResponse.model_validate(station)
