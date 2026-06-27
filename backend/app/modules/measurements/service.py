from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.measurements.models import Measurement


async def get_latest_measurements(
    db: AsyncSession,
    limit: int = 100,
) -> list[Measurement]:
    """Latest measurement per station — uses DISTINCT ON (station_id)."""
    from sqlalchemy import text

    # DISTINCT ON is PostgreSQL-specific but very efficient here
    stmt = text("""
        SELECT DISTINCT ON (station_id) *
        FROM measurements
        ORDER BY station_id, measured_at DESC
        LIMIT :limit
    """)
    result = await db.execute(stmt, {"limit": limit})
    rows = result.mappings().all()

    measurements = []
    for row in rows:
        m = Measurement(**{k: v for k, v in row.items()})
        measurements.append(m)
    return measurements


async def get_station_measurements(
    db: AsyncSession,
    station_id: UUID,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    limit: int = 200,
) -> list[Measurement]:
    stmt = (
        select(Measurement)
        .where(Measurement.station_id == station_id)
        .order_by(desc(Measurement.measured_at))
        .limit(limit)
    )
    if from_dt:
        stmt = stmt.where(Measurement.measured_at >= from_dt)
    if to_dt:
        stmt = stmt.where(Measurement.measured_at <= to_dt)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_latest_for_station(
    db: AsyncSession,
    station_id: UUID,
) -> Measurement | None:
    stmt = (
        select(Measurement)
        .where(Measurement.station_id == station_id)
        .order_by(desc(Measurement.measured_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
