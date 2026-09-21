#!/usr/bin/env python3
"""
Rebuilds the SSK clothing store pages.

Scans the folder structure:

    <Product Type>/<Design Name>/<Colour>.png

...and regenerates:

    index.html              the store front, filterable by product type
    designs/<slug>.html     one page per design, showing every colour

Swatch colours are sampled from the garment itself, so they always match the
real product.

Usage (from this folder):   python build-page.py

Add a new design by dropping in a folder of colour PNGs and re-running it.
"""

import json
import os
import re
import sys
from collections import Counter

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "index.html")
DESIGN_DIR = os.path.join(HERE, "designs")

SITE_TITLE = "Stafford Shotokan Karate Club Clothing"
EYEBROW = "2026 Range"
LOGO = "ssk-logo-white-300dpi.png"

# Colours sold in adult sizes only, keyed by product type.
ADULT_ONLY = {
    "T-Shirts": {"Orange_Crush", "Purple"},
}

KIDS_SIZES = ["3–4 yrs", "5–6 yrs", "7–8 yrs", "9–11 yrs", "12–13 yrs"]
ADULT_SIZES = ["S", "M", "L", "XL", "2XL"]

# Order the product types appear in. Anything not listed is appended A–Z.
TYPE_ORDER = ["T-Shirts", "Hoodies"]

# Order colours appear in on a card. Anything not listed is appended A–Z.
COLOUR_ORDER = [
    "Arctic_White", "Natural_Stone", "Light_Blue", "Airforce_Blue", "Blue",
    "New_French_Navy", "Bottle_Green", "Fire_Red", "Maroon", "Orange_Crush",
    "Purple", "Dusty_Purple", "Charcoal", "Solid_Charcoal", "Black", "Deep_Black",
]


# --------------------------------------------------------------------------
# Scanning
# --------------------------------------------------------------------------

def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def ordered(items, preferred):
    known = [x for x in preferred if x in items]
    rest = sorted(set(items) - set(preferred), key=natural_key)
    return known + rest


def pretty(stem):
    return stem.replace("_", " ")


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def design_title(folder):
    """'Design 7 - Mount Fuji (Option A)' -> (7, 'Mount Fuji (Option A)')"""
    m = re.match(r"\s*Design\s+(\d+)\s*[-–]\s*(.+)", folder)
    if m:
        return int(m.group(1)), m.group(2).strip()
    return None, folder.strip()


def garment_hex(path):
    """Modal colour of the left-hand (front) garment body, ignoring the print."""
    im = Image.open(path).convert("RGBA")
    im.thumbnail((500, 500))
    w, h = im.size
    px = im.load()
    counts = Counter()
    for y in range(int(h * 0.15), int(h * 0.92), 2):
        for x in range(int(w * 0.03), int(w * 0.48), 2):
            r, g, b, a = px[x, y]
            if a < 250:
                continue
            counts[(r // 4 * 4, g // 4 * 4, b // 4 * 4)] += 1
    if not counts:
        return "#cccccc"
    (r, g, b), _ = counts.most_common(1)[0]
    return "#%02x%02x%02x" % (r, g, b)


def scan():
    types = [d for d in os.listdir(HERE)
             if os.path.isdir(os.path.join(HERE, d))
             and not d.startswith(".")
             and d != "designs"]
    swatch_cache = {}
    products = []

    for ptype in ordered(types, TYPE_ORDER):
        tpath = os.path.join(HERE, ptype)
        folders = [d for d in os.listdir(tpath)
                   if os.path.isdir(os.path.join(tpath, d))]
        for folder in sorted(folders, key=natural_key):
            dpath = os.path.join(tpath, folder)
            stems = [f[:-4] for f in os.listdir(dpath) if f.lower().endswith(".png")]
            if not stems:
                print(f"  ! skipping (no images): {ptype}/{folder}")
                continue
            num, title = design_title(folder)
            with Image.open(os.path.join(dpath, stems[0] + ".png")) as probe:
                iw, ih = probe.size
            colours = []
            for stem in ordered(stems, COLOUR_ORDER):
                key = (ptype, stem)
                if key not in swatch_cache:
                    swatch_cache[key] = garment_hex(os.path.join(dpath, stem + ".png"))
                colours.append({
                    "file": stem,
                    "name": pretty(stem),
                    "hex": swatch_cache[key],
                    "adultOnly": stem in ADULT_ONLY.get(ptype, set()),
                })
            products.append({
                "type": ptype,
                "n": num,
                "folder": folder,
                "title": title,
                "path": f"{ptype}/{folder}",
                "slug": slugify(f"{ptype}-{folder}"),
                "w": iw,
                "h": ih,
                "colours": colours,
            })
    return products


# --------------------------------------------------------------------------
# Shared CSS
# --------------------------------------------------------------------------

CSS = r"""
:root{
  --ink-900:#070402; --ink-800:#1c140f; --ink-700:#2c211a; --ink-600:#4a3b30;
  --ink-500:#6f5d4f; --ink-400:#9b8c7e; --ink-300:#c9bdb0; --ink-200:#e6ddd0;
  --ink-100:#f3ece1; --paper:#fbf7ef; --gi-white:#ffffff;
  --green-700:#3c6e14; --green-600:#4f8f1a; --green-200:#d7e9c2;
  --gold-600:#bf9c05; --burnt-600:#823d0e;
  --radius-md:14px; --radius-lg:22px;
  --shadow-sm:0 1px 3px rgba(44,33,26,.10);
  --shadow-md:0 6px 20px rgba(44,33,26,.12);
  --shadow-lg:0 18px 46px rgba(44,33,26,.22);
  --ease-out:cubic-bezier(.2,.7,.3,1);
  --font:"Noto Sans","Segoe UI",system-ui,-apple-system,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
html{scrollbar-gutter:stable}
body{font-family:var(--font); color:var(--ink-600); background:var(--paper);
  -webkit-font-smoothing:antialiased; line-height:1.5}
img{display:block;max-width:100%}

/* Header */
.site-header{background:var(--ink-900); color:var(--gi-white);
  padding:26px 0 30px; border-bottom:4px solid var(--gold-600)}
.header-inner{max-width:1280px; margin:0 auto; padding:0 24px;
  display:flex; align-items:center; justify-content:space-between; gap:24px}
.header-text h1{font-size:clamp(24px,3.6vw,40px); font-weight:600;
  letter-spacing:-.01em; margin:0; color:var(--gi-white); line-height:1.12}
.header-text p{margin:10px 0 0; color:#cfc4b6; font-size:15px; max-width:56ch}
.header-text .eyebrow{display:block; font-size:11px; letter-spacing:.18em;
  text-transform:uppercase; font-weight:600; color:var(--gold-600); margin:0 0 8px}
.logo{width:clamp(78px,11vw,120px); height:auto; flex:none}
.back{display:inline-flex; align-items:center; gap:7px; margin:0 0 10px;
  color:#cfc4b6; text-decoration:none; font-size:13px; font-weight:600;
  letter-spacing:.04em}
.back:hover{color:#fff; text-decoration:underline}

.wrap{max-width:1280px; margin:0 auto; padding:0 24px}

/* Buttons */
.btn{font:inherit; font-size:13px; font-weight:600; cursor:pointer;
  border:1px solid var(--ink-300); background:var(--gi-white); color:var(--ink-700);
  border-radius:999px; padding:8px 16px; box-shadow:var(--shadow-sm);
  text-decoration:none; display:inline-flex; align-items:center; gap:7px;
  transition:transform .16s var(--ease-out), background .16s var(--ease-out),
             border-color .16s var(--ease-out)}
.btn:hover{transform:translateY(-1px); background:var(--ink-100)}
.btn:focus-visible{outline:3px solid var(--green-600); outline-offset:3px}
.btn.primary{background:var(--green-600); border-color:var(--green-700); color:#fff}
.btn.primary:hover{background:var(--green-700)}
.btn-enlarge{position:absolute; right:22px; bottom:22px; z-index:2;
  background:rgba(7,4,2,.78); border-color:rgba(255,255,255,.28); color:#fff;
  font-size:11px; letter-spacing:.06em; text-transform:uppercase; padding:7px 14px;
  backdrop-filter:blur(2px)}
.btn-enlarge:hover{background:rgba(7,4,2,.92); color:#fff}

/* Filter bar */
.toolbar{position:sticky; top:0; z-index:20; background:rgba(251,247,239,.94);
  backdrop-filter:blur(6px); border-bottom:1px solid var(--ink-200);
  margin-bottom:26px}
.toolbar-inner{max-width:1280px; margin:0 auto; padding:14px 24px;
  display:flex; flex-wrap:wrap; gap:14px; align-items:center;
  justify-content:space-between}
.filters{display:flex; gap:8px; flex-wrap:wrap; margin:0; padding:0; list-style:none}
.filter{font:inherit; font-size:14px; font-weight:600; cursor:pointer;
  border:1px solid var(--ink-300); background:var(--gi-white); color:var(--ink-700);
  border-radius:999px; padding:9px 18px; box-shadow:var(--shadow-sm);
  transition:transform .16s var(--ease-out), background .16s var(--ease-out)}
.filter:hover{transform:translateY(-1px)}
.filter:focus-visible{outline:3px solid var(--green-600); outline-offset:3px}
.filter[aria-pressed="true"]{background:var(--green-600);
  border-color:var(--green-700); color:#fff}
.filter .count{opacity:.65; font-weight:500}
.result-count{font-size:13px; color:var(--ink-400); margin:0}

.note{display:flex; align-items:flex-start; gap:10px; margin:0 0 24px;
  background:#fdf3e6; border:1px solid #edd6b4; color:var(--burnt-600);
  border-radius:var(--radius-md); padding:12px 16px; font-size:14px; font-weight:500}
.note strong{color:var(--ink-800)}
.note .dots{display:flex; gap:4px; flex:none; margin-top:3px}
.note .dots i{width:14px;height:14px;border-radius:50%;display:block;
  box-shadow:0 0 0 2px #fff,0 0 0 3px rgba(0,0,0,.12)}

/* Grid */
.grid{display:grid; gap:26px; margin:0 0 60px;
  grid-template-columns:repeat(auto-fill,minmax(420px,1fr))}
@media (max-width:900px){ .grid{grid-template-columns:1fr} }

.card{background:var(--gi-white); border-radius:var(--radius-lg);
  box-shadow:var(--shadow-md); overflow:hidden; display:flex; flex-direction:column;
  transition:box-shadow .25s var(--ease-out), transform .25s var(--ease-out)}
.card:hover{box-shadow:var(--shadow-lg); transform:translateY(-2px)}
.card[hidden]{display:none}

.card-head{padding:16px 22px 12px; border-bottom:1px solid var(--ink-200)}
.card-kicker{display:flex; align-items:center; gap:10px; margin:0 0 4px}
.pill{font-size:10px; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
  border-radius:999px; padding:3px 10px; background:var(--green-200);
  color:var(--green-700)}
.pill.hoodies{background:#e2e0ef; color:#3b357a}
.card-num{font-size:11px; font-weight:700; letter-spacing:.12em;
  text-transform:uppercase; color:var(--ink-400)}
.card-title{margin:0; font-size:19px; font-weight:600; color:var(--ink-900);
  line-height:1.25}

.shot{position:relative; background:var(--ink-100); padding:14px}
.shot img{width:100%; height:auto; border-radius:10px;
  transition:opacity .18s var(--ease-out)}
.shot.loading img{opacity:.25}
.views{margin:0; font-size:11px; color:var(--ink-400); text-align:center;
  letter-spacing:.14em; text-transform:uppercase; font-weight:600;
  padding:0 0 12px; background:var(--ink-100)}

.card-body{padding:16px 22px 22px; display:flex; flex-direction:column;
  gap:14px; flex:1}
.swatch-label{margin:0 0 8px; font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; font-weight:600; color:var(--ink-400)}
.swatch-label b{color:var(--ink-800); font-weight:600; letter-spacing:0;
  text-transform:none; font-size:14px; margin-left:8px}
.swatches{display:flex; flex-wrap:wrap; gap:9px; padding:0; margin:0; list-style:none}
.swatch{width:34px; height:34px; border-radius:50%; padding:0; cursor:pointer;
  border:1px solid var(--ink-300); background-clip:padding-box;
  box-shadow:var(--shadow-sm); position:relative;
  transition:transform .16s var(--ease-out), box-shadow .16s var(--ease-out)}
.swatch:hover{transform:translateY(-2px)}
.swatch:focus-visible{outline:3px solid var(--green-600); outline-offset:3px}
.swatch[aria-pressed="true"]{box-shadow:0 0 0 2px var(--gi-white),
  0 0 0 4px var(--green-600), var(--shadow-sm)}
.swatch.adult-only::after{content:"A"; position:absolute; right:-3px; bottom:-3px;
  width:15px; height:15px; border-radius:50%; background:var(--ink-900); color:#fff;
  font-size:9px; font-weight:700; display:grid; place-items:center;
  border:1.5px solid #fff}

.sizes{border-top:1px solid var(--ink-200); padding-top:14px}
.size-row{display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px}
.size-row:last-of-type{margin-bottom:0}
.size-key{font-size:11px; letter-spacing:.12em; text-transform:uppercase;
  font-weight:700; color:var(--ink-400); width:52px; flex:none}
.chip{font-size:12px; font-weight:600; color:var(--ink-700);
  background:var(--ink-100); border:1px solid var(--ink-200);
  border-radius:999px; padding:4px 11px}
.size-row.muted .chip{background:transparent; color:var(--ink-300);
  border-style:dashed}
.adult-msg{margin:10px 0 0; font-size:12.5px; color:var(--burnt-600);
  font-weight:600; background:#fdf3e6; border-radius:10px; padding:8px 12px;
  display:none}
.card.is-adult-only .adult-msg{display:block}

.card-foot{margin-top:auto; padding-top:14px; border-top:1px solid var(--ink-200);
  display:flex; justify-content:flex-end}

.empty{display:none; text-align:center; padding:60px 20px; color:var(--ink-400)}

/* Design page */
.design-intro{display:flex; flex-wrap:wrap; gap:24px; align-items:flex-start;
  justify-content:space-between; margin:28px 0 24px}
.design-intro .sizes{border-top:none; padding-top:0; flex:1 1 320px}
.colour-grid{display:grid; gap:26px; margin:0 0 60px;
  grid-template-columns:repeat(auto-fill,minmax(400px,1fr))}
@media (max-width:860px){ .colour-grid{grid-template-columns:1fr} }
.colour-card{background:var(--gi-white); border-radius:var(--radius-lg);
  box-shadow:var(--shadow-md); overflow:hidden;
  transition:box-shadow .25s var(--ease-out), transform .25s var(--ease-out)}
.colour-card:hover{box-shadow:var(--shadow-lg); transform:translateY(-2px)}
.colour-bar{display:flex; align-items:center; gap:11px; padding:14px 20px;
  border-bottom:1px solid var(--ink-200)}
.colour-bar .dot{width:26px; height:26px; border-radius:50%; flex:none;
  border:1px solid var(--ink-300); box-shadow:var(--shadow-sm)}
.colour-bar h2{margin:0; font-size:16px; font-weight:600; color:var(--ink-900)}
.colour-bar .tag{margin-left:auto; font-size:10px; font-weight:700;
  letter-spacing:.1em; text-transform:uppercase; border-radius:999px;
  padding:3px 10px; background:#fdf3e6; color:var(--burnt-600);
  border:1px solid #edd6b4}

/* Lightbox */
.lightbox{position:fixed; inset:0; background:rgba(44,33,26,.82); display:none;
  align-items:center; justify-content:center; z-index:50; padding:24px}
.lightbox.open{display:flex}
.lightbox figure{margin:0; max-width:1500px; width:100%; text-align:center}
.lightbox img{width:100%; height:auto; max-height:76vh; object-fit:contain;
  background:var(--paper); border-radius:var(--radius-md); padding:12px}
.lightbox figcaption{color:#fff; margin-top:16px; font-size:15px; font-weight:500}
.lightbox figcaption span{color:#cfc4b6; font-weight:400}
.lb-close,.lb-nav{font:inherit; border:1px solid rgba(255,255,255,.34);
  background:rgba(7,4,2,.78); color:#fff; cursor:pointer; position:absolute;
  display:grid; place-items:center; line-height:1;
  box-shadow:0 4px 14px rgba(0,0,0,.4);
  transition:background .16s var(--ease-out), transform .16s var(--ease-out)}
.lb-close:hover,.lb-nav:hover{background:rgba(7,4,2,.95)}
.lb-close:focus-visible,.lb-nav:focus-visible{outline:3px solid var(--gold-600);
  outline-offset:3px}
.lb-close{top:18px; right:22px; width:44px; height:44px; border-radius:50%;
  font-size:22px}
.lb-nav{top:50%; margin-top:-28px; width:56px; height:56px; border-radius:50%;
  font-size:26px; font-weight:700}
.lb-nav:hover{transform:scale(1.06)}
.lb-prev{left:18px} .lb-next{right:18px}
@media (max-width:640px){
  .lb-nav{width:46px; height:46px; margin-top:-23px; font-size:22px}
  .lb-prev{left:8px} .lb-next{right:8px}
}

footer{border-top:1px solid var(--ink-200); padding:26px 0 44px; font-size:13px;
  color:var(--ink-400); text-align:center}
footer .kanji{color:var(--gold-600); font-size:16px; margin-bottom:6px}

@media print{
  .swatches,.lightbox,.toolbar,.btn,.card-foot{display:none!important}
  .card,.colour-card{break-inside:avoid; box-shadow:none;
    border:1px solid var(--ink-200)}
}
"""


# Lightbox markup + behaviour, shared by both page types. The page supplies a
# `lbColoursFor(i)` function returning the colour array for lightbox item i.
LIGHTBOX_HTML = r"""
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true"
     aria-label="Enlarged garment image">
  <button class="lb-close" id="lbClose" aria-label="Close">&times;</button>
  <button class="lb-nav lb-prev" id="lbPrev" aria-label="Previous colour">&#8249;</button>
  <button class="lb-nav lb-next" id="lbNext" aria-label="Next colour">&#8250;</button>
  <figure>
    <img id="lbImg" alt="">
    <figcaption id="lbCap" aria-live="polite"></figcaption>
  </figure>
</div>
"""

LIGHTBOX_JS = r"""
const lb = document.getElementById("lightbox");
const lbImg = document.getElementById("lbImg");
const lbCap = document.getElementById("lbCap");
let lbItem = 0, lbColour = 0, lbOpener = null;

const outside = () => [...document.body.children]
  .filter(el => el !== lb && el.tagName !== "SCRIPT");

function openLb(item, ci, opener){
  lbItem = item; lbColour = ci; lbOpener = opener || null;
  paintLb(); lb.classList.add("open");
  document.body.style.overflow = "hidden";
  outside().forEach(el => el.setAttribute("inert", ""));
  document.getElementById("lbClose").focus();
}
function closeLb(){
  lb.classList.remove("open");
  document.body.style.overflow = "";
  outside().forEach(el => el.removeAttribute("inert"));
  if (lbOpener) lbOpener.focus();
  lbOpener = null;
}
function stepLb(dir){
  const list = lbColoursFor(lbItem);
  lbColour = (lbColour + dir + list.length) % list.length;
  paintLb();
  onLbStep(lbItem, lbColour);
}
document.getElementById("lbClose").addEventListener("click", closeLb);
document.getElementById("lbPrev").addEventListener("click", () => stepLb(-1));
document.getElementById("lbNext").addEventListener("click", () => stepLb(1));
lb.addEventListener("click", e => { if (e.target === lb) closeLb(); });
document.addEventListener("keydown", e => {
  if (!lb.classList.contains("open")) return;
  if (e.key === "Escape") closeLb();
  if (e.key === "ArrowLeft") stepLb(-1);
  if (e.key === "ArrowRight") stepLb(1);
});
"""


def head(title, css_extra=""):
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}{css_extra}</style>
</head>
<body>
"""


FOOTER = """
<footer>
  <div class="kanji">空手道</div>
  Stafford Shotokan Karate · 2026 clothing range
</footer>
"""


def adult_note(colours):
    """The 'adult sizes only' banner for a set of colours, or '' if none apply."""
    adult = []
    for c in colours:
        if c["adultOnly"] and c["name"] not in [a["name"] for a in adult]:
            adult.append(c)
    if not adult:
        return ""
    dots = "".join(f'<i style="background:{c["hex"]}"></i>' for c in adult)
    names = " and ".join(filter(None, [
        ", ".join(c["name"] for c in adult[:-1]),
        adult[-1]["name"],
    ]))
    verb = "is" if len(adult) == 1 else "are"
    return (f'<p class="note" id="adultNote">'
            f'<span class="dots" aria-hidden="true">{dots}</span>'
            f'<span><strong>{esc(names)} {verb} available in adult sizes only.</strong> '
            f"Every other colour comes in both kids' and adult sizes.</span></p>")


def size_rows(adult_only=False):
    kids = "".join(f'<span class="chip">{s}</span>' for s in KIDS_SIZES)
    adult = "".join(f'<span class="chip">{s}</span>' for s in ADULT_SIZES)
    muted = " muted" if adult_only else ""
    return (f'<div class="size-row kids{muted}"><span class="size-key">Kids</span>{kids}</div>'
            f'<div class="size-row"><span class="size-key">Adult</span>{adult}</div>')


# --------------------------------------------------------------------------
# Store front
# --------------------------------------------------------------------------

INDEX_BODY = r"""
<header class="site-header">
  <div class="header-inner">
    <div class="header-text">
      <span class="eyebrow">__EYEBROW__</span>
      <h1>__TITLE__</h1>
      <p>Tap a colour dot to preview any design, or open a design to see every
         colour side by side. Each image shows the front and the back.</p>
    </div>
    <img class="logo" src="__LOGO__" alt="Stafford Shotokan Karate club logo">
  </div>
</header>

<div class="toolbar">
  <div class="toolbar-inner">
    <ul class="filters" id="filters" role="group" aria-label="Filter by product type"></ul>
    <p class="result-count" id="resultCount" aria-live="polite"></p>
  </div>
</div>

<main class="wrap">
  __ADULT_NOTE__

  <noscript>
    <p class="note" style="background:#f3ece1;border-color:#c9bdb0;color:#4a3b30">
      This page needs JavaScript to show the designs and colour options.
      Please enable it, or contact the club for a printed copy of the range.
    </p>
  </noscript>

  <div class="grid" id="grid"></div>
  <p class="empty" id="empty">Nothing to show for that filter.</p>
</main>
__FOOTER__
__LIGHTBOX__
<script>
const PRODUCTS = __DATA__;
const KIDS  = __KIDS__;
const ADULT = __ADULT__;

const TYPES = [...new Set(PRODUCTS.map(p => p.type))];
const grid = document.getElementById("grid");
const emptyMsg = document.getElementById("empty");
const resultCount = document.getElementById("resultCount");

const src = (p, colour) =>
  p.path.split("/").map(encodeURIComponent).join("/") + "/" +
  encodeURIComponent(colour.file) + ".png";
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const h = s => String(s).replace(/[&<>"']/g, ch =>
  ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));

/* ---------- Filters ---------- */
const filters = document.getElementById("filters");
[["all", "All"], ...TYPES.map(t => [t, t])].forEach(([value, label]) => {
  const n = value === "all" ? PRODUCTS.length
                            : PRODUCTS.filter(p => p.type === value).length;
  const li = document.createElement("li");
  const b = document.createElement("button");
  b.className = "filter";
  b.type = "button";
  b.innerHTML = `${label}<span class="count"> ${n}</span>`;
  b.setAttribute("aria-pressed", value === "all" ? "true" : "false");
  b.addEventListener("click", () => setFilter(value));
  li.appendChild(b);
  filters.appendChild(li);
});

function setFilter(value){
  [...filters.querySelectorAll(".filter")].forEach((b, i) => {
    const v = i === 0 ? "all" : TYPES[i - 1];
    b.setAttribute("aria-pressed", v === value ? "true" : "false");
  });
  let shown = 0;
  [...grid.children].forEach(card => {
    const match = value === "all" || card.dataset.type === value;
    card.hidden = !match;
    if (match) shown++;
  });
  emptyMsg.style.display = shown ? "none" : "block";
  resultCount.textContent =
    `${shown} design${shown === 1 ? "" : "s"}` +
    (value === "all" ? "" : ` · ${value}`);

  // Only show the adult-sizes note when a visible design actually has one.
  const note = document.getElementById("adultNote");
  if (note){
    const relevant = PRODUCTS.some(p =>
      (value === "all" || p.type === value) && p.colours.some(c => c.adultOnly));
    note.hidden = !relevant;
  }
}

/* ---------- Cards ---------- */
PRODUCTS.forEach((p, pi) => {
  const card = document.createElement("article");
  card.className = "card";
  card.dataset.index = pi;
  card.dataset.type = p.type;
  card.innerHTML = `
    <div class="card-head">
      <p class="card-kicker">
        <span class="pill ${slug(p.type)}">${h(p.type)}</span>
        ${p.n ? `<span class="card-num">Design ${p.n}</span>` : ""}
      </p>
      <h2 class="card-title">${h(p.title)}</h2>
    </div>
    <div class="shot">
      <img alt="" width="${p.w}" height="${p.h}" loading="lazy" decoding="async">
      <button class="btn btn-enlarge" type="button">Click to Enlarge</button>
    </div>
    <p class="views">Front &nbsp;·&nbsp; Back</p>
    <div class="card-body">
      <div>
        <p class="swatch-label">Colour <b class="cname"></b></p>
        <ul class="swatches"></ul>
      </div>
      <div class="sizes">
        ${SIZE_ROWS}
        <p class="adult-msg"></p>
      </div>
      <div class="card-foot">
        <a class="btn primary" href="designs/${encodeURIComponent(p.slug)}.html"
           aria-label="View all ${p.colours.length} colours of ${h(p.title)}">View</a>
      </div>
    </div>`;

  const list = card.querySelector(".swatches");
  p.colours.forEach((colour, ci) => {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.className = "swatch" + (colour.adultOnly ? " adult-only" : "");
    b.style.background = colour.hex;
    b.type = "button";
    b.title = colour.name + (colour.adultOnly ? " (adult sizes only)" : "");
    b.setAttribute("aria-label", b.title);
    b.setAttribute("aria-pressed", ci === 0 ? "true" : "false");
    b.addEventListener("click", () => select(card, pi, ci));
    li.appendChild(b);
    list.appendChild(li);
  });

  const enlarge = card.querySelector(".btn-enlarge");
  enlarge.addEventListener("click", () =>
    openLb(pi, +card.dataset.colour, enlarge));

  grid.appendChild(card);
  select(card, pi, 0);
});

function select(card, pi, ci){
  const p = PRODUCTS[pi];
  const colour = p.colours[ci];
  card.dataset.colour = ci;
  const shot = card.querySelector(".shot");
  const img = card.querySelector(".shot img");
  shot.classList.add("loading");
  img.onload = () => shot.classList.remove("loading");
  img.onerror = () => shot.classList.remove("loading");
  img.src = src(p, colour);
  img.alt = `${p.title} ${p.type.toLowerCase()} in ${colour.name} — front and back`;
  card.querySelector(".cname").textContent = colour.name;
  card.querySelector(".btn-enlarge").setAttribute(
    "aria-label", `Click to enlarge ${p.title} in ${colour.name}`);
  card.querySelectorAll(".swatch").forEach((b, i) =>
    b.setAttribute("aria-pressed", i === ci ? "true" : "false"));
  card.classList.toggle("is-adult-only", colour.adultOnly);
  card.querySelector(".size-row.kids").classList.toggle("muted", colour.adultOnly);
  card.querySelector(".adult-msg").textContent =
    `${colour.name} is available in adult sizes only.`;
}

/* ---------- Lightbox hooks ---------- */
const lbColoursFor = pi => PRODUCTS[pi].colours;
const onLbStep = (pi, ci) => select(grid.children[pi], pi, ci);
function paintLb(){
  const p = PRODUCTS[lbItem], c = p.colours[lbColour];
  lbImg.src = src(p, c);
  lbImg.alt = `${p.title} ${p.type.toLowerCase()} in ${c.name} — front and back`;
  lbCap.innerHTML =
    `<strong>${h(p.type)} · ${p.n ? "Design " + p.n + " · " : ""}${h(p.title)}</strong>` +
    ` &nbsp;<span>${h(c.name)}${c.adultOnly ? " — adult sizes only" : ""}</span>`;
}
__LIGHTBOX_JS__

setFilter("all");
</script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Per-design page
# --------------------------------------------------------------------------

DESIGN_BODY = r"""
<header class="site-header">
  <div class="header-inner">
    <div class="header-text">
      <a class="back" href="../index.html">&#8249;&nbsp; All designs</a>
      <span class="eyebrow">__KICKER__</span>
      <h1>__DESIGN_TITLE__</h1>
      <p>__COLOUR_COUNT__ colours, front and back. Click any image to enlarge it,
         then use the arrows to move between colours.</p>
    </div>
    <img class="logo" src="../__LOGO__" alt="Stafford Shotokan Karate club logo">
  </div>
</header>

<main class="wrap">
  <div class="design-intro">
    <div class="sizes">
      __SIZE_ROWS__
    </div>
    <a class="btn" href="../index.html">&#8249;&nbsp; Back to all designs</a>
  </div>

  __ADULT_NOTE__

  <div class="colour-grid">
    __TILES__
  </div>
</main>
__FOOTER__
__LIGHTBOX__
<script>
const DESIGN = __DATA__;

const src = c =>
  "../" + DESIGN.path.split("/").map(encodeURIComponent).join("/") + "/" +
  encodeURIComponent(c.file) + ".png";

document.querySelectorAll(".btn-enlarge").forEach(btn => {
  btn.addEventListener("click", () => openLb(0, +btn.dataset.colour, btn));
});

const lbColoursFor = () => DESIGN.colours;
const onLbStep = () => {};
function paintLb(){
  const c = DESIGN.colours[lbColour];
  lbImg.src = src(c);
  lbImg.alt = `${DESIGN.title} ${DESIGN.type.toLowerCase()} in ${c.name} — front and back`;
  lbCap.innerHTML =
    `<strong>${DESIGN.type} · ${DESIGN.n ? "Design " + DESIGN.n + " · " : ""}${DESIGN.title}</strong>` +
    ` &nbsp;<span>${c.name}${c.adultOnly ? " — adult sizes only" : ""}</span>`;
}
__LIGHTBOX_JS__
</script>
</body>
</html>
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def url_path(path):
    from urllib.parse import quote
    return "/".join(quote(seg, safe="") for seg in path.split("/"))


def design_page(p):
    tiles = []
    for ci, c in enumerate(p["colours"]):
        img = f'../{url_path(p["path"])}/{url_path(c["file"])}.png'
        tag = ('<span class="tag">Adult sizes only</span>' if c["adultOnly"] else "")
        tiles.append(f"""
    <article class="colour-card">
      <div class="colour-bar">
        <span class="dot" style="background:{c['hex']}" aria-hidden="true"></span>
        <h2>{esc(c['name'])}</h2>
        {tag}
      </div>
      <div class="shot">
        <img src="{img}" width="{p['w']}" height="{p['h']}"
             loading="lazy" decoding="async"
             alt="{esc(p['title'])} {esc(p['type'].lower())} in {esc(c['name'])} — front and back">
        <button class="btn btn-enlarge" type="button" data-colour="{ci}"
                aria-label="Click to enlarge {esc(c['name'])}">Click to Enlarge</button>
      </div>
      <p class="views">Front &nbsp;·&nbsp; Back</p>
    </article>""")

    note = adult_note(p["colours"])

    kicker = p["type"] + (f" · Design {p['n']}" if p["n"] else "")
    title = f"{p['title']} — {p['type']} — Stafford Shotokan Karate"

    body = (DESIGN_BODY
            .replace("__KICKER__", esc(kicker))
            .replace("__DESIGN_TITLE__", esc(p["title"]))
            .replace("__COLOUR_COUNT__", str(len(p["colours"])))
            .replace("__LOGO__", LOGO)
            .replace("__SIZE_ROWS__", size_rows())
            .replace("__ADULT_NOTE__", note)
            .replace("__TILES__", "\n".join(tiles))
            .replace("__FOOTER__", FOOTER)
            .replace("__LIGHTBOX__", LIGHTBOX_HTML)
            .replace("__LIGHTBOX_JS__", LIGHTBOX_JS)
            .replace("__DATA__", json.dumps(p, ensure_ascii=False, indent=2)))
    return head(title) + body


# --------------------------------------------------------------------------

def main():
    print("Scanning...")
    products = scan()
    if not products:
        sys.exit("No product folders found.")

    # Store front ----------------------------------------------------------
    index = head(SITE_TITLE) + (
        INDEX_BODY
        .replace("__EYEBROW__", EYEBROW)
        .replace("__TITLE__", SITE_TITLE)
        .replace("__LOGO__", LOGO)
        .replace("__ADULT_NOTE__",
                 adult_note([c for p in products for c in p["colours"]]))
        .replace("__FOOTER__", FOOTER)
        .replace("__LIGHTBOX__", LIGHTBOX_HTML)
        .replace("__LIGHTBOX_JS__", LIGHTBOX_JS)
        .replace("${SIZE_ROWS}", size_rows())
        .replace("__KIDS__", json.dumps(KIDS_SIZES, ensure_ascii=False))
        .replace("__ADULT__", json.dumps(ADULT_SIZES, ensure_ascii=False))
        .replace("__DATA__", json.dumps(products, ensure_ascii=False, indent=2)))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(index)

    # Design pages ---------------------------------------------------------
    os.makedirs(DESIGN_DIR, exist_ok=True)
    wanted = set()
    for p in products:
        name = p["slug"] + ".html"
        wanted.add(name)
        with open(os.path.join(DESIGN_DIR, name),
                  "w", encoding="utf-8", newline="\n") as f:
            f.write(design_page(p))

    # Clear out pages for designs that no longer exist.
    for stale in sorted(set(os.listdir(DESIGN_DIR)) - wanted):
        if not stale.endswith(".html"):
            continue
        try:
            os.remove(os.path.join(DESIGN_DIR, stale))
            print(f"  removed stale page: designs/{stale}")
        except OSError as e:
            print(f"  ! could not remove designs/{stale}: {e}")

    by_type = {}
    for p in products:
        by_type.setdefault(p["type"], []).append(p)
    print(f"\nWrote index.html + {len(products)} pages in designs/")
    for t, items in by_type.items():
        print(f"  {t}: {len(items)} designs, "
              f"{sum(len(i['colours']) for i in items)} images")


if __name__ == "__main__":
    main()
