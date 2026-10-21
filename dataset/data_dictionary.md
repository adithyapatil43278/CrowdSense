# Synthetic University Library Crowd Dataset

## Overview
- Rows: 10,000 observations
- Target: `people_present` (integer count of people in the library)
- Assumed library capacity: 600 people
- Data are synthetic and are not measured attendance records from a real library.
- Random seed: 42
- Observation dates span 2025-01-01 through 2025-12-31.
- Observations are sampled at library operating hours (07:00–22:00); this is not a complete hourly time series.
- Target counts are constrained to 50–600 because this dataset represents sampled periods with at least 50 people present.

## Columns
| Column | Meaning | Type / unit |
|---|---|---|
| `date` | Simulated calendar date | YYYY-MM-DD; reference/optional feature |
| `hour` | Hour of observation | Integer, 7–22 |
| `day_of_week` | Day of week, Monday=0 through Sunday=6 | Integer |
| `is_holiday` | Whether the observation is marked as a holiday | Binary (0/1) |
| `is_exam_period` | Whether the observation falls in a simulated exam period | Binary (0/1) |
| `days_to_exam` | Simulated days until an exam/assessment date | Integer, 0–60 |
| `rainfall_mm` | Simulated rainfall for the observation | Millimetres |
| `temperature_c` | Simulated outdoor temperature | Degrees Celsius |
| `is_semester_break` | Whether the observation falls in a simulated semester break | Binary (0/1) |
| `library_capacity` | Assumed maximum occupancy | People |
| `people_present` | Simulated number of people present; regression target | People |

## Generation assumptions
Attendance is simulated from a time-of-day profile, day-of-week effects, exam-period effects, days-to-exam effects, holidays, semester breaks, modest weather adjustments, day-level variation, and observation-level random noise. Counts are rounded to integers and clipped to [50, library_capacity].

## Important limitations
This is a demonstration dataset, not empirical evidence about real library attendance. The relationships and coefficients are assumptions chosen for a plausible ML exercise. High model accuracy only demonstrates that a model can learn these simulated relationships; it does not establish real-world predictive validity. `date` can be excluded from the first model, and `day_of_week` can optionally be one-hot encoded or represented cyclically. Since rows are sampled observations across dates rather than a complete time series, do not assume each date/hour combination is present exactly once.
