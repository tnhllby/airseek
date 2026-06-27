from datetime import datetime, timezone

import pytest

from app.schemas import RawMeasurement
from app.validator import validate


def _make(
    lat: float = 42.87,
    lon: float = 74.57,
    pm25: float | None = 24.5,
    aqi: int | None = 87,
    **kwargs,
) -> RawMeasurement:
    return RawMeasurement(
        source="openaq",
        external_station_id="test-001",
        station_name="Test Station",
        latitude=lat,
        longitude=lon,
        measured_at=datetime(2026, 6, 24, 10, 0, tzinfo=timezone.utc),
        pm25=pm25,
        aqi=aqi,
        **kwargs,
    )


class TestValidatorBounds:
    def test_valid_measurement_passes(self):
        result = validate([_make()])
        assert len(result.valid) == 1
        assert result.rejected_count == 0

    def test_aqi_out_of_range_rejected(self):
        result = validate([_make(aqi=600)])
        assert result.rejected_count == 1
        assert "aqi" in result.rejected[0][1]

    def test_pm25_negative_rejected(self):
        result = validate([_make(pm25=-1.0)])
        assert result.rejected_count == 1

    def test_temperature_extreme_rejected(self):
        result = validate([_make(temperature=100.0)])
        assert result.rejected_count == 1

    def test_humidity_over_100_rejected(self):
        result = validate([_make(humidity=101.0)])
        assert result.rejected_count == 1


class TestValidatorLocation:
    def test_outside_bishkek_rejected(self):
        result = validate([_make(lat=55.75, lon=37.61)])  # Moscow
        assert result.rejected_count == 1
        assert "outside Bishkek" in result.rejected[0][1]

    def test_edge_of_bishkek_passes(self):
        result = validate([_make(lat=42.5, lon=74.2)])
        assert len(result.valid) == 1


class TestValidatorEmptyValues:
    def test_no_measurement_values_rejected(self):
        result = validate([_make(pm25=None, aqi=None)])
        assert result.rejected_count == 1
        assert "no measurement values" in result.rejected[0][1]

    def test_only_temperature_passes(self):
        result = validate([_make(pm25=None, aqi=None, temperature=22.0)])
        assert len(result.valid) == 1


class TestValidatorBatch:
    def test_mixed_batch(self):
        good = _make()
        bad = _make(aqi=999)
        result = validate([good, bad])
        assert len(result.valid) == 1
        assert result.rejected_count == 1

    def test_empty_input(self):
        result = validate([])
        assert len(result.valid) == 0
        assert result.rejected_count == 0
