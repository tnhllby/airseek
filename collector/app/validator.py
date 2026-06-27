"""
Валидация и фильтрация измерений перед записью в БД.
Отбрасывает явно некорректные данные, не трогая бизнес-логику.
"""
from dataclasses import dataclass

from app.core.logging import get_logger
from app.schemas import RawMeasurement

logger = get_logger(__name__)

# Физически допустимые диапазоны значений
BOUNDS: dict[str, tuple[float, float]] = {
    "aqi": (0, 500),
    "pm25": (0, 1000),
    "pm10": (0, 1000),
    "co": (0, 150),          # мг/м³
    "no2": (0, 2000),        # мкг/м³
    "so2": (0, 2000),
    "o3": (0, 1000),
    "temperature": (-60, 60),
    "humidity": (0, 100),
}

# Координаты Бишкека (с запасом ~50 км)
BISHKEK_LAT_RANGE = (42.5, 43.3)
BISHKEK_LON_RANGE = (74.2, 75.0)


@dataclass
class ValidationResult:
    valid: list[RawMeasurement]
    rejected: list[tuple[RawMeasurement, str]]  # (measurement, reason)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)


def _check_bounds(measurement: RawMeasurement) -> list[str]:
    """Проверяет числовые поля на выход за физические границы."""
    errors: list[str] = []
    for field, (lo, hi) in BOUNDS.items():
        value = getattr(measurement, field, None)
        if value is None:
            continue
        if not lo <= value <= hi:
            errors.append(f"{field}={value} out of range [{lo}, {hi}]")
    return errors


def _check_location(measurement: RawMeasurement) -> str | None:
    """Проверяет, что координаты попадают в район Бишкека."""
    lat_ok = BISHKEK_LAT_RANGE[0] <= measurement.latitude <= BISHKEK_LAT_RANGE[1]
    lon_ok = BISHKEK_LON_RANGE[0] <= measurement.longitude <= BISHKEK_LON_RANGE[1]
    if not lat_ok or not lon_ok:
        return (
            f"coordinates ({measurement.latitude}, {measurement.longitude}) "
            "outside Bishkek bounds"
        )
    return None


def _has_any_measurement(measurement: RawMeasurement) -> bool:
    """Отклоняем запись если нет ни одного показателя."""
    fields = ["aqi", "pm25", "pm10", "co", "no2", "so2", "o3", "temperature", "humidity"]
    return any(getattr(measurement, f) is not None for f in fields)


def validate(measurements: list[RawMeasurement]) -> ValidationResult:
    valid: list[RawMeasurement] = []
    rejected: list[tuple[RawMeasurement, str]] = []

    for m in measurements:
        reasons: list[str] = []

        if not _has_any_measurement(m):
            reasons.append("no measurement values provided")

        loc_error = _check_location(m)
        if loc_error:
            reasons.append(loc_error)

        bound_errors = _check_bounds(m)
        reasons.extend(bound_errors)

        if reasons:
            reason_str = "; ".join(reasons)
            logger.warning(
                "validation.rejected",
                station=m.station_name,
                source=m.source,
                reasons=reason_str,
            )
            rejected.append((m, reason_str))
        else:
            valid.append(m)

    logger.info(
        "validation.done",
        total=len(measurements),
        valid=len(valid),
        rejected=len(rejected),
    )
    return ValidationResult(valid=valid, rejected=rejected)
