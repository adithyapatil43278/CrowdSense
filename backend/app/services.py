from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd
import joblib

from .config import get_settings


FEATURES = [
    "hour", "day_of_week", "is_holiday", "is_exam_period", "days_to_exam",
    "rainfall_mm", "temperature_c", "is_semester_break", "library_capacity",
]


def _default_weather(day: date) -> tuple[float, float]:
    settings = get_settings()
    params = {
        "latitude": settings.weather_latitude,
        "longitude": settings.weather_longitude,
        "daily": "temperature_2m_max,precipitation_sum",
        "timezone": "auto",
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
    }
    if settings.weather_api_key:
        params["apikey"] = settings.weather_api_key
    try:
        response = httpx.get(settings.weather_api_url, params=params, timeout=8)
        response.raise_for_status()
        daily = response.json().get("daily", {})
        return float(daily.get("precipitation_sum", [0])[0]), float(daily.get("temperature_2m_max", [29])[0])
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return 0.0, 29.0


def predict(payload: dict) -> int:
    settings = get_settings()
    model_path = Path(settings.model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Prediction model not found: {model_path}")
    day = payload["prediction_date"]
    rainfall, temperature = _default_weather(day)
    row = {
        "hour": payload["hour"],
        "day_of_week": day.weekday(),
        "is_holiday": payload["is_holiday"],
        "is_exam_period": payload["is_exam_period"],
        "days_to_exam": payload["days_to_exam"],
        "rainfall_mm": rainfall if payload.get("rainfall_mm") is None else payload["rainfall_mm"],
        "temperature_c": temperature if payload.get("temperature_c") is None else payload["temperature_c"],
        "is_semester_break": payload["is_semester_break"],
        "library_capacity": payload["library_capacity"],
    }
    model = joblib.load(model_path)
    prediction = float(model.predict(pd.DataFrame([row], columns=FEATURES))[0])
    return max(0, min(payload["library_capacity"], round(prediction)))
