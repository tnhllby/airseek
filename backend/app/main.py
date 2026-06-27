from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

# Import routers — this also registers all SQLAlchemy models transitively
from app.modules.ai.router import router as ai_router
from app.modules.measurements.router import router as measurements_router
from app.modules.notifications.router import router as notifications_router
from app.modules.stations.router import router as stations_router
from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("backend.starting", ai_provider=settings.ai_provider)
    yield
    logger.info("backend.stopped")


app = FastAPI(
    title="AirSeek API",
    description="Air quality monitoring API for Bishkek, Kyrgyzstan",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"

app.include_router(stations_router, prefix=PREFIX)
app.include_router(measurements_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(notifications_router, prefix=PREFIX)
app.include_router(ai_router, prefix=PREFIX)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "airseek-backend"}
