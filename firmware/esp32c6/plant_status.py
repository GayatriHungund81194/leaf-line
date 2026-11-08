"""Continuously reads soil moisture and reports it to the backend.

Reads the capacitive moisture sensor every CHECK_INTERVAL_MS, converts
the raw reading to a 0-100% scale using the calibration values in
calibration.py, and POSTs it to the FastAPI backend over Wi-Fi. The
backend (not this device) decides and stores the watering state - all
animations live on the web frontend, not on this board's screen.
"""

from time import sleep_ms, ticks_ms, ticks_diff

import network
import urequests
from machine import Pin, ADC

from calibration import DRY_VALUE, WET_VALUE
from wifi_config import WIFI_SSID, WIFI_PASSWORD

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
        print("Wi-Fi connection failed - will retry on the next reading")
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


def read_moisture_percent():
    """Sample the sensor 10x and return the averaged, calibrated moisture %."""
    total = 0
    for _ in range(10):
        total += sensor.read_u16()
        sleep_ms(50)
    raw_reading = total / 10

    moisture_percent = (DRY_VALUE - raw_reading) / (DRY_VALUE - WET_VALUE) * 100
    moisture_percent = max(0, min(100, moisture_percent))

    print("Raw:", raw_reading, "| Moisture:", round(moisture_percent, 1), "%")
    return moisture_percent


connect_wifi()

last_check = ticks_ms() - CHECK_INTERVAL_MS   # take the first reading immediately

while True:
    now = ticks_ms()
    if ticks_diff(now, last_check) >= CHECK_INTERVAL_MS:
        last_check = now
        if not network.WLAN(network.STA_IF).isconnected():
            connect_wifi()
        moisture = read_moisture_percent()
        post_reading(moisture)
    sleep_ms(100)
