"""Greenness keyer for dull / uneven green screens where chroma-distance keys eat skin and hair.

alpha = 0 where (G - max(R, B)) >= HI, 1 where <= LO, linear in between; light edge blur;
green spill removed by capping G at max(R, B) on semi-transparent and edge pixels.
Rows above GARBAGE_Y (wall above the screen) are always transparent.

Normally driven by key.py (test / run --greenness LO HI GARBAGE_Y). Approved defaults: LO 6, HI 16.
Usage (stream): ffmpeg ... -f rawvideo -pix_fmt rgb24 - | greenness_key.py W H LO HI GARBAGE_Y | ffmpeg -f rawvideo -pix_fmt rgba ...
Usage (single frame): greenness_key.py --test in.png out.png LO HI GARBAGE_Y
"""
import sys

import numpy as np


def key(rgb: np.ndarray, lo: float, hi: float, garbage_y: int) -> np.ndarray:
    f = rgb.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    greenness = g - np.maximum(r, b)
    alpha = np.clip((hi - greenness) / (hi - lo), 0.0, 1.0)
    # soften the matte edge by one pixel (cheap 3x3 box blur on alpha only)
    pad = np.pad(alpha, 1, mode="edge")
    alpha = sum(pad[dy : dy + alpha.shape[0], dx : dx + alpha.shape[1]] for dy in range(3) for dx in range(3)) / 9.0
    alpha[:garbage_y] = 0.0
    # despill: wherever green exceeds red/blue, pull it down to their max
    g2 = np.minimum(g, np.maximum(r, b) + 4)
    out = np.dstack([r, g2, b, alpha * 255.0])
    return np.clip(out, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    if sys.argv[1] == "--test":
        from PIL import Image

        src, dst, lo, hi, gy = sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6])
        rgb = np.asarray(Image.open(src).convert("RGB"))
        Image.fromarray(key(rgb, lo, hi, gy)).save(dst)
        sys.exit()
    w, h, lo, hi, gy = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
    size = w * h * 3
    inp, out = sys.stdin.buffer, sys.stdout.buffer
    while True:
        buf = inp.read(size)
        if len(buf) < size:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        out.write(key(frame, lo, hi, gy).tobytes())
