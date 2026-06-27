from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: UUID | None = None
    type: str
    title: str
    body: str
    aqi_value: int | None = None
    is_sent: bool
    sent_at: datetime | None = None
    created_at: datetime
