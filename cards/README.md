# Squarespace product cards

One image per design, each showing the front and back plus every colour it
comes in, with sizes and the adult-only colours noted. Rebuild them any time
with `python build-cards.py`.

## Putting them on the site

1. In Squarespace, open the clothing page and click **Edit**.
2. Add a section, choose **Images**, then a **Grid** gallery (a gallery block
   in a page works too).
3. Upload the `t-shirts-*.jpg` files. They are numbered, so they land in
   design order.
4. In the gallery's design settings set the aspect ratio to **4:5** (or
   "Original") so nothing is cropped, and turn **Lightbox** on so members can
   tap a card to see it full size.
5. Repeat with a second gallery for the `hoodies-*.jpg` files.
6. Optional: paste each card's title and description from
   [captions.md](captions.md) into the image settings. This helps search and
   screen readers; the card itself already shows everything.

To update later, re-run the script and replace the changed images in the
gallery.
