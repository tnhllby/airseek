import httpx

from app.modules.ai.adapters.base import AnalysisResult, BaseLLMAdapter
from app.modules.ai.adapters.claude import _extract_aqi, _extract_recommendations

_SYSTEM_PROMPT = (
    "You are an air quality analyst for Bishkek, Kyrgyzstan. "
    "Analyze the provided data and give a concise summary with health recommendations."
)


class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def analyze(self, context: str, question: str | None = None) -> AnalysisResult:
        prompt = f"{_SYSTEM_PROMPT}\n\n{context}"
        if question:
            prompt += f"\n\nQuestion: {question}"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            text = resp.json().get("response", "")

        predicted_aqi = _extract_aqi(text)

        return AnalysisResult(
            summary=text,
            recommendations=_extract_recommendations(text),
            predicted_aqi=predicted_aqi,
            confidence=0.6 if predicted_aqi else None,
            model_name=f"ollama/{self._model}",
            model_version=self._model,
        )
