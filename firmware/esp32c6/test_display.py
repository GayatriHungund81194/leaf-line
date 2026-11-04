"""Sanity check: fills the ST7789 screen red, to confirm the driver,
wiring, and pin mapping are correct before building anything on top."""

from machine import Pin, SPI
import st7789py as st7789

spi = SPI(1, baudrate=40000000, polarity=0, phase=0,
          sck=Pin(7), mosi=Pin(6))

backlight = Pin(22, Pin.OUT)
backlight.value(1)

tft = st7789.ST7789(
    spi,
    240,
    320,
    reset=Pin(21, Pin.OUT),
    dc=Pin(15, Pin.OUT),
    cs=Pin(14, Pin.OUT),
    backlight=backlight,
    rotation=0,
)

tft.fill(st7789.RED)
print("Sent RED fill to display")
