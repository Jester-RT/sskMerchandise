# Squarespace clothing listing

`snippet.html` is a ready-to-paste listing of every t-shirt and hoodie design.
Each design is a card with a picture, colour dots that swap the picture, and
the sizes. Cards stack one per row on phones and sit side by side on wider
screens. It is plain HTML and CSS with no JavaScript, so it works on every
Squarespace plan.

## Adding it to a page

1. Open `snippet.html`, select everything and copy it.
2. In Squarespace, edit the page, add a **Code** block, and paste.
3. Make sure the block's display option is **HTML** (not Markdown or plain
   code) and save.

The pictures load from GitHub Pages
(`https://jester-rt.github.io/sskMerchandise/squarespace/img/`), so they show
once this folder is on `main`. Check
<https://jester-rt.github.io/sskMerchandise/squarespace/preview.html> to see
the same listing outside Squarespace.

## Updating it

Add or change the PNGs under `T-Shirts/` or `Hoodies/`, run
`python build-squarespace.py`, merge to `main`, then paste the new
`snippet.html` over the old one. If only a picture changed, re-pasting isn't
needed.
