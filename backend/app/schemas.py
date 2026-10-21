from datetime import date, datetime

from pydantic import BaseModel, Field


class SensorEventIn(BaseModel):
    event_type: str = Field(pattern="^(enter|exit)$")
    source_event_id: str | None = Field(default=None, max_length=120)
    occurred_at: datetime | None = None


class ManualCrowdIn(BaseModel):
    observation_date: date
    hour: int = Field(ge=0, le=23)
    people_present: int = Field(ge=0, le=100000)
    entries: int = Field(default=0, ge=0)
    exits: int = Field(default=0, ge=0)


class PredictionIn(BaseModel):
    prediction_date: date
    hour: int = Field(ge=0, le=23)
    is_holiday: int = Field(default=0, ge=0, le=1)
    is_exam_period: int = Field(default=0, ge=0, le=1)
    days_to_exam: int = Field(default=30, ge=0, le=365)
    is_semester_break: int = Field(default=0, ge=0, le=1)
    library_capacity: int = Field(default=600, ge=1, le=100000)
    rainfall_mm: float | None = Field(default=None, ge=0)
    temperature_c: float | None = Field(default=None, ge=-80, le=80)
