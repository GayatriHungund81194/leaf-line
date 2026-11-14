"""Continuously monitors soil moisture and shows the matching animation.

Reads the capacitive moisture sensor every CHECK_INTERVAL_MS, converts
the raw reading to a 0-100% scale using the calibration values in
calibration.py, and switches between three animations on the ST7789
screen depending on the active plant's thresholds: a cute blinking
pot-plant character, upright and bright when happy, wilted and muted
when overwatered or needing water (needs_water also shows a tilted
watering can pouring drops onto it). Runs forever - no restart needed
as conditions change.
"""

from time import sleep_ms, ticks_ms, ticks_diff, ticks_add
import math

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
CYAN = st7789.CYAN
BLUE = st7789.BLUE


def rgb565(r, g, b):
    """Pack 8-bit RGB into the 16-bit color this display expects."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


# cute pot-plant character palettes - happy is bright and warm, overwatered
# is muted and cool, so the two read as distinct at a glance
HAPPY_PAL = {
    "bg": rgb565(240, 248, 235),
    "pot_body": rgb565(70, 150, 160),
    "pot_band": rgb565(250, 245, 230),
    "pot_shadow": rgb565(50, 120, 130),
    "leaf_light": rgb565(150, 210, 110),
    "leaf_dark": rgb565(95, 165, 80),
    "limb": rgb565(70, 130, 60),
    "blush": rgb565(235, 140, 130),
    "pupil": CYAN,
}

OVERWATERED_PAL = {
    "bg": rgb565(210, 225, 235),
    "pot_body": rgb565(95, 115, 120),
    "pot_band": rgb565(220, 215, 200),
    "pot_shadow": rgb565(70, 90, 95),
    "leaf_light": rgb565(195, 190, 130),
    "leaf_dark": rgb565(160, 150, 85),
    "limb": rgb565(120, 112, 65),
    "blush": None,
    "pupil": BLUE,
}

NEEDS_WATER_PAL = {
    "bg": rgb565(245, 235, 215),
    "pot_body": rgb565(150, 100, 70),
    "pot_band": rgb565(230, 210, 180),
    "pot_shadow": rgb565(120, 80, 55),
    "leaf_light": rgb565(190, 170, 110),
    "leaf_dark": rgb565(150, 130, 80),
    "limb": rgb565(140, 115, 70),
    "blush": None,
    "pupil": rgb565(140, 100, 60),
}

CAN_COLOR = rgb565(190, 160, 80)
CAN_SHADE = rgb565(155, 128, 55)
CAN_HILITE = rgb565(215, 190, 115)
WATER_COLOR = rgb565(110, 180, 210)

# ---- static plant data, mirroring the backend's own thresholds for
# ---- this plant (keep these in sync with the Plant row in the backend) ----
PLANTS = {
    "anthurium": {"name": "Anthurium", "threshold_low": 30, "threshold_high": 45},
}

ACTIVE_PLANT = "anthurium"  # which plant THIS board is monitoring
CHECK_INTERVAL_MS = 5000     # how often to re-read the sensor

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


# ---------------- cute pot-plant character (happy + overwatered) ----------------
POT_CX = 86
POT_TOP_Y = 210
POT_BOTTOM_Y = 280

LEFT_EYE_CX, RIGHT_EYE_CX, EYE_CY = POT_CX - 18, POT_CX + 18, POT_TOP_Y + 18
EYE_HALF_W, EYE_HALF_H = 14, 18
BORDER = 3
PUPIL_HALF = 7

MOUTH_X0, MOUTH_X1 = POT_CX - 20, POT_CX + 20
MOUTH_CENTER_Y = EYE_CY + 16
MOUTH_DEPTH = 10

STEM_X = POT_CX

HAPPY_BLOBS = [
    (-32, -8, 16, 12), (32, -8, 16, 12),
    (-20, -30, 15, 11), (20, -30, 15, 11),
    (-8, -48, 13, 10), (8, -48, 13, 10),
    (0, -62, 12, 9),
]
OVERWATERED_BLOBS = [
    (-22, 25, 12, 9), (22, 25, 12, 9),
    (-14, 5, 11, 8), (14, 5, 11, 8),
    (-6, -10, 10, 7), (6, -10, 10, 7),
]
NEEDS_WATER_BLOBS = OVERWATERED_BLOBS  # same droop shape, different palette


def draw_pot(pal):
    """Draw the barrel-shaped pot: rim band, bulging body, base shadow."""
    draw_rect_row(POT_TOP_Y, POT_TOP_Y + 10, 36, pal["pot_band"])
    draw_rect_row(POT_TOP_Y + 10, POT_TOP_Y + 45, 44, pal["pot_body"])
    draw_rect_row(POT_TOP_Y + 45, POT_BOTTOM_Y, 36, pal["pot_body"])
    draw_rect_row(POT_BOTTOM_Y - 8, POT_BOTTOM_Y, 36, pal["pot_shadow"])


def draw_rect_row(y0, y1, half_w, color):
    """Fill a horizontal band centered on POT_CX, from y0 to y1."""
    tft.fill_rect(POT_CX - half_w, y0, half_w * 2, y1 - y0, color)


def draw_leaves(blobs, pal, stem_height):
    """Draw a cluster of glossy leaf blobs radiating from the stem top.

    Each leaf is two layered ellipses - a full-size dark base, then a
    smaller light highlight offset toward the upper-left - for a shiny,
    cuter look instead of a flat single-color blob. A short stem_height
    (with blobs that droop below the crown) reads as wilted."""
    crown_y = POT_TOP_Y - stem_height
    tft.line(STEM_X, POT_TOP_Y, STEM_X, crown_y, pal["limb"])
    for dx, dy, half_w, half_h in blobs:
        cx, cy = STEM_X + dx, crown_y + dy
        fill_ellipse(cx, cy, half_w, half_h, pal["leaf_dark"])
        fill_ellipse(cx - half_w // 4, cy - half_h // 4,
                     int(half_w * 0.6), int(half_h * 0.6), pal["leaf_light"])


def draw_limbs(pal, raised):
    """Draw arm nubs (raised when happy, drooped when overwatered) and legs."""
    arm_y = POT_TOP_Y + 10
    if raised:
        tft.fill_rect(POT_CX - 48, arm_y - 10, 14, 6, pal["limb"])
        tft.fill_rect(POT_CX + 34, arm_y - 10, 14, 6, pal["limb"])
    else:
        tft.fill_rect(POT_CX - 48, arm_y + 14, 14, 6, pal["limb"])
        tft.fill_rect(POT_CX + 34, arm_y + 14, 14, 6, pal["limb"])
    tft.fill_rect(POT_CX - 28, POT_BOTTOM_Y, 10, 16, pal["limb"])
    tft.fill_rect(POT_CX + 18, POT_BOTTOM_Y, 10, 16, pal["limb"])


def draw_mouth(color, smiling):
    """Draw a single curved mouth stroke: smile (dips down) or frown (peaks up)."""
    sign = 1 if smiling else -1
    half_width = (MOUTH_X1 - MOUTH_X0) // 2
    prev = None
    x = MOUTH_X0
    while x <= MOUTH_X1:
        t = (x - POT_CX) / half_width
        y = int(MOUTH_CENTER_Y + sign * MOUTH_DEPTH * (1 - t * t))
        if prev is not None:
            tft.line(prev[0], prev[1], x, y, color)
            tft.line(prev[0], prev[1] + 1, x, y + 1, color)
        prev = (x, y)
        x += 2


def draw_blush(color):
    """Draw small blush ellipses below-outside each eye."""
    for cx in (LEFT_EYE_CX - 2, RIGHT_EYE_CX + 2):
        fill_ellipse(cx, EYE_CY + 3, 4, 3, color)


# ---------------- shared blink animation (happy + overwatered) ----------------
_blink_open = True
_blink_next_toggle = 0
_blink_pupil = None
_blink_bg = None


def draw_eyes(open_, pupil_color, bg_color):
    """Draw both eyes open (bordered pupil) or closed (a simple eyelid line)."""
    if open_:
        for cx in (LEFT_EYE_CX, RIGHT_EYE_CX):
            fill_ellipse(cx, EYE_CY, EYE_HALF_W, EYE_HALF_H, BLACK)
            fill_ellipse(cx, EYE_CY, EYE_HALF_W - BORDER, EYE_HALF_H - BORDER, WHITE)
            fill_ellipse(cx, EYE_CY, PUPIL_HALF + 1, PUPIL_HALF + 1, BLACK)
            fill_ellipse(cx, EYE_CY, PUPIL_HALF, PUPIL_HALF, pupil_color)
    else:
        for cx in (LEFT_EYE_CX, RIGHT_EYE_CX):
            fill_ellipse(cx, EYE_CY, EYE_HALF_W, EYE_HALF_H, bg_color)
            tft.fill_rect(cx - EYE_HALF_W, EYE_CY - 2, EYE_HALF_W * 2, 4, BLACK)


def setup_blinking(pupil_color, bg_color):
    """Start the blink cycle fresh: eyes open, next blink in 2s."""
    global _blink_open, _blink_next_toggle, _blink_pupil, _blink_bg
    _blink_pupil, _blink_bg = pupil_color, bg_color
    _blink_open = True
    draw_eyes(True, pupil_color, bg_color)
    _blink_next_toggle = ticks_add(ticks_ms(), 2000)


def step_blink():
    """Toggle the eyes open/closed once their scheduled time arrives."""
    global _blink_open, _blink_next_toggle
    tick_now = ticks_ms()
    if ticks_diff(tick_now, _blink_next_toggle) >= 0:
        if _blink_open:
            draw_eyes(False, _blink_pupil, _blink_bg)
            _blink_next_toggle = ticks_add(tick_now, 200)
        else:
            draw_eyes(True, _blink_pupil, _blink_bg)
            _blink_next_toggle = ticks_add(tick_now, 2000)
        _blink_open = not _blink_open


def setup_happy():
    """Draw the happy pot character: bright colors, raised arms, smile, blush."""
    tft.fill(HAPPY_PAL["bg"])
    draw_leaves(HAPPY_BLOBS, HAPPY_PAL, stem_height=90)
    draw_pot(HAPPY_PAL)
    draw_mouth(BLACK, smiling=True)
    draw_blush(HAPPY_PAL["blush"])
    draw_limbs(HAPPY_PAL, raised=True)
    setup_blinking(HAPPY_PAL["pupil"], HAPPY_PAL["bg"])


def setup_overwatered():
    """Draw the overwatered pot character: muted colors, drooped arms, frown."""
    tft.fill(OVERWATERED_PAL["bg"])
    draw_leaves(OVERWATERED_BLOBS, OVERWATERED_PAL, stem_height=35)
    draw_pot(OVERWATERED_PAL)
    draw_mouth(BLACK, smiling=False)
    draw_limbs(OVERWATERED_PAL, raised=False)
    setup_blinking(OVERWATERED_PAL["pupil"], OVERWATERED_PAL["bg"])


# ---------------- needs_water (wilted plant + watering can) ----------------
CAN_CX, CAN_CY = 55, 90
CAN_NOZZLE = (CAN_CX + 55, CAN_CY + 30)
NEEDS_WATER_STEM_HEIGHT = 35
NEEDS_WATER_CROWN_Y = POT_TOP_Y - NEEDS_WATER_STEM_HEIGHT

_nw_drops = []
NW_DROP_W, NW_DROP_H = 3, 8
NW_NUM_DROPS = 3


def draw_watering_can():
    """Draw a tilted watering can: handle, lid, glossy body, spout, nozzle."""
    cx, cy = CAN_CX, CAN_CY

    handle_top = cy - 25
    prev = None
    x = cx - 8
    while x <= cx + 8:
        t = (x - cx) / 8
        y = int(handle_top + 10 * t * t)
        if prev is not None:
            tft.line(prev[0], prev[1], x, y, CAN_SHADE)
        prev = (x, y)
        x += 1

    fill_ellipse(cx, cy - 15, 9, 5, CAN_SHADE)
    fill_ellipse(cx, cy, 18, 13, CAN_COLOR)
    fill_ellipse(cx - 5, cy - 4, 9, 6, CAN_HILITE)

    tip_x, tip_y = CAN_NOZZLE
    tft.line(cx + 16, cy - 2, tip_x, tip_y, CAN_COLOR)
    tft.line(cx + 16, cy - 1, tip_x, tip_y + 1, CAN_COLOR)
    tft.line(cx + 17, cy - 2, tip_x + 1, tip_y, CAN_COLOR)
    fill_ellipse(tip_x, tip_y, 4, 3, CAN_SHADE)
    fill_ellipse(tip_x, tip_y, 3, 2, CAN_COLOR)


def setup_needs_water():
    """Draw the wilted plant with a pouring watering can above it."""
    global _nw_drops
    tft.fill(NEEDS_WATER_PAL["bg"])
    draw_leaves(NEEDS_WATER_BLOBS, NEEDS_WATER_PAL, stem_height=NEEDS_WATER_STEM_HEIGHT)
    draw_pot(NEEDS_WATER_PAL)
    draw_mouth(BLACK, smiling=False)
    draw_limbs(NEEDS_WATER_PAL, raised=False)
    draw_watering_can()
    setup_blinking(NEEDS_WATER_PAL["pupil"], NEEDS_WATER_PAL["bg"])

    _, nozzle_y = CAN_NOZZLE
    _nw_drops = [nozzle_y + i * 15 for i in range(NW_NUM_DROPS)]


def step_needs_water():
    """Blink the face and advance each water drop from the nozzle downward."""
    step_blink()
    tip_x, _ = CAN_NOZZLE
    _, nozzle_y = CAN_NOZZLE
    for i, y in enumerate(_nw_drops):
        if nozzle_y <= y <= NEEDS_WATER_CROWN_Y:
            tft.fill_rect(tip_x, y, NW_DROP_W, NW_DROP_H, NEEDS_WATER_PAL["bg"])
        y += 3
        if y > NEEDS_WATER_CROWN_Y:
            y = nozzle_y
        _nw_drops[i] = y
        if nozzle_y <= y <= NEEDS_WATER_CROWN_Y:
            tft.fill_rect(tip_x, y, NW_DROP_W, NW_DROP_H, WATER_COLOR)


# ---------------- main loop ----------------
STATES = {
    "happy": (setup_happy, step_blink),
    "overwatered": (setup_overwatered, step_blink),
    "needs_water": (setup_needs_water, step_needs_water),
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
