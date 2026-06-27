"""
Планировщик задач сбора данных.
Запускает все активные адаптеры по расписанию, валидирует и сохраняет данные.
"""
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.adapters import BaseSourceAdapter, HttpSensorAdapter, IQAirAdapter, OpenAQAdapter
from app.config import settings
from app.core.logging import get_logger
from app.database import AsyncSessionFactory
from app.validator import validate
from app.writer import save_measurements_batch

logger = get_logger(__name__)


def build_adapters() -> list[BaseSourceAdapter]:
    """Собирает список активных адаптеров из конфига."""
    adapters: list[BaseSourceAdapter] = []

    if settings.enable_openaq:
        adapters.append(OpenAQAdapter())
        logger.info("adapter.registered", source="openaq")

    if settings.enable_iqair:
        if not settings.iqair_api_key:
            logger.warning("adapter.skipped", source="iqair", reason="no API key")
        else:
            adapters.append(IQAirAdapter())
            logger.info("adapter.registered", source="iqair")

    if settings.enable_http_sensors:
        if not settings.http_sensor_url_list:
            logger.warning("adapter.skipped", source="http_sensor", reason="no URLs configured")
        else:
            adapters.append(HttpSensorAdapter())
            logger.info("adapter.registered", source="http_sensor", count=len(settings.http_sensor_url_list))

    return adapters


async def collect_all(adapters: list[BaseSourceAdapter]) -> None:
    """Один полный цикл сбора: fetch → validate → save."""
    logger.info("collect.start", adapter_count=len(adapters))

    all_raw = []
    for adapter in adapters:
        async with adapter:
            raw = await adapter.safe_fetch()
            all_raw.extend(raw)

    if not all_raw:
        logger.warning("collect.empty", message="No measurements fetched from any source")
        return

    result = validate(all_raw)

    if result.valid:
        async with AsyncSessionFactory() as session:
            saved = await save_measurements_batch(session, result.valid)
        logger.info("collect.done", saved=saved, rejected=result.rejected_count)
    else:
        logger.warning("collect.all_rejected", total=len(all_raw))


def create_scheduler(adapters: list[BaseSourceAdapter]) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        collect_all,
        trigger=IntervalTrigger(seconds=settings.collect_interval_seconds),
        args=[adapters],
        id="collect_all",
        name="Collect air quality data from all sources",
        max_instances=1,           # не запускать параллельно если предыдущий не завершился
        misfire_grace_time=60,     # пропустить, если опоздали больше 60 сек
    )

    return scheduler
