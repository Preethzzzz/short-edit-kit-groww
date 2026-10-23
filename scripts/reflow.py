"""Re-wrap a wide news-clipping screenshot into shorter stacked lines, splitting only at word gaps.

Usage: python reflow.py in.png out.png max_width
Pixels are copied as-is (no retyping), so the clipping stays a faithful screenshot.
"""
import sys

import numpy as np
from PIL import Image

src, dst, max_w = sys.argv[1], sys.argv[2], int(sys.argv[3])
im = Image.open(src).convert("RGB")
dark = np.asarray(im.convert("L")) < 160

rows = dark.any(axis=1)
lines, y = [], 0
while y < len(rows):
    if rows[y]:
        y0 = y
        while y < len(rows) and rows[y]:
            y += 1
        lines.append((y0, y))
    y += 1

pad = 10
pieces = []
for y0, y1 in lines:
    cols = dark[y0:y1].any(axis=0)
    xs = np.where(cols)[0]
    x0, x1 = xs[0], xs[-1] + 1
    # word gaps: runs of empty columns at least ~22% of the line height wide
    min_gap = max(6, int((y1 - y0) * 0.22))
    gaps, x = [], x0
    while x < x1:
        if not cols[x]:
            g0 = x
            while x < x1 and not cols[x]:
                x += 1
            if x - g0 >= min_gap:
                gaps.append((g0 + x) // 2)
        x += 1
    cuts, start = [], x0
    while x1 - start > max_w:
        cand = [g for g in gaps if start < g <= start + max_w]
        if not cand:
            break
        cuts.append(cand[-1])
        start = cand[-1]
    edges = [x0] + cuts + [x1]
    for k, (a, b) in enumerate(zip(edges, edges[1:])):
        # Pad only the true line ends; inner edges sit exactly on a word-gap midpoint.
        left = max(0, a - pad) if k == 0 else a
        right = min(im.width, b + pad) if k == len(edges) - 2 else b
        pieces.append(im.crop((left, max(0, y0 - pad), right, min(im.height, y1 + pad))))

out_w = max(p.width for p in pieces)
line_gap = 14
out_h = sum(p.height for p in pieces) + line_gap * (len(pieces) - 1)
out = Image.new("RGB", (out_w, out_h), "white")
yy = 0
for p in pieces:
    out.paste(p, (0, yy))
    yy += p.height + line_gap
out.save(dst)
print(f"{dst}: {out.size[0]}x{out.size[1]}, {len(pieces)} lines")
