"""
make_balls.py — WPA-correct ball textures.

WPA sec.16, verbatim: "The object balls numbered 1 through 8 have solid
colors... The object balls numbered 9 through 15 are white with a centered
band of color... Each object ball has its number printed twice, opposite each
other, one of the two numbers upside down, black on a white round background.
The two printed numbers 6 and 9 are underscored."

The previous set got this wrong in three ways: one number instead of two, no
inverted second print, and no underscore on the 6 and the 9 — which is the
only thing telling them apart when a ball is lying either way up.

Equirectangular, sized for a UV sphere: u is longitude, v is latitude, so the
two number discs sit at opposite longitudes on the equator and the stripe is
a band of constant latitude.

    .venv/bin/python make_balls.py   ->  assets/balls9/ball_*.png
"""
import os

from PIL import Image, ImageDraw, ImageFont

import wpa_spec as S

HERE = os.path.dirname(os.path.realpath(__file__))
OUT = os.path.join(HERE, "assets", "balls9")
W, H = 2048, 1024
DISC_R = 150                     # white number background, in pixels
STRIPE_HALF = 0.235              # band half-height in v, centred on equator


def _font(size):
    for path in ("/System/Library/Fonts/Helvetica.ttc",
                 "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                 "/Library/Fonts/Arial.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _srgb(linear):
    """wpa_spec keeps colours linear; textures are read as sRGB."""
    out = []
    for c in linear:
        c = max(0.0, min(1.0, c))
        s = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
        out.append(int(round(s * 255)))
    return tuple(out)


def _number_disc(img, cx, cy, number, flip):
    """A white disc carrying the number, upside down on the second print."""
    d = ImageDraw.Draw(img)
    d.ellipse([cx - DISC_R, cy - DISC_R, cx + DISC_R, cy + DISC_R],
              fill=(255, 255, 255))
    size = 190 if number < 10 else 165
    font = _font(size)
    text = str(number)
    tile = Image.new("RGBA", (DISC_R * 2, DISC_R * 2), (255, 255, 255, 0))
    td = ImageDraw.Draw(tile)
    bbox = td.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = DISC_R - tw / 2 - bbox[0]
    ty = DISC_R - th / 2 - bbox[1] - 6
    td.text((tx, ty), text, font=font, fill=(12, 12, 12, 255))
    if number in S.UNDERSCORED:
        # sec.16: the 6 and the 9 are underscored so they can be told apart
        y = ty + th + 20
        td.line([DISC_R - tw / 2 - 6, y, DISC_R + tw / 2 + 6, y],
                fill=(12, 12, 12, 255), width=13)
    if flip:
        tile = tile.rotate(180)
    img.paste(tile, (int(cx - DISC_R), int(cy - DISC_R)), tile)


def make_ball(number):
    hue = _srgb(S.BALL_HUES[number])
    white = (242, 240, 233)
    if number <= 8:
        img = Image.new("RGB", (W, H), hue)
    else:
        img = Image.new("RGB", (W, H), white)
        d = ImageDraw.Draw(img)
        top = int(H * (0.5 - STRIPE_HALF))
        bot = int(H * (0.5 + STRIPE_HALF))
        d.rectangle([0, top, W, bot], fill=hue)
    # two prints, opposite each other, the second one inverted (sec.16)
    for i, u in enumerate((0.25, 0.75)):
        _number_disc(img, u * W, H * 0.5, number, flip=(i == 1))
    return img


def make_cue():
    img = Image.new("RGB", (W, H), _srgb(S.CUE_BALL_RGB))
    d = ImageDraw.Draw(img)
    for u in (0.25, 0.75):
        d.ellipse([u * W - 26, H * 0.5 - 26, u * W + 26, H * 0.5 + 26],
                  fill=(196, 32, 32))          # measle spots, for spin reading
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for n in range(1, 16):
        make_ball(n).save(os.path.join(OUT, "ball_%d.png" % n))
    make_cue().save(os.path.join(OUT, "ball_cue.png"))
    print("wrote 16 textures to %s" % OUT)
    print("  solids 1-8, stripes 9-15 (centred band), two prints each,")
    print("  second inverted, %s underscored" % (", ".join(
        str(x) for x in S.UNDERSCORED)))


if __name__ == "__main__":
    main()
