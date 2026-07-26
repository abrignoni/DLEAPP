"""Generate DLEAPP logo/banner assets from the source artwork.

The DLEAPP icon is artwork by Johann Polewczyk: three stacked application
windows with a pointer, in a flat style with heavy dark outlines. The original
is kept untouched at ``assets/source/DLEAPP_art_original.png`` (rust tile); this
script recolors the tile to DLEAPP's plum brand color and derives every asset
used by the app, the HTML report and the repo.

DLEAPP brand palette (taken from the artwork itself):
    tile   #5F3A5C  plum / aubergine     (unclaimed in the LEAPP family)
    ink    #2A1710  dark brown outlines
    gold   #F2B035  primary accent
    blue   #2A7FD4  secondary accent
    grey   #D5D9DE  neutral / inputs
    cream  #F7F0E0  light text

Run:  python admin/scripts/generate_logo.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

DL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE = os.path.join(DL, "assets", "source", "DLEAPP_art_original.png")

RUST = (163, 78, 42)      # tile color in the source artwork
PLUM = (95, 58, 92)       # #5F3A5C  DLEAPP tile
PILL = (74, 45, 72)       # #4A2D48  slightly darker plum for banner pills
INK = (42, 23, 16)        # #2A1710
GOLD = (242, 176, 53)     # #F2B035
CREAM = (247, 240, 224)   # #F7F0E0


def _font(size, bold=True):
    cands = ([
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ] if bold else ["/System/Library/Fonts/Supplemental/Arial.ttf"])
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def recolor(img, new=PLUM, old=RUST, tol=70.0):
    """Replace the tile color, feathering anti-aliased fringes so the artwork
    (outlines, windows, pointer) is left untouched."""
    arr = np.array(img.convert("RGBA")).astype(np.float32)
    rgb = arr[..., :3]
    dist = np.sqrt(((rgb - np.array(old, dtype=np.float32)) ** 2).sum(axis=-1))
    weight = np.clip(1.0 - (dist / tol) ** 2, 0.0, 1.0)[..., None]
    arr[..., :3] = rgb + (np.array(new, dtype=np.float32) - rgb) * weight
    return Image.fromarray(arr.round().astype(np.uint8), "RGBA")


def tile_only(img, tile_color=PLUM, tol=70.0):
    """Crop to the rounded tile, dropping the artwork's outer drop shadow."""
    arr = np.array(img.convert("RGBA"))
    rgb = arr[..., :3].astype(np.float32)
    dist = np.sqrt(((rgb - np.array(tile_color, dtype=np.float32)) ** 2).sum(axis=-1))
    ys, xs = np.where((dist < tol) & (arr[..., 3] > 200))
    if not len(xs):
        return img
    return img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def _rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                        radius=radius, fill=255)
    return m


def make_banner(mark, design_h=640, pill=PILL, text=GOLD):
    """Wide wordmark banner: tile mark + large DLEAPP wordmark on a pill.

    Mirrors the other LEAPP banners (a tight ~4:1 lockup, no tagline) so it can
    be shown small in the HTML report and the GUI header.
    """
    pad = int(design_h * 0.09)
    gap = int(design_h * 0.06)
    mark_h = int(design_h * 0.82)
    font = _font(int(design_h * 0.60))

    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    bb = probe.textbbox((0, 0), "DLEAPP", font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]

    width = pad + mark_h + gap + tw + pad
    banner = Image.new("RGBA", (width, design_h), (0, 0, 0, 0))
    plate = Image.new("RGBA", (width, design_h), pill + (255,))
    plate.putalpha(_rounded_mask((width, design_h), int(design_h * 0.20)))
    banner.alpha_composite(plate)

    m = mark.resize((mark_h, mark_h), Image.LANCZOS)
    banner.alpha_composite(m, (pad, (design_h - mark_h) // 2))

    d = ImageDraw.Draw(banner)
    d.text((pad + mark_h + gap, (design_h - th) // 2 - bb[1]), "DLEAPP",
           font=font, fill=text)
    return banner


def save(img, rel):
    path = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print(f"wrote {rel} {img.size}")


if __name__ == "__main__":
    src = Image.open(SOURCE).convert("RGBA")
    plum = recolor(src, PLUM)          # full artwork, plum tile, with shadow
    mark = tile_only(plum, PLUM)       # just the tile, no drop shadow

    # square marks
    save(plum.resize((1024, 1024), Image.LANCZOS), "assets/DLEAPP_logo.png")
    save(mark.resize((256, 256), Image.LANCZOS), "assets/icon.png")
    save(plum.resize((512, 512), Image.LANCZOS), "scripts/_elements/logo.png")

    # wide wordmark banner: HTML report (shown ~88px) and GUI header (208x52)
    banner = make_banner(mark)
    save(banner, "scripts/_elements/DLEAPP_banner.png")
    save(banner, "assets/DLEAPP_banner.png")

    # NOTE: assets/leapps_r_logo.png is the shared leapps.org family logo and is
    # intentionally not generated here.
    print("done")
