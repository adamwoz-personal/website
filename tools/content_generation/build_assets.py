#!/usr/bin/env python3
"""Generate favicon, apple-touch-icon, and Open Graph card.

All outputs written to adam/assets/ so they are served under
https://wosotowsky.org/adam/assets/.

Design: Georgia Tech-inspired black with gold "AW" monogram.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


GT_BLACK = (10, 18, 32)
GT_GOLD = (179, 163, 105)
GT_GOLD_BRIGHT = (234, 170, 0)
GT_NAVY = (0, 48, 87)
GT_RED = (200, 16, 46)
INK_ON_DARK = (247, 240, 220)


def _load_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_monogram(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), GT_BLACK)
    draw = ImageDraw.Draw(img)
    # Gold border ring
    border = max(2, size // 16)
    draw.rectangle([0, 0, size - 1, size - 1], outline=GT_GOLD, width=border)
    font = _load_font(int(size * 0.55))
    text = "AW"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1] - size * 0.02),
        text,
        fill=GT_GOLD_BRIGHT,
        font=font,
    )
    return img


def make_og_card(width: int = 1200, height: int = 630) -> Image.Image:
    img = Image.new("RGB", (width, height), GT_BLACK)
    draw = ImageDraw.Draw(img)

    # Gold accent bar down the left
    bar_w = 24
    draw.rectangle([0, 0, bar_w, height], fill=GT_GOLD)

    # Navy diagonal band across the bottom third
    band_top = int(height * 0.72)
    draw.rectangle([0, band_top, width, height], fill=GT_NAVY)
    draw.rectangle([0, band_top, width, band_top + 6], fill=GT_GOLD)

    # Name
    name_font = _load_font(84)
    tagline_font = _load_font(38, bold=False)
    domain_font = _load_font(30)

    x0 = bar_w + 60
    draw.text((x0, 120), "Adam Wosotowsky", fill=GT_GOLD_BRIGHT, font=name_font)

    tagline1 = "Threat researcher \u00b7 Engineering leader \u00b7 Inventor"
    draw.text((x0, 250), tagline1, fill=INK_ON_DARK, font=tagline_font)

    tagline2 = "Two decades of malware, botnet, and threat-intelligence work."
    draw.text((x0, 310), tagline2, fill=(200, 210, 224), font=tagline_font)

    tagline3 = "Two U.S. patents. Hundreds of press interviews."
    draw.text((x0, 360), tagline3, fill=(200, 210, 224), font=tagline_font)

    draw.text((x0, band_top + 40), "wosotowsky.org/adam", fill=GT_GOLD_BRIGHT, font=domain_font)

    return img


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate site favicon and OG card.")
    parser.add_argument("--out", default="adam/assets", help="output directory")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fav32 = make_monogram(32)
    fav32.save(out / "favicon.png", "PNG")

    apple = make_monogram(180)
    apple.save(out / "apple-touch-icon.png", "PNG")

    og = make_og_card()
    og.save(out / "og-card.png", "PNG", optimize=True)

    # Also produce a classic .ico (multi-size)
    ico16 = make_monogram(16)
    ico32 = make_monogram(32)
    ico48 = make_monogram(48)
    ico16.save(out / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    del ico32, ico48

    print(f"Wrote favicon.png, favicon.ico, apple-touch-icon.png, og-card.png in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
