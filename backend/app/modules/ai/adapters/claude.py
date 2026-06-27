import anthropic

from app.modules.ai.adapters.base import AnalysisResult, BaseLLMAdapter

_SYSTEM_PROMPT = """You are an air quality analyst for Bishkek, Kyrgyzstan.
Analyze the provided measurement data and respond in the same language as the user's question (Russian or English).
Always include:
1. A brief summary of current air quality conditions
2. Health recommendations for sensitive groups and the general public
3. Your best estimate of the current AQI if not already provided

Be concise and practical. Focus on actionable advice."""


class ClaudeAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def analyze(self, context: str, question: str | None = None) -> AnalysisResult:
        user_message = context
        if question:
            user_message += f"\n\nUser question: {question}"

        message = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text = message.content[0].text

        # Try to extract AQI estimate from response
        predicted_aqi = _extract_aqi(text)

        return AnalysisResult(
            summary=text,
            recommendations=_extract_recommendations(text),
            predicted_aqi=predicted_aqi,
            confidence=0.8 if predicted_aqi else None,
            model_name=f"claude/{self._model}",
            model_version=self._model,
        )


def _extract_aqi(text: str) -> int | None:
    """Best-effort AQI extraction from response text."""
    import re
    for pattern in [r"AQI[:\s]+(\d+)", r"(\d+)\s*AQI", r"индекс[:\s]+(\d+)"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 500:
                return val
    return None


def _extract_recommendations(text: str) -> str:
    """Return the full text as recommendations if no clear section found."""
    lower = text.lower()
    for marker in ["recommendation", "рекомендаци", "advice", "совет"]:
        idx = lower.find(marker)
        if idx != -1:
            return text[idx:].strip()
    return text
