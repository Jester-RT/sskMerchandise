#!/usr/bin/env python3
"""
Builds a paste-in product listing for the Squarespace site.

Reads the same folder structure as build-page.py:

    <Product Type>/<Design Name>/<Colour>.png

...and writes:

    squarespace/img/<design>/<colour>.jpg   web-sized copy of every image
    squarespace/snippet.html                paste this into a Squarespace
                                            Code Block
    squarespace/preview.html                the same snippet on a plain page,
                                            for checking it locally

The snippet is plain HTML and CSS (no JavaScript), so it works on every
Squarespace plan. Cards stack one per row on phones and sit side by side on
wider screens. Tapping a colour dot swaps the picture.

The snippet loads its images from GitHub Pages, so they appear once this
branch is merged to main. Pass --base to point it somewhere else, e.g.

    python build-squarespace.py --base https://example.com/img/

Usage (from this folder):   python build-squarespace.py
"""

import argparse
import html
import importlib.util
import os
import sys

sys.dont_write_bytecode = True  # keep build-page.py from leaving a __pycache__ folder

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "squarespace")
IMG_DIR = os.path.join(OUT_DIR, "img")

PAGES_BASE = "https://jester-rt.github.io/sskMerchandise/squarespace/img/"

# Reuse the scanner, ordering and size rules from the store-page builder.
_spec = importlib.util.spec_from_file_location("build_page", os.path.join(HERE, "build-page.py"))
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

IMG_WIDTH = 1000          # wide enough for a sharp picture on a phone
IMG_BG = (243, 236, 225)  # matches the card's image panel, --ink-100

# The colour each card opens on, first match wins.
DEFAULT_COLOURS = ["Deep_Black", "Black"]


def esc(s):
    return html.escape(str(s), quote=True)


def singular(ptype):
    return {"T-Shirts": "T-Shirt", "Hoodies": "Hoodie"}.get(ptype, ptype.rstrip("s"))


def join_names(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------

def web_image(src, dst):
    """A trimmed, flattened, web-sized JPEG copy of a front-and-back PNG."""
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return
    im = Image.open(src).convert("RGBA")
    box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if box:
        im = im.crop(box)
    pad = round(im.width * 0.03)
    flat = Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), IMG_BG)
    flat.paste(im, (pad, pad), im)
    if flat.width > IMG_WIDTH:
        flat = flat.resize((IMG_WIDTH, round(flat.height * IMG_WIDTH / flat.width)), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    flat.save(dst, "JPEG", quality=82, optimize=True, progressive=True)


def image_size(path):
    with Image.open(path) as im:
        return im.size


# --------------------------------------------------------------------------
# Snippet
# --------------------------------------------------------------------------

def css(max_colours, types):
    show = []
    for k in range(max_colours):
        show.append(f".ssk-shop .ssk-r{k}:checked~.ssk-pic .ssk-i{k},"
                    f".ssk-shop .ssk-r{k}:checked~.ssk-body .ssk-n{k}{{display:block}}")
        show.append(f".ssk-shop .ssk-r{k}:checked~.ssk-body .ssk-s{k}"
                    f"{{box-shadow:0 0 0 3px #fff,0 0 0 5px #4f8f1a}}")
        show.append(f".ssk-shop .ssk-r{k}:focus-visible~.ssk-body .ssk-s{k}"
                    f"{{outline:3px solid #4f8f1a;outline-offset:6px}}")
    for t in types:
        slug = bp.slugify(t)
        show.append(f".ssk-shop #ssk-f-{slug}:checked~.ssk-tabs label[for=ssk-f-{slug}]"
                    f"{{background:#4f8f1a;border-color:#3c6e14;color:#fff}}")
        others = [bp.slugify(o) for o in types if o != t]
        for o in others:
            show.append(f".ssk-shop #ssk-f-{slug}:checked~.ssk-grid .ssk-t-{o}{{display:none}}")
    return """
.ssk-shop{--ink:#1c140f;--muted:#6f5d4f;--line:#e6ddd0;--panel:#f3ece1;--green:#4f8f1a;
  font-family:inherit;color:var(--ink);max-width:1200px;margin:0 auto}
.ssk-shop *{box-sizing:border-box}
.ssk-shop .ssk-hide{position:absolute;opacity:0;width:1px;height:1px;margin:0;pointer-events:none}
.ssk-shop .ssk-tabs{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}
.ssk-shop .ssk-tabs label{cursor:pointer;font-size:15px;font-weight:600;line-height:1;
  padding:11px 18px;border:1px solid #c9bdb0;border-radius:999px;background:#fff;color:var(--ink)}
.ssk-shop #ssk-f-all:checked~.ssk-tabs label[for=ssk-f-all]{background:#4f8f1a;border-color:#3c6e14;color:#fff}
.ssk-shop .ssk-tabs label:hover{border-color:var(--green)}
.ssk-shop .ssk-hide:focus-visible~.ssk-tabs{outline:3px solid var(--green);outline-offset:4px;border-radius:12px}
.ssk-shop .ssk-grid{display:grid;gap:20px;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr))}
.ssk-shop .ssk-card{position:relative;background:#fff;border:1px solid var(--line);
  border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.ssk-shop .ssk-pic{background:var(--panel);aspect-ratio:var(--ar);position:relative}
.ssk-shop .ssk-pic a{display:none;width:100%;height:100%}
.ssk-shop .ssk-pic img{display:block;width:100%;height:100%;object-fit:contain;margin:0}
.ssk-shop .ssk-body{padding:14px 16px 18px}
.ssk-shop .ssk-kicker{margin:0 0 2px;font-size:12px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:#9b8c7e}
.ssk-shop .ssk-title{margin:0 0 12px;font-size:20px;font-weight:700;line-height:1.2;color:var(--ink)}
.ssk-shop .ssk-cname{margin:0 0 10px;font-size:14px;color:var(--muted);min-height:1.4em}
.ssk-shop .ssk-cname>span{display:none}
.ssk-shop .ssk-cname b{color:var(--ink)}
.ssk-shop .ssk-sw{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 14px}
.ssk-shop .ssk-sw label{cursor:pointer;width:30px;height:30px;border-radius:50%;
  background:var(--c);box-shadow:0 0 0 2px #fff,0 0 0 3px rgba(0,0,0,.18);position:relative}
.ssk-shop .ssk-sw label.ssk-adult::after{content:"A";position:absolute;right:-6px;top:-6px;
  width:15px;height:15px;border-radius:50%;background:#823d0e;color:#fff;font-size:9px;
  font-weight:700;line-height:15px;text-align:center}
.ssk-shop .ssk-sizes{margin:0;font-size:13px;color:var(--muted);line-height:1.5}
.ssk-shop .ssk-sizes b{color:var(--ink)}
.ssk-shop .ssk-note{color:#823d0e}
.ssk-shop .ssk-tip{margin:0 0 16px;font-size:14px;color:var(--muted)}
""" + "\n".join(show) + "\n"


def card(p, base):
    ptype = bp.slugify(p["type"])
    did = p["slug"]
    cols = p["colours"]
    default = next((i for name in DEFAULT_COLOURS for i, c in enumerate(cols) if c["file"] == name), 0)
    w, h = image_size(os.path.join(IMG_DIR, p["slug"], cols[0]["file"] + ".jpg"))

    radios, pics, names, swatches = [], [], [], []
    for k, c in enumerate(cols):
        rid = f"ssk-{did}-{k}"
        checked = " checked" if k == default else ""
        radios.append(f'<input class="ssk-hide ssk-r{k}" type="radio" name="ssk-{did}" '
                      f'id="{rid}"{checked} aria-label="{esc(c["name"])}">')
        url = f"{base}{p['slug']}/{c['file']}.jpg"
        alt = f"{singular(p['type'])} design {p['n']}, {p['title']}, in {c['name']}, front and back"
        pics.append(f'<a class="ssk-i{k}" href="{esc(url)}" target="_blank" rel="noopener">'
                    f'<img src="{esc(url)}" alt="{esc(alt)}" loading="lazy" width="{w}" height="{h}"></a>')
        adult = " · adult sizes only" if c["adultOnly"] else ""
        names.append(f'<span class="ssk-n{k}">Colour: <b>{esc(c["name"])}</b>'
                     f'<span class="ssk-note">{adult}</span></span>')
        cls = f"ssk-s{k}" + (" ssk-adult" if c["adultOnly"] else "")
        swatches.append(f'<label for="{rid}" class="{cls}" style="--c:{c["hex"]}" '
                        f'title="{esc(c["name"])}"></label>')

    adult = [c["name"] for c in cols if c["adultOnly"]]
    kids = f"{bp.KIDS_SIZES[0].split('–')[0]}–{bp.KIDS_SIZES[-1].split('–')[-1]}"  # 3–13 yrs
    sizes = f"<b>Kids</b> {kids} · <b>Adult</b> {bp.ADULT_SIZES[0]}–{bp.ADULT_SIZES[-1]}"
    if adult:
        sizes += (f'<br><span class="ssk-note">{esc(join_names(adult))} '
                  f'{"is" if len(adult) == 1 else "are"} adult sizes only.</span>')

    kicker = f"{singular(p['type'])} · Design {p['n']}" if p["n"] is not None else singular(p["type"])
    return (f'<article class="ssk-card ssk-t-{ptype}">'
            + "".join(radios)
            + f'<div class="ssk-pic" style="--ar:{w}/{h}">' + "".join(pics) + "</div>"
            + '<div class="ssk-body">'
            + f'<p class="ssk-kicker">{esc(kicker)}</p>'
            + f'<h3 class="ssk-title">{esc(p["title"])}</h3>'
            + '<p class="ssk-cname">' + "".join(names) + "</p>"
            + '<div class="ssk-sw">' + "".join(swatches) + "</div>"
            + f'<p class="ssk-sizes">{sizes}</p>'
            + "</div></article>")


def snippet(products, base):
    types = list(dict.fromkeys(p["type"] for p in products))
    max_colours = max(len(p["colours"]) for p in products)
    tabs_in = ['<input class="ssk-hide" type="radio" name="ssk-filter" id="ssk-f-all" checked>']
    tabs = [f'<label for="ssk-f-all">All ({len(products)})</label>']
    for t in types:
        slug = bp.slugify(t)
        n = sum(1 for p in products if p["type"] == t)
        tabs_in.append(f'<input class="ssk-hide" type="radio" name="ssk-filter" id="ssk-f-{slug}">')
        tabs.append(f'<label for="ssk-f-{slug}">{esc(t)} ({n})</label>')
    return ("<!-- SSK clothing range. Generated by build-squarespace.py; edit there, not here. -->\n"
            f"<style>{css(max_colours, types)}</style>\n"
            '<div class="ssk-shop">'
            + "".join(tabs_in)
            + '<div class="ssk-tabs">' + "".join(tabs) + "</div>"
            + '<p class="ssk-tip">Tap a colour to see it. Tap a picture to open it full size. '
              'Colours marked <b style="color:#823d0e">A</b> come in adult sizes only.</p>'
            + '<div class="ssk-grid">\n' + "\n".join(card(p, base) for p in products)
            + "\n</div></div>\n")


PREVIEW = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SSK clothing preview</title>
<style>body{margin:0;padding:24px 16px;background:#fff;
font-family:"Helvetica Neue",Arial,sans-serif}</style>
</head><body>
%s
</body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=PAGES_BASE, help="URL the img/ folder is served from")
    args = ap.parse_args()
    base = args.base if args.base.endswith("/") else args.base + "/"

    products = bp.scan()
    for p in products:
        for c in p["colours"]:
            web_image(os.path.join(HERE, p["path"], c["file"] + ".png"),
                      os.path.join(IMG_DIR, p["slug"], c["file"] + ".jpg"))

    with open(os.path.join(OUT_DIR, "snippet.html"), "w", encoding="utf-8") as fh:
        fh.write(snippet(products, base))
    with open(os.path.join(OUT_DIR, "preview.html"), "w", encoding="utf-8") as fh:
        fh.write(PREVIEW % snippet(products, "img/"))
    print(f"Wrote {len(products)} designs to squarespace/snippet.html")


if __name__ == "__main__":
    main()
