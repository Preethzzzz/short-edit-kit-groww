"""Deterministic QA of a finished job (files only). Writes work/qa_checks.md, prints PASS/FAIL counts.

Usage: qa_check.py JOB_DIR [--voice-words work/words_qa.json]

Checks:
  numbers   every number shown on screen (cue props, end card) appears in the script or work/facts.txt
  checks    plan.checks arithmetic ({"expr": "99*151", "equals": "14949"} or "atLeast"), parsed safely, no eval
  captions  numbers in each English caption = numbers in its Hinglish span; timing inside the video; no overlap; length
  audio     (with --voice-words: a fresh transcript of out voice) each caption window has speech that matches its span
  layout    nothing in the header band; captions inside the safe zone; cards inside the card area
  timing    cues inside the video; no stretch over brand pacing.failStaticSec (FAIL) / maxStaticSec (WARN) without a
            card, item, punch-in or framing change; end card + RA present
  audio-out loudness of out/final.mp4 within 1 LU of the brand target, true peak under the ceiling (needs the render)
"""
import argparse
import ast
import operator
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_core as al  # noqa: E402
import kitcfg  # noqa: E402

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def norm(n):
    n = n.replace(",", "")
    return n.rstrip("0").rstrip(".") if "." in n else n


def nums(s):
    return {norm(n) for n in NUM.findall(s)}


def strings(x, skip=("src", "icon", "tone")):
    if isinstance(x, dict):
        for k, v in x.items():
            if k in skip or k == "at" or k.endswith("At"):
                continue
            yield from strings(v, skip)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v, skip)
    elif isinstance(x, str):
        yield x


OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def arith(expr):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        raise ValueError("only numbers and + - * / allowed")

    return ev(ast.parse(expr.replace(",", ""), mode="eval"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--voice-words")
    a = ap.parse_args()
    J = os.path.abspath(a.job)
    W = lambda *p: os.path.join(J, "work", *p)  # noqa: E731
    edit, plan = kitcfg.load(W("edit.json")), kitcfg.load(W("plan.json"))
    script = open(W("script.txt"), encoding="utf-8").read()
    allowed = nums(script)
    for extra in ("script_raw.txt", "facts.txt"):
        if os.path.exists(W(extra)):
            allowed |= nums(open(W(extra), encoding="utf-8").read())
    res = []  # (status, area, message)

    for c in edit["cues"]:
        for s in strings(c["props"]):
            for n in nums(s) - allowed:
                res.append(("FAIL", "numbers", f"{c['id']} ({c['component']}): '{n}' in \"{s}\" is not in the script or facts.txt"))
    for chk in plan.get("checks", []):
        try:
            v = arith(chk["expr"])
            if "atLeast" in chk:
                want = float(str(chk["atLeast"]).replace(",", ""))
                ok, exp = v >= want, f">= {chk['atLeast']}"
            else:
                ok, exp = abs(v - float(str(chk["equals"]).replace(",", ""))) < 0.005 + 1e-9 * abs(v), chk["equals"]
            res.append(("PASS" if ok else "FAIL", "checks", f"{chk.get('label', chk['expr'])}: {chk['expr']} = {v:g}, expected {exp}"))
        except (ValueError, SyntaxError, KeyError) as e:
            res.append(("FAIL", "checks", f"bad check {chk}: {e}"))

    dur, caps = edit["duration"], edit["captions"]
    spans = [c for c in plan.get("captions", []) if "span" in c]
    if len(spans) == len(caps):
        for c, p in zip(caps, spans):
            if nums(p["span"]) != nums(c["text"]):
                res.append(("FAIL", "captions", f"{c['from']:.2f}s numbers differ: \"{p['span']}\" vs \"{c['text']}\""))
    for i, c in enumerate(caps):
        if not (0 <= c["from"] < c["to"] <= dur + 0.01):
            res.append(("FAIL", "captions", f"caption {i} timing {c['from']}-{c['to']} outside 0-{dur}"))
        if i and c["from"] < caps[i - 1]["to"] - 0.01:
            res.append(("FAIL", "captions", f"caption {i} overlaps the previous one"))
        if len(c["text"]) > edit["brand"]["captions"].get("maxChars", 48) * 2:
            res.append(("FAIL", "captions", f"caption {i} too long ({len(c['text'])} chars)"))

    if a.voice_words and len(spans) == len(caps):
        vw = kitcfg.load(a.voice_words)
        for c, p in zip(caps, spans):
            heard = [w["word"] for w in vw if c["from"] - 0.15 <= (w["start"] + w["end"]) / 2 <= c["to"] + 0.15]
            want = p["span"].split()
            pairs = al.dp_align(want, heard)
            r = len(pairs) / max(1, len(want))
            if r < 0.6:
                res.append(("FAIL", "audio", f"{c['from']:.2f}s caption span matched {r:.0%} of heard audio: script \"{p['span']}\" | heard \"{' '.join(heard)}\""))
        res.append(("PASS", "audio", f"{len(caps)} caption windows compared with a fresh transcript"))

    L = edit["brand"]["layout"]
    if L["captionTop"] < L["headerBandBottom"] or L["captionTop"] + 140 > L["safe"]["bottom"]:
        res.append(("FAIL", "layout", f"caption top {L['captionTop']} outside the safe zone"))
    if L["cardTop"] < L["headerBandBottom"]:
        res.append(("FAIL", "layout", f"card top {L['cardTop']} inside the header band (0-{L['headerBandBottom']})"))
    for c in edit["cues"]:
        if not (0 <= c["from"] < c["to"] <= dur + 0.01):
            res.append(("FAIL", "timing", f"cue {c['id']} {c['from']}-{c['to']} outside 0-{dur}"))
    def at_times(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if (k == "at" or k.endswith("At")) and isinstance(v, (int, float)):
                    yield float(v)
                else:
                    yield from at_times(v)
        elif isinstance(x, list):
            for v in x:
                yield from at_times(v)

    items = {t for c in edit["cues"] for t in at_times(c["props"]) if c["from"] <= t <= c["to"]}
    marks = sorted({0.0, dur} | items | {p["from"] for p in edit.get("punches", [])} | {c["from"] for c in edit["cues"]} | {c["to"] for c in edit["cues"]} | {s["out"] for s in edit["segments"]} | {t["from"] for t in edit.get("talk", [])})
    pc = edit["brand"].get("pacing", {"maxStaticSec": 4.0, "failStaticSec": 6.0})
    for x, y in zip(marks, marks[1:]):
        if y - x > pc["failStaticSec"]:
            res.append(("FAIL", "timing", f"{x:.1f}-{y:.1f}s: {y - x:.1f}s with no card, item, punch-in or framing change (brand: nothing static over 5 s)"))
        elif y - x > pc["maxStaticSec"]:
            res.append(("WARN", "timing", f"{x:.1f}-{y:.1f}s: {y - x:.1f}s with no change (brand: change every 2-4 s)"))
    video = os.path.join(J, "out", "final.mp4")
    if os.path.exists(video):
        import json as _json
        import subprocess

        au = kitcfg.brand(kitcfg.load(os.path.join(J, "job.json")).get("brand", "") if os.path.exists(os.path.join(J, "job.json")) else "")["audio"]
        txt = subprocess.run([kitcfg.ffmpeg(), "-hide_banner", "-i", video, "-vn", "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
        m = _json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", txt)[-1])
        li, tp = float(m["input_i"]), float(m["input_tp"])
        ok = abs(li - au["lufs"]) <= 1.0 and tp <= au["truePeak"] + 0.3
        res.append(("PASS" if ok else "FAIL", "audio-out", f"final.mp4 loudness {li:.1f} LUFS (target {au['lufs']}), true peak {tp:.1f} dBTP (ceiling {au['truePeak']})"))
    ec = edit.get("endCard")
    if not ec or "{" in ec["ra"] or not ec["text"]:
        res.append(("FAIL", "compliance", "end card / RA line missing or unfilled"))

    fails = [r for r in res if r[0] == "FAIL"]
    out = W("qa_checks.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Automated checks: {'PASS' if not fails else 'FAIL'}\n\n")
        for r in res:
            f.write(f"- **{r[0]}** [{r[1]}] {r[2]}\n")
        if not res:
            f.write("- all checks passed\n")
    print(f"{out}: {'PASS' if not fails else 'FAIL'} ({len(fails)} fail, {sum(r[0] == 'WARN' for r in res)} warn, {sum(r[0] == 'PASS' for r in res)} pass)")


if __name__ == "__main__":
    main()
