"""
Внутренний контракт данных. Все адаптеры возвращают список RawMeasurement.
Writer принимает только RawMeasurement — не знает, откуда пришли данные.
"""
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, field_validator


class RawMeasurement(BaseModel):
    # Идентификация источника
    source: str                          # 'openaq' | 'iqair' | 'physical'
    external_station_id: str             # ID станции в системе-источнике
    station_name: str

    # Геопозиция
    latitude: float
    longitude: float

    # Время измерения (UTC)
    measured_at: datetime

    # Показатели (None = не предоставлено источником)
    aqi: int | None = None
    pm25: float | None = None            # мкг/м³
    pm10: float | None = None
    co: float | None = None              # мг/м³
    no2: float | None = None             # мкг/м³
    so2: float | None = None
    o3: float | None = None
    temperature: float | None = None     # °C
    humidity: float | None = None        # %

    # Исходный ответ от API для отладки
    source_raw: dict[str, Any] | None = None

    @field_validator("measured_at", mode="before")
    @classmethod
    def ensure_utc(cls, v: Any) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError(f"Invalid latitude: {v}")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError(f"Invalid longitude: {v}")
        return v
