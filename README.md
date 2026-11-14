# 🌿 Leaf-Line

Your plants are bad at asking for water. Leaf-Line asks for them.

An ESP32-C6 with a capacitive soil moisture sensor reads real moisture
data and reports it over Wi-Fi to a FastAPI backend, which decides
whether each plant is happy, thirsty, or overwatered — both the
device's own screen and a web frontend show a cute animated pixel-art
pot-plant character for the result, before the fern starts dramatically
wilting for attention.

Built as a learning project to go from "I write automation scripts" to
"I ship a real backend and drive real hardware" — one deliberate step
at a time: schemas, then storage, then decision logic, then the
hardware side.

## How it works

```
[ ESP32-C6 + capacitive moisture sensor ]
          │  reads every 5 seconds, converts raw ADC to a calibrated
          │  0-100% moisture reading, decides its OWN local status
          │  from a copy of the plant's thresholds, and shows a cute
          │  blinking pot-plant character on its own ST7789 screen
          │
          ▼  (over Wi-Fi, HTTP POST, in parallel with the local decision)
[ FastAPI backend ]  ── classifies the same reading against the plant's
          │             two thresholds: needs_water / happy / overwatered
          ▼
[ SQLite ]  stores every reading and each plant's current watering state
          │
          ▼  (polled every 5s, over CORS, by the browser)
[ web frontend ]  plain HTML/CSS/JS, shows the matching pixel-art sprite:
                   happy, needs water (watering can), or overwatered (puddle)
```

The device's on-screen decision and the backend's decision are computed
independently from the same reading, using the same thresholds kept in
sync by hand (`PLANTS` in `plant_status.py` vs. the `Plant` row in the
database) - they should normally agree, but if you ever change one
without the other, the device's screen and the website can briefly
disagree. This happened once in testing because a temporary threshold
override meant for a quick visual check was left deployed.

A plant doesn't have one threshold, it has two:

- below `moisture_threshold_low` → `needs_water`
- above `moisture_threshold_high` → `overwatered`
- in between → `happy`

Classification is stateless (recomputed fresh from every new reading,
no "dead zone" memory) - an earlier version tried a hysteresis dead
zone to resist sensor noise near a boundary, but that only works
cleanly for a single binary flag. Extending it to three states let a
plant get stuck "overwatered" forever with no path back to "happy"
without first passing through "needs_water", which was wrong. The
device already averages 10 samples per reading, which handles most of
the noise a dead zone would otherwise guard against.

## Status

🚧 Under construction. Built so far:

**Backend**
- [x] API schemas for plants and sensor readings (`backend/app/schemas.py`)
- [x] Database models with a real foreign key relationship (`backend/app/database_models.py`)
- [x] `POST /plants` — register a new plant
- [x] `GET /plants` — list every plant
- [x] `POST /sensorreading` — record a reading and update watering state
- [x] `GET /plants/{plant_id}/status` — happy / needs_water / overwatered
- [x] Real three-state watering status (`needs_water` + `overwatered` flags,
      mutually exclusive) — not just a binary "needs water or not"
- [x] CORS enabled, so the browser-based frontend can call the API directly

**Firmware (ESP32-C6, MicroPython)**
- [x] Capacitive moisture sensor wired and calibrated against real dry/wet soil
      (`firmware/esp32c6/calibration.py`)
- [x] Continuous loop, checking the sensor every `CHECK_INTERVAL_MS` (5s by
      default) — not deep sleep. A continuously-animated on-device screen
      needs the chip awake the whole time, which was tried and reverted:
      see "Deep sleep vs. the on-device screen" below
      (`firmware/esp32c6/plant_status.py`)
- [x] A cute pot-plant character on the device's own ST7789 screen - bright
      with raised arms and a smile when happy, muted with drooped arms and
      a frown when overwatered, and wilted with a tilted watering can
      pouring drops onto it when it needs water. Built from the same
      row-swept-ellipse technique used for the web sprites, adapted to
      this driver's actual primitives (no filled polygons or arcs
      available here, unlike the Pillow-based sprite generator)
- [x] Wi-Fi + POST real readings to the FastAPI backend every cycle — verified
      live with a real plant: readings and the backend's own computed
      watering state both update in the real database, wirelessly, automatically
- [x] Reconnects automatically if Wi-Fi drops
- [x] `main.py` runs `plant_status.py` automatically on every power-up/reset -
      verified standalone (no `mpremote run`, no laptop needed to start it)

**Deep sleep vs. the on-device screen** - these two goals conflict, and
can't both be true at once:
- Deep sleep (`machine.deepsleep()`) powers the chip down almost
  entirely between readings, extending a power bank from ~41 hours to
  potentially weeks - but the screen and backlight power down with it,
  so there's no continuous animation, only a brief flash on each wake.
- A continuously-animated screen needs the chip (and backlight) awake
  the whole time, which means no deep sleep and the shorter ~41 hour
  power bank life.

This project currently runs the continuous/animated version, by
request - the deep-sleep version still exists in git history
(`git show 954c9ff:firmware/esp32c6/plant_status.py`) if the tradeoff
is ever worth revisiting.

**Frontend**
- [x] Plain HTML/CSS/JS page — no build step, no framework, matching the
      rest of this project's lightweight style (`frontend/`)
- [x] Polls `GET /plants/{id}/status` every 5 seconds and shows the matching
      sprite, moisture %, and a status label — verified live against a real
      plant, no manual refresh needed

**Assets**
- [x] Pixel-art plant-character sprites — happy, needs_water (with a
      pouring watering can), overwatered (yellowing + puddle) — generated
      programmatically, see `assets/sprites/`

**Not started**
- [ ] Automated tests
- [ ] OTA firmware updates (device currently needs a USB connection to update)

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
    main.py                  # boot entry point - runs on every power-up, starts plant_status
    plant_status.py          # the real thing: sensor -> screen + Wi-Fi -> backend, on a loop
    calibration.py           # DRY_VALUE / WET_VALUE - edit these to recalibrate
    wifi_config.py            # WIFI_SSID / WIFI_PASSWORD - gitignored, create locally
    test_sensor.py            # calibration helper: prints 30 raw readings
    test_wifi.py               # sanity check: connects and prints the IP
    test_http.py                # sanity check: POSTs one test reading
    drivers/                   # third-party ST7789 driver (MIT licensed)
frontend/
  index.html                  # the page
  style.css
  app.js                       # polls /status, swaps the sprite - edit
                                 # BACKEND_URL/PLANT_ID here
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

To see the actual frontend (not just curl), start the backend with
`--host 0.0.0.0`, then in a separate terminal:

```sh
cd ~/Desktop/Leaf-Line
python3 -m http.server 8080
```

and open `http://localhost:8080/frontend/index.html` in a real browser
(not by double-clicking the file - browsers block fetch requests from
plain `file://` pages). Edit `BACKEND_URL` and `PLANT_ID` at the top of
`frontend/app.js` to match your setup first.

## Tech

- **FastAPI** — the web framework
- **SQLAlchemy + SQLite** — storage
- **Pydantic** — request/response validation
- **ESP32-C6 + MicroPython** — the thing that actually goes near the dirt
- **ST7789 (172×320 LCD)** — the on-device screen, driven directly by a
  third-party MicroPython driver
- **Plain HTML/CSS/JS** — the frontend, no build step or framework
