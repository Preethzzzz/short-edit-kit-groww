"""Un-mixing keyer for yellow-green dull screens and long hair, where greenness_key.py leaves an olive fringe.

Greenness is measured relative to brightness (lo/hi in %), so the screen in the shadow of the hair keys out too;
the screen colour is un-mixed from partly transparent pixels, then an average despill pulls wisps back to brown.
Rows above GARBAGE_Y (wall above the screen) are always transparent. Breakout Short (29 Oct 2026): lo 2, hi 18.

Normally driven by key.py (test / run --greenness LO HI GARBAGE_Y --unmix).
Usage (stream): ffmpeg ... -f rawvideo -pix_fmt rgb24 - | unmix_key.py W H LO HI GARBAGE_Y | ffmpeg -f rawvideo -pix_fmt rgba ...
Usage (single frame): unmix_key.py --test in.png out.png LO HI GARBAGE_Y
"""
import sys

import numpy as np


def key(rgb: np.ndarray, lo: float, hi: float, garbage_y: int) -> np.ndarray:
    f = rgb.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    # greenness relative to brightness, so the screen in the shadow of the hair keys out too (lo/hi in %)
    greenness = 100.0 * (g - np.maximum(r, b)) / np.maximum(g, 40.0)
    alpha = np.clip((hi - greenness) / (hi - lo), 0.0, 1.0)
    # soften the matte edge by one pixel (cheap 3x3 box blur on alpha only)
    pad = np.pad(alpha, 1, mode="edge")
    alpha = sum(pad[dy : dy + alpha.shape[0], dx : dx + alpha.shape[1]] for dy in range(3) for dx in range(3)) / 9.0
    alpha[:garbage_y] = 0.0
    # un-mix the screen colour from partly transparent pixels (hair strands): F = (C - (1-a)S) / a
    bg = alpha < 0.02
    S = np.median(f[bg], axis=0) if bg.sum() > 1000 else np.array([131.0, 155.0, 77.0])
    a3 = np.maximum(alpha, 0.15)[..., None]
    fg = (f - (1.0 - a3) * S) / a3
    fg = np.where((alpha > 0.98)[..., None], f, fg)
    r, g, b = fg[..., 0], fg[..., 1], fg[..., 2]
    # despill: wherever green exceeds red/blue, pull it down to their max
    g2 = np.minimum(g, (r + b) / 2.0 + 4)  # average despill: also pulls the yellow-green wisps back to brown
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
