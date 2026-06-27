from openai import AsyncOpenAI

from app.modules.ai.adapters.base import AnalysisResult, BaseLLMAdapter
from app.modules.ai.adapters.claude import _extract_aqi, _extract_recommendations

_SYSTEM_PROMPT = """You are an air quality analyst for Bishkek, Kyrgyzstan.
Analyze the provided measurement data and respond in the same language as the user's question.
Provide: current conditions summary, health recommendations, AQI estimate if not given."""


class DeepSeekAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        self._model = model

    async def analyze(self, context: str, question: str | None = None) -> AnalysisResult:
        user_message = context
        if question:
            user_message += f"\n\nUser question: {question}"

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1024,
        )
        text = response.choices[0].message.content or ""
        predicted_aqi = _extract_aqi(text)

        return AnalysisResult(
            summary=text,
            recommendations=_extract_recommendations(text),
            predicted_aqi=predicted_aqi,
            confidence=0.75 if predicted_aqi else None,
            model_name=f"deepseek/{self._model}",
            model_version=self._model,
        )
