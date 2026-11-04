"""Generate every NZHub icon from the NZ brush glyph.

Source: black-on-white 1600x1600 NZ_monochrome.png. Crops the NZ+star mark,
extracts an alpha mask, then emits:
  - mipmap-*: ic_launcher.webp / ic_launcher_round.webp (48..192px)
  - mipmap-*: ic_launcher_foreground.webp (108dp adaptive: 108..432px)
  - mipmap-anydpi-v26 adaptive XML incl. Android 13 monochrome layer
  - drawable-*dpi: ic_stat_name.webp (white status-bar glyph, 24..96px)
  - drawable-*dpi: ic_stat_name_black.webp (same, replaces png)
  - drawable-*dpi: ic_splash_24dp.webp (24..96px)
  - drawable/app_banner.webp (TV banner 640x360)
"""
import pathlib
from PIL import Image, ImageDraw, ImageOps

SRC = pathlib.Path(r"C:\Users\nzboost\Pictures\avatars\NZ_monochrome.png")
RES = pathlib.Path(r"C:\Users\nzboost\Documents\workspace\happ-src\apktool\res")

BG = (43, 43, 43, 255)          # matches @color/ic_launcher_background #2b2b2b
WHITE = (255, 255, 255, 255)

DENSITIES = [("mdpi", 1), ("hdpi", 1.5), ("xhdpi", 2), ("xxhdpi", 3), ("xxxhdpi", 4)]

# ---------------------------------------------------------------- glyph mask
src = Image.open(SRC).convert("L")
w, h = src.size
# central region holding the NZ letters + star (exclude plane and palms)
region = src.crop((int(w * 0.17), int(h * 0.20), int(w * 0.87), int(h * 0.775)))
mask = region.point(lambda v: 255 if v < 128 else 0)
# erase palm frond (bottom-right) and stray sliver (bottom edge)
d = ImageDraw.Draw(mask)
d.rectangle((1040, 620, mask.width, mask.height), fill=0)
d.rectangle((0, 845, mask.width, mask.height), fill=0)
bbox = mask.getbbox()
mask = ImageOps.autocontrast(mask.crop(bbox))
print("glyph mask size:", mask.size)
glyph = mask  # mask is alpha; 'color' layers provide fill


def glyph_on(size, color, scale, dy=0.0):
    """Transparent canvas, glyph centered, occupying `scale` of canvas side."""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * scale)
    gw = int(inner * glyph.width / glyph.height)
    g = mask.resize((gw, inner), Image.LANCZOS)
    layer = Image.new("RGBA", g.size, color)
    x = (size - gw) // 2
    y = (size - inner) // 2 + int(dy * size)
    canvas.paste(layer, (x, y), g)
    return canvas


def tile(size, scale, dy=0.0):
    """Full-bleed dark tile with white glyph (legacy launcher raster)."""
    t = Image.new("RGBA", (size, size), BG)
    g = glyph_on(size, WHITE, scale, dy)
    t.alpha_composite(g)
    return t


def save_webp(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", lossless=True, method=6)
    print("wrote", path.relative_to(RES), im.size)


# 1. legacy launcher rasters
for name, s in DENSITIES:
    px = int(48 * s)
    save_webp(tile(px, 0.62), RES / f"mipmap-{name}" / "ic_launcher.webp")
    save_webp(tile(px, 0.62), RES / f"mipmap-{name}" / "ic_launcher_round.webp")

# 2. adaptive foreground: 108dp canvas, glyph in 66/108 safe zone
for name, s in DENSITIES:
    px = int(108 * s)
    save_webp(glyph_on(px, WHITE, 0.42), RES / f"mipmap-{name}" / "ic_launcher_foreground.webp")

# 3. status bar / notification glyphs (alpha-only, white)
for name, s in DENSITIES:
    px = int(24 * s)
    g = glyph_on(px, WHITE, 0.86)
    save_webp(g, RES / f"drawable-{name}" / "ic_stat_name.webp")
    save_webp(g, RES / f"drawable-{name}" / "ic_stat_name_black.webp")

# 4. splash icon
for name, s in DENSITIES:
    px = int(24 * s)
    save_webp(tile(px, 0.70), RES / f"drawable-{name}" / "ic_splash_24dp.webp")

# 5. TV banner 320x180dp -> xhdpi raster
banner = Image.new("RGBA", (640, 360), BG)
mark = glyph_on(360, WHITE, 0.60)
banner.alpha_composite(mark, ((640 - 360) // 2, (360 - 360) // 2))
save_webp(banner, RES / "drawable" / "app_banner.webp")

# 6. purge superseded originals
for stale in [
    RES / "drawable" / "app_banner.xml",
    RES / "drawable" / "ic_stat_name.xml",
]:
    for name, s in DENSITIES:
        p = RES / f"drawable-{name}" / "ic_stat_name_black.png"
        if p.exists():
            p.unlink()
            print("removed", p.relative_to(RES))
        p = RES / f"drawable-{name}" / "ic_splash_24dp.png"
        if p.exists():
            p.unlink()
            print("removed", p.relative_to(RES))
    if stale.exists():
        stale.unlink()
        print("removed", stale.relative_to(RES))
