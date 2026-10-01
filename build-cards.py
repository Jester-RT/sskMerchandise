#!/usr/bin/env python3
"""
Builds one ready-to-upload product card image per design for the Squarespace
site.

Reads the same folder structure as build-page.py:

    <Product Type>/<Design Name>/<Colour>.png

...and writes:

    cards/<type>-<nn>-<design>.jpg    one 1600x2000 card per design: a large
                                      front-and-back view plus every colour
    cards/captions.md                 title and caption for each card, ready
                                      to paste into Squarespace

Usage (from this folder):   python build-cards.py

Add a new design or colour by dropping in its PNGs and re-running it.
"""

import importlib.util
import os
import sys

sys.dont_write_bytecode = True  # keep build-page.py from leaving a __pycache__ folder

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "cards")

# Reuse the scanner, ordering and size rules from the store-page builder.
_spec = importlib.util.spec_from_file_location("build_page", os.path.join(HERE, "build-page.py"))
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

W, H = 1600, 2000
MARGIN = 70

INK_900 = (7, 4, 2)
INK_800 = (28, 20, 15)
INK_400 = (155, 140, 126)
INK_200 = (230, 221, 208)
INK_100 = (243, 236, 225)
PAPER = (251, 247, 239)
WHITE = (255, 255, 255)
GOLD = (191, 156, 5)
BURNT = (130, 61, 14)
HEADER_SUB = (207, 196, 182)

# The colour shown large at the top of each card, first match wins.
HERO_COLOURS = ["Deep_Black", "Black"]

FONT_CANDIDATES = {
    "regular": ["NotoSans-Regular.ttf", "segoeui.ttf", "Arial.ttf", "arial.ttf",
                "LiberationSans-Regular.ttf", "DejaVuSans.ttf"],
    "bold": ["NotoSans-SemiBold.ttf", "NotoSans-Bold.ttf", "segoeuib.ttf",
             "Arial Bold.ttf", "arialbd.ttf", "LiberationSans-Bold.ttf",
             "DejaVuSans-Bold.ttf"],
}
FONT_DIRS = [
    HERE,
    "C:/Windows/Fonts",
    "/Library/Fonts", "/System/Library/Fonts/Supplemental",
    os.path.expanduser("~/Library/Fonts"),
    "/usr/share/fonts/truetype/noto", "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/dejavu",
]


def font(weight, size):
    for name in FONT_CANDIDATES[weight]:
        for d in FONT_DIRS:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


# --------------------------------------------------------------------------
# Image helpers
# --------------------------------------------------------------------------

def load(path):
    return Image.open(path).convert("RGBA")


def trimmed(im):
    """Crop away the transparent border."""
    box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    return im.crop(box) if box else im


def front_only(im):
    """The left-hand (front) garment from a front-and-back image."""
    return trimmed(im.crop((0, 0, im.width // 2, im.height)))


def fit(im, max_w, max_h):
    scale = min(max_w / im.width, max_h / im.height)
    return im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))),
                     Image.LANCZOS)


def paste_centered(canvas, im, cx, cy):
    canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def centered_text(draw, cx, y, s, f, fill):
    draw.text((cx - text_w(draw, s, f) / 2, y), s, font=f, fill=fill)


def tracked(s):
    """Letter-spaced caps, as used for the eyebrows on the store page."""
    return " ".join(s.upper())


# --------------------------------------------------------------------------
# Card
# --------------------------------------------------------------------------

def card_filename(p):
    num = f"{p['n']:02d}" if p["n"] is not None else "00"
    return f"{bp.slugify(p['type'])}-{num}-{bp.slugify(p['title'])}.jpg"


def singular(ptype):
    return {"T-Shirts": "T-Shirt", "Hoodies": "Hoodie"}.get(ptype, ptype.rstrip("s"))


def adult_only_names(p):
    return [c["name"] for c in p["colours"] if c["adultOnly"]]


def join_names(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def build_card(p, logo):
    card = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(card)

    # Header band
    header_h = 250
    d.rectangle((0, 0, W, header_h), fill=INK_900)
    d.rectangle((0, header_h, W, header_h + 8), fill=GOLD)
    eyebrow = f"{p['type']}  ·  Design {p['n']}" if p["n"] is not None else p["type"]
    d.text((MARGIN, 58), tracked(eyebrow), font=font("bold", 26), fill=GOLD)
    title_f = font("bold", 78)
    while text_w(d, p["title"], title_f) > W - 2 * MARGIN - 220 and title_f.size > 40:
        title_f = font("bold", title_f.size - 4)
    d.text((MARGIN, 104), p["title"], font=title_f, fill=WHITE)
    d.text((MARGIN, 104 + title_f.size + 14), "Stafford Shotokan Karate  ·  2026 clothing range",
           font=font("regular", 28), fill=HEADER_SUB)
    lg = fit(logo, 170, 170)
    card.alpha_composite(lg, (W - MARGIN - lg.width, (header_h - lg.height) // 2))

    # Hero: front and back in one colour
    hero_c = next((c for name in HERO_COLOURS for c in p["colours"] if c["file"] == name),
                  p["colours"][0])
    hero = fit(trimmed(load(os.path.join(HERE, p["path"], hero_c["file"] + ".png"))),
               W - 2 * MARGIN, 720)
    hero_top = header_h + 8 + 50
    paste_centered(card, hero, W / 2, hero_top + 360)
    cap_y = hero_top + 720 + 18
    centered_text(d, W / 2, cap_y, f"Front and back, shown in {hero_c['name']}",
                  font("regular", 26), INK_400)

    # Colour grid
    n = len(p["colours"])
    cols = 5 if n > 8 else 4 if n > 4 else n
    rows = -(-n // cols)
    section_y = cap_y + 70
    d.line((MARGIN, section_y, W - MARGIN, section_y), fill=INK_200, width=2)
    d.text((MARGIN, section_y + 26), tracked(f"Available in {n} colours"),
           font=font("bold", 24), fill=INK_400)

    gap = 22
    cell_w = (W - 2 * MARGIN - gap * (cols - 1)) / cols
    grid_top = section_y + 80
    footer_top = H - 150
    label_h = 78
    cell_h = min(cell_w * 1.0, (footer_top - 30 - grid_top - gap * (rows - 1)) / rows - label_h)
    name_f = font("bold", 26)
    note_f = font("regular", 21)
    for i, c in enumerate(p["colours"]):
        r, k = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        row_off = (cols - in_row) * (cell_w + gap) / 2  # centre a short last row
        x = MARGIN + row_off + k * (cell_w + gap)
        y = grid_top + r * (cell_h + label_h + gap)
        d.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=18, fill=INK_100)
        thumb = fit(front_only(load(os.path.join(HERE, p["path"], c["file"] + ".png"))),
                    cell_w - 36, cell_h - 30)
        paste_centered(card, thumb, x + cell_w / 2, y + cell_h / 2)
        centered_text(d, x + cell_w / 2, y + cell_h + 12, c["name"], name_f, INK_800)
        if c["adultOnly"]:
            centered_text(d, x + cell_w / 2, y + cell_h + 46, "Adult sizes only", note_f, BURNT)

    # Footer: sizes
    d.rectangle((0, footer_top, W, H), fill=INK_100)
    d.line((0, footer_top, W, footer_top), fill=INK_200, width=2)
    kids = f"{bp.KIDS_SIZES[0].split('–')[0]}–{bp.KIDS_SIZES[-1].split('–')[-1]}"  # 3–13 yrs
    sizes = f"Kids  {kids}     ·     Adult  {bp.ADULT_SIZES[0]}–{bp.ADULT_SIZES[-1]}"
    centered_text(d, W / 2, footer_top + 32, sizes, font("bold", 32), INK_800)
    adult = adult_only_names(p)
    if adult:
        verb = "is" if len(adult) == 1 else "are"
        line = f"{join_names(adult)} {verb} adult sizes only. Every other colour comes in kids' and adult sizes."
    else:
        line = "Every colour comes in both kids' and adult sizes."
    centered_text(d, W / 2, footer_top + 84, line, font("regular", 25), INK_400)

    return card.convert("RGB")


def caption(p):
    names = [c["name"] for c in p["colours"]]
    text = f"{singular(p['type'])} in {len(names)} colours: {join_names(names)}."
    adult = adult_only_names(p)
    if adult:
        text += f" {join_names(adult)} {'is' if len(adult) == 1 else 'are'} adult sizes only."
    return text


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    logo = trimmed(load(os.path.join(HERE, bp.LOGO)))
    products = bp.scan()
    keep = set()
    lines = ["# Card titles and captions", "",
             "Paste these into each image's title and description in Squarespace.", ""]
    current = None
    for p in products:
        if p["type"] != current:
            current = p["type"]
            lines += [f"## {current}", ""]
        name = card_filename(p)
        keep.add(name)
        build_card(p, logo).save(os.path.join(OUT_DIR, name), "JPEG", quality=88,
                                 optimize=True, progressive=True)
        title = f"Design {p['n']}: {p['title']}" if p["n"] is not None else p["title"]
        lines += [f"**{name}**  ", f"Title: {title}  ", f"Description: {caption(p)}", ""]
        print(f"  {name}")
    for f in os.listdir(OUT_DIR):  # drop cards for designs that no longer exist
        if f.endswith(".jpg") and f not in keep:
            os.remove(os.path.join(OUT_DIR, f))
    with open(os.path.join(OUT_DIR, "captions.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"Wrote {len(products)} cards to cards/")


if __name__ == "__main__":
    main()
