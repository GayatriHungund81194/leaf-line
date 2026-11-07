"""Connects to Wi-Fi and prints the assigned IP address, then exits."""

import time

import network

from wifi_config import WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

print("Connecting", end="")
for _ in range(20):
    if wlan.isconnected():
        break
    print(".", end="")
    time.sleep(1)

if wlan.isconnected():
    print("\nConnected! IP address:", wlan.ifconfig()[0])
else:
    print("\nFailed to connect")
