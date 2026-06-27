"""
Записывает провалидированные измерения в PostgreSQL.
Логика upsert станции + insert измерения.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Measurement, Station
from app.schemas import RawMeasurement

logger = get_logger(__name__)


async def upsert_station(session: AsyncSession, raw: RawMeasurement) -> uuid.UUID:
    """
    Находит станцию по (source, external_id) или создаёт новую.
    Возвращает station.id.
    """
    stmt = select(Station).where(
        Station.source == raw.source,
        Station.external_id == raw.external_station_id,
    )
    result = await session.execute(stmt)
    station = result.scalar_one_or_none()

    if station is None:
        station = Station(
            name=raw.station_name,
            latitude=raw.latitude,
            longitude=raw.longitude,
            source=raw.source,
            external_id=raw.external_station_id,
        )
        session.add(station)
        await session.flush()
        logger.info("station.created", name=raw.station_name, source=raw.source)
    else:
        # Обновляем координаты если источник их изменил
        station.latitude = raw.latitude
        station.longitude = raw.longitude

    return station.id


async def save_measurement(session: AsyncSession, raw: RawMeasurement) -> None:
    station_id = await upsert_station(session, raw)

    measurement = Measurement(
        station_id=station_id,
        measured_at=raw.measured_at,
        aqi=raw.aqi,
        pm25=raw.pm25,
        pm10=raw.pm10,
        co=raw.co,
        no2=raw.no2,
        so2=raw.so2,
        o3=raw.o3,
        temperature=raw.temperature,
        humidity=raw.humidity,
        source_raw=raw.source_raw,
    )
    session.add(measurement)
    logger.debug(
        "measurement.saved",
        station=raw.station_name,
        aqi=raw.aqi,
        measured_at=raw.measured_at.isoformat(),
    )


async def save_measurements_batch(
    session: AsyncSession,
    measurements: list[RawMeasurement],
) -> int:
    """Сохраняет список измерений в одной транзакции. Возвращает кол-во сохранённых."""
    if not measurements:
        return 0

    saved = 0
    for raw in measurements:
        try:
            await save_measurement(session, raw)
            saved += 1
        except Exception as exc:
            logger.error(
                "measurement.save_failed",
                station=raw.station_name,
                error=str(exc),
            )

    await session.commit()
    logger.info("batch.saved", count=saved, total=len(measurements))
    return saved
