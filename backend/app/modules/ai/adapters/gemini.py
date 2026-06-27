from fastapi import HTTPException, status
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.modules.ai.adapters.base import AnalysisResult, BaseLLMAdapter
from app.modules.ai.adapters.claude import _extract_aqi, _extract_recommendations

_SYSTEM_PROMPT = (
    "You are an air quality analyst for Bishkek, Kyrgyzstan. "
    "Analyze the provided measurement data and respond in the same language as the user's question "
    "(Russian or English). Always include: a brief summary of current conditions, "
    "health recommendations for sensitive groups and the general public, "
    "and your best AQI estimate if not already provided. Be concise and practical."
)


class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def analyze(self, context: str, question: str | None = None) -> AnalysisResult:
        user_message = context
        if question:
            user_message += f"\n\nUser question: {question}"

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    max_output_tokens=1024,
                    temperature=0.4,
                ),
            )
        except genai_errors.ClientError as exc:
            http_code = exc.code if hasattr(exc, "code") else 500
            if http_code == 429:
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Gemini rate limit exceeded. Retry after a minute.",
                )
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"Gemini error: {exc}")
        text = response.text or ""
        predicted_aqi = _extract_aqi(text)

        return AnalysisResult(
            summary=text,
            recommendations=_extract_recommendations(text),
            predicted_aqi=predicted_aqi,
            confidence=0.8 if predicted_aqi else None,
            model_name=f"gemini/{self._model}",
            model_version=self._model,
        )
