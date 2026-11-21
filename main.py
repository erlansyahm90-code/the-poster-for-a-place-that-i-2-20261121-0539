#!/usr/bin/env python3
"""VELMORA — travel poster for a place that isn't there.

A 1024x1024 travel poster drawn from scratch with PIL (stdlib + Pillow
only, no network, fully deterministic). The invented place: Velmora, a
cliff town where the sea falls UP — ribbons of water rise from the bay
into the evening sky. No quotes, no star ratings, no borrowed landmark.
"""
import hashlib
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(draw, box, top, bottom):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        draw.line([(x0, y), (x1, y)], fill=lerp(top, bottom, t))


def bezier(p0, p1, p2, n=90):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def spaced_text(draw, cx, y, text, font, fill, tracking=0):
    """Draw centered text with manual letter tracking."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def main():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)

    # --- sky: indigo dusk down to amber horizon -------------------------
    vgrad(d, (0, 0, W, 660), (22, 34, 77), (232, 115, 74))
    # warm band just above the horizon
    vgrad(d, (0, 560, W, 660), (232, 115, 74), (245, 185, 66))

    # --- stars in the upper sky (deterministic) -------------------------
    star_xy = [(80, 60), (150, 130), (240, 50), (330, 110), (700, 70),
               (820, 120), (900, 55), (950, 180), (420, 40), (40, 200),
               (990, 300), (120, 300), (860, 240), (560, 90), (680, 160)]
    for sx, sy in star_xy:
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 240, 200))

    # --- clouds: soft warm streaks --------------------------------------
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for cx, cy, rx, ry, alpha in [(180, 300, 150, 10, 32), (830, 260, 170, 11, 30),
                                  (300, 420, 120, 8, 24), (760, 430, 130, 8, 24)]:
        g.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(255, 190, 150, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    d = ImageDraw.Draw(img)

    # --- sun with glow ---------------------------------------------------
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for r, a in [(210, 26), (170, 40), (135, 60)]:
        g.ellipse([640 - r, 590 - r, 640 + r, 590 + r], fill=(255, 190, 90, a))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)
    d.ellipse([640 - 95, 590 - 95, 640 + 95, 590 + 95], fill=(255, 216, 138))
    d.ellipse([640 - 78, 590 - 78, 640 + 78, 590 + 78], fill=(255, 226, 160))

    # --- sea: teal gradient below the horizon ---------------------------
    vgrad(d, (0, 660, W, H), (38, 96, 112), (10, 42, 62))

    # --- sun reflection on the water ------------------------------------
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    # broken shimmer dashes under the sun (deterministic offsets)
    segs = [(690, 70, 150), (730, 95, 120), (780, 120, 90),
            (840, 150, 60), (910, 185, 40), (980, 220, 26)]
    for row, (y, half_w, a) in enumerate(segs):
        x = 640 - half_w
        while x < 640 + half_w:
            seg_w = 26 + ((row * 37 + int(x)) % 41)
            g.rectangle([x, y, min(x + seg_w, 640 + half_w), y + 7],
                        fill=(255, 205, 120, a))
            x += seg_w + 18
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    # --- cliffs: dark silhouettes framing the bay ------------------------
    d.polygon([(0, 1024), (0, 700), (60, 640), (150, 560), (230, 520),
               (260, 660), (210, 1024)], fill=(18, 26, 52))
    d.polygon([(1024, 1024), (1024, 680), (960, 620), (880, 540), (800, 520),
               (790, 660), (850, 1024)], fill=(18, 26, 52))
    # warm rim light on the cliff edges facing the sun
    d.line([(230, 520), (260, 660)], fill=(245, 150, 80), width=4)
    d.line([(800, 520), (790, 660)], fill=(245, 150, 80), width=4)

    # --- the upward sea: ribbons of water rising into the sky -----------
    def ribbon(p0, p1, p2, width, color):
        pts = bezier(p0, p1, p2)
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=color, width=width)
        # spray dots near the top of the arc
        for i in range(0, len(pts), 6):
            x, y = pts[i]
            r = 3 if i > len(pts) * 0.6 else 2
            d.ellipse([x - r, y - r, x + r, y + r], fill=(225, 240, 250))

    ribbon((380, 660), (300, 430), (420, 300), 10, (207, 232, 245))
    ribbon((520, 660), (620, 420), (600, 320), 8, (190, 222, 240))
    ribbon((455, 660), (470, 450), (540, 360), 5, (220, 238, 248))
    # where the ribbons leave the water: bright foam rings
    for cx in (380, 520, 455):
        d.ellipse([cx - 30, 654, cx + 30, 668], outline=(230, 242, 250), width=3)

    # --- lighthouse on the left cliff ------------------------------------
    d.polygon([(96, 560), (116, 560), (112, 470), (100, 470)], fill=(245, 240, 220))
    d.rectangle([94, 452, 118, 472], fill=(30, 40, 70))
    d.ellipse([98, 440, 114, 456], fill=(255, 220, 130))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.polygon([(112, 448), (330, 400), (330, 470)], fill=(255, 230, 150, 55))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    # --- cliff town on the right ledge ------------------------------------
    houses = [(806, 552, 44, 38), (852, 538, 38, 52), (894, 556, 46, 34),
              (940, 542, 36, 50), (824, 596, 38, 32), (868, 590, 44, 38),
              (916, 600, 36, 28)]
    for hx, hy, hw, hh in houses:
        d.rectangle([hx, hy, hx + hw, hy + hh], fill=(242, 232, 208))
        d.polygon([(hx - 2, hy), (hx + hw / 2, hy - 12), (hx + hw + 2, hy)],
                  fill=(40, 52, 84))
        # one warm lit window per house, sized to the house
        d.rectangle([hx + hw // 5, hy + hh // 4, hx + 2 * hw // 5, hy + hh // 2],
                    fill=(255, 196, 90))

    # --- sailboats in the bay --------------------------------------------
    def boat(bx, by, s):
        d.polygon([(bx, by), (bx + 26 * s, by), (bx + 13 * s, by - 34 * s)],
                  fill=(245, 240, 225))
        d.polygon([(bx + 28 * s, by), (bx + 46 * s, by), (bx + 28 * s, by - 24 * s)],
                  fill=(230, 220, 200))
        d.polygon([(bx - 8 * s, by), (bx + 54 * s, by), (bx + 44 * s, by + 10 * s),
                   (bx + 2 * s, by + 10 * s)], fill=(20, 30, 55))

    boat(300, 760, 1.0)
    boat(700, 830, 0.8)

    # --- birds -------------------------------------------------------------
    for bx, by, s in [(250, 300, 1.0), (300, 270, 0.8), (700, 330, 0.9), (760, 300, 0.7)]:
        d.arc([bx - 10 * s, by - 6 * s, bx, by + 6 * s], 200, 340,
              fill=(30, 40, 70), width=3)
        d.arc([bx, by - 6 * s, bx + 10 * s, by + 6 * s], 200, 340,
              fill=(30, 40, 70), width=3)

    # --- title: place name set into the picture ---------------------------
    title_font = ImageFont.truetype(SERIF_BOLD, 118)
    sub_font = ImageFont.truetype(SANS_BOLD, 30)
    # soft shadow under the title for legibility over the sky
    spaced_text(d, W // 2 + 3, 73, "VELMORA", title_font, (20, 30, 66), tracking=14)
    spaced_text(d, W // 2, 70, "VELMORA", title_font, (255, 243, 214), tracking=14)
    spaced_text(d, W // 2, 196, "WHERE THE SEA FALLS UP", sub_font,
                (255, 214, 140), tracking=8)
    # small ornament: line — diamond — line
    d.line([(372, 248), (482, 248)], fill=(255, 214, 140), width=2)
    d.line([(542, 248), (652, 248)], fill=(255, 214, 140), width=2)
    d.polygon([(512, 240), (520, 248), (512, 256), (504, 248)], fill=(255, 214, 140))

    img = img.convert("RGB")
    out_path = os.path.join(OUT_DIR, "entry.png")
    os.makedirs(OUT_DIR, exist_ok=True)
    img.save(out_path, "PNG")
    # local copy for inspection / repo
    here = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(here, "entry.png")
    img.save(local_path, "PNG")
    data = open(local_path, "rb").read()
    print("wrote", out_path, len(data), "bytes")
    print("sha256", hashlib.sha256(data).hexdigest())
    print("size", img.size)


if __name__ == "__main__":
    main()
