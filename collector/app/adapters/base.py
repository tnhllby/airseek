"""
Абстрактный адаптер источника данных.
Каждый новый источник реализует только fetch() — всё остальное в BaseSourceAdapter.
"""
from abc import ABC, abstractmethod

import httpx

from app.core.logging import get_logger
from app.schemas import RawMeasurement

logger = get_logger(__name__)

# Таймаут HTTP-запросов по умолчанию
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class BaseSourceAdapter(ABC):
    """
    Контракт:
      - fetch() → list[RawMeasurement]  (может вернуть пустой список)
      - source_name: str — уникальный идентификатор источника
    """

    source_name: str

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BaseSourceAdapter":
        self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Adapter must be used as async context manager")
        return self._client

    @abstractmethod
    async def fetch(self) -> list[RawMeasurement]:
        """Запросить данные из источника и вернуть нормализованные измерения."""
        ...

    async def safe_fetch(self) -> list[RawMeasurement]:
        """Обёртка с обработкой ошибок — вызывается из scheduler."""
        try:
            results = await self.fetch()
            logger.info(
                "adapter.fetch_ok",
                source=self.source_name,
                count=len(results),
            )
            return results
        except httpx.TimeoutException:
            logger.warning("adapter.timeout", source=self.source_name)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "adapter.http_error",
                source=self.source_name,
                status=exc.response.status_code,
            )
        except Exception as exc:
            logger.error(
                "adapter.unexpected_error",
                source=self.source_name,
                error=str(exc),
                exc_info=True,
            )
        return []
