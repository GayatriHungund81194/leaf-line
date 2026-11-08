# 🌿 Leaf-Line

Your plants are bad at asking for water. Leaf-Line asks for them.

An ESP32-C6 with a capacitive soil moisture sensor reads real moisture
data and reports it over Wi-Fi to a FastAPI backend, which decides
whether each plant is happy, thirsty, or overwatered — a web frontend
then shows an animated pixel-art face for the result, before the fern
starts dramatically wilting for attention.

Built as a learning project to go from "I write automation scripts" to
"I ship a real backend and drive real hardware" — one deliberate step
at a time: schemas, then storage, then decision logic, then the
hardware side.

## How it works

```
[ ESP32-C6 + capacitive moisture sensor ]
          │  reads every 5 seconds, converts raw ADC to a
          │  calibrated 0-100% moisture reading
          │
          ▼  (over Wi-Fi, HTTP POST - no screen, no on-device decision)
[ FastAPI backend ]  ── compares reading against the plant's thresholds
          │             using hysteresis, so noisy readings near the
          │             boundary don't flicker the decision
          ▼
[ SQLite ]  stores every reading and each plant's current watering state
          │
          ▼  (next: GET /plants/{id}/status, polled)
[ web frontend ]  shows the matching pixel-art sprite: happy, needs
                   water (watering can), or overwatered (puddle)
```

A plant doesn't have one threshold, it has two:

- below `moisture_threshold_low` → flagged as needing water
- above `moisture_threshold_high` → flagged as overwatered
- anywhere in between → happy, whatever it was already flagged as stays
  unchanged right at the edges (hysteresis), so a borderline reading
  doesn't flip the decision back and forth every time a new one comes in

## Status

🚧 Under construction. Built so far:

**Backend**
- [x] API schemas for plants and sensor readings (`backend/app/schemas.py`)
- [x] Database models with a real foreign key relationship (`backend/app/database_models.py`)
- [x] `POST /plants` — register a new plant
- [x] `GET /plants` — list every plant
- [x] `POST /sensorreading` — record a reading and update watering state
- [x] `GET /plants/{plant_id}/status` — does this plant need water right now?
- [x] Hysteresis, so sensor noise near the threshold doesn't flicker the decision

**Firmware (ESP32-C6, MicroPython)**
- [x] Capacitive moisture sensor wired and calibrated against real dry/wet soil
      (`firmware/esp32c6/calibration.py`)
- [x] Continuous monitoring loop — re-reads the sensor every 5 seconds
      (`firmware/esp32c6/plant_status.py`)
- [x] Wi-Fi + POST real readings to the FastAPI backend every cycle — verified
      live: readings and the backend's own hysteresis-based `needs_water`
      state both update in the real database, wirelessly, automatically
- [x] Reconnects automatically if Wi-Fi drops
- No on-device screen/animation logic - this board is sensor-only; all
  decisions and all visuals live on the backend and frontend, not the device
  (the `drivers/`, `happy_plant.py`, `plant_needs_water.py`, `test_display.py`
  files are kept as standalone ST7789 demos, unused by `plant_status.py`)

**Assets**
- [x] Pixel-art plant-character sprites for the future web frontend — happy,
      needs_water (with a pouring watering can), overwatered (yellowing +
      puddle) — generated programmatically, see `assets/sprites/`

**Not started**
- [ ] Web frontend — poll `/status`, show the matching sprite
- [ ] Automated tests

## Project layout

```
backend/
  requirements.txt
  app/
    main.py                 # FastAPI app entry point
    database.py              # SQLAlchemy engine, session, declarative base
    database_models.py       # Plant and SensorReading tables
    schemas.py                # Pydantic request/response shapes
    routers/
      plants.py               # create/list plants, watering status
      readings.py             # record sensor readings
  tests/
firmware/
  esp32c6/
    plant_status.py          # the real thing: live sensor -> Wi-Fi -> backend -> animation loop
    calibration.py           # DRY_VALUE / WET_VALUE - edit these to recalibrate
    wifi_config.py            # WIFI_SSID / WIFI_PASSWORD - gitignored, create locally
    happy_plant.py           # standalone demo: blinking happy face
    plant_needs_water.py     # standalone demo: falling rain
    test_display.py          # sanity check: fills the screen red
    test_sensor.py            # calibration helper: prints 30 raw readings
    test_wifi.py               # sanity check: connects and prints the IP
    test_http.py                # sanity check: POSTs one test reading
    drivers/                  # third-party ST7789 + font files (MIT licensed)
assets/
  sprites/
    generate_sprites.py      # regenerate all three sprites (needs Pillow)
    happy.gif / .png
    needs_water.gif / .png
    overwatered.gif / .png
NOTES.md                      # learning notes written along the way
```

## Getting started

```sh
python3 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

(The venv lives at the project root since it's shared with the firmware
tooling (`esptool`, `mpremote`), not just the backend.)

To run the firmware's Wi-Fi-connected monitoring loop, create
`firmware/esp32c6/wifi_config.py` (gitignored, never committed) with:

```python
WIFI_SSID = "your-network-name"
WIFI_PASSWORD = "your-network-password"
```

Then update `BACKEND_URL` in `plant_status.py` to your machine's LAN IP
(find it with `ipconfig getifaddr en0` on Mac), and start the backend
with `uvicorn app.main:app --host 0.0.0.0` so it's reachable from the
ESP32 over Wi-Fi, not just from localhost.

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
- **ESP32-C6 + MicroPython** — the thing that actually goes near the dirt
- **ST7789 (172×320 LCD)** — the on-device display
