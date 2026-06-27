from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StationBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    description: str | None = None
    district: str | None = None
    source: str
    is_active: bool = True


class StationResponse(StationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str | None = None
    created_at: datetime
    updated_at: datetime


class StationWithDistance(StationResponse):
    distance_km: float
