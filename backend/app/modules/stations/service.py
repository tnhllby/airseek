import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.stations.models import Station


async def get_stations(db: AsyncSession, active_only: bool = True) -> list[Station]:
    stmt = select(Station)
    if active_only:
        stmt = stmt.where(Station.is_active == True)  # noqa: E712
    stmt = stmt.order_by(Station.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_station(db: AsyncSession, station_id: UUID) -> Station | None:
    result = await db.execute(select(Station).where(Station.id == station_id))
    return result.scalar_one_or_none()


async def get_nearest_stations(
    db: AsyncSession,
    lat: float,
    lon: float,
    limit: int = 5,
) -> list[tuple[Station, float]]:
    """Returns list of (station, distance_km) sorted by distance."""
    stations = await get_stations(db)

    def _haversine(s: Station) -> float:
        r = 6371.0
        lat1, lon1 = math.radians(float(s.latitude)), math.radians(float(s.longitude))
        lat2, lon2 = math.radians(lat), math.radians(lon)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return r * 2 * math.asin(math.sqrt(a))

    ranked = sorted(((s, _haversine(s)) for s in stations), key=lambda x: x[1])
    return ranked[:limit]
