from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas import RawMeasurement


def _base() -> dict:
    return {
        "source": "openaq",
        "external_station_id": "test-001",
        "station_name": "Test",
        "latitude": 42.87,
        "longitude": 74.57,
        "measured_at": "2026-06-24T10:00:00Z",
    }


class TestRawMeasurement:
    def test_valid_minimal(self):
        m = RawMeasurement(**_base(), pm25=10.0)
        assert m.pm25 == 10.0
        assert m.measured_at.tzinfo is not None

    def test_timestamp_z_suffix_parsed(self):
        m = RawMeasurement(**_base())
        assert m.measured_at.tzinfo == timezone.utc

    def test_naive_datetime_gets_utc(self):
        data = {**_base(), "measured_at": datetime(2026, 6, 24, 10, 0)}
        m = RawMeasurement(**data)
        assert m.measured_at.tzinfo is not None

    def test_invalid_latitude(self):
        with pytest.raises(ValidationError):
            RawMeasurement(**{**_base(), "latitude": 200.0})

    def test_invalid_longitude(self):
        with pytest.raises(ValidationError):
            RawMeasurement(**{**_base(), "longitude": -200.0})

    def test_all_fields_none_allowed(self):
        m = RawMeasurement(**_base())
        assert m.aqi is None
        assert m.pm25 is None
