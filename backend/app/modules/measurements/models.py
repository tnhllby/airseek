from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    measured_at = Column(DateTime(timezone=True), nullable=False)
    aqi = Column(BigInteger)
    pm25 = Column(Numeric(7, 2))
    pm10 = Column(Numeric(7, 2))
    co = Column(Numeric(7, 2))
    no2 = Column(Numeric(7, 2))
    so2 = Column(Numeric(7, 2))
    o3 = Column(Numeric(7, 2))
    temperature = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    source_raw = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    station = relationship("Station", back_populates="measurements", lazy="noload")
