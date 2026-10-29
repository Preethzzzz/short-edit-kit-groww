"""Contact sheet of stills from a render, for review without watching the video.

Usage: stills.py VIDEO OUT.png [--edit edit.json] [--times 1.2,5,9.8] [--cols 5]
Default times: the middle of every cue in edit.json, plus the middle of every gap over 1.5 s between cues
(talk stretches, where only the presenter is on screen), or every 4 s. One PNG, each still labelled with its time.
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("out")
ap.add_argument("--edit")
ap.add_argument("--times")
ap.add_argument("--cols", type=int, default=5)
a = ap.parse_args()

if a.times:
    times = [float(x) for x in a.times.split(",")]
elif a.edit:
    e = kitcfg.load(a.edit)
    cues = sorted(e["cues"], key=lambda c: c["from"])
    times = [round((c["from"] + c["to"]) / 2, 2) for c in cues] or [i * 4.0 for i in range(int(e["duration"] // 4))]
    end = e["endCard"]["from"] if e.get("endCard") else e["duration"]
    last = 0.0
    for c in cues + [{"from": end, "to": end}]:  # talk stretches between cues
        if c["from"] - last > 1.5:
            times.append(round((last + c["from"]) / 2, 2))
        last = max(last, c["to"])
    times.sort()
    if e.get("endCard"):
        times.append(round(e["endCard"]["from"] + 1.0, 2))
else:
    sys.exit("give --edit or --times")

tiles = []
with tempfile.TemporaryDirectory() as d:
    for i, t in enumerate(times):
        p = os.path.join(d, f"{i}.png")
        subprocess.run([kitcfg.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t), "-i", a.video, "-frames:v", "1", "-vf", "scale=270:480", p], check=True)
        im = Image.open(p).convert("RGB")
        ImageDraw.Draw(im).rectangle([0, 0, 70, 22], fill="black")
        ImageDraw.Draw(im).text((4, 4), f"{t:.1f}s", fill="white")
        tiles.append(im)
rows = (len(tiles) + a.cols - 1) // a.cols
sheet = Image.new("RGB", (270 * min(a.cols, len(tiles)), 480 * rows), "white")
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % a.cols) * 270, (i // a.cols) * 480))
sheet.save(a.out)
print(f"{a.out}: {len(tiles)} stills at {', '.join(f'{t:.1f}' for t in times)}")
