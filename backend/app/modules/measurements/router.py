from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.modules.measurements import service
from app.modules.measurements.schemas import MeasurementResponse
from app.modules.stations.models import Station

router = APIRouter(tags=["measurements"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/measurements/latest", response_model=list[MeasurementResponse])
async def latest_measurements(
    db: DbSession,
    limit: int = Query(100, ge=1, le=500),
) -> list[MeasurementResponse]:
    measurements = await service.get_latest_measurements(db, limit=limit)
    return [MeasurementResponse.model_validate(m) for m in measurements]


@router.get("/stations/{station_id}/measurements", response_model=list[MeasurementResponse])
async def station_measurements(
    station_id: UUID,
    db: DbSession,
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    limit: int = Query(200, ge=1, le=1000),
) -> list[MeasurementResponse]:
    # Verify station exists
    result = await db.execute(select(Station).where(Station.id == station_id))
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Station not found")

    measurements = await service.get_station_measurements(
        db, station_id, from_dt=from_dt, to_dt=to_dt, limit=limit
    )
    return [MeasurementResponse.model_validate(m) for m in measurements]


@router.get("/stations/{station_id}/measurements/latest", response_model=MeasurementResponse)
async def latest_station_measurement(
    station_id: UUID,
    db: DbSession,
) -> MeasurementResponse:
    measurement = await service.get_latest_for_station(db, station_id)
    if measurement is None:
        raise NotFoundError("No measurements found for this station")
    return MeasurementResponse.model_validate(measurement)
