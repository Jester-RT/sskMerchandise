#!/usr/bin/env python3
"""
Builds a banner showing every design (front, or back where most of the
print is), for linking to the
clothing page from elsewhere on the club site.

Writes:   squarespace/clothing-banner.png

Each design is shown in a different colour so the banner shows off the range.
Re-run after adding a design:   python build-banner.py
"""

import importlib.util
import os
import sys

sys.dont_write_bytecode = True  # keep build-page.py from leaving a __pycache__ folder

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "squarespace", "clothing-banner.png")

_spec = importlib.util.spec_from_file_location("build_page", os.path.join(HERE, "build-page.py"))
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

W, H = 2400, 1000
PER_ROW = 8
PAD = 50

# Designs whose main print is on the back, shown back-side in the banner.
BACK_SIDE = {
    "T-Shirts": {2, 3, 8, 11, 13, 14, 17},
    "Hoodies": {1, 2, 4, 5},
}

# Colours to cycle through, so neighbouring designs differ. Black garments
# are left out because they disappear on the site's black background.
CYCLE = ["Fire_Red", "Arctic_White", "Airforce_Blue", "Bottle_Green", "Orange_Crush",
         "Natural_Stone", "Purple", "Blue", "Maroon", "New_French_Navy", "Dusty_Purple"]


def halves(path):
    """The front (left) and back (right) garments, each trimmed."""
    im = Image.open(path).convert("RGBA")
    out = []
    for box in ((0, 0, im.width // 2, im.height), (im.width // 2, 0, im.width, im.height)):
        half = im.crop(box)
        bbox = half.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
        out.append(half.crop(bbox) if bbox else half)
    return out


def main():
    products = bp.scan()
    rows = -(-len(products) // PER_ROW)
    cell_w = (W - 2 * PAD) / PER_ROW
    cell_h = (H - 2 * PAD) / rows
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # transparent
    i = 0
    for n, p in enumerate(products):
        files = [c["file"] for c in p["colours"]]
        choice = None
        for k in range(len(CYCLE)):
            cand = CYCLE[(i + k) % len(CYCLE)]
            if cand in files:
                choice, i = cand, i + k + 1
                break
        choice = choice or files[0]
        front, back = halves(os.path.join(HERE, p["path"], choice + ".png"))
        im = back if p["n"] in BACK_SIDE.get(p["type"], set()) else front
        scale = min((cell_w * 0.92) / im.width, (cell_h * 0.92) / im.height)
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        r, c = divmod(n, PER_ROW)
        in_row = min(PER_ROW, len(products) - r * PER_ROW)
        x0 = PAD + (PER_ROW - in_row) * cell_w / 2  # centre a short last row
        cx = x0 + (c + 0.5) * cell_w
        cy = PAD + (r + 0.5) * cell_h
        canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))
    canvas.save(OUT, optimize=True)
    print(f"Wrote {os.path.relpath(OUT, HERE)} ({len(products)} designs)")


if __name__ == "__main__":
    main()
