import uuid

from sqlalchemy import Boolean, Column, Numeric, String, Text
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    district = Column(String(100))
    source = Column(String(50), nullable=False)
    external_id = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    measurements = relationship("Measurement", back_populates="station", lazy="noload")
    subscriptions = relationship("UserSubscription", back_populates="station", lazy="noload")
    predictions = relationship("AIPrediction", back_populates="station", lazy="noload")
