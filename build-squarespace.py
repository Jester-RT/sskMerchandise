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

# Price list shown above the cards: (garment, kids' price, adults' price).
PRICES = [
    ("T-Shirts", "£20", "£25"),
    ("Hoodies", "£25", "£35"),
]

ORDER_NOTE = ("Orders for clothing should be given to a club committee member at a "
              "training session. Please indicate design number, colour and size when ordering.")

# Reuse the scanner, ordering and size rules from the store-page builder.
_spec = importlib.util.spec_from_file_location("build_page", os.path.join(HERE, "build-page.py"))
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

IMG_WIDTH = 1000          # wide enough for a sharp picture on a phone card
ZOOM_WIDTH = 2000         # full-screen view, only downloaded when opened
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

def web_image(src, dst, width):
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
    if flat.width > width:
        flat = flat.resize((width, round(flat.height * width / flat.width)), Image.LANCZOS)
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
        show.append(f".ssk-shop .ssk-r{k}:checked~.ssk-zoom:checked~.ssk-pic .ssk-i{k}{{display:flex}}")
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
.ssk-shop{--page-text:#f3ece1; /* text that sits on the page background (black) */
  --zoom-top:120px;  /* full-screen view: room left for the site header */
  --zoom-bottom:120px; /* ...and for the Show front/back button */
  --ink:#1c140f;--muted:#6f5d4f;--line:#e6ddd0;--panel:#f3ece1;--green:#4f8f1a;
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
.ssk-shop .ssk-pic .ssk-im{display:none;width:100%;height:100%;cursor:zoom-in;margin:0}
.ssk-shop .ssk-pic img{display:block;width:100%;height:100%;object-fit:contain;margin:0}
.ssk-shop .ssk-pic .ssk-big,.ssk-shop .ssk-pic .ssk-close{display:none}
/* Full-screen view: a checkbox per card, toggled by tapping the picture */
.ssk-shop .ssk-zoom:checked~.ssk-pic{position:fixed;inset:0;z-index:2147483000;
  aspect-ratio:auto;overflow:hidden;overscroll-behavior:contain}
.ssk-shop .ssk-zoom:checked~.ssk-pic .ssk-im{cursor:zoom-out;min-height:100%;padding:var(--zoom-top) 0 var(--zoom-bottom);
  align-items:center;justify-content:center}
.ssk-shop .ssk-zoom:checked~.ssk-pic .ssk-small{display:none}
.ssk-shop .ssk-pic .ssk-bw{display:none}
/* One garment at a time: the image is twice the frame's width, slid left for the back */
.ssk-shop .ssk-zoom:checked~.ssk-pic .ssk-bw{display:block;position:relative;overflow:hidden;
  aspect-ratio:var(--har);
  width:min(94vw,calc((100vh - var(--zoom-top) - var(--zoom-bottom) - 16px) * var(--har)));
  width:min(94vw,calc((100dvh - var(--zoom-top) - var(--zoom-bottom) - 16px) * var(--har)))}
.ssk-shop .ssk-zoom:checked~.ssk-pic .ssk-big{display:block;width:200%;height:100%;max-width:none;
  object-fit:fill;transition:transform .35s ease}
.ssk-shop .ssk-back:checked~.ssk-pic .ssk-big{transform:translateX(-50%)}
.ssk-shop .ssk-flip{display:none}
.ssk-shop .ssk-zoom:checked~.ssk-pic .ssk-flip{display:block;position:fixed;left:50%;bottom:calc(var(--zoom-bottom) / 2 - 10px);
  transform:translateX(-50%);z-index:1;cursor:pointer;padding:13px 26px;border-radius:999px;
  background:#070402;color:#fff;font-size:17px;font-weight:700;line-height:1;white-space:nowrap;
  box-shadow:0 6px 20px rgba(0,0,0,.3)}
.ssk-shop .ssk-flip .ssk-to-front,.ssk-shop .ssk-back:checked~.ssk-pic .ssk-to-back{display:none}
.ssk-shop .ssk-back:checked~.ssk-pic .ssk-to-front{display:inline}
.ssk-shop .ssk-back:focus-visible~.ssk-pic .ssk-flip{outline:3px solid var(--green);outline-offset:3px}
.ssk-shop .ssk-zoom:checked~.ssk-pic .ssk-close{display:grid;place-items:center;position:fixed;
  top:calc(var(--zoom-top) + 4px);right:14px;z-index:1;width:46px;height:46px;border-radius:50%;cursor:pointer;
  background:rgba(7,4,2,.82);color:#fff;font-size:28px;line-height:1;font-weight:400}
.ssk-shop .ssk-zoom:focus-visible~.ssk-pic{outline:3px solid var(--green);outline-offset:-3px}
.ssk-shop .ssk-body{padding:14px 16px 18px}
.ssk-shop .ssk-head{display:flex;align-items:center;gap:14px;margin:0 0 14px}
.ssk-shop .ssk-no{flex:none;width:64px;height:64px;border-radius:14px;background:var(--green);
  color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1}
.ssk-shop .ssk-no small{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;opacity:.85}
.ssk-shop .ssk-no b{font-size:32px;font-weight:800;margin-top:3px}
.ssk-shop .ssk-ref{margin:0 0 2px;font-size:15px;font-weight:800;letter-spacing:.06em;
  text-transform:uppercase;color:#3c6e14}
.ssk-shop .ssk-kicker{margin:0 0 2px;font-size:12px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:#9b8c7e}
.ssk-shop .ssk-title{margin:0;font-size:20px;font-weight:700;line-height:1.2;color:var(--ink)}
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
.ssk-shop .ssk-tip{margin:0 0 20px;font-size:18px;line-height:1.5;color:var(--page-text)}
.ssk-shop .ssk-intro{color:var(--page-text);margin:0 0 28px;font-size:18px;line-height:1.5;
  display:grid;gap:24px}
@media (max-width:767px){.ssk-shop{--zoom-top:90px;--zoom-bottom:110px}}
@media (min-width:768px){.ssk-shop .ssk-intro{grid-template-columns:1fr minmax(300px,440px);gap:48px}}
.ssk-shop .ssk-intro-h{margin:0 0 10px;font-size:22px;font-weight:700;color:var(--page-text)}
.ssk-shop .ssk-prices{border-collapse:collapse;width:100%;max-width:440px;margin:0;
  font-size:18px;color:var(--page-text)}
.ssk-shop .ssk-prices th,.ssk-shop .ssk-prices td{padding:10px 14px;text-align:left;
  border-bottom:1px solid rgba(255,255,255,.25)}
.ssk-shop .ssk-prices thead th{font-size:13px;letter-spacing:.1em;text-transform:uppercase;
  color:#bf9c05;border-bottom:2px solid #bf9c05}
.ssk-shop .ssk-prices td{font-weight:700;font-size:20px}
.ssk-shop .ssk-intro p{margin:0;max-width:60ch}
.ssk-shop .ssk-badge{display:inline-block;width:22px;height:22px;border-radius:50%;
  background:#823d0e;color:#fff;font-size:13px;font-weight:700;line-height:22px;
  text-align:center;vertical-align:1px;box-shadow:0 0 0 1px rgba(255,255,255,.6)}
""" + "\n".join(show) + "\n"


def card(p, base):
    ptype = bp.slugify(p["type"])
    did = p["slug"]
    cols = p["colours"]
    default = next((i for name in DEFAULT_COLOURS for i, c in enumerate(cols) if c["file"] == name), 0)
    w, h = image_size(os.path.join(IMG_DIR, p["slug"], cols[0]["file"] + ".jpg"))

    zid, bid = f"ssk-z-{did}", f"ssk-b-{did}"
    hw, hh = image_size(os.path.join(IMG_DIR, p["slug"], cols[0]["file"] + "-large.jpg"))
    radios, pics, names, swatches = [], [], [], []
    for k, c in enumerate(cols):
        rid = f"ssk-{did}-{k}"
        checked = " checked" if k == default else ""
        radios.append(f'<input class="ssk-hide ssk-r{k}" type="radio" name="ssk-{did}" '
                      f'id="{rid}"{checked} aria-label="{esc(c["name"])}">')
        url = f"{base}{p['slug']}/{c['file']}.jpg"
        alt = f"{singular(p['type'])} design {p['n']}, {p['title']}, in {c['name']}, front and back"
        big = f"{base}{p['slug']}/{c['file']}-large.jpg"
        pics.append(f'<label for="{zid}" class="ssk-im ssk-i{k}">'
                    f'<img class="ssk-small" src="{esc(url)}" alt="{esc(alt)}" loading="lazy" '
                    f'width="{w}" height="{h}">'
                    f'<span class="ssk-bw"><img class="ssk-big" src="{esc(big)}" alt="{esc(alt)}" '
                    f'loading="lazy"></span></label>')
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

    ref = f"{singular(p['type'])} · Design {p['n']}" if p["n"] is not None else singular(p["type"])
    num = (f'<div class="ssk-no" aria-hidden="true"><small>No.</small><b>{p["n"]}</b></div>'
           if p["n"] is not None else "")
    return (f'<article class="ssk-card ssk-t-{ptype}">'
            + "".join(radios)
            + f'<input class="ssk-hide ssk-zoom" type="checkbox" id="{zid}" '
              f'aria-label="Full-screen view of {esc(p["title"])}">'
            + f'<input class="ssk-hide ssk-back" type="checkbox" id="{bid}" aria-label="Show the back">'
            + f'<div class="ssk-pic" style="--ar:{w}/{h};--har:{hw / 2 / hh:.4f}">' + "".join(pics)
            + f'<label for="{bid}" class="ssk-flip"><span class="ssk-to-back">Show back &rarr;</span>'
              f'<span class="ssk-to-front">&larr; Show front</span></label>'
            + f'<label for="{zid}" class="ssk-close" aria-label="Close">&times;</label></div>'
            + '<div class="ssk-body">'
            + f'<div class="ssk-head">{num}<div>'
            + f'<p class="ssk-ref">{esc(ref)}</p>'
            + f'<h3 class="ssk-title">{esc(p["title"])}</h3></div></div>'
            + '<p class="ssk-cname">' + "".join(names) + "</p>"
            + '<div class="ssk-sw">' + "".join(swatches) + "</div>"
            + f'<p class="ssk-sizes">{sizes}</p>'
            + "</div></article>")


def intro():
    rows = "".join(f"<tr><th scope=\"row\">{esc(g)}</th><td>{esc(k)}</td><td>{esc(a)}</td></tr>"
                   for g, k, a in PRICES)
    return ('<div class="ssk-intro">'
            f'<div><p class="ssk-intro-h">Ordering</p><p>{esc(ORDER_NOTE)}</p></div>'
            '<div><p class="ssk-intro-h">Prices</p>'
            '<table class="ssk-prices"><thead><tr><th></th><th scope="col">Children</th>'
            f'<th scope="col">Adults</th></tr></thead><tbody>{rows}</tbody></table></div></div>')


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
            + intro()
            + "".join(tabs_in)
            + '<div class="ssk-tabs">' + "".join(tabs) + "</div>"
            + '<p class="ssk-tip">Tap a colour to see it. Tap a picture to see it full screen. '
              'Colours marked <span class="ssk-badge">A</span> come in adult sizes only.</p>'
            + '<div class="ssk-grid">\n' + "\n".join(card(p, base) for p in products)
            + "\n</div></div>\n")


PREVIEW = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SSK clothing preview</title>
<style>body{margin:0;padding:24px 16px;background:#000;
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
            src = os.path.join(HERE, p["path"], c["file"] + ".png")
            web_image(src, os.path.join(IMG_DIR, p["slug"], c["file"] + ".jpg"), IMG_WIDTH)
            web_image(src, os.path.join(IMG_DIR, p["slug"], c["file"] + "-large.jpg"), ZOOM_WIDTH)

    with open(os.path.join(OUT_DIR, "snippet.html"), "w", encoding="utf-8") as fh:
        fh.write(snippet(products, base))
    with open(os.path.join(OUT_DIR, "preview.html"), "w", encoding="utf-8") as fh:
        fh.write(PREVIEW % snippet(products, "img/"))
    print(f"Wrote {len(products)} designs to squarespace/snippet.html")


if __name__ == "__main__":
    main()
