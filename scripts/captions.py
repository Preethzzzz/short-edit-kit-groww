"""Export the English captions of a job as SRT and WebVTT (edited timeline), e.g. for a YouTube upload.
Usage: captions.py JOB_DIR [--edit work/edit.json] [--out out/captions]
Captions are written into plan.json by the editor and resolved to seconds by build_plan.py (edit.json).
Writes OUT.srt and OUT.vtt. Prints one summary line: count, coverage, longest line, gaps and overlaps.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402


def ts(sec: float, sep: str) -> str:
    ms = int(round(max(sec, 0) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}{sep}{ms % 1000:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--edit", default="work/edit.json")
    ap.add_argument("--out", default="out/captions")
    a = ap.parse_args()
    edit = kitcfg.load(os.path.join(a.job, a.edit))
    caps = edit.get("captions", [])
    if not caps:
        sys.exit(f"no captions in {a.edit}: add them to plan.json and run build_plan")
    out = os.path.join(a.job, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    srt, vtt = [], ["WEBVTT", ""]
    for n, c in enumerate(caps, 1):
        srt += [str(n), f"{ts(c['from'], ',')} --> {ts(c['to'], ',')}", c["text"], ""]
        vtt += [f"{ts(c['from'], '.')} --> {ts(c['to'], '.')}", c["text"], ""]
    open(out + ".srt", "w", encoding="utf-8").write("\n".join(srt))
    open(out + ".vtt", "w", encoding="utf-8").write("\n".join(vtt))
    shown = sum(c["to"] - c["from"] for c in caps)
    overlaps = sum(1 for p, c in zip(caps, caps[1:]) if c["from"] < p["to"] - 1e-3)
    gaps = sum(1 for p, c in zip(caps, caps[1:]) if c["from"] - p["to"] > 1.0)
    longest = max(len(c["text"]) for c in caps)
    print(f"{out}.srt/.vtt: {len(caps)} captions, {shown:.1f}s of {edit['duration']:.1f}s shown, longest {longest} chars, "
          f"{gaps} gaps over 1 s, {overlaps} overlaps")


if __name__ == "__main__":
    main()
