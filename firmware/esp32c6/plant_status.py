"""Continuously monitors soil moisture and shows the matching animation.

Reads the capacitive moisture sensor every CHECK_INTERVAL_MS, converts
the raw reading to a 0-100% scale using the calibration values in
calibration.py, and switches between three animations on the ST7789
screen depending on the active plant's thresholds: a blinking happy
face, a falling-rain "needs water" screen, or a static "overwatered"
frown. Runs forever - no restart needed as conditions change.
"""

from time import sleep_ms, ticks_ms, ticks_diff, ticks_add
import math
import random

from machine import Pin, SPI, ADC
import network
import urequests
import st7789py as st7789
from calibration import DRY_VALUE, WET_VALUE
from wifi_config import WIFI_SSID, WIFI_PASSWORD

spi = SPI(1, baudrate=40000000, polarity=0, phase=0,
          sck=Pin(7), mosi=Pin(6))

backlight = Pin(22, Pin.OUT)
backlight.value(1)

tft = st7789.ST7789(
    spi, 240, 320,
    reset=Pin(21, Pin.OUT),
    dc=Pin(15, Pin.OUT),
    cs=Pin(14, Pin.OUT),
    backlight=backlight,
    rotation=0,
)
tft.xstart = 34

BLACK = st7789.BLACK
WHITE = st7789.WHITE
YELLOW = st7789.YELLOW
CYAN = st7789.CYAN
RED = st7789.RED
BLUE = st7789.BLUE

SCREEN_W = 172
SCREEN_H = 320

# ---- static plant data, standing in for the backend until the real
# ---- POST /plants calls are wired up ----
PLANTS = {
    "fern": {"name": "Fred the Fern", "threshold_low": 30, "threshold_high": 70},
    "succulent": {"name": "Spike the Succulent", "threshold_low": 10, "threshold_high": 35},
}

ACTIVE_PLANT = "fern"     # which plant THIS board is monitoring
CHECK_INTERVAL_MS = 5000  # how often to re-read the sensor

PLANT_ID = 1   # the backend's id for ACTIVE_PLANT - must already exist there
BACKEND_URL = "http://192.168.1.164:8000/sensorreading"

sensor = ADC(Pin(1))
sensor.atten(ADC.ATTN_11DB)


def connect_wifi():
    """Connect to Wi-Fi, waiting up to 10s. Returns True if connected."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(10):
            if wlan.isconnected():
                break
            sleep_ms(1000)
    if wlan.isconnected():
        print("Wi-Fi connected, IP:", wlan.ifconfig()[0])
    else:
        print("Wi-Fi connection failed - continuing with local display only")
    return wlan.isconnected()


def post_reading(moisture_percent):
    """POST the reading to the backend. Never raises - just logs failures,
    so a network hiccup never crashes the monitoring loop."""
    try:
        response = urequests.post(
            BACKEND_URL,
            json={"plant_id": PLANT_ID, "moisture_reading": moisture_percent},
        )
        response.close()
    except OSError as e:
        print("POST failed:", e)


def read_status():
    """Sample the sensor, convert to a moisture %, and return the status."""
    total = 0
    for _ in range(10):
        total += sensor.read_u16()
        sleep_ms(50)
    raw_reading = total / 10

    moisture_percent = (DRY_VALUE - raw_reading) / (DRY_VALUE - WET_VALUE) * 100
    moisture_percent = max(0, min(100, moisture_percent))

    plant = PLANTS[ACTIVE_PLANT]
    if moisture_percent < plant["threshold_low"]:
        status = "needs_water"
    elif moisture_percent > plant["threshold_high"]:
        status = "overwatered"
    else:
        status = "happy"

    print("Raw:", raw_reading, "| Moisture:", round(moisture_percent, 1),
          "% | Status:", status)
    post_reading(moisture_percent)
    return status


def fill_ellipse(cx, cy, half_w, half_h, color):
    """Fill an oval by sweeping row by row and computing each row's width."""
    y = -half_h
    while y <= half_h:
        t = y / half_h
        row_half_w = int(half_w * math.sqrt(max(0, 1 - t * t)))
        if row_half_w > 0:
            tft.fill_rect(cx - row_half_w, cy + y, row_half_w * 2, 1, color)
        y += 1


LEFT_EYE_CX, RIGHT_EYE_CX, EYE_CY = 58, 114, 100
EYE_HALF_W, EYE_HALF_H = 15, 20
BORDER = 3
PUPIL_HALF = 8

# ---------------- happy (blinking smile) ----------------
_happy_blink_open = True
_happy_next_toggle = 0


def _draw_eyes_open(pupil_color):
    """Draw both eyes: border, inset eyeball, bordered pupil in pupil_color."""
    for cx in (LEFT_EYE_CX, RIGHT_EYE_CX):
        fill_ellipse(cx, EYE_CY, EYE_HALF_W, EYE_HALF_H, BLACK)
        fill_ellipse(cx, EYE_CY, EYE_HALF_W - BORDER, EYE_HALF_H - BORDER, WHITE)
        fill_ellipse(cx, EYE_CY, PUPIL_HALF + 1, PUPIL_HALF + 1, BLACK)
        fill_ellipse(cx, EYE_CY, PUPIL_HALF, PUPIL_HALF, pupil_color)


def _draw_eyes_closed(bg_color):
    """Erase both eyes back to bg_color and draw a closed-eyelid line."""
    for cx in (LEFT_EYE_CX, RIGHT_EYE_CX):
        fill_ellipse(cx, EYE_CY, EYE_HALF_W, EYE_HALF_H, bg_color)
        tft.fill_rect(cx - EYE_HALF_W, EYE_CY - 2, EYE_HALF_W * 2, 4, BLACK)


def setup_happy():
    """Draw the happy face once: yellow background, smile, open eyes."""
    global _happy_blink_open, _happy_next_toggle
    tft.fill(YELLOW)

    mouth_x_start, mouth_x_end = 50, 122
    mouth_center_x = (mouth_x_start + mouth_x_end) // 2
    half_width = (mouth_x_end - mouth_x_start) // 2
    corner_y = 175
    top_depth = 8
    bottom_depth = 30

    x = mouth_x_start
    while x <= mouth_x_end:
        t = (x - mouth_center_x) / half_width
        shape = 1 - t * t
        top_y = int(corner_y + top_depth * shape)
        bottom_y = int(corner_y + bottom_depth * shape)
        gap = bottom_y - top_y
        if gap > 0:
            tft.fill_rect(x, top_y, 2, gap, RED)
        x += 2

    _happy_blink_open = True
    _draw_eyes_open(CYAN)
    _happy_next_toggle = ticks_add(ticks_ms(), 2000)


def step_happy():
    """Toggle the eyes open/closed once their scheduled time arrives."""
    global _happy_blink_open, _happy_next_toggle
    tick_now = ticks_ms()
    if ticks_diff(tick_now, _happy_next_toggle) >= 0:
        if _happy_blink_open:
            _draw_eyes_closed(YELLOW)
            _happy_next_toggle = ticks_add(tick_now, 200)
        else:
            _draw_eyes_open(CYAN)
            _happy_next_toggle = ticks_add(tick_now, 2000)
        _happy_blink_open = not _happy_blink_open


# ---------------- overwatered (static frown) ----------------
def setup_overwatered():
    """Draw the overwatered face once: blue background, frown, eyes."""
    tft.fill(BLUE)

    mouth_x_start, mouth_x_end = 50, 122
    mouth_center_x = (mouth_x_start + mouth_x_end) // 2
    half_width = (mouth_x_end - mouth_x_start) // 2
    center_y = 195
    depth = 15

    x = mouth_x_start
    prev = None
    while x <= mouth_x_end:
        t = (x - mouth_center_x) / half_width
        y = int(center_y - depth * (1 - t * t))
        if prev is not None:
            tft.line(prev[0], prev[1], x, y, BLACK)
            tft.line(prev[0], prev[1] + 1, x, y + 1, BLACK)
        prev = (x, y)
        x += 2

    _draw_eyes_open(BLUE)


def step_overwatered():
    """Static screen - nothing to animate."""


# ---------------- needs_water (falling rain) ----------------
_drops = []
DROP_W, DROP_H = 4, 14
NUM_DROPS = 14


def setup_rain():
    """Reset the drops list on a black background."""
    global _drops
    tft.fill(BLACK)
    _drops = []
    for _ in range(NUM_DROPS):
        x = random.randint(0, SCREEN_W - DROP_W)
        y = random.randint(-SCREEN_H, 0)
        speed = random.randint(4, 9)
        _drops.append([x, y, speed])


def step_rain():
    """Erase, move, and redraw every drop one frame forward."""
    for drop in _drops:
        x, y, speed = drop
        if 0 <= y and y + DROP_H <= SCREEN_H:
            tft.fill_rect(x, y, DROP_W, DROP_H, BLACK)
        y += speed
        if y + DROP_H > SCREEN_H:
            y = random.randint(-40, 0)
            x = random.randint(0, SCREEN_W - DROP_W)
            drop[0] = x
        drop[1] = y
        if 0 <= y and y + DROP_H <= SCREEN_H:
            tft.fill_rect(x, y, DROP_W, DROP_H, CYAN)


# ---------------- main loop ----------------
STATES = {
    "happy": (setup_happy, step_happy),
    "overwatered": (setup_overwatered, step_overwatered),
    "needs_water": (setup_rain, step_rain),
}

connect_wifi()

current_status = read_status()
setup_fn, step_fn = STATES[current_status]
setup_fn()

last_check = ticks_ms()

while True:
    now = ticks_ms()
    if ticks_diff(now, last_check) >= CHECK_INTERVAL_MS:
        last_check = now
        new_status = read_status()
        if new_status != current_status:
            current_status = new_status
            setup_fn, step_fn = STATES[current_status]
            setup_fn()
    step_fn()
    sleep_ms(30)
