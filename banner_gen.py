#!/usr/bin/env python3
"""
img2braille2.py - sharp braille art.

What's new in v2:
  - CLAHE (local contrast): dark areas no longer collapse into solid blocks
  - unsharp mask: defined edges before dithering
  - --mode combo: forced outlines over shading -> "sharp"
  - --dither bayer: regular noise, much cleaner than Floyd-Steinberg
  - --color: 24-bit braille in Windows Terminal (the biggest leap in quality)
  - --bg dark|light: correct polarity for your terminal

Typical usage:
    python img2braille2.py photo.jpg -w 150 --mode combo --color
    python img2braille2.py photo.jpg -w 180 --dither bayer --clahe 3.0

Dependencies: pillow, numpy
"""

import argparse
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

DOT_BITS = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
], dtype=np.float32)


# --------------------------------------------------------------------------
# preparazione
# --------------------------------------------------------------------------

def load_rgb(path):
    img = Image.open(path)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
    return img.convert("RGB")


def target_size(size, char_width, font_aspect):
    """Cella braille = 2x4 punti; cella di testo alta font_aspect volte la
    larghezza. I punti risultano quadrati solo se compensi."""
    w, h = size
    px_w = char_width * 2
    px_h = px_w * (h / w) * (4.0 / (2.0 * font_aspect))
    px_h = max(4, int(round(px_h / 4)) * 4)
    return px_w, px_h


# --------------------------------------------------------------------------
# contrasto locale
# --------------------------------------------------------------------------

def clahe(a, clip=2.0, tiles=8):
    """Contrast Limited Adaptive Histogram Equalization, solo numpy.
    a: array uint8. Ritorna uint8."""
    if clip <= 0:
        return a
    h, w = a.shape
    ty = tx = tiles
    th = -(-h // ty)
    tw = -(-w // tx)
    pad = np.pad(a, ((0, ty * th - h), (0, tx * tw - w)), mode="edge")

    maps = np.empty((ty, tx, 256), dtype=np.float32)
    limit = max(1.0, clip * (th * tw) / 256.0)
    for i in range(ty):
        for j in range(tx):
            tile = pad[i * th:(i + 1) * th, j * tw:(j + 1) * tw]
            hist = np.bincount(tile.ravel(), minlength=256).astype(np.float32)
            excess = np.maximum(hist - limit, 0).sum()
            hist = np.minimum(hist, limit) + excess / 256.0
            cdf = np.cumsum(hist)
            cdf = (cdf - cdf[0]) / max(cdf[-1] - cdf[0], 1e-6) * 255.0
            maps[i, j] = cdf

    # interpolazione bilineare fra i centri dei tile
    yy = np.arange(h, dtype=np.float32) / th - 0.5
    xx = np.arange(w, dtype=np.float32) / tw - 0.5
    i0 = np.clip(np.floor(yy).astype(int), 0, ty - 1)
    j0 = np.clip(np.floor(xx).astype(int), 0, tx - 1)
    i1 = np.clip(i0 + 1, 0, ty - 1)
    j1 = np.clip(j0 + 1, 0, tx - 1)
    wy = np.clip(yy - np.floor(yy), 0, 1)[:, None]
    wx = np.clip(xx - np.floor(xx), 0, 1)[None, :]

    v = a
    def look(ii, jj):
        return maps[ii[:, None], jj[None, :], v]

    out = (look(i0, j0) * (1 - wy) * (1 - wx) +
           look(i0, j1) * (1 - wy) * wx +
           look(i1, j0) * wy * (1 - wx) +
           look(i1, j1) * wy * wx)
    return np.clip(out, 0, 255).astype(np.uint8)


def sobel_mag(a):
    a = a.astype(np.float32)
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    p = np.pad(a, 1, mode="edge")
    gx = sum(kx[i, j] * p[i:i + a.shape[0], j:j + a.shape[1]]
             for i in range(3) for j in range(3))
    gy = sum(kx.T[i, j] * p[i:i + a.shape[0], j:j + a.shape[1]]
             for i in range(3) for j in range(3))
    m = np.hypot(gx, gy)
    return m / m.max() * 255.0 if m.max() > 0 else m


# --------------------------------------------------------------------------
# dithering
# --------------------------------------------------------------------------

def dither_bayer(a):
    h, w = a.shape
    t = np.tile(BAYER8, (-(-h // 8), -(-w // 8)))[:h, :w]
    t = (t + 0.5) / 64.0 * 255.0
    return a.astype(np.float32) > t


def dither_fs(a):
    return np.asarray(Image.fromarray(a, mode="L").convert("1"), dtype=bool)


def dither_none(a, threshold):
    return a >= threshold


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def render(on, rgb=None):
    """on: bool array dei punti accesi. rgb: array HxWx3 per il colore."""
    h, w = on.shape
    lines = []
    for y in range(0, h, 4):
        row = []
        for x in range(0, w, 2):
            code = 0
            for (dx, dy), bit in DOT_BITS.items():
                yy, xx = y + dy, x + dx
                if yy < h and xx < w and on[yy, xx]:
                    code |= bit
            ch = chr(0x2800 + code)
            if rgb is not None and code:
                cell_on = on[y:y + 4, x:x + 2]
                cell_px = rgb[y:y + 4, x:x + 2]
                sel = cell_px[cell_on[:cell_px.shape[0], :cell_px.shape[1]]]
                if len(sel):
                    r, g, b = sel.mean(axis=0).astype(int)
                    ch = f"\x1b[38;2;{r};{g};{b}m{ch}"
            row.append(ch)
        line = "".join(row)
        if rgb is not None:
            line += "\x1b[0m"
        lines.append(line)
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("-w", "--width", type=int, default=150)
    ap.add_argument("-o", "--out")
    ap.add_argument("--mode", choices=["tone", "edges", "combo"], default="combo",
                    help="combo = chiaroscuro + contorni forzati (piu' nitido)")
    ap.add_argument("--dither", choices=["fs", "bayer", "none"], default="fs")
    ap.add_argument("--threshold", type=int, default=128)
    ap.add_argument("--clahe", type=float, default=2.0,
                    help="forza del contrasto locale, 0 per disattivarlo")
    ap.add_argument("--tiles", type=int, default=8)
    ap.add_argument("--sharpen", type=float, default=1.2,
                    help="unsharp mask, 0 per disattivarlo")
    ap.add_argument("--edge-strength", type=float, default=80.0,
                    help="percentile: piu' alto = meno contorni (default 80)")
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--bg", choices=["dark", "light"], default="dark",
                    help="dark: i punti accesi sono chiari (terminale scuro)")
    ap.add_argument("--color", action="store_true",
                    help="colore ANSI 24 bit per cella")
    ap.add_argument("--font-aspect", type=float, default=2.0)
    args = ap.parse_args()

    src = load_rgb(args.image)
    size = target_size(src.size, args.width, args.font_aspect)
    src = src.resize(size, Image.LANCZOS)

    gray = src.convert("L")
    if args.sharpen > 0:
        gray = gray.filter(ImageFilter.UnsharpMask(
            radius=1.5, percent=int(args.sharpen * 100), threshold=2))
    a = np.asarray(gray, dtype=np.uint8)

    if args.clahe > 0:
        a = clahe(a, clip=args.clahe, tiles=args.tiles)
    else:
        a = np.asarray(ImageOps.autocontrast(Image.fromarray(a), cutoff=2))

    if abs(args.gamma - 1.0) > 1e-6:
        a = np.clip(((a / 255.0) ** (1.0 / args.gamma)) * 255, 0, 255).astype(np.uint8)

    edges = None
    if args.mode in ("edges", "combo"):
        m = sobel_mag(np.asarray(gray, dtype=np.uint8))
        edges = m >= np.percentile(m, args.edge_strength)

    if args.mode == "edges":
        on = edges
    else:
        if args.dither == "bayer":
            bright = dither_bayer(a)
        elif args.dither == "fs":
            bright = dither_fs(a)
        else:
            bright = dither_none(a, args.threshold)
        # su fondo scuro accendiamo i pixel chiari, su fondo chiaro gli scuri
        on = bright if args.bg == "dark" else ~bright
        if edges is not None:
            on = on | edges

    rgb = np.asarray(src, dtype=np.uint8) if args.color else None
    lines = render(on, rgb)
    text = "\n".join(lines)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Scritto {args.out}: {len(lines)} righe", file=sys.stderr)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
