"""
Адаптер IQAir / AirVisual API.
Документация: https://api-docs.iqair.com/
Бесплатный тариф: 10 000 вызовов/месяц, 1 запрос/сек.
"""
from datetime import datetime, timezone

from app.adapters.base import BaseSourceAdapter
from app.config import settings
from app.core.logging import get_logger
from app.schemas import RawMeasurement

logger = get_logger(__name__)

IQAIR_BASE_URL = "https://api.airvisual.com/v2"


class IQAirAdapter(BaseSourceAdapter):
    source_name = "iqair"

    def __init__(self) -> None:
        super().__init__()
        self._api_key = settings.iqair_api_key
        self._city = settings.iqair_city
        self._state = settings.iqair_state
        self._country = settings.iqair_country

    async def fetch(self) -> list[RawMeasurement]:
        if not self._api_key:
            logger.warning("iqair.no_api_key")
            return []

        resp = await self.client.get(
            f"{IQAIR_BASE_URL}/city",
            params={
                "city": self._city,
                "state": self._state,
                "country": self._country,
                "key": self._api_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "success":
            logger.error("iqair.api_error", response=data)
            return []

        return [self._parse(data["data"])]

    def _parse(self, data: dict) -> RawMeasurement:
        location = data.get("location", {})
        coords = location.get("coordinates", [0, 0])

        current = data.get("current", {})
        pollution = current.get("pollution", {})
        weather = current.get("weather", {})

        ts_str = pollution.get("ts", "")
        try:
            measured_at = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            measured_at = datetime.now(timezone.utc)

        return RawMeasurement(
            source=self.source_name,
            external_station_id=f"iqair_{self._city}_{self._state}".lower().replace(" ", "_"),
            station_name=f"{self._city}, {self._state}",
            latitude=float(coords[1]),   # IQAir: [lon, lat]
            longitude=float(coords[0]),
            measured_at=measured_at,
            aqi=pollution.get("aqius"),  # US AQI
            pm25=pollution.get("p2", {}).get("conc"),
            pm10=pollution.get("p1", {}).get("conc"),
            temperature=weather.get("tp"),
            humidity=weather.get("hu"),
            source_raw=data,
        )
