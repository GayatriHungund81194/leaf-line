# 🌿 Leaf-Line

Your plants are bad at asking for water. Leaf-Line asks for them.

An ESP32 with a cheap soil moisture sensor reports in over Wi-Fi, this
backend decides who's thirsty, and a tiny on-device display animates
when it's time to grab the watering can — before the fern starts
dramatically wilting for attention.

Built as a learning project to go from "I write automation scripts" to
"I ship a real backend" — one deliberate step at a time: schemas, then
storage, then the decision logic, then the hardware side.

## How it works

```
[ ESP32 + moisture sensor ]
          │  HTTP POST, on a timer
          ▼
[ FastAPI backend ]  ── compares reading against the plant's thresholds
          │             using hysteresis, so noisy readings near the
          │             boundary don't flicker the decision
          ▼
[ SQLite ]  stores every reading and each plant's current watering state
          │
          ▼
[ ESP32 + OLED ]  polls "needs water?" and animates accordingly
```

A plant doesn't have one threshold, it has two:

- below `moisture_threshold_low` → flagged as needing water
- above `moisture_threshold_high` → flagged as watered
- anywhere in between → whatever it was already flagged as, unchanged

That dead zone is what keeps a borderline reading from flipping the
decision back and forth every time a new reading comes in.

## Status

🚧 Under construction. Built so far:

- [x] API schemas for plants and sensor readings (`app/schemas.py`)
- [x] Database models with a real foreign key relationship (`app/database_models.py`)
- [x] `POST /plants` — register a new plant
- [x] `GET /plants` — list every plant
- [x] `POST /sensorreading` — record a reading and update watering state
- [x] `GET /plants/{plant_id}/status` — does this plant need water right now?
- [x] Hysteresis, so sensor noise near the threshold doesn't flicker the decision
- [ ] ESP32 firmware + OLED animation
- [ ] Automated tests

## Project layout

```
app/
  main.py               # FastAPI app entry point
  database.py           # SQLAlchemy engine, session, declarative base
  database_models.py    # Plant and SensorReading tables
  schemas.py             # Pydantic request/response shapes
  routers/
    plants.py            # create/list plants, watering status
    readings.py          # record sensor readings
firmware/                 # reference ESP32 sketch (coming soon)
tests/
NOTES.md                  # learning notes written along the way
```

## Getting started

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Try it

```sh
curl -X POST http://127.0.0.1:8000/plants \
  -H "Content-Type: application/json" \
  -d '{"name": "Fred the Fern", "category": "ferns", "quantity": 1, "moisture_threshold_low": 25.0, "moisture_threshold_high": 35.0, "added_date": "2026-10-18T09:00:00"}'

curl -X POST http://127.0.0.1:8000/sensorreading \
  -H "Content-Type: application/json" \
  -d '{"plant_id": 1, "moisture_reading": 18.0}'

curl http://127.0.0.1:8000/plants/1/status
```

## Tech

- **FastAPI** — the web framework
- **SQLAlchemy + SQLite** — storage
- **Pydantic** — request/response validation
- **ESP32** — the thing that actually goes near the dirt
