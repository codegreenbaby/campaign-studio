"""Map a photo onto a two-colour ramp (shadow -> highlight) and darken it, so it reads as texture.

  .venv/Scripts/python tools/duotone.py IN OUT --dark "#07060B" --light "#7B3FE4" --gamma 1.6 --max 0.55

--gamma > 1 pushes mid-tones down; --max caps the brightest output (0..1 of the light colour).
"""
import argparse
from PIL import Image, ImageOps


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--dark", default="#07060B"); ap.add_argument("--light", default="#7B3FE4")
    ap.add_argument("--gamma", type=float, default=1.6); ap.add_argument("--max", type=float, default=0.55)
    ap.add_argument("--width", type=int, default=2000)
    a = ap.parse_args()
    im = Image.open(a.src).convert("L")
    if im.width > a.width:
        im = im.resize((a.width, round(im.height * a.width / im.width)), Image.LANCZOS)
    lut = [round(255 * a.max * (i / 255) ** a.gamma) for i in range(256)]
    im = im.point(lut)
    out = ImageOps.colorize(im, black=hex_rgb(a.dark), white=hex_rgb(a.light))
    out.save(a.dst, quality=88, optimize=True, progressive=True)
    print(a.dst, out.size)


if __name__ == "__main__":
    main()
