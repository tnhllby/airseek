"""
Точка входа сервиса сбора данных.
Запуск: python -m app.main
"""
import asyncio
import signal
import sys
import warnings

# tzlocal на Windows иногда видит расхождение UTC-offset — это не влияет на работу,
# т.к. scheduler явно использует timezone="UTC"
warnings.filterwarnings("ignore", message="Timezone offset does not match", module="tzlocal")

from app.core.logging import get_logger, setup_logging
from app.scheduler import build_adapters, collect_all, create_scheduler

setup_logging()
logger = get_logger(__name__)


async def run() -> None:
    logger.info("collector.starting")

    adapters = build_adapters()
    if not adapters:
        logger.error("collector.no_adapters", message="No adapters configured, exiting")
        sys.exit(1)

    logger.info("collector.initial_run")
    await collect_all(adapters)

    scheduler = create_scheduler(adapters)
    scheduler.start()
    logger.info("collector.scheduler_started")

    stop_event = asyncio.Event()

    if sys.platform != "win32":  # add_signal_handler доступен только на Unix
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

    try:
        await stop_event.wait()
    finally:
        scheduler.shutdown(wait=False)
        logger.info("collector.stopped")


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        # На Windows Ctrl+C бросает KeyboardInterrupt напрямую
        logger.info("collector.stopped")


if __name__ == "__main__":
    main()
