from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "movie-planner-mcp-cover.png"

W, H = 800, 440
FONT_REG = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size=size)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def rounded_rect(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def draw_centered(draw: ImageDraw.ImageDraw, y: int, text: str, fnt, fill, line_gap: int = 8):
    lines = text.split("\n")
    total_h = sum(text_size(draw, line, fnt)[1] for line in lines) + line_gap * (len(lines) - 1)
    cy = y - total_h // 2
    for line in lines:
        tw, th = text_size(draw, line, fnt)
        draw.text(((W - tw) // 2, cy), line, font=fnt, fill=fill)
        cy += th + line_gap


def draw_logo(draw: ImageDraw.ImageDraw):
    x, y = 40, 38
    rounded_rect(draw, (x, y, x + 42, y + 42), 10, fill=(39, 77, 151), outline=(68, 103, 190), width=1)
    # Simple popcorn bucket icon, deterministic instead of emoji font rendering.
    bx, by = x + 12, y + 13
    draw.polygon([(bx, by + 8), (bx + 18, by + 8), (bx + 15, by + 25), (bx + 3, by + 25)], fill=(248, 248, 245))
    draw.line((bx + 2, by + 10, bx + 5, by + 24), fill=(213, 41, 71), width=2)
    draw.line((bx + 9, by + 9, bx + 9, by + 25), fill=(213, 41, 71), width=2)
    draw.line((bx + 16, by + 10, bx + 13, by + 24), fill=(213, 41, 71), width=2)
    for px, py in [(bx + 2, by + 5), (bx + 7, by + 1), (bx + 12, by + 4), (bx + 17, by + 2)]:
        draw.ellipse((px, py, px + 7, py + 7), fill=(255, 223, 116))
    draw.text((x + 52, y + 11), "Movie Planner", font=font(20, True), fill=(255, 255, 255))


def draw_pill(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, border, fill, *, check: bool = False):
    f = font(14, True)
    tw, th = text_size(draw, label, f)
    pad_x = 17
    h = 35
    w = tw + pad_x * 2 + (20 if check else 0)
    rounded_rect(draw, (x, y, x + w, y + h), 10, fill=fill, outline=border, width=2)
    draw.text((x + pad_x, y + (h - th) // 2 - 2), label, font=f, fill=(255, 255, 255))
    if check:
        cx = x + pad_x + tw + 12
        cy = y + 18
        draw.line((cx - 5, cy, cx - 1, cy + 5), fill=(31, 255, 143), width=3)
        draw.line((cx - 1, cy + 5, cx + 8, cy - 6), fill=(31, 255, 143), width=3)
    return x + w


def build():
    img = Image.new("RGB", (W, H))
    px = img.load()
    left = (92, 20, 48)
    mid = (17, 11, 31)
    right = (32, 19, 83)
    for y in range(H):
        for x in range(W):
            tx = x / (W - 1)
            ty = y / (H - 1)
            if tx < 0.48:
                t = tx / 0.48
                base = tuple(lerp(left[i], mid[i], t) for i in range(3))
            else:
                t = (tx - 0.48) / 0.52
                base = tuple(lerp(mid[i], right[i], t) for i in range(3))
            vignette = 1.0 - 0.18 * abs(ty - 0.5)
            px[x, y] = tuple(max(0, min(255, int(c * vignette))) for c in base)

    draw = ImageDraw.Draw(img)
    draw_logo(draw)

    title = "Movie Planner MCP\nдля нейросетей"
    subtitle = "Билеты, база, планы — без ручного поиска"
    draw_centered(draw, 180, title, font(40, True), (255, 255, 255), line_gap=2)
    draw_centered(draw, 244, subtitle, font(19, True), (197, 190, 214), line_gap=0)

    y = 370
    labels = [
        ("Запрос", (255, 43, 130), (75, 21, 57)),
        ("LLM", (132, 84, 255), (44, 26, 95)),
        ("Movie Planner", (12, 224, 122), (11, 88, 48)),
    ]
    widths = [text_size(draw, label, font(14, True))[0] + 34 for label, _, _ in labels]
    total = sum(widths) + 28 * 2
    x = (W - total) // 2
    for idx, (label, border, fill) in enumerate(labels):
        x2 = draw_pill(draw, x, y, label, border, fill, check=(idx == len(labels) - 1))
        if idx < len(labels) - 1:
            ax = x2 + 11
            ay = y + 17
            draw.line((ax, ay, ax + 16, ay), fill=(178, 173, 196), width=2)
            draw.polygon([(ax + 16, ay), (ax + 10, ay - 5), (ax + 10, ay + 5)], fill=(178, 173, 196))
            x = x2 + 28
        else:
            x = x2

    footer = "поиск • личная база • прокат • партнёрские ссылки"
    fw, fh = text_size(draw, footer, font(14, True))
    draw.text(((W - fw) // 2, 409), footer, font=font(14, True), fill=(124, 116, 151))

    OUT.parent.mkdir(exist_ok=True)
    img.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
