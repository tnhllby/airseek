from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: UUID
    measured_at: datetime
    aqi: int | None = None
    pm25: float | None = None
    pm10: float | None = None
    co: float | None = None
    no2: float | None = None
    so2: float | None = None
    o3: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    created_at: datetime


class LatestMeasurementResponse(MeasurementResponse):
    station_name: str
    station_latitude: float
    station_longitude: float
    station_district: str | None = None
