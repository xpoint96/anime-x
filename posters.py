from __future__ import annotations

import colorsys
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 420, 588
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
OUT_DIR = Path(__file__).parent / "static" / "posters" / "u"


def _rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return int(r * 255), int(g * 255), int(b * 255)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines[:3]


def _gradient(c1, c2) -> Image.Image:
    top = Image.new("RGB", (W, H), c1)
    bottom = Image.new("RGB", (W, H), c2)
    mask = Image.linear_gradient("L").resize((W, H))
    return Image.composite(bottom, top, mask)


def _ellipse(draw, xy, fill, outline=None, width=1):
    draw.ellipse(xy, fill=fill, outline=outline, width=width)


def scene(draw: ImageDraw.ImageDraw, rng: random.Random, hue: float, kind: int) -> None:
    accent = _rgb(hue, 0.75, 0.95)
    dim = _rgb(hue + 0.08, 0.55, 0.35)
    pale = _rgb(hue, 0.2, 0.98)
    ink = _rgb(hue + 0.5, 0.4, 0.08)

    if kind == 0:  # moon over hills
        _ellipse(draw, (W * 0.18, 40, W * 0.82, 310), pale)
        _ellipse(draw, (W * 0.28, 70, W * 0.72, 260), dim)
        for i in range(4):
            y = 280 + i * 55
            draw.polygon(
                [(0, y + 80), (W * rng.uniform(0.2, 0.5), y), (W, y + 90), (W, H), (0, H)],
                fill=_rgb(hue, 0.55, 0.22 + i * 0.08),
            )
    elif kind == 1:  # torii / shrine
        draw.rectangle((70, 90, W - 70, 130), fill=accent)
        draw.rectangle((90, 70, W - 90, 95), fill=accent)
        draw.rectangle((100, 130, 128, 470), fill=accent)
        draw.rectangle((W - 128, 130, W - 100, 470), fill=accent)
        _ellipse(draw, (150, 180, 270, 300), pale)
    elif kind == 2:  # city
        for i in range(9):
            x = 18 + i * 44
            h = rng.randint(160, 420)
            draw.rectangle((x, H - h, x + 36, H - 90), fill=_rgb(hue, 0.4, 0.18 + (i % 3) * 0.1))
            for wy in range(H - h + 16, H - 110, 22):
                if rng.random() > 0.35:
                    draw.rectangle((x + 8, wy, x + 16, wy + 10), fill=accent)
        _ellipse(draw, (240, 40, 360, 160), pale)
    elif kind == 3:  # forest
        for i in range(18):
            x = rng.randint(10, W - 40)
            top = rng.randint(80, 280)
            draw.polygon([(x, H - 80), (x + 18, top), (x + 36, H - 80)], fill=_rgb(hue, 0.7, 0.25 + rng.random() * 0.25))
        _ellipse(draw, (40, 50, 170, 180), pale)
    elif kind == 4:  # train / tracks
        draw.polygon([(40, 360), (W - 20, 250), (W - 20, 330), (40, 440)], fill=dim)
        draw.rectangle((70, 250, 250, 390), fill=accent)
        draw.rectangle((250, 280, 340, 390), fill=_rgb(hue, 0.6, 0.7))
        _ellipse(draw, (100, 400, 150, 450), ink)
        _ellipse(draw, (200, 400, 250, 450), ink)
        for i in range(8):
            y = 420 + i * 18
            draw.line((0, y, W, y - 40), fill=pale, width=2)
    elif kind == 5:  # school window
        draw.rectangle((50, 80, W - 50, 420), fill=_rgb(hue, 0.15, 0.9))
        draw.rectangle((50, 80, W - 50, 420), outline=ink, width=10)
        draw.line((W // 2, 80, W // 2, 420), fill=ink, width=8)
        draw.line((50, 250, W - 50, 250), fill=ink, width=8)
        _ellipse(draw, (80, 110, 180, 210), accent)
    elif kind == 6:  # sea
        _ellipse(draw, (W * 0.25, 70, W * 0.75, 280), pale)
        for i in range(7):
            y = 300 + i * 35
            draw.arc(( -40, y, W + 40, y + 90), 0, 180, fill=accent, width=6)
    elif kind == 7:  # mecha geometry
        pts = [(W // 2, 70), (W - 50, 250), (W // 2, 480), (50, 250)]
        draw.polygon(pts, fill=dim, outline=accent)
        draw.regular_polygon((W // 2, 250, 90), 6, rotation=rng.randint(0, 50), fill=accent)
        draw.rectangle((W // 2 - 18, 200, W // 2 + 18, 360), fill=pale)
    elif kind == 8:  # fox
        draw.polygon([(210, 120), (90, 420), (330, 420)], fill=dim)
        draw.polygon([(150, 90), (190, 220), (210, 160)], fill=accent)
        draw.polygon([(270, 90), (230, 220), (210, 160)], fill=accent)
        _ellipse(draw, (170, 230, 250, 310), pale)
        _ellipse(draw, (185, 250, 205, 270), ink)
        _ellipse(draw, (225, 250, 245, 270), ink)
    elif kind == 9:  # sword
        draw.polygon([(W // 2, 50), (W // 2 + 18, 360), (W // 2 - 18, 360)], fill=pale)
        draw.rectangle((W // 2 - 70, 350, W // 2 + 70, 375), fill=accent)
        draw.rectangle((W // 2 - 12, 375, W // 2 + 12, 460), fill=dim)
        _ellipse(draw, (40, 80, 160, 200), _rgb(hue + 0.12, 0.5, 0.4))
    elif kind == 10:  # portal
        for i in range(8, 0, -1):
            pad = 30 + i * 18
            _ellipse(draw, (pad, pad + 20, W - pad, 420 - pad), _rgb(hue + i * 0.03, 0.7, 0.2 + i * 0.08))
        _ellipse(draw, (140, 150, 280, 300), pale)
    elif kind == 11:  # tea steam
        _ellipse(draw, (120, 300, 300, 470), dim)
        draw.rectangle((150, 280, 270, 320), fill=accent)
        for i in range(5):
            x = 170 + i * 18
            draw.arc((x, 90 + i * 8, x + 40, 280), 200, 340, fill=pale, width=4)
    elif kind == 12:  # lighthouse
        draw.polygon([(W // 2, 80), (W // 2 + 55, 430), (W // 2 - 55, 430)], fill=dim)
        draw.rectangle((W // 2 - 28, 70, W // 2 + 28, 120), fill=accent)
        draw.polygon([(W // 2, 90), (W, 40), (W, 160)], fill=_rgb(hue, 0.4, 0.95))
        draw.polygon([(0, 430), (W // 2, 360), (W, 450), (W, H), (0, H)], fill=_rgb(hue + 0.1, 0.5, 0.25))
    elif kind == 13:  # garden
        for i in range(12):
            x = rng.randint(30, W - 70)
            y = rng.randint(80, 380)
            r = rng.randint(18, 48)
            _ellipse(draw, (x, y, x + r * 2, y + r * 2), _rgb(hue + i * 0.04, 0.65, 0.75))
        draw.rectangle((W // 2 - 8, 200, W // 2 + 8, 500), fill=dim)
    elif kind == 14:  # radio tower
        draw.polygon([(W // 2, 40), (80, 500), (W - 80, 500)], outline=accent)
        draw.line((W // 2, 40, W // 2, 500), fill=pale, width=6)
        for i in range(6):
            y = 80 + i * 70
            w = 20 + i * 22
            draw.line((W // 2 - w, y, W // 2 + w, y), fill=accent, width=4)
        _ellipse(draw, (W // 2 - 16, 36, W // 2 + 16, 68), accent)
    elif kind == 15:  # throne
        draw.rectangle((110, 180, 310, 460), fill=dim)
        draw.rectangle((80, 150, 340, 200), fill=accent)
        draw.polygon([(80, 150), (210, 60), (340, 150)], fill=pale)
        draw.rectangle((150, 250, 270, 320), fill=_rgb(hue, 0.3, 0.55))
    elif kind == 16:  # abyss
        for i in range(10):
            pad = i * 22
            draw.polygon(
                [(W // 2, 40 + pad), (W - 40 - pad, 500 - pad), (40 + pad, 500 - pad)],
                outline=_rgb(hue, 0.7, 0.9 - i * 0.07),
            )
        _ellipse(draw, (180, 220, 240, 280), accent)
    else:  # lantern festival
        for i in range(14):
            x = 20 + (i % 7) * 56
            y = 70 + (i // 7) * 160 + rng.randint(-20, 20)
            _ellipse(draw, (x, y, x + 44, y + 70), _rgb(hue + i * 0.05, 0.8, 0.9))
            draw.line((x + 22, y + 70, x + 22, y + 110), fill=pale, width=2)


def make_poster(item: dict) -> Image.Image:
    rng = random.Random(item["id"] * 104729 + 13)
    hue = (item["id"] * 0.14159265 + item["id"] * 0.07) % 1.0
    c1 = _rgb(hue, 0.62, 0.18)
    c2 = _rgb(hue + 0.14, 0.55, 0.42)
    img = _gradient(c1, c2)
    overlay = img.copy()
    draw = ImageDraw.Draw(overlay)
    scene(draw, rng, hue, item["id"] % 18)
    # unique spark field so even same scene never matches
    for _ in range(40 + (item["id"] % 30)):
        x, y = rng.randint(0, W), rng.randint(0, int(H * 0.7))
        r = rng.randint(1, 3)
        draw.ellipse((x, y, x + r, y + r), fill=_rgb(hue, 0.2, 1.0))
    img = Image.blend(img, overlay, 0.92)
    img = img.filter(ImageFilter.SMOOTH)
    draw = ImageDraw.Draw(img)
    # bottom plate + title
    draw.rectangle((0, H - 150, W, H), fill=(8, 12, 10))
    draw.rectangle((0, H - 154, W, H - 150), fill=_rgb(hue, 0.8, 0.9))
    title_font = _font(28)
    lines = _wrap(draw, item["title"], title_font, W - 40)
    y = H - 128
    for line in lines:
        draw.text((20, y), line, font=title_font, fill=(240, 252, 245))
        y += 34
    meta = f"{item['year']}  ·  {item['genre']}"
    draw.text((20, H - 36), meta, font=_font(16), fill=_rgb(hue, 0.15, 0.75))
    # unique mark
    mark = item["id"]
    draw.pieslice((W - 78, 18, W - 18, 78), mark % 360, (mark * 3) % 360, fill=_rgb(hue, 0.85, 0.95))
    return img


def poster_name(item_id: int) -> str:
    return f"u/{item_id:04d}.jpg"


def ensure_poster(item: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{item['id']:04d}.jpg"
    if not path.exists():
        make_poster(item).save(path, "JPEG", quality=86, optimize=True)
    return path


def ensure_all(items: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in items:
        ensure_poster(item)
