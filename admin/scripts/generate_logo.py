"""Generate DLEAPP logo/banner assets.

A desktop application window (bright cyan bezel, title bar, lit screen) with a
glowing Electron atom inside, in the Electron-Teal-on-Navy palette. Rendered
supersampled (SS x) then downscaled for crisp high-resolution output.

Run:  python admin/scripts/generate_logo.py
Outputs: assets/ (logo, icon, badge) and scripts/_elements/ (report banner, logo).
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SS = 4  # supersample factor

TILE_TOP = (22, 52, 79)     # #16344F
TILE_BOT = (8, 20, 32)      # #081420
BEZEL    = (10, 29, 46)     # #0A1D2E  window frame
BORDER   = (76, 212, 232)   # #4CD4E8  bright bezel line
SCR_TOP  = (28, 62, 92)     # #1C3E5C  screen
SCR_BOT  = (18, 41, 62)     # #12293E
TITLE    = (14, 34, 52)     # #0E2234
DIVIDER  = (52, 132, 168)   # #3484A8
TEAL     = (51, 214, 192)   # #33D6C0
CYAN     = (111, 230, 255)  # #6FE6FF
DOTMUT   = (70, 120, 150)
WHITE    = (233, 252, 255)
TAGLINE_GRAY = (150, 179, 199)


def _font(bold, size):
    cands = ([
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
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


def _rmask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return m


def _vgrad(size, top, bot, radius=0):
    w, h = size
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    im = col.resize((w, h)).convert("RGBA")
    if radius:
        im.putalpha(_rmask((w, h), radius))
    return im


def draw_mark(S, tile=True):
    """Draw the mark at pixel size S (call via render() for supersampling)."""
    k = S / 512.0
    def R(x): return x * k
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    if tile:
        img.alpha_composite(_vgrad((S, S), TILE_TOP, TILE_BOT, int(R(112))))

    wx0, wy0, wx1, wy1 = R(84), R(120), R(428), R(404)
    rad, tbar, ins = R(26), R(58), R(10)
    d = ImageDraw.Draw(img)

    # bezel outer glow
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([wx0, wy0, wx1, wy1], radius=rad,
                                           outline=BORDER + (150,), width=int(R(6)))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(R(10))))

    # frame
    d.rounded_rectangle([wx0, wy0, wx1, wy1], radius=rad, fill=BEZEL)

    # lit screen
    sx0, sy0, sx1, sy1 = wx0 + ins, wy0 + tbar, wx1 - ins, wy1 - ins
    screen = _vgrad((int(sx1 - sx0), int(sy1 - sy0)), SCR_TOP, SCR_BOT, int(R(12)))
    gw, gh = screen.size
    rg = Image.new("L", (gw, gh), 0)
    rgd = ImageDraw.Draw(rg)
    cxg, cyg = gw * 0.5, gh * 0.52
    for i in range(28, 0, -1):
        a = int(64 * (i / 28.0) ** 2)
        rr = R(165) * (i / 28.0)
        rgd.ellipse([cxg - rr, cyg - rr * 0.72, cxg + rr, cyg + rr * 0.72], fill=a)
    rg = rg.filter(ImageFilter.GaussianBlur(R(22)))
    wash = Image.new("RGBA", (gw, gh), TEAL + (0,))
    wash.putalpha(rg)
    screen.alpha_composite(wash)
    img.alpha_composite(screen, (int(sx0), int(sy0)))

    # title bar + divider + dots
    tb = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(tb).rounded_rectangle([wx0 + ins, wy0 + ins, wx1 - ins, wy0 + tbar],
                                         radius=R(12), corners=(True, True, False, False), fill=TITLE)
    img.alpha_composite(tb)
    d.line([wx0 + ins, wy0 + tbar, wx1 - ins, wy0 + tbar], fill=DIVIDER + (255,), width=max(1, int(R(3))))
    for i, c in enumerate((CYAN, TEAL, DOTMUT)):
        cx, cy, rr = wx0 + ins + R(24) + i * R(30), wy0 + ins + R(20), R(10)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c)

    # bright inner bezel line
    d.rounded_rectangle([wx0, wy0, wx1, wy1], radius=rad, outline=BORDER, width=max(2, int(R(4))))

    # Electron atom (glow + sharp)
    cx, cy, rx, ry = R(256), R(288), R(92), R(35)
    lw = max(2, int(R(9)))
    orbits = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for ang in (0, 60, 120):
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=TEAL, width=lw)
        orbits.alpha_composite(layer.rotate(ang, resample=Image.BICUBIC, center=(cx, cy)))
    img.alpha_composite(orbits.filter(ImageFilter.GaussianBlur(R(5))))
    img.alpha_composite(orbits)

    fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    for ang in (0, 120, 240):
        ex, ey, er = cx + rx * math.cos(math.radians(ang)), cy + rx * math.sin(math.radians(ang)), R(11)
        fd.ellipse([ex - er, ey - er, ex + er, ey + er], fill=CYAN)
        fd.ellipse([ex - er * 0.4, ey - er * 0.4, ex + er * 0.4, ey + er * 0.4], fill=WHITE)
    nr = R(17)
    fd.ellipse([cx - nr, cy - nr, cx + nr, cy + nr], fill=CYAN)
    fd.ellipse([cx - nr * 0.45, cy - nr * 0.45, cx + nr * 0.45, cy + nr * 0.45], fill=WHITE)
    img.alpha_composite(fg.filter(ImageFilter.GaussianBlur(R(4))))
    img.alpha_composite(fg)
    return img


def render(target, tile=True):
    return draw_mark(target * SS, tile=tile).resize((target, target), Image.LANCZOS)


def save(img, rel):
    path = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", rel, img.size)


def make_banner(w, h, mark_px, name_size, tag_size, rad):
    b = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    b.alpha_composite(_vgrad((w, h), TILE_TOP, TILE_BOT, rad))
    m = int(mark_px)
    mark = draw_mark(m * SS, tile=False).resize((m, m), Image.LANCZOS)
    b.alpha_composite(mark, (int(h * 0.075), (h - m) // 2))
    d = ImageDraw.Draw(b)
    tx = int(h * 0.075) + m + int(w * 0.03)
    d.text((tx, int(h * 0.23)), "DLEAPP", font=_font(True, name_size), fill=CYAN)
    if tag_size:
        d.text((tx + 4, int(h * 0.66)), "Desktop Logs · Events · Protobuf Parser",
               font=_font(False, tag_size), fill=TAGLINE_GRAY)
    return b


if __name__ == "__main__":
    save(render(1024), "assets/DLEAPP_logo.png")
    save(render(1024), "assets/icon.png")
    save(render(1024), "scripts/_elements/logo.png")
    save(make_banner(2000, 400, 340, 150, 56, 52), "scripts/_elements/DLEAPP_banner.png")
    save(make_banner(700, 300, 250, 118, 0, 40), "assets/leapps_r_logo.png")
    print("done")
