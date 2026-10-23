"""Build segments.json (kept pieces of the raw take) from the raw transcript.

Usage: make_segments.py words_raw.json segments.json [--keep A-B,C-D] [--cut A-B,C-D] [--brand groww]

--keep  raw ranges to use, in playback order (the chosen takes). Default: whole clip.
--cut   raw ranges to remove (retakes, extra words, fillers). Applied after --keep.
Pauses longer than brand audio.pauseMaxSec are shortened to audio.pauseKeepSec.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402


def spans(s):
    return [tuple(float(x) for x in p.split("-")) for p in s.split(",") if p.strip()] if s else []


def subtract(ranges, cuts):
    for c0, c1 in cuts:
        nxt = []
        for a, b in ranges:
            if c1 <= a or c0 >= b:
                nxt.append((a, b))
                continue
            if c0 > a:
                nxt.append((a, c0))
            if c1 < b:
                nxt.append((c1, b))
        ranges = nxt
    return ranges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("out")
    ap.add_argument("--keep", default="")
    ap.add_argument("--cut", default="")
    ap.add_argument("--brand", default="")
    a = ap.parse_args()
    aud = kitcfg.brand(a.brand)["audio"]
    pmax, pkeep = aud["pauseMaxSec"], aud["pauseKeepSec"]
    words = kitcfg.load(a.words)
    ranges = spans(a.keep) or [(max(0.0, words[0]["start"] - 0.15), words[-1]["end"] + 0.25)]
    ranges = subtract(ranges, spans(a.cut))

    segs, trimmed, saved = [], 0, 0.0
    for r0, r1 in ranges:
        ws = [w for w in words if r0 <= (w["start"] + w["end"]) / 2 < r1]
        if not ws:
            continue
        s0 = max(r0, ws[0]["start"] - pkeep / 2)
        for w, nx in zip(ws, ws[1:]):
            gap = nx["start"] - w["end"]
            if gap > pmax:
                segs.append({"src0": round(s0, 3), "src1": round(w["end"] + pkeep / 2, 3)})
                s0 = nx["start"] - pkeep / 2
                trimmed += 1
                saved += gap - pkeep
        segs.append({"src0": round(s0, 3), "src1": round(min(r1, ws[-1]["end"] + pkeep / 2), 3)})
    segs = [s for s in segs if s["src1"] - s["src0"] >= 0.05]
    kitcfg.save(segs, a.out, indent=0)
    total = sum(s["src1"] - s["src0"] for s in segs)
    print(f"{a.out}: {len(segs)} segments, {total:.2f}s, {trimmed} pauses trimmed ({saved:.1f}s saved), {len(spans(a.cut))} cuts")


if __name__ == "__main__":
    main()
