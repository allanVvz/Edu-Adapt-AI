"""
Render Unicode emoji to PNG so they can be embedded faithfully in PDFs.

ReportLab's built-in fonts (Helvetica/Times) have no emoji glyphs, so an emoji
placed directly in a Paragraph renders as an empty box. Instead we rasterize
each emoji once (via Pillow + Noto Color Emoji) to a cached PNG and embed that
image — the pictogram then appears exactly as designed.

The font is installed in the Docker image (see apps/api/Dockerfile:
`fonts-noto-color-emoji`). If the font is missing (e.g. local dev outside the
container), `emoji_to_png` returns None and callers fall back gracefully.
"""
import hashlib
import os
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - Pillow always present in the API image
    Image = ImageDraw = ImageFont = None  # type: ignore

# Noto Color Emoji is a bitmap font; its only embedded strike is 109px.
_FONT_PATH = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_NATIVE_SIZE = 109
_DEFAULT_CACHE = "/app/static/emoji"

_font_cache: Optional["ImageFont.FreeTypeFont"] = None
_font_unavailable = False


def _get_font() -> Optional["ImageFont.FreeTypeFont"]:
    global _font_cache, _font_unavailable
    if _font_unavailable:
        return None
    if _font_cache is not None:
        return _font_cache
    if ImageFont is None or not os.path.isfile(_FONT_PATH):
        _font_unavailable = True
        return None
    try:
        _font_cache = ImageFont.truetype(_FONT_PATH, _NATIVE_SIZE)
        return _font_cache
    except Exception:
        _font_unavailable = True
        return None


def emoji_to_png(emoji: str, size: int = 96, cache_dir: str = _DEFAULT_CACHE) -> Optional[str]:
    """
    Rasterize *emoji* to a square transparent PNG and return its absolute path.

    Results are cached on disk keyed by (emoji, size). Returns None when the
    emoji font is unavailable or rendering fails — callers should fall back.
    """
    if not emoji or Image is None:
        return None
    font = _get_font()
    if font is None:
        return None

    key = hashlib.md5(f"{emoji}|{size}".encode("utf-8")).hexdigest()
    path = os.path.join(cache_dir, f"{key}.png")
    if os.path.isfile(path):
        return path

    try:
        os.makedirs(cache_dir, exist_ok=True)
        canvas = Image.new("RGBA", (_NATIVE_SIZE + 40, _NATIVE_SIZE + 40), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((20, 20), emoji, font=font, embedded_color=True)

        bbox = canvas.getbbox()
        glyph = canvas.crop(bbox) if bbox else canvas

        # Fit into a square keeping aspect ratio, centered, transparent padding.
        gw, gh = glyph.size
        scale = (size - 4) / max(gw, gh)
        nw, nh = max(1, round(gw * scale)), max(1, round(gh * scale))
        glyph = glyph.resize((nw, nh), Image.LANCZOS)

        square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        square.paste(glyph, ((size - nw) // 2, (size - nh) // 2), glyph)
        square.save(path)
        return path
    except Exception:
        return None
