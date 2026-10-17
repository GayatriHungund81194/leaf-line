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
[ FastAPI backend ]  ── compares reading against per-plant threshold
          │
          ▼
[ SQLite ]  stores every reading, so you can see trends over time
          │
          ▼
[ ESP32 + OLED ]  polls "needs water?" and animates accordingly
```

## Status

🚧 Under construction. Built so far:

- [x] API schemas for plants and sensor readings (`app/schemas.py`)
- [x] Database models with a real foreign key relationship (`app/database_models.py`)
- [ ] Route handlers (`POST /plants`, `POST /readings`, ...)
- [ ] Watering decision logic
- [ ] The actual FastAPI app
- [ ] ESP32 firmware + OLED animation

## Project layout

```
app/
  database.py          # SQLAlchemy engine, session, declarative base
  database_models.py   # Plant and SensorReading tables
  schemas.py            # Pydantic request/response shapes
  routers/              # route handlers (coming soon)
firmware/                # reference ESP32 sketch (coming soon)
tests/
NOTES.md                 # learning notes written along the way
```

## Getting started

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Tech

- **FastAPI** — the web framework
- **SQLAlchemy + SQLite** — storage
- **Pydantic** — request/response validation
- **ESP32** — the thing that actually goes near the dirt
