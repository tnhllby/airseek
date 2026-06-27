from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.config import settings
from app.core.exceptions import NotFoundError
from app.modules.ai.adapters.base import BaseLLMAdapter
from app.modules.ai.models import AIPrediction
from app.modules.measurements.models import Measurement
from app.modules.stations.models import Station


def get_adapter() -> BaseLLMAdapter:
    provider = settings.ai_provider
    match provider:
        case "claude":
            if not settings.claude_api_key:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "CLAUDE_API_KEY not configured")
            from app.modules.ai.adapters.claude import ClaudeAdapter
            return ClaudeAdapter(settings.claude_api_key, settings.claude_model)
        case "deepseek":
            if not settings.deepseek_api_key:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "DEEPSEEK_API_KEY not configured")
            from app.modules.ai.adapters.deepseek import DeepSeekAdapter
            return DeepSeekAdapter(settings.deepseek_api_key, settings.deepseek_model)
        case "gemini":
            if not settings.gemini_api_key:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "GEMINI_API_KEY not configured")
            from app.modules.ai.adapters.gemini import GeminiAdapter
            return GeminiAdapter(settings.gemini_api_key, settings.gemini_model)
        case _:
            from app.modules.ai.adapters.local_llm import OllamaAdapter
            return OllamaAdapter(settings.ollama_url, settings.ollama_model)


def _format_context(
    station: Station,
    measurements: list[Measurement],
) -> str:
    if not measurements:
        return f"Station: {station.name}\nNo recent measurements available."

    latest = measurements[0]
    lines = [
        f"Station: {station.name}",
        f"Location: lat={float(station.latitude):.4f}, lon={float(station.longitude):.4f}",
        f"District: {station.district or 'Unknown'}",
        "",
        "Latest reading:",
    ]
    for field in ("aqi", "pm25", "pm10", "co", "no2", "so2", "o3", "temperature", "humidity"):
        val = getattr(latest, field)
        if val is not None:
            lines.append(f"  {field}: {float(val):.2f}")
    lines.append(f"  measured_at: {latest.measured_at.isoformat()}")

    if len(measurements) > 1:
        lines += ["", f"Historical data (last {len(measurements)} readings):"]
        pm25_vals = [float(m.pm25) for m in measurements if m.pm25 is not None]
        aqi_vals = [int(m.aqi) for m in measurements if m.aqi is not None]
        if pm25_vals:
            lines.append(f"  PM2.5 avg: {sum(pm25_vals)/len(pm25_vals):.2f}, max: {max(pm25_vals):.2f}")
        if aqi_vals:
            lines.append(f"  AQI avg: {sum(aqi_vals)/len(aqi_vals):.0f}, max: {max(aqi_vals)}")

    return "\n".join(lines)


async def analyze(
    db: AsyncSession,
    station_id: UUID | None,
    question: str | None,
    hours: int = 24,
) -> AIPrediction:
    # Pick first active station if none specified (citywide = representative station)
    if station_id is None:
        result = await db.execute(
            select(Station).where(Station.is_active == True).limit(1)  # noqa: E712
        )
        station = result.scalar_one_or_none()
    else:
        result = await db.execute(select(Station).where(Station.id == station_id))
        station = result.scalar_one_or_none()

    if station is None:
        raise NotFoundError("Station not found")

    from_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    measurements_result = await db.execute(
        select(Measurement)
        .where(
            Measurement.station_id == station.id,
            Measurement.measured_at >= from_dt,
        )
        .order_by(desc(Measurement.measured_at))
        .limit(50)
    )
    measurements = list(measurements_result.scalars().all())

    context = _format_context(station, measurements)
    prediction_type = "citywide_analysis" if station_id is None else "station_analysis"

    adapter = get_adapter()
    result_data = await adapter.analyze(context, question)

    prediction = AIPrediction(
        station_id=station.id,
        model_name=result_data.model_name,
        model_version=result_data.model_version,
        prediction_type=prediction_type,
        predicted_at=datetime.now(timezone.utc),
        predicted_aqi=result_data.predicted_aqi,
        confidence=result_data.confidence,
        summary=result_data.summary,
        recommendations=result_data.recommendations,
        raw_response={"question": question, "context_lines": len(context.splitlines())},
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)
    return prediction


async def get_predictions(
    db: AsyncSession,
    station_id: UUID,
    limit: int = 10,
) -> list[AIPrediction]:
    result = await db.execute(
        select(AIPrediction)
        .where(AIPrediction.station_id == station_id)
        .order_by(desc(AIPrediction.predicted_at))
        .limit(limit)
    )
    return list(result.scalars().all())
