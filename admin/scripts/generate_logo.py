"""Generate DLEAPP logo/banner assets from the source vector artwork.

The DLEAPP icon is artwork by Johann Polewczyk: three stacked application
windows with a pointer. James Habben's idea gave each window the window
controls of a different desktop OS, so the icon says "desktop apps, any
platform" at a glance:

    back   amber  - Linux  : circular controls on the left
    middle blue   - Windows: line glyphs on the right
    front  light  - macOS  : traffic lights on the left

``assets/source/DLEAPP_art.svg`` is the working master (plum tile, OS controls,
dimensional shading). Johann's original flat artwork is kept untouched beside it
as ``DLEAPP_art_original.svg``. This script renders every asset used by the app,
the HTML report and the repo straight from the master vector.

DLEAPP brand palette (taken from the artwork itself):
    tile   #5F3A5C  plum / aubergine     (unclaimed in the LEAPP family)
    ink    #2A1710  dark outlines
    gold   #F2B035  primary accent
    blue   #2A7FD4  secondary accent
    grey   #D5D9DE  neutral / inputs
    cream  #F7F0E0  light text

Requires ``rsvg-convert`` (librsvg) for SVG rendering and ``iconutil`` for the
macOS .icns. Run:  python admin/scripts/generate_logo.py
"""
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

DL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE_SVG = os.path.join(DL, "assets", "source", "DLEAPP_art.svg")

PLUM = "#5F3A5C"          # DLEAPP tile
PILL = (74, 45, 72)       # #4A2D48  darker plum for banner pills
GOLD = (242, 176, 53)     # #F2B035  wordmark

ICNS_SIZES = [16, 32, 128, 256, 512]  # each also rendered @2x


def _font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/HelveticaNeue.ttc"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def brand_svg():
    """The master artwork (plum tile, per-OS window controls)."""
    with open(SOURCE_SVG, "r", encoding="utf-8") as fh:
        svg = fh.read()
    if PLUM not in svg:
        raise SystemExit(f"tile color {PLUM} not found in {SOURCE_SVG}")
    return svg


def mark_svg(svg):
    """The tile alone: cropped to the rounded square, drop shadow removed, so
    it can be placed on a colored pill without a halo."""
    svg = svg.replace('viewBox="0 0 1024 1024" width="1024" height="1024"',
                      'viewBox="100 100 824 824" width="824" height="824"')
    return svg.replace('<g filter="url(#tileSh)">', "<g>")


def render(svg_text, size, out_path):
    """Render SVG text to a PNG of size x size using rsvg-convert."""
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False,
                                     encoding="utf-8") as tmp:
        tmp.write(svg_text)
        tmp_path = tmp.name
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                        tmp_path, "-o", out_path], check=True)
    finally:
        os.unlink(tmp_path)
    return Image.open(out_path).convert("RGBA")


def _rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                        radius=radius, fill=255)
    return m


def make_banner(mark, design_h=640, pill=PILL, text=GOLD):
    """Wide wordmark banner: tile mark + large DLEAPP wordmark on a pill.

    Mirrors the other LEAPP banners (a tight lockup, no tagline) so it reads
    well small in the HTML report and the GUI header.
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

    banner.alpha_composite(mark.resize((mark_h, mark_h), Image.LANCZOS),
                           (pad, (design_h - mark_h) // 2))
    ImageDraw.Draw(banner).text(
        (pad + mark_h + gap, (design_h - th) // 2 - bb[1]), "DLEAPP",
        font=font, fill=text)
    return banner


def build_icns(svg, out_rel):
    """Render each icon size straight from the vector, then pack an .icns."""
    if not shutil.which("iconutil"):
        print("skip .icns (iconutil not available)")
        return
    work = tempfile.mkdtemp(suffix=".iconset")
    try:
        for s in ICNS_SIZES:
            render(svg, s, os.path.join(work, f"icon_{s}x{s}.png"))
            render(svg, s * 2, os.path.join(work, f"icon_{s}x{s}@2x.png"))
        out = os.path.join(DL, out_rel)
        subprocess.run(["iconutil", "-c", "icns", work, "-o", out], check=True)
        print(f"wrote {out_rel}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    if not shutil.which("rsvg-convert"):
        raise SystemExit("rsvg-convert (librsvg) is required to render the SVG")

    svg = brand_svg()

    # the brand vector itself (README, leapps.org, print)
    out_svg = os.path.join(DL, "assets", "DLEAPP_logo.svg")
    with open(out_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("wrote assets/DLEAPP_logo.svg")

    # square marks, each rendered from the vector at its final size
    render(svg, 1024, os.path.join(DL, "assets/DLEAPP_logo.png"))
    print("wrote assets/DLEAPP_logo.png (1024)")
    render(svg, 256, os.path.join(DL, "assets/icon.png"))
    print("wrote assets/icon.png (256)")
    render(svg, 512, os.path.join(DL, "scripts/_elements/logo.png"))
    print("wrote scripts/_elements/logo.png (512)")

    # wide wordmark banner: HTML report (shown ~88px) and GUI header (208x52)
    mark = render(mark_svg(svg), 1024,
                  os.path.join(tempfile.gettempdir(), "dleapp_mark.png"))
    banner = make_banner(mark)
    for rel in ("scripts/_elements/DLEAPP_banner.png", "assets/DLEAPP_banner.png"):
        banner.save(os.path.join(DL, rel))
        print(f"wrote {rel} {banner.size}")

    build_icns(svg, "assets/icon.icns")

    # NOTE: assets/leapps_r_logo.png is the shared leapps.org family logo and is
    # intentionally not generated here.
    print("done")
