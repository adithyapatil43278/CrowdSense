import csv
import io
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import func, select, tuple_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .config import ROOT_DIR, get_settings
from .db import get_db, init_db
from .models import HourlyCrowd, OccupancyState, SensorEvent
from .schemas import ManualCrowdIn, PredictionIn, SensorEventIn
from .services import predict

app = FastAPI(title="Indoor Crowd Monitor", version="1.0.0")
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=ROOT_DIR / "frontend" / "static"), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()


def require_token(authorization: str | None = Header(default=None)) -> None:
    expected = get_settings().api_token
    if not authorization or authorization.removeprefix("Bearer ").strip() != expected:
        raise HTTPException(status_code=401, detail="Valid bearer token required")


def state(db: Session) -> OccupancyState:
    result = db.get(OccupancyState, 1)
    if result is None:
        result = OccupancyState(id=1, current_occupancy=0)
        db.add(result)
        db.flush()
    return result


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    today = date.today()
    current = state(db).current_occupancy
    entries = db.scalar(select(func.count(SensorEvent.id)).where(SensorEvent.event_type == "enter", func.date(SensorEvent.occurred_at) == today)) or 0
    exits = db.scalar(select(func.count(SensorEvent.id)).where(SensorEvent.event_type == "exit", func.date(SensorEvent.occurred_at) == today)) or 0
    rows = db.scalars(select(HourlyCrowd).order_by(HourlyCrowd.observation_date.desc(), HourlyCrowd.hour.desc()).limit(168)).all()
    return {"current_occupancy": current, "daily_entries": entries, "daily_exits": exits, "history": [
        {"date": r.observation_date.isoformat(), "hour": r.hour, "people_present": r.people_present, "entries": r.entries, "exits": r.exits} for r in reversed(rows)
    ]}


@app.post("/api/events", dependencies=[Depends(require_token)])
def record_event(payload: SensorEventIn, db: Session = Depends(get_db)) -> dict:
    if payload.source_event_id and db.scalar(select(SensorEvent).where(SensorEvent.source_event_id == payload.source_event_id)):
        return {"accepted": False, "duplicate": True, "occupancy": state(db).current_occupancy}
    current = state(db)
    delta = 1 if payload.event_type == "enter" else -1
    current.current_occupancy = max(0, current.current_occupancy + delta)
    event = SensorEvent(event_type=payload.event_type, source_event_id=payload.source_event_id, occurred_at=payload.occurred_at or datetime.utcnow())
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"accepted": False, "duplicate": True, "occupancy": state(db).current_occupancy}
    return {"accepted": True, "duplicate": False, "occupancy": current.current_occupancy}


@app.post("/api/history/manual", dependencies=[Depends(require_token)])
def manual_history(payload: ManualCrowdIn, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(select(HourlyCrowd).where(HourlyCrowd.observation_date == payload.observation_date, HourlyCrowd.hour == payload.hour))
    if row is None:
        row = HourlyCrowd(**payload.model_dump(), source="manual")
        db.add(row)
    else:
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
        row.source = "manual"
    db.commit()
    return {"saved": True}


@app.post("/api/history/import", dependencies=[Depends(require_token)])
async def import_history(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    try:
        content = (await file.read()).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(content))
    required = {"date", "hour", "people_present"}
    if not required.issubset(reader.fieldnames or set()):
        raise HTTPException(status_code=400, detail=f"CSV requires columns: {', '.join(sorted(required))}")

    parsed: dict[tuple[date, int], ManualCrowdIn] = {}
    for raw in reader:
        try:
            data = ManualCrowdIn(
                observation_date=date.fromisoformat(raw["date"]), hour=int(raw["hour"]),
                people_present=int(raw["people_present"]), entries=int(raw.get("entries") or 0), exits=int(raw.get("exits") or 0),
            )
        except (ValueError, TypeError, ValidationError):
            raise HTTPException(status_code=400, detail=f"Invalid row: {raw}")
        parsed[(data.observation_date, data.hour)] = data

    keys = list(parsed)
    existing = {}
    if keys:
        existing_rows = db.scalars(
            select(HourlyCrowd).where(
                tuple_(HourlyCrowd.observation_date, HourlyCrowd.hour).in_(keys)
            )
        ).all()
        existing = {(row.observation_date, row.hour): row for row in existing_rows}

    for key, data in parsed.items():
        row = existing.get(key)
        if row is None:
            db.add(HourlyCrowd(**data.model_dump(), source="csv"))
        else:
            for field, value in data.model_dump().items():
                setattr(row, field, value)
            row.source = "csv"

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="CSV import could not be saved to the database") from exc
    return {"imported": len(parsed)}


@app.post("/api/predict", dependencies=[Depends(require_token)])
def prediction(payload: PredictionIn) -> dict:
    try:
        value = predict(payload.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"prediction_date": payload.prediction_date, "hour": payload.hour, "predicted_crowd": value}


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(ROOT_DIR / "frontend" / "index.html")
