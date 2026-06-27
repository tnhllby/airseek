"""
Адаптер для физических датчиков с HTTP-интерфейсом.
Ожидаемый формат ответа от датчика (GET /data):
{
  "id": "sensor-001",
  "name": "Датчик Ала-Тоо",
  "lat": 42.8746,
  "lon": 74.5698,
  "timestamp": "2026-06-24T10:30:00Z",
  "pm25": 24.5,
  "pm10": 38.2,
  "co": 0.8,
  "no2": 12.1,
  "so2": 5.0,
  "o3": 45.0,
  "temperature": 22.1,
  "humidity": 45.0,
  "aqi": 87
}
"""
import asyncio
from datetime import datetime, timezone

from app.adapters.base import BaseSourceAdapter
from app.config import settings
from app.core.logging import get_logger
from app.schemas import RawMeasurement

logger = get_logger(__name__)


class HttpSensorAdapter(BaseSourceAdapter):
    source_name = "physical"

    def __init__(self) -> None:
        super().__init__()
        self._urls = settings.http_sensor_url_list

    async def fetch(self) -> list[RawMeasurement]:
        if not self._urls:
            return []

        tasks = [self._fetch_one(url) for url in self._urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        measurements: list[RawMeasurement] = []
        for url, result in zip(self._urls, results):
            if isinstance(result, Exception):
                logger.error("http_sensor.fetch_failed", url=url, error=str(result))
                continue
            if result is not None:
                measurements.append(result)

        return measurements

    async def _fetch_one(self, base_url: str) -> RawMeasurement | None:
        url = f"{base_url.rstrip('/')}/data"
        resp = await self.client.get(url)
        resp.raise_for_status()
        data = resp.json()
        return self._parse(data, base_url)

    def _parse(self, data: dict, base_url: str) -> RawMeasurement | None:
        sensor_id = data.get("id") or base_url
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            logger.warning("http_sensor.no_coords", sensor_id=sensor_id)
            return None

        ts_raw = data.get("timestamp")
        try:
            measured_at = datetime.fromisoformat(
                str(ts_raw).replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            measured_at = datetime.now(timezone.utc)

        return RawMeasurement(
            source=self.source_name,
            external_station_id=str(sensor_id),
            station_name=data.get("name") or f"Sensor-{sensor_id}",
            latitude=float(lat),
            longitude=float(lon),
            measured_at=measured_at,
            aqi=data.get("aqi"),
            pm25=data.get("pm25"),
            pm10=data.get("pm10"),
            co=data.get("co"),
            no2=data.get("no2"),
            so2=data.get("so2"),
            o3=data.get("o3"),
            temperature=data.get("temperature"),
            humidity=data.get("humidity"),
            source_raw=data,
        )
