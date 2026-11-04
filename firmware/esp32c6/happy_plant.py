"""Standalone demo: draws a blinking smiley face with a filled smile
and vertical oval eyes on the ST7789 screen, for testing the display
and the blink animation loop in isolation from the sensor/backend."""

from time import sleep_ms
import math

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

YELLOW = st7789.YELLOW
WHITE = st7789.WHITE
CYAN = st7789.CYAN
BLACK = st7789.BLACK
RED = st7789.RED

tft.fill(YELLOW)

# mouth: a smile-shaped open mouth, built by sweeping across x and filling
# a vertical strip between a shallow "top" curve and a deeper "bottom" curve.
# At the corners the two curves meet (0 gap = pointed corner); at the
# center they're far apart (wide open mouth) - this is what makes it a
# smile shape rather than a symmetric oval.
mouth_x_start, mouth_x_end = 50, 122
mouth_center_x = (mouth_x_start + mouth_x_end) // 2
half_width = (mouth_x_end - mouth_x_start) // 2
corner_y = 175
top_depth = 8
bottom_depth = 30

x = mouth_x_start
while x <= mouth_x_end:
    t = (x - mouth_center_x) / half_width         # ranges from -1 to 1
    shape = 1 - t * t                              # 0 at corners, 1 at center
    top_y = int(corner_y + top_depth * shape)
    bottom_y = int(corner_y + bottom_depth * shape)
    gap = bottom_y - top_y
    if gap > 0:
        tft.fill_rect(x, top_y, 2, gap, RED)
    x += 2

def fill_ellipse(cx, cy, half_w, half_h, color):
    """Fill an oval by sweeping row by row and computing each row's width."""
    y = -half_h
    while y <= half_h:
        row_t = y / half_h
        row_half_w = int(half_w * math.sqrt(max(0, 1 - row_t * row_t)))
        if row_half_w > 0:
            tft.fill_rect(cx - row_half_w, cy + y, row_half_w * 2, 1, color)
        y += 1

LEFT_EYE_CX, RIGHT_EYE_CX, EYE_CY = 58, 114, 100
EYE_HALF_W, EYE_HALF_H = 15, 20     # bigger, oval (taller than wide)
BORDER = 3
PUPIL_HALF = 8

def draw_eyes_open():
    """Draw both eyes: border, inset white eyeball, bordered cyan pupil."""
    for cx in (LEFT_EYE_CX, RIGHT_EYE_CX):
        fill_ellipse(cx, EYE_CY, EYE_HALF_W, EYE_HALF_H, BLACK)
        fill_ellipse(cx, EYE_CY, EYE_HALF_W - BORDER, EYE_HALF_H - BORDER, WHITE)
        fill_ellipse(cx, EYE_CY, PUPIL_HALF + 1, PUPIL_HALF + 1, BLACK)
        fill_ellipse(cx, EYE_CY, PUPIL_HALF, PUPIL_HALF, CYAN)

def draw_eyes_closed():
    """Erase both eyes back to the background and draw a closed-eyelid line."""
    for cx in (LEFT_EYE_CX, RIGHT_EYE_CX):
        fill_ellipse(cx, EYE_CY, EYE_HALF_W, EYE_HALF_H, YELLOW)
        tft.fill_rect(cx - EYE_HALF_W, EYE_CY - 2, EYE_HALF_W * 2, 4, BLACK)

while True:
    draw_eyes_open()
    sleep_ms(2000)
    draw_eyes_closed()
    sleep_ms(200)
