"""Align script words to Whisper word timings inside the kept segments.

Usage: align.py words.json segments.json script.txt aligned.json

words.json: Whisper words on the RAW clip (or the edited voice with an identity segments file).
segments.json: [{"src0", "src1"}, ...] raw seconds in playback order; "out" is filled in and saved back.
aligned.json: [{"t0", "t1", "text", "matched"}] edited-timeline seconds, one per script word.
Unmatched script words are interpolated between neighbours and listed as runs (missing or misheard narration).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_core as al  # noqa: E402
import kitcfg  # noqa: E402

words_path, seg_path, script_path, out_path = sys.argv[1:5]
raw = kitcfg.load(words_path)
segs = kitcfg.load(seg_path)
script_words = open(script_path, encoding="utf-8").read().split()

# Transcript words inside kept segments, mapped onto the edited timeline.
kept, out_t = [], 0.0
for s in segs:
    for w in raw:
        mid = (w["start"] + w["end"]) / 2
        if s["src0"] <= mid < s["src1"]:
            kept.append({"t0": out_t + max(0.0, w["start"] - s["src0"]), "t1": out_t + min(s["src1"], w["end"]) - s["src0"], "w": w["word"]})
    s["out"] = round(out_t, 3)
    out_t += s["src1"] - s["src0"]

pairs = al.dp_align(script_words, [k["w"] for k in kept])
out = []
for k, w in enumerate(script_words):
    if k in pairs:
        t = kept[pairs[k]]
        out.append({"t0": round(t["t0"], 3), "t1": round(t["t1"], 3), "text": w, "matched": True})
    else:
        out.append({"t0": None, "t1": None, "text": w, "matched": False})

anchors = [k for k, o in enumerate(out) if o["matched"]]
for k, o in enumerate(out):
    if o["matched"]:
        continue
    prev = max([a for a in anchors if a < k], default=None)
    nxt = min([a for a in anchors if a > k], default=None)
    if prev is None:
        t0, t1, span, pos = 0.0, out[nxt]["t0"], nxt, k
    elif nxt is None:
        t0, t1, span, pos = out[prev]["t1"], out[prev]["t1"] + 0.35 * (len(out) - prev), len(out) - prev, k - prev
    else:
        t0, t1, span, pos = out[prev]["t1"], out[nxt]["t0"], nxt - prev, k - prev
    step = (t1 - t0) / max(1, span)
    o["t0"] = round(t0 + step * (pos - (0 if prev is None else 1)), 3)
    o["t1"] = round(o["t0"] + max(0.12, step * 0.9), 3)

kitcfg.save(out, out_path, indent=0)
kitcfg.save(segs, seg_path, indent=0)

runs, cur = [], []
for k, o in enumerate(out):
    if not o["matched"]:
        cur.append(k)
    elif cur:
        runs.append(cur)
        cur = []
if cur:
    runs.append(cur)
n, m = len(script_words), sum(o["matched"] for o in out)
print(f"script words {n}, transcript words kept {len(kept)}, matched {m} ({m / max(1, n):.0%}), edit length {out_t:.2f}s")
for r in runs:  # every run: 1-2 word misses are often substitutions that flip meaning ("nahi" heard as "rahi")
    print(f"  unmatched {out[r[0]]['t0']:6.2f}s: {' '.join(script_words[i] for i in r)}")
