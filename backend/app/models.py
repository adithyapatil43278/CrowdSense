from datetime import datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class SensorEvent(Base):
    __tablename__ = "sensor_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(5))
    source_event_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class OccupancyState(Base):
    __tablename__ = "occupancy_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HourlyCrowd(Base):
    __tablename__ = "hourly_crowd"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observation_date: Mapped[datetime] = mapped_column(Date, index=True)
    hour: Mapped[int] = mapped_column(Integer)
    people_present: Mapped[int] = mapped_column(Integer)
    entries: Mapped[int] = mapped_column(Integer, default=0)
    exits: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(30), default="manual")
    __table_args__ = (UniqueConstraint("observation_date", "hour", name="uq_hourly_date_hour"),)


class ImportRecord(Base):
    __tablename__ = "import_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    row_count: Mapped[int] = mapped_column(Integer)
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)
