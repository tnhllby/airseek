from datetime import datetime, timezone

import pytest
import respx
import httpx

from app.adapters.openaq import OpenAQAdapter, OPENAQ_BASE_URL, KYRGYZSTAN_COUNTRY_ID

LOCATIONS_RESPONSE = {
    "results": [
        {
            "id": 12345,
            "name": "Bishkek Central",
            "coordinates": {"latitude": 42.8746, "longitude": 74.5698},
        }
    ]
}

LATEST_RESPONSE = {
    "results": [
        {
            "parameter": {"name": "pm25"},
            "value": 24.5,
            "lastUpdated": "2026-06-24T10:30:00Z",
        },
        {
            "parameter": {"name": "pm10"},
            "value": 38.2,
            "lastUpdated": "2026-06-24T10:30:00Z",
        },
    ]
}


@pytest.mark.asyncio
class TestOpenAQAdapter:
    @respx.mock
    async def test_fetch_returns_measurement(self):
        respx.get(f"{OPENAQ_BASE_URL}/locations").mock(
            return_value=httpx.Response(200, json=LOCATIONS_RESPONSE)
        )
        respx.get(f"{OPENAQ_BASE_URL}/locations/12345/latest").mock(
            return_value=httpx.Response(200, json=LATEST_RESPONSE)
        )

        async with OpenAQAdapter() as adapter:
            results = await adapter.fetch()

        assert len(results) == 1
        m = results[0]
        assert m.source == "openaq"
        assert m.external_station_id == "12345"
        assert m.pm25 == 24.5
        assert m.pm10 == 38.2
        assert m.latitude == 42.8746
        assert m.longitude == 74.5698

    @respx.mock
    async def test_fetch_uses_numeric_country_id(self):
        """Проверяет что запрос использует числовой country_id=69, не строку 'KG'."""
        route = respx.get(f"{OPENAQ_BASE_URL}/locations").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        async with OpenAQAdapter() as adapter:
            await adapter.fetch()

        url = str(route.calls[0].request.url)
        assert f"country_id={KYRGYZSTAN_COUNTRY_ID}" in url

    @respx.mock
    async def test_fetch_empty_locations(self):
        respx.get(f"{OPENAQ_BASE_URL}/locations").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        async with OpenAQAdapter() as adapter:
            results = await adapter.fetch()

        assert results == []

    @respx.mock
    async def test_safe_fetch_on_http_error_returns_empty(self):
        respx.get(f"{OPENAQ_BASE_URL}/locations").mock(
            return_value=httpx.Response(429)
        )

        async with OpenAQAdapter() as adapter:
            results = await adapter.safe_fetch()

        assert results == []

    @respx.mock
    async def test_fetch_skips_location_without_coords(self):
        no_coords = {
            "results": [{"id": 99, "name": "No Coords", "coordinates": None}]
        }
        respx.get(f"{OPENAQ_BASE_URL}/locations").mock(
            return_value=httpx.Response(200, json=no_coords)
        )
        respx.get(f"{OPENAQ_BASE_URL}/locations/99/latest").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        async with OpenAQAdapter() as adapter:
            results = await adapter.fetch()

        assert results == []

    @respx.mock
    async def test_fetch_skips_location_with_no_measurements(self):
        respx.get(f"{OPENAQ_BASE_URL}/locations").mock(
            return_value=httpx.Response(200, json=LOCATIONS_RESPONSE)
        )
        respx.get(f"{OPENAQ_BASE_URL}/locations/12345/latest").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        async with OpenAQAdapter() as adapter:
            results = await adapter.fetch()

        assert results == []

    @respx.mock
    async def test_latest_http_error_skips_location(self):
        """429 на /latest не должен ронять весь fetch."""
        respx.get(f"{OPENAQ_BASE_URL}/locations").mock(
            return_value=httpx.Response(200, json=LOCATIONS_RESPONSE)
        )
        respx.get(f"{OPENAQ_BASE_URL}/locations/12345/latest").mock(
            return_value=httpx.Response(429)
        )

        async with OpenAQAdapter() as adapter:
            results = await adapter.fetch()

        assert results == []
