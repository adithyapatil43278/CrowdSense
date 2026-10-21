import csv
from datetime import date

from backend.app.db import SessionLocal, init_db
from backend.app.models import HourlyCrowd

init_db()
db = SessionLocal()
try:
    with open("dataset/university_library_crowd.csv", newline="", encoding="utf-8") as source:
        for raw in csv.DictReader(source):
            row = HourlyCrowd(observation_date=date.fromisoformat(raw["date"]), hour=int(raw["hour"]), people_present=int(raw["people_present"]), source="seed")
            existing = db.query(HourlyCrowd).filter_by(observation_date=row.observation_date, hour=row.hour).first()
            if not existing:
                db.add(row)
        db.commit()
finally:
    db.close()
print("Historical records seeded.")
