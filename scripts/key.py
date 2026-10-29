"""Green-screen key + presenter grade -> VP9-alpha webm for Remotion.

Usage:
  key.py sample RAW [--t 3]                     # screen colour + which keyer to use
  key.py test RAW OUT.png [--t 3] (--color 0x95D623 --sim 0.11 --blend 0.05 | --greenness 6 16 GARBAGE_Y)
                                                # 3 strengths side by side on dark, + hole % in the subject area
  key.py run RAW OUT.webm (--color .. --sim .. --blend .. | --greenness LO HI GARBAGE_Y) [--trim A-B] [--no-grade]
  key.py run RAW OUT.mp4 --plain [--trim A-B] [--clean X,Y,W,H ...]
                                                # no green screen: grade only, opaque 1080x1920 H.264;
                                                # --clean paints out wall marks (stickers, switches) in
                                                # raw-pixel boxes with a feathered plate of the fitted wall
                                                # gradient (static camera + plain wall only); use it for
                                                # anything near the logo (brand: logo clear zone)
                                                # (use layout "full"; card-top needs a keyed presenter)

The grade (brand presenterGrade) is applied to the keyed layer only. --trim A-B keeps raw A..B and
writes OUT.json {"offset": A} so segment times stay in raw-clip seconds.
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

FF = kitcfg.ffmpeg()
HERE = os.path.dirname(os.path.abspath(__file__))


def frame(raw, t):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", raw, "-frames:v", "1", tmp], check=True)
    im = np.asarray(Image.open(tmp).convert("RGB"))
    os.unlink(tmp)
    return im


def fps_of(raw):
    import av

    with av.open(raw) as c:
        r = c.streams.video[0].average_rate
    return float(r)


def holes(alpha):
    """Transparent pixels enclosed by the subject (not reachable from the frame edge), as % of the subject area."""
    t = alpha[::4, ::4] < 128
    reach = np.zeros_like(t)
    reach[0, :], reach[-1, :], reach[:, 0], reach[:, -1] = t[0, :], t[-1, :], t[:, 0], t[:, -1]
    while True:
        grow = reach.copy()
        grow[1:] |= reach[:-1]
        grow[:-1] |= reach[1:]
        grow[:, 1:] |= reach[:, :-1]
        grow[:, :-1] |= reach[:, 1:]
        grow &= t
        if (grow == reach).all():
            break
        reach = grow
    subject = (~t).sum()
    return float((t & ~reach).sum() / max(1, subject) * 100)


def chroma_alpha(raw, t, color, sim, blend):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    vf = f"chromakey={color}:{sim}:{blend},despill=type=green,format=rgba"
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", raw, "-frames:v", "1", "-vf", vf, tmp], check=True)
    im = np.asarray(Image.open(tmp).convert("RGBA"))
    os.unlink(tmp)
    return im


def on_dark(rgba):
    a = rgba[..., 3:4] / 255.0
    return (rgba[..., :3] * a + np.array([32, 32, 32]) * (1 - a)).astype(np.uint8)


def wall_plate(raw, boxes, out_png, t=1.0, ring=60, feather=24):
    """Full-frame RGBA plate: inside each box, the wall's smooth gradient (quadratic fit per channel on a
    ring of wall around the box), feathered alpha at the edges, transparent elsewhere."""
    rgb = frame(raw, t).astype(float)
    hh, ww, _ = rgb.shape
    plate = np.zeros((hh, ww, 4))
    for x, y, w, h in boxes:
        x0, y0, x1, y1 = max(0, x - ring), max(0, y - ring), min(ww, x + w + ring), min(hh, y + h + ring)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        inside = (xx >= x) & (xx < x + w) & (yy >= y) & (yy < y + h)
        A = np.stack([np.ones_like(xx), xx, yy, xx * xx, yy * yy, xx * yy], -1).reshape(-1, 6).astype(float)
        A /= np.array([1, ww, hh, ww * ww, hh * hh, ww * hh])
        fit = np.empty((y1 - y0, x1 - x0, 3))
        for ch in range(3):
            v = rgb[y0:y1, x0:x1, ch].reshape(-1)
            coef, *_ = np.linalg.lstsq(A[~inside.reshape(-1)], v[~inside.reshape(-1)], rcond=None)
            fit[..., ch] = (A @ coef).reshape(fit.shape[:2])
        # alpha: 1 inside the box, falling to 0 over `feather` px outside it
        dx = np.maximum(np.maximum(x - xx, xx - (x + w - 1)), 0)
        dy = np.maximum(np.maximum(y - yy, yy - (y + h - 1)), 0)
        alpha = np.clip(1 - np.hypot(dx, dy) / feather, 0, 1)
        region = plate[y0:y1, x0:x1]
        keep = alpha > region[..., 3]
        region[keep, :3] = fit[keep]
        region[keep, 3] = alpha[keep]
    Image.fromarray(np.clip(np.dstack([plate[..., :3], plate[..., 3:] * 255]), 0, 255).astype(np.uint8), "RGBA").save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["sample", "test", "run"])
    ap.add_argument("raw")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--t", type=float, default=3.0)
    ap.add_argument("--color")
    ap.add_argument("--sim", type=float, default=0.11)
    ap.add_argument("--blend", type=float, default=0.05)
    ap.add_argument("--greenness", nargs=3, type=float, metavar=("LO", "HI", "GARBAGE_Y"))
    ap.add_argument("--trim")
    ap.add_argument("--no-grade", action="store_true")
    ap.add_argument("--brand", default="")
    ap.add_argument("--plain", action="store_true", help="footage without a green screen: grade + scale only, no key")
    ap.add_argument("--clean", action="append", default=[], metavar="X,Y,W,H", help="--plain: raw-pixel box to paint out with the fitted wall (repeatable)")
    a = ap.parse_args()

    if a.mode == "sample":
        im = frame(a.raw, a.t).astype(int)
        h, w, _ = im.shape
        strip = np.concatenate([im[int(h * 0.2) : int(h * 0.8), : int(w * 0.08)], im[int(h * 0.2) : int(h * 0.8), -int(w * 0.08) :]], axis=1).reshape(-1, 3)
        g = strip[(strip[:, 1] > strip[:, 0]) & (strip[:, 1] > strip[:, 2])]
        if len(g) < 100:
            sys.exit("no green found at the frame edges; pick another --t")
        med = np.median(g, axis=0).astype(int)
        gn = g[:, 1] - np.maximum(g[:, 0], g[:, 2])
        p10, p50, p90 = np.percentile(gn, [10, 50, 90])
        rec = ("chromakey" if p50 >= 60 and (p90 - p10) < 50 else "greenness (dull/uneven screen)") if p50 >= 15 \
            else "--plain (no green screen in this shot: nothing to key; layout 'full')"
        print(f"{w}x{h} frame, screen colour 0x{med[0]:02X}{med[1]:02X}{med[2]:02X}, greenness p10/p50/p90 {p10:.0f}/{p50:.0f}/{p90:.0f} -> use {rec}")
        return

    if a.mode == "test":
        tiles, notes = [], []
        if a.greenness:
            sys.path.insert(0, HERE)
            from greenness_key import key as gkey

            lo, hi, gy = a.greenness
            rgb = frame(a.raw, a.t)
            for d in (-2, 0, 2):
                rgba = gkey(rgb, lo + d, hi + d, int(gy))
                tiles.append(on_dark(rgba))
                notes.append(f"lo {lo + d:g} hi {hi + d:g}: holes {holes(rgba[..., 3]):.1f}%")
        else:
            for d in (-0.02, 0, 0.02):
                rgba = chroma_alpha(a.raw, a.t, a.color, round(a.sim + d, 3), a.blend)
                tiles.append(on_dark(rgba))
                notes.append(f"sim {a.sim + d:.2f}: holes {holes(rgba[..., 3]):.1f}%")
        sheet = Image.fromarray(np.concatenate(tiles, axis=1))
        sheet.thumbnail((1620, 960))
        sheet.save(a.out)
        print(f"{a.out} (left to right) " + "; ".join(notes) + "  [holes = enclosed transparent % of the subject; want ~0]")
        return

    grade = "" if a.no_grade else kitcfg.brand(a.brand)["presenterGrade"]
    trim = []
    if a.trim:
        t0, t1 = a.trim.split("-")
        trim = ["-ss", t0, "-to", t1]
        kitcfg.save({"offset": float(t0)}, os.path.splitext(a.out)[0] + ".json")
    if a.plain:
        # --clean: one static plate over the raw frame (a fitted, feathered wall fill for each box).
        inputs, graph, cur = ["-i", a.raw], [], "0:v"
        if a.clean:
            plate = os.path.splitext(a.out)[0] + "_clean.png"
            wall_plate(a.raw, [tuple(int(v) for v in c.split(",")) for c in a.clean], plate)
            inputs += ["-loop", "1", "-i", plate]
            graph.append("[0:v][1:v]overlay=0:0:shortest=1[c]")
            cur = "c"
        graph.append(f"[{cur}]scale=1080:1920:flags=lanczos,format=yuv420p" + (f",{grade}" if grade else "") + "[v]")
        start = time.time()
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *trim, *inputs, "-filter_complex", ";".join(graph), "-map", "[v]", "-an", "-c:v", "libx264",
                        "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], check=True)
        print(f"{a.out}: {os.path.getsize(a.out) / 1e6:.0f} MB, plain (no key) in {time.time() - start:.0f}s, grade {'off' if not grade else 'brand'}")
        return
    post = "split[k][a];[a]alphaextract[al];[k]format=yuv420p" + (f",{grade}" if grade else "") + "[g];[g][al]alphamerge,format=yuva420p[v]"
    enc = ["-map", "[v]", "-an", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0", "-row-mt", "1",
           "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", a.out]
    start = time.time()
    if a.greenness:
        lo, hi, gy = a.greenness
        h, w, _ = frame(a.raw, 1.0).shape
        fps = fps_of(a.raw)
        dec = subprocess.Popen([FF, "-hide_banner", "-loglevel", "error", *trim, "-i", a.raw, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        keyer = subprocess.Popen([sys.executable, os.path.join(HERE, "greenness_key.py"), str(w), str(h), str(lo), str(hi), str(int(gy))], stdin=dec.stdout, stdout=subprocess.PIPE)
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-",
                        "-filter_complex", "[0:v]" + post, *enc], stdin=keyer.stdout, check=True)
    else:
        vf = f"[0:v]chromakey={a.color}:{a.sim}:{a.blend},despill=type=green,format=yuva444p," + post
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *trim, "-i", a.raw, "-filter_complex", vf, *enc], check=True)
    mb = os.path.getsize(a.out) / 1e6
    print(f"{a.out}: {mb:.0f} MB, keyed in {time.time() - start:.0f}s, grade {'off' if not grade else 'brand'}")


if __name__ == "__main__":
    main()
