"""Prints 30 raw moisture sensor readings, 500ms apart, then exits.

Used for calibration: run this while the sensor sits in dry soil, then
again while it sits in soil saturated to field capacity, and average
each run's stable readings to get the DRY_VALUE/WET_VALUE for
calibration.py. Exits on its own (unlike the other firmware scripts),
so it never holds the serial port open."""

from time import sleep_ms

from machine import Pin, ADC

sensor = ADC(Pin(1))
sensor.atten(ADC.ATTN_11DB)   # allows reading the full 0-3.3V range

for i in range(30):
    value = sensor.read_u16()
    print("raw reading:", value)
    sleep_ms(500)

print("done")
