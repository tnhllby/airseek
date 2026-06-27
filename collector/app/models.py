"""
SQLAlchemy models — зеркало схемы backend. Collector только читает stations
и пишет measurements, поэтому здесь только необходимые таблицы.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Numeric,
    String, Text, ForeignKey, JSON, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Station(Base):
    __tablename__ = "stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    district = Column(String(100))
    source = Column(String(50), nullable=False)   # 'openaq' | 'iqair' | 'physical'
    external_id = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    measurements = relationship("Measurement", back_populates="station")


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

    station = relationship("Station", back_populates="measurements")
