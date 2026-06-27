from unittest.mock import patch

import pytest
import respx
import httpx

from app.adapters.http_sensor import HttpSensorAdapter


SENSOR_RESPONSE = {
    "id": "sensor-001",
    "name": "Датчик Ала-Тоо",
    "lat": 42.8746,
    "lon": 74.5698,
    "timestamp": "2026-06-24T10:30:00Z",
    "pm25": 24.5,
    "pm10": 38.2,
    "aqi": 87,
    "temperature": 22.1,
    "humidity": 45.0,
}


@pytest.mark.asyncio
class TestHttpSensorAdapter:
    @respx.mock
    async def test_fetch_single_sensor(self):
        with patch("app.config.settings.http_sensor_urls", "http://192.168.1.10"):
            with patch("app.config.settings.enable_http_sensors", True):
                respx.get("http://192.168.1.10/data").mock(
                    return_value=httpx.Response(200, json=SENSOR_RESPONSE)
                )

                adapter = HttpSensorAdapter()
                adapter._urls = ["http://192.168.1.10"]
                async with adapter:
                    results = await adapter.fetch()

        assert len(results) == 1
        m = results[0]
        assert m.source == "physical"
        assert m.external_station_id == "sensor-001"
        assert m.pm25 == 24.5
        assert m.aqi == 87

    @respx.mock
    async def test_fetch_sensor_timeout_returns_empty(self):
        respx.get("http://192.168.1.10/data").mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        adapter = HttpSensorAdapter()
        adapter._urls = ["http://192.168.1.10"]
        async with adapter:
            results = await adapter.fetch()

        assert results == []

    async def test_no_urls_returns_empty(self):
        adapter = HttpSensorAdapter()
        adapter._urls = []
        async with adapter:
            results = await adapter.fetch()
        assert results == []

    @respx.mock
    async def test_sensor_without_coords_skipped(self):
        no_coords = {**SENSOR_RESPONSE, "lat": None, "lon": None}
        respx.get("http://192.168.1.10/data").mock(
            return_value=httpx.Response(200, json=no_coords)
        )

        adapter = HttpSensorAdapter()
        adapter._urls = ["http://192.168.1.10"]
        async with adapter:
            results = await adapter.fetch()

        assert results == []
