import argparse
import hashlib
import os
import time

import requests
import serial


def event_id(event_type: str, line: str) -> str:
    return hashlib.sha256(f"{event_type}:{line}:{time.time_ns()}".encode()).hexdigest()


def run(port: str, baud: int, backend_url: str, token: str) -> None:
    with serial.Serial(port, baud, timeout=1) as device:
        print(f"Listening on {port}; sending events to {backend_url}")
        while True:
            raw = device.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="ignore").strip()
            event_type = "enter" if "******** ENTER ********" in line else "exit" if "******** EXIT ********" in line else None
            if event_type is None:
                continue
            payload = {"event_type": event_type, "source_event_id": event_id(event_type, line)}
            response = requests.post(f"{backend_url.rstrip('/')}/api/events", json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            response.raise_for_status()
            print(response.json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino crowd counter HTTP bridge")
    parser.add_argument("--port", default=os.getenv("SERIAL_PORT", "COM3"))
    parser.add_argument("--baud", type=int, default=int(os.getenv("SERIAL_BAUD", "9600")))
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--token", default=os.getenv("API_TOKEN", "change-me"))
    args = parser.parse_args()
    run(args.port, args.baud, args.backend_url, args.token)
