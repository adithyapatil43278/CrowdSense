"""
Reproduce university_library_crowd.csv (synthetic data).
Requires: numpy, pandas
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 10_000
start = pd.Timestamp("2025-01-01")
dates = start + pd.to_timedelta(rng.integers(0, 365, size=n), unit="D")
hours = rng.integers(7, 23, size=n)
day_of_week = dates.dayofweek.to_numpy()
is_weekend = (day_of_week >= 5).astype(int)
is_holiday = (rng.random(n) < np.where(is_weekend == 1, 0.025, 0.045)).astype(int)
day_index = (dates - start).days.to_numpy()
exam_windows = (((day_index >= 35) & (day_index <= 55)) |
                ((day_index >= 125) & (day_index <= 145)) |
                ((day_index >= 245) & (day_index <= 265)) |
                ((day_index >= 315) & (day_index <= 335)))
is_exam_period = (exam_windows & (rng.random(n) < 0.93)).astype(int)
break_windows = (((day_index >= 75) & (day_index <= 89)) |
                 ((day_index >= 180) & (day_index <= 194)) |
                 ((day_index >= 275) & (day_index <= 289)) |
                 ((day_index >= 350) & (day_index <= 364)))
is_semester_break = (break_windows & (rng.random(n) < 0.94)).astype(int)
days_to_exam = np.where(is_exam_period == 1, rng.integers(0, 8, n), rng.integers(8, 61, n)).astype(int)
doy = dates.dayofyear.to_numpy()
temperature_c = 29.0 + 3.2 * np.sin(2 * np.pi * (doy - 80) / 365) + rng.normal(0, 2.4, n)
temperature_c = np.clip(temperature_c, 20, 42).round(1)
rain_probability = 0.12 + 0.13 * (np.sin(2 * np.pi * (doy - 150) / 365) + 1) / 2
rainfall_mm = np.where(rng.random(n) < rain_probability, rng.gamma(1.5, 5.0, n), 0.0)
rainfall_mm = np.clip(rainfall_mm, 0, 45).round(1)
library_capacity = np.full(n, 600, dtype=int)
hour_profile = {7: .18, 8: .28, 9: .42, 10: .58, 11: .70, 12: .77, 13: .82, 14: .90, 15: .96, 16: 1., 17: .98, 18: .92, 19: .82, 20: .68, 21: .52, 22: .34}
hour_effect = np.array([hour_profile[int(h)] for h in hours])
expected = 245 * hour_effect
weekday_effect = np.where(day_of_week == 0, 1.00, np.where(day_of_week == 1, 1.04, np.where(day_of_week == 2, 1.06, np.where(day_of_week == 3, 1.03, np.where(day_of_week == 4, .98, np.where(day_of_week == 5, .72, .58))))))
expected *= weekday_effect
expected += is_exam_period * (105 + 4.0 * np.maximum(0, 14 - days_to_exam))
expected -= is_semester_break * 95
expected -= is_holiday * 75
expected += is_exam_period * is_weekend * 32
expected -= is_semester_break * is_weekend * 18
expected += np.where(rainfall_mm > 0, np.minimum(rainfall_mm, 20) * 1.1, 0)
expected -= np.maximum(0, temperature_c - 34) * 5.0
expected -= np.maximum(0, 23 - temperature_c) * 1.8
unique_dates = pd.date_range(start, periods=365, freq="D")
daily_latent = dict(zip(unique_dates, rng.normal(0, 20, len(unique_dates))))
daily_effect = np.array([daily_latent[pd.Timestamp(d)] for d in dates])
people = np.rint(expected + daily_effect + rng.normal(0, 28, n)).astype(int)
people = np.clip(people, 50, library_capacity)
df = pd.DataFrame({
    "date": dates.strftime("%Y-%m-%d"), "hour": hours, "day_of_week": day_of_week,
    "is_holiday": is_holiday, "is_exam_period": is_exam_period, "days_to_exam": days_to_exam,
    "rainfall_mm": rainfall_mm, "temperature_c": temperature_c,
    "is_semester_break": is_semester_break, "library_capacity": library_capacity,
    "people_present": people
}).sort_values(["date", "hour"]).reset_index(drop=True)
df.to_csv("university_library_crowd.csv", index=False)
print(df.head())
print(df["people_present"].describe())
