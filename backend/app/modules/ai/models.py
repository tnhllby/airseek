from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    prediction_type = Column(String(50), nullable=False)  # 'analysis' | 'forecast'
    predicted_at = Column(DateTime(timezone=True), nullable=False)
    predicted_aqi = Column(BigInteger)
    confidence = Column(Numeric(4, 3))
    summary = Column(Text)
    recommendations = Column(Text)
    raw_response = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    station = relationship("Station", back_populates="predictions", lazy="noload")
