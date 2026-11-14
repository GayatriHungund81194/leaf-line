"""Reads soil moisture once per wake cycle, reports it to the backend,
then deep-sleeps until the next check.

Deep sleep powers the chip down almost entirely between readings -
far less power than staying awake and polling in a loop. A deep sleep
"wake" is actually a full reset: the chip reboots and main.py runs
this file from the top again, which is what makes this repeat forever
without needing a while loop.
"""

from time import sleep_ms

import network
import urequests
from machine import ADC, Pin, deepsleep

from calibration import DRY_VALUE, WET_VALUE
from wifi_config import WIFI_PASSWORD, WIFI_SSID

ACTIVE_PLANT = "anthurium"  # which plant THIS board is monitoring (label only)
CHECK_INTERVAL_HOURS = 4
CHECK_INTERVAL_MS = int(CHECK_INTERVAL_HOURS * 60 * 60 * 1000)

PLANT_ID = 1   # the backend's id for ACTIVE_PLANT - must already exist there
BACKEND_URL = "http://192.168.1.164:8000/sensorreading"

sensor = ADC(Pin(1))
sensor.atten(ADC.ATTN_11DB)


def connect_wifi():
    """Connect to Wi-Fi, waiting up to 10s. Returns True if connected."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(10):
        if wlan.isconnected():
            break
        sleep_ms(1000)
    if wlan.isconnected():
        print("Wi-Fi connected, IP:", wlan.ifconfig()[0])
    else:
        print("Wi-Fi connection failed - will try again next wake")
    return wlan.isconnected()


def post_reading(moisture_percent):
    """POST the reading to the backend. Never raises - just logs failures,
    so a network hiccup never prevents the device from going back to sleep."""
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
moisture = read_moisture_percent()
post_reading(moisture)

print("Sleeping for", CHECK_INTERVAL_HOURS, "hours...")
deepsleep(CHECK_INTERVAL_MS)
