"""
Адаптер OpenAQ API v3.
Документация: https://docs.openaq.org/

Стратегия сбора:
  1. GET /v3/locations?countries_id=69       — станции Кыргызстана
  2. GET /v3/locations/{id}/sensors          — сенсоры с последними значениями

Важно:
  - countries_id (мн.ч.), не country_id — country_id игнорируется и возвращает Гану
  - /latest возвращает sensorsId без имени параметра; /sensors содержит parameter.name и latest.value
"""
import asyncio
from datetime import datetime, timezone

from app.adapters.base import BaseSourceAdapter
from app.config import settings
from app.core.logging import get_logger
from app.schemas import RawMeasurement

logger = get_logger(__name__)

OPENAQ_BASE_URL = "https://api.openaq.org/v3"

# Числовой id Кыргызстана в OpenAQ (/v3/countries → id=69)
KYRGYZSTAN_COUNTRY_ID = 69

# Задержка между запросами — 50 станций × 0.3s ≈ 15 сек на цикл
REQUEST_DELAY = 0.3

PARAM_MAP: dict[str, str] = {
    "pm25":             "pm25",
    "pm10":             "pm10",
    "co":               "co",
    "no2":              "no2",
    "so2":              "so2",
    "o3":               "o3",
    "temperature":      "temperature",
    "relativehumidity": "humidity",
}


class OpenAQAdapter(BaseSourceAdapter):
    source_name = "openaq"

    def __init__(self) -> None:
        super().__init__()
        self._api_key = settings.openaq_api_key

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _get_locations(self) -> list[dict]:
        """Запрос 1: все активные станции Кыргызстана."""
        resp = await self.client.get(
            f"{OPENAQ_BASE_URL}/locations",
            headers=self._headers(),
            params={
                "countries_id": KYRGYZSTAN_COUNTRY_ID,
                "limit": 50,
            },
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

    async def _get_sensors(self, location_id: int) -> list[dict]:
        """
        GET /v3/locations/{id}/sensors
        Каждый sensor: {"parameter": {"name": "pm25"}, "latest": {"value": ..., "datetime": {"utc": "..."}}}
        В отличие от /latest, содержит имя параметра — не только sensorsId.
        """
        resp = await self.client.get(
            f"{OPENAQ_BASE_URL}/locations/{location_id}/sensors",
            headers=self._headers(),
        )
        if resp.status_code == 429:
            logger.warning("openaq.rate_limited", location_id=location_id)
            return []
        resp.raise_for_status()
        return resp.json().get("results", [])

    async def _get_all_sensors(self, location_ids: list[int]) -> dict[int, list[dict]]:
        """Последовательно запрашивает sensors для каждой станции с задержкой."""
        sensors_map: dict[int, list[dict]] = {}

        for loc_id in location_ids:
            try:
                sensors_map[loc_id] = await self._get_sensors(loc_id)
            except Exception as exc:
                logger.warning("openaq.sensors_failed", location_id=loc_id, error=str(exc))
            await asyncio.sleep(REQUEST_DELAY)

        return sensors_map

    def _parse_location(
        self,
        location: dict,
        sensors: list[dict],
    ) -> RawMeasurement | None:
        coords = location.get("coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        if lat is None or lon is None:
            return None

        fields: dict[str, float] = {}
        measured_at: datetime | None = None

        for sensor in sensors:
            param = (sensor.get("parameter") or {}).get("name", "").lower()
            field = PARAM_MAP.get(param)
            if not field:
                continue

            latest = sensor.get("latest") or {}
            value = latest.get("value")
            if value is not None:
                fields[field] = float(value)

            ts_str = (latest.get("datetime") or {}).get("utc", "")
            if ts_str:
                try:
                    t = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if measured_at is None or t > measured_at:
                        measured_at = t
                except ValueError:
                    pass

        if not fields:
            return None

        if measured_at is None:
            measured_at = datetime.now(timezone.utc)

        return RawMeasurement(
            source=self.source_name,
            external_station_id=str(location["id"]),
            station_name=location.get("name") or f"OpenAQ-{location['id']}",
            latitude=float(lat),
            longitude=float(lon),
            measured_at=measured_at,
            pm25=fields.get("pm25"),
            pm10=fields.get("pm10"),
            co=fields.get("co"),
            no2=fields.get("no2"),
            so2=fields.get("so2"),
            o3=fields.get("o3"),
            temperature=fields.get("temperature"),
            humidity=fields.get("humidity"),
            source_raw={"location_id": location["id"]},
        )

    async def fetch(self) -> list[RawMeasurement]:
        locations = await self._get_locations()
        if not locations:
            logger.warning("openaq.no_locations", country_id=KYRGYZSTAN_COUNTRY_ID)
            return []

        logger.info("openaq.locations_found", count=len(locations))

        location_ids = [loc["id"] for loc in locations if loc.get("id")]
        sensors_map = await self._get_all_sensors(location_ids)

        loc_index = {loc["id"]: loc for loc in locations}
        results: list[RawMeasurement] = []

        for loc_id, sensors in sensors_map.items():
            loc = loc_index.get(loc_id)
            if not loc:
                continue
            measurement = self._parse_location(loc, sensors)
            if measurement:
                results.append(measurement)

        return results
