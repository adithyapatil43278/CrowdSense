# Indoor Crowd Monitor

An indoor occupancy monitoring and crowd prediction web application for a university library. The project combines a FastAPI backend, PostgreSQL database, browser dashboard, Arduino serial bridge, and a supplied scikit-learn model.

The application can run locally or on a Linux server such as an AWS EC2 instance. The frontend is served by FastAPI, so a separate frontend server is not required.

## Features

- Live occupancy dashboard with current occupancy, daily entries, and daily exits
- Seven-day hourly occupancy history chart
- Manual hourly crowd-history entry
- CSV import for historical crowd data
- Crowd prediction using the supplied `HistGradientBoosting` model
- Optional weather enrichment from the Open-Meteo API
- Arduino event ingestion through the serial bridge
- Bearer-token protection for write and prediction endpoints
- Duplicate sensor-event protection using source event IDs
- Occupancy clamped at zero so exit events cannot produce negative occupancy
- PostgreSQL for deployment and SQLite-compatible configuration for tests

## Architecture

```text
Browser
  |
  v
FastAPI application
  |              \
  v               v
PostgreSQL       scikit-learn model
  ^
  |
Arduino serial bridge on the USB-connected computer
```

The Arduino bridge reads serial lines and forwards only lines containing:

- `******** ENTER ********`
- `******** EXIT ********`

The bridge can run on a different computer from the backend. In a cloud deployment, the bridge remains on the computer physically connected to the Arduino and sends HTTPS requests to the public backend URL.

## Project structure

```text
backend/app/       FastAPI application, configuration, database models, and services
frontend/          HTML, CSS, and browser JavaScript
hardware_bridge/   Arduino serial-to-HTTP bridge
model/             Prediction model artifact and notebook
dataset/           Historical crowd data
scripts/           Database initialization and optional data seeding
tests/             Automated API tests
```

## Requirements

- Python 3.11 or newer
- PostgreSQL for normal local or server use
- An Arduino and USB-connected computer for live sensor events
- Internet access for the optional Open-Meteo weather request

The model and Python dependencies are pinned in [backend/requirements.txt](backend/requirements.txt). The serial bridge dependency is pinned in [hardware_bridge/requirements.txt](hardware_bridge/requirements.txt).

## Local setup

### 1. Create the PostgreSQL database

Using a PostgreSQL administrator account, create a database user and database:

```sql
CREATE USER crowd_user WITH PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE crowd_monitor OWNER crowd_user;
```

Do not commit the real password or any other secret to GitHub.

### 2. Create a Python environment

Run these commands from the project root:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Install the application and hardware-bridge dependencies:

```bash
pip install -r backend/requirements.txt -r hardware_bridge/requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and update the values:

```text
DATABASE_URL=postgresql+psycopg://crowd_user:password@localhost:5432/crowd_monitor
API_TOKEN=replace-with-a-long-random-token
MODEL_PATH=./model/crowd_prediction_model.pkl
```

The remaining variables configure Open-Meteo, the prediction location, and allowed CORS origins. Keep `.env` local; it is excluded by `.gitignore`.

### 4. Initialize and optionally seed the database

```bash
python scripts/init_db.py
python scripts/seed_history.py
```

The seed command is optional and imports records from `dataset/university_library_crowd.csv`.

### 5. Start the web application

```bash
uvicorn backend.app.main:app --reload
```

Open <http://127.0.0.1:8000> in a browser. The API health endpoint is available at <http://127.0.0.1:8000/api/health>.

The protected browser actions use the token stored as `crowd_api_token` in browser `localStorage`. For local development, set it through the browser developer console:

```javascript
localStorage.crowd_api_token = "your-api-token";
```

### 6. Start the Arduino bridge

On the computer connected to the Arduino:

```bash
python hardware_bridge/serial_bridge.py \
  --port COM3 \
  --backend-url http://127.0.0.1:8000 \
  --token YOUR_TOKEN
```

On Linux, replace `COM3` with the Arduino serial device, such as `/dev/ttyUSB0`.

## Testing

The tests use SQLite and configure their own test environment. Run them from the project root:

```bash
pytest -q
```

The tests cover authenticated API access, idempotent sensor events, and the non-negative occupancy behavior.

## AWS EC2 deployment

The application does not require a major source-code rewrite for EC2 deployment. It does require normal server configuration:

1. Launch a Linux EC2 instance and restrict its security group to SSH, HTTP, and HTTPS. Do not expose PostgreSQL port `5432` publicly.
2. Install Python, PostgreSQL, Nginx, and Git.
3. Copy the project to the instance and create a production `.env`.
4. Create the PostgreSQL database and user.
5. Install `backend/requirements.txt`.
6. Run `python scripts/init_db.py`.
7. Run Uvicorn as a systemd service bound to `127.0.0.1:8000`.
8. Configure Nginx as an HTTPS reverse proxy to Uvicorn.
9. Set the Arduino bridge's `--backend-url` to the EC2 HTTPS URL.

For a small deployment, PostgreSQL can run on the EC2 instance. Amazon RDS for PostgreSQL is an alternative when managed backups, maintenance, and database isolation are needed.

The model file must be copied to the server, and `MODEL_PATH` should point to it. Use the same Python and dependency versions as local development to reduce the risk of model deserialization differences.

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection URL |
| `API_TOKEN` | Bearer token for protected endpoints |
| `MODEL_PATH` | Path to the serialized prediction model |
| `WEATHER_API_URL` | Weather service endpoint |
| `WEATHER_API_KEY` | Optional weather API key |
| `WEATHER_LATITUDE` | Prediction weather latitude |
| `WEATHER_LONGITUDE` | Prediction weather longitude |
| `CORS_ORIGINS` | Comma-separated allowed browser origins |

## Security notes

- Never commit `.env`, database credentials, or real API tokens.
- Use a long random `API_TOKEN` outside local development.
- Use HTTPS for public deployments.
- Keep PostgreSQL bound to the private server network and do not open port `5432` to the Internet.
- The current bearer-token authentication is intended for a controlled project deployment, not a full multi-user identity system.

## License

No license has been selected for this project yet. Add a license before distributing the repository publicly.
