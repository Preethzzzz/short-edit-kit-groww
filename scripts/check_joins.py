"""Verify every cut: re-transcribe the joined audio around each join in the edited voice.

Usage: check_joins.py voice.m4a segments.json [--lang hi] [--window 1.6] [--only 3,7]
One line per join: edited time, raw times on both sides, and what Whisper hears across the join.
A clean cut reads as the script with no clipped or doubled word.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402

SR = 16000
ap = argparse.ArgumentParser()
ap.add_argument("voice")
ap.add_argument("segments")
ap.add_argument("--lang", default="hi")
ap.add_argument("--window", type=float, default=1.6)
ap.add_argument("--only", default="")
a = ap.parse_args()

from faster_whisper import WhisperModel  # noqa: E402
from faster_whisper.audio import decode_audio  # noqa: E402

segs = kitcfg.load(a.segments)
t, joins = 0.0, []
for i, s in enumerate(segs):
    if i:
        joins.append((i, t, segs[i - 1]["src1"], s["src0"]))
    t += s["src1"] - s["src0"]
only = {int(x) for x in a.only.split(",") if x}
model = WhisperModel(kitcfg.cfg()["model"], device="cpu", compute_type="int8")
audio = decode_audio(a.voice, sampling_rate=SR)
for i, at, r1, r0 in joins:
    if only and i not in only:
        continue
    piece = audio[int(max(0, at - a.window) * SR) : int((at + a.window) * SR)]
    out, _ = model.transcribe(piece, language=a.lang, beam_size=5, vad_filter=False)
    text = " ".join(s.text.strip() for s in out)
    print(f"#{i:<3} {at:7.2f}s  raw {r1:7.2f}|{r0:<7.2f}  {text}")
print(f"{len(joins)} joins")
