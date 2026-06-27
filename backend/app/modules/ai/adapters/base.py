from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    summary: str
    recommendations: str
    predicted_aqi: int | None
    confidence: float | None
    model_name: str
    model_version: str | None = None


class BaseLLMAdapter(ABC):
    @abstractmethod
    async def analyze(self, context: str, question: str | None = None) -> AnalysisResult: ...
