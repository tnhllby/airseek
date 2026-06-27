from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalyzeRequest(BaseModel):
    station_id: UUID | None = None  # None = city-wide analysis
    question: str | None = None
    hours: int = 24  # look-back window


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: UUID
    model_name: str
    prediction_type: str
    predicted_at: datetime
    predicted_aqi: int | None = None
    confidence: float | None = None
    summary: str | None = None
    recommendations: str | None = None
    created_at: datetime
