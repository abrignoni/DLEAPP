"""Generate DLEAPP logo assets (Electron atom inside a desktop window)."""
import math, os
from PIL import Image, ImageDraw, ImageFont

import os as _os
DL = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))

NAVY_TOP = (18, 49, 74)     # #12314A
NAVY_BOT = (10, 24, 38)     # #0A1826
PANEL    = (22, 50, 75)     # #16324B
PANEL_BD = (42, 86, 120)    # #2A5678
TITLE    = (15, 39, 64)     # #0F2740
TEAL     = (46, 196, 182)   # #2EC4B6
CYAN     = (69, 196, 224)   # #45C4E0
DOTMUTED = (58, 110, 142)   # #3A6E8E


def _font(bold, size):
    cands = ([
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ] if bold else [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ])
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return m


def _v_gradient(size, top, bot):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h))


def draw_mark(S, tile=True):
    """Square mark at size S. If tile, draw the rounded navy background."""
    k = S / 512.0
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if tile:
        grad = _v_gradient((S, S), NAVY_TOP, NAVY_BOT).convert("RGBA")
        grad.putalpha(_rounded_mask((S, S), int(112 * k)))
        img.alpha_composite(grad)

    def R(x): return int(x * k)
    # desktop window
    win = [R(92), R(126), R(420), R(398)]
    d.rounded_rectangle(win, radius=R(22), fill=PANEL, outline=PANEL_BD, width=max(2, R(3)))
    # title bar (rounded top only)
    d.rounded_rectangle([win[0], win[1], win[2], R(178)], radius=R(22),
                        corners=(True, True, False, False), fill=TITLE)
    d.rectangle([win[0], R(160), win[2], R(178)], fill=TITLE)
    # window control dots
    for i, c in enumerate((CYAN, TEAL, DOTMUTED)):
        cx = R(120 + i * 26)
        d.ellipse([cx - R(8), R(144) - R(8), cx + R(8), R(144) + R(8)], fill=c)

    # electron atom, centered in the window body
    cx, cy = 256 * k, 292 * k
    rx, ry = 96 * k, 38 * k
    lw = max(3, R(7))
    for ang in (0, 60, 120):
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(
            [cx - rx, cy - ry, cx + rx, cy + ry], outline=TEAL, width=lw)
        layer = layer.rotate(ang, resample=Image.BICUBIC, center=(cx, cy))
        img.alpha_composite(layer)
    # electrons on the orbits + nucleus
    er = R(9)
    for ang in (0, 120, 240):
        ex = cx + rx * math.cos(math.radians(ang))
        ey = cy + rx * math.sin(math.radians(ang))
        # rotate point to sit on the tilted orbit set
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=CYAN)
    nr = R(15)
    d.ellipse([cx - nr, cy - nr, cx + nr, cy + nr], fill=CYAN)
    d.ellipse([cx - R(6), cy - R(6), cx + R(6), cy + R(6)], fill=(233, 252, 255))
    return img


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", path, img.size)


# --- square marks ---
save(draw_mark(512), f"{DL}/assets/DLEAPP_logo.png")
save(draw_mark(256), f"{DL}/assets/icon.png")
save(draw_mark(256), f"{DL}/scripts/_elements/logo.png")

# --- banner (mark + wordmark + tagline) ---
BW, BH = 1000, 200
banner = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
bg = _v_gradient((BW, BH), NAVY_TOP, NAVY_BOT).convert("RGBA")
bg.putalpha(_rounded_mask((BW, BH), 26))
banner.alpha_composite(bg)
mark = draw_mark(168, tile=False)
banner.alpha_composite(mark, (24, 16))
bd = ImageDraw.Draw(banner)
bd.text((210, 52), "DLEAPP", font=_font(True, 74), fill=CYAN)
bd.text((214, 132), "Desktop Logs · Events · Protobuf Parser",
        font=_font(False, 28), fill=(150, 179, 199))
save(banner, f"{DL}/scripts/_elements/DLEAPP_banner.png")

# --- small family badge (GUI, resized to 110x51) ---
badge = Image.new("RGBA", (240, 112), (0, 0, 0, 0))
bbg = _v_gradient((240, 112), NAVY_TOP, NAVY_BOT).convert("RGBA")
bbg.putalpha(_rounded_mask((240, 112), 18))
badge.alpha_composite(bbg)
badge.alpha_composite(draw_mark(96, tile=False), (8, 8))
ImageDraw.Draw(badge).text((104, 40), "DLEAPP", font=_font(True, 34), fill=CYAN)
save(badge, f"{DL}/assets/leapps_r_logo.png")

print("done")
