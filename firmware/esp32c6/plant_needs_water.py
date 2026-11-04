"""Standalone demo: falling-rain animation on a black background, for
testing the "needs water" visual in isolation from the sensor/backend."""

from time import sleep_ms
import random

from machine import Pin, SPI
import st7789py as st7789

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
CYAN = st7789.CYAN

tft.fill(BLACK)

SCREEN_W = 172
SCREEN_H = 320
DROP_W, DROP_H = 4, 14
NUM_DROPS = 14

# each drop: [x, y, speed] - speed varies so rain looks natural, not uniform
drops = []
for i in range(NUM_DROPS):
    x = random.randint(0, SCREEN_W - DROP_W)
    y = random.randint(-SCREEN_H, 0)   # start above the screen, staggered
    speed = random.randint(4, 9)
    drops.append([x, y, speed])

while True:
    for drop in drops:
        x, y, speed = drop

        # erase the drop's OLD position before moving it
        if 0 <= y and y + DROP_H <= SCREEN_H:
            tft.fill_rect(x, y, DROP_W, DROP_H, BLACK)

        y += speed
        if y + DROP_H > SCREEN_H:
            # hit the bottom edge - disappear, then respawn above the screen
            y = random.randint(-40, 0)
            x = random.randint(0, SCREEN_W - DROP_W)
            drop[0] = x
        drop[1] = y

        # draw the drop at its NEW position, only if it fully fits on screen
        if 0 <= y and y + DROP_H <= SCREEN_H:
            tft.fill_rect(x, y, DROP_W, DROP_H, CYAN)

    sleep_ms(40)
