from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.modules.ai import service
from app.modules.ai.schemas import AnalyzeRequest, PredictionResponse

router = APIRouter(prefix="/ai", tags=["ai"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/analyze", response_model=PredictionResponse, status_code=201)
async def analyze(request: AnalyzeRequest, db: DbSession) -> PredictionResponse:
    prediction = await service.analyze(
        db,
        station_id=request.station_id,
        question=request.question,
        hours=request.hours,
    )
    return PredictionResponse.model_validate(prediction)


@router.get("/predictions/{station_id}", response_model=list[PredictionResponse])
async def get_predictions(
    station_id: UUID,
    db: DbSession,
    limit: int = Query(10, ge=1, le=50),
) -> list[PredictionResponse]:
    predictions = await service.get_predictions(db, station_id, limit=limit)
    if not predictions:
        raise NotFoundError("No predictions found for this station")
    return [PredictionResponse.model_validate(p) for p in predictions]
