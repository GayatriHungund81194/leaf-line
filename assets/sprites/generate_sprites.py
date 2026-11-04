"""Generates Leaf-Line's pixel-art plant sprites: happy, needs_water
(wilted + a pouring watering can), and overwatered (yellowing + a
puddle), each as both a static PNG and an animated GIF.

Requires Pillow (`pip install Pillow`). Run from this directory:
    python3 generate_sprites.py
"""

import math

from PIL import Image, ImageDraw

GRID_W, GRID_H = 44, 58
SCALE = 8

POT_TOP_Y = 38
POT_BOTTOM_Y = POT_TOP_Y + 12
POT_CX = 22
STEM_X = 22
STEM_TOP_Y = {"happy": 14, "sad": 22, "overwatered": 22}

PALETTES = {
    "happy": {
        "pot_body": (70, 130, 150, 255), "pot_band": (230, 225, 210, 255),
        "pot_shadow": (50, 105, 125, 255), "stem": (70, 130, 60, 255),
        "leaf_a": (120, 190, 90, 255), "leaf_b": (90, 165, 75, 255),
        "leaf_c": (150, 210, 110, 255), "limb": (70, 130, 60, 255),
        "face": (35, 35, 35, 255), "blush": (235, 140, 130, 180),
    },
    "sad": {
        "pot_body": (90, 115, 125, 255), "pot_band": (210, 205, 190, 255),
        "pot_shadow": (70, 92, 100, 255), "stem": (135, 125, 70, 255),
        "leaf_a": (175, 170, 105, 255), "leaf_b": (150, 145, 85, 255),
        "leaf_c": (195, 190, 130, 255), "limb": (120, 112, 65, 255),
        "face": (35, 35, 35, 255), "blush": (0, 0, 0, 0),
    },
    "overwatered": {
        "pot_body": (100, 110, 95, 255), "pot_band": (200, 200, 180, 255),
        "pot_shadow": (75, 85, 72, 255), "stem": (150, 150, 70, 255),
        "leaf_a": (205, 200, 90, 255), "leaf_b": (170, 175, 80, 255),
        "leaf_c": (150, 130, 60, 255), "limb": (130, 128, 65, 255),
        "face": (35, 35, 35, 255), "blush": (0, 0, 0, 0),
    },
}

PUDDLE_COLOR = (120, 185, 215, 180)
PUDDLE_EDGE = (90, 150, 180, 200)

CAN_COLOR = (190, 160, 80, 255)
CAN_SHADE = (155, 128, 55, 255)
CAN_HILITE = (215, 190, 115, 255)
WATER_COLOR = (110, 180, 210, 255)


def rotate(px, py, angle_deg):
    """Rotate a local (px, py) point by angle_deg around the origin."""
    a = math.radians(angle_deg)
    return (px * math.cos(a) - py * math.sin(a),
            px * math.sin(a) + py * math.cos(a))


def blade_leaf(base_x, base_y, length, width, angle_deg, curve):
    """A single pointed blade-leaf polygon, rotated to angle_deg."""
    hw = width / 2
    local = [
        (0, 0), (hw, -length * 0.3), (hw * 0.55 + curve, -length * 0.7),
        (0, -length), (-hw * 0.55 + curve, -length * 0.7), (-hw, -length * 0.3),
    ]
    return [(base_x + rotate(x, y, angle_deg)[0], base_y + rotate(x, y, angle_deg)[1])
            for x, y in local]


def draw_pot(draw, pal):
    """Draw the barrel-shaped pot body, rim band, and base shadow."""
    rows = [(POT_TOP_Y, POT_TOP_Y + 3, 7), (POT_TOP_Y + 3, POT_TOP_Y + 9, 9),
            (POT_TOP_Y + 9, POT_BOTTOM_Y, 7)]
    for y0, y1, half_w in rows:
        draw.rectangle([POT_CX - half_w, y0, POT_CX + half_w, y1], fill=pal["pot_body"])
    draw.rectangle([POT_CX - 7, POT_TOP_Y, POT_CX + 7, POT_TOP_Y + 2], fill=pal["pot_band"])
    draw.rectangle([POT_CX - 7, POT_BOTTOM_Y - 3, POT_CX + 7, POT_BOTTOM_Y],
                    fill=pal["pot_shadow"])


def draw_face(draw, pal, mood, blink=False):
    """Draw round eyes (or a blink line), optional blush, and a mood-matched mouth."""
    eye_y = POT_TOP_Y + 6
    if blink:
        draw.line([(POT_CX - 7, eye_y + 1), (POT_CX - 4, eye_y + 1)], fill=pal["face"], width=1)
        draw.line([(POT_CX + 4, eye_y + 1), (POT_CX + 7, eye_y + 1)], fill=pal["face"], width=1)
    else:
        draw.ellipse([POT_CX - 7, eye_y, POT_CX - 4, eye_y + 3], fill=pal["face"])
        draw.ellipse([POT_CX + 4, eye_y, POT_CX + 7, eye_y + 3], fill=pal["face"])
    if pal["blush"][3] > 0:
        draw.ellipse([POT_CX - 9, eye_y + 3, POT_CX - 6, eye_y + 5], fill=pal["blush"])
        draw.ellipse([POT_CX + 6, eye_y + 3, POT_CX + 9, eye_y + 5], fill=pal["blush"])
    mouth_y = eye_y + 5
    if mood == "happy":
        draw.arc([POT_CX - 5, mouth_y - 3, POT_CX + 5, mouth_y + 3], 20, 160,
                  fill=pal["face"], width=2)
    else:
        draw.arc([POT_CX - 5, mouth_y - 1, POT_CX + 5, mouth_y + 5], 200, 340,
                  fill=pal["face"], width=2)


def draw_limbs(draw, pal, mood):
    """Draw stubby arm and leg nubs, raised for happy, drooped otherwise."""
    arm_y = POT_TOP_Y + 7
    if mood == "happy":
        draw.rectangle([POT_CX - 13, arm_y - 3, POT_CX - 9, arm_y + 1], fill=pal["limb"])
        draw.rectangle([POT_CX + 9, arm_y - 3, POT_CX + 13, arm_y + 1], fill=pal["limb"])
    else:
        draw.rectangle([POT_CX - 12, arm_y + 3, POT_CX - 8, arm_y + 7], fill=pal["limb"])
        draw.rectangle([POT_CX + 8, arm_y + 3, POT_CX + 12, arm_y + 7], fill=pal["limb"])
    draw.rectangle([POT_CX - 7, POT_BOTTOM_Y, POT_CX - 3, POT_BOTTOM_Y + 4], fill=pal["limb"])
    draw.rectangle([POT_CX + 3, POT_BOTTOM_Y, POT_CX + 7, POT_BOTTOM_Y + 4], fill=pal["limb"])


def draw_crown(draw, pal, mood, extra_angle=0):
    """Draw the stem and its radiating blade leaves (upright for happy, drooping otherwise)."""
    stem_top = STEM_TOP_Y[mood]
    draw.line([(STEM_X, POT_TOP_Y + 2), (STEM_X, stem_top)], fill=pal["stem"], width=2)
    if mood == "happy":
        blades = [(-70, 15, 4.5, 2), (-35, 19, 5.5, -1), (-10, 21, 6, 0),
                  (15, 21, 6, 0), (40, 19, 5.5, 1), (75, 15, 4.5, -2)]
    else:
        blades = [(-150, 10, 4, 1), (-170, 13, 4.5, 0), (180, 11, 5, -1),
                  (165, 9, 4, 1), (145, 8, 3.5, 0)]
    colors = [pal["leaf_b"], pal["leaf_a"], pal["leaf_c"],
              pal["leaf_c"], pal["leaf_a"], pal["leaf_b"]]
    for (angle, length, width, curve), color in zip(blades, colors):
        poly = blade_leaf(STEM_X, stem_top, length, width, angle + extra_angle, curve)
        draw.polygon(poly, fill=color)


def draw_puddle(draw, wobble=0):
    """Draw a rippling puddle at the base of the pot (overwatered state)."""
    cy = POT_BOTTOM_Y + 6
    half_w = 15 + wobble
    draw.ellipse([POT_CX - half_w, cy - 3, POT_CX + half_w, cy + 3], fill=PUDDLE_EDGE)
    draw.ellipse([POT_CX - half_w + 2, cy - 2, POT_CX + half_w - 2, cy + 2], fill=PUDDLE_COLOR)
    draw.arc([POT_CX - 6, cy - 1, POT_CX + 2, cy + 2], 200, 340, fill=PUDDLE_EDGE, width=1)


def render_plant(mood, extra_angle=0, bob=0, blink=False, puddle_wobble=None):
    """Compose one full frame of the plant character for the given mood."""
    pal = PALETTES[mood]
    img = Image.new("RGBA", (GRID_W, GRID_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_crown(draw, pal, mood, extra_angle)
    if puddle_wobble is not None:
        draw_puddle(draw, puddle_wobble)
    draw_pot(draw, pal)
    draw_face(draw, pal, mood, blink)
    draw_limbs(draw, pal, mood)
    if bob:
        shifted = Image.new("RGBA", (GRID_W, GRID_H), (0, 0, 0, 0))
        shifted.paste(img, (0, bob), img)
        img = shifted
    return img


def draw_can_upright():
    """Draw the watering can upright (body, lid, handle, spout, nozzle)."""
    img = Image.new("RGBA", (42, 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.arc([5, 0, 21, 18], 190, 350, fill=CAN_SHADE, width=2)
    d.ellipse([6, 11, 20, 17], fill=CAN_SHADE)
    d.ellipse([7, 10, 19, 15], fill=CAN_COLOR)
    d.ellipse([4, 14, 26, 32], fill=CAN_COLOR)
    d.pieslice([4, 22, 26, 32], 0, 180, fill=CAN_SHADE)
    d.ellipse([7, 17, 17, 23], fill=CAN_HILITE)
    d.polygon([(24, 18), (37, 8), (39, 10), (27, 22)], fill=CAN_COLOR)
    d.ellipse([35, 5, 41, 11], fill=CAN_SHADE)
    d.ellipse([36, 6, 40, 10], fill=CAN_COLOR)
    return img


CAN_UPRIGHT = draw_can_upright()


def render_alert(tilt_extra=0, drop_offsets=()):
    """Compose one frame of the needs-water state: wilted plant + tilted can + drops."""
    base = render_plant("sad")
    canvas = Image.new("RGBA", (GRID_W, GRID_H), (0, 0, 0, 0))
    canvas.paste(base, (0, 0), base)

    can = CAN_UPRIGHT.rotate(-28 + tilt_extra, expand=True, resample=Image.NEAREST)
    can_small = can.resize((can.width // 2, can.height // 2), Image.NEAREST)
    can_x, can_y = -6, -6
    canvas.paste(can_small, (can_x, can_y), can_small)

    draw = ImageDraw.Draw(canvas)
    spout_tip = (can_x + can_small.width - 4, can_y + can_small.height - 6)
    for dx, dy in drop_offsets:
        x, y = spout_tip[0] + dx, spout_tip[1] + dy
        if 0 <= y < GRID_H:
            draw.rectangle([x, y, x + 1, y + 2], fill=WATER_COLOR)
    return canvas


def to_sprite_sheet_gif(frames, name, duration=300):
    """Scale up each frame and save as an animated GIF plus a first-frame PNG."""
    big = [f.resize((GRID_W * SCALE, GRID_H * SCALE), Image.NEAREST) for f in frames]
    big[0].save(name, save_all=True, append_images=big[1:], duration=duration, loop=0, disposal=2)
    big[0].save(name.replace(".gif", ".png"))


def main():
    """Generate and save all three sprite animations."""
    happy_frames = [
        render_plant("happy", extra_angle=0),
        render_plant("happy", extra_angle=5),
        render_plant("happy", extra_angle=0),
        render_plant("happy", extra_angle=-5),
        render_plant("happy", extra_angle=0, blink=True),
    ]
    to_sprite_sheet_gif(happy_frames, "happy.gif", duration=280)

    alert_frames = [
        render_alert(tilt_extra=0, drop_offsets=[(0, 0)]),
        render_alert(tilt_extra=-3, drop_offsets=[(0, 4), (3, -2)]),
        render_alert(tilt_extra=0, drop_offsets=[(0, 8), (3, 2), (-2, -3)]),
        render_alert(tilt_extra=-3, drop_offsets=[(3, 6), (-2, 1)]),
    ]
    to_sprite_sheet_gif(alert_frames, "needs_water.gif", duration=220)

    overwatered_frames = [
        render_plant("overwatered", bob=0, puddle_wobble=0),
        render_plant("overwatered", bob=1, puddle_wobble=1),
        render_plant("overwatered", bob=0, puddle_wobble=2),
        render_plant("overwatered", bob=1, puddle_wobble=1),
    ]
    to_sprite_sheet_gif(overwatered_frames, "overwatered.gif", duration=400)

    print("done")


if __name__ == "__main__":
    main()
