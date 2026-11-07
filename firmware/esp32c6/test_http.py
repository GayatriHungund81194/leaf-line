"""Connects to Wi-Fi, then POSTs a test reading to the backend and
prints the response, to confirm end-to-end connectivity."""

import time

import network
import urequests

from wifi_config import WIFI_SSID, WIFI_PASSWORD

BACKEND_URL = "http://192.168.1.164:8000/sensorreading"
PLANT_ID = 1

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

for _ in range(20):
    if wlan.isconnected():
        break
    time.sleep(1)

print("IP:", wlan.ifconfig()[0])

response = urequests.post(
    BACKEND_URL,
    json={"plant_id": PLANT_ID, "moisture_reading": 42.0},
)
print("Status:", response.status_code)
print("Body:", response.text)
response.close()
