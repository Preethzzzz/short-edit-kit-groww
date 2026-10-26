"""Resolve a JSON edit plan (script phrases) into edit.json (seconds) for the Remotion `Short` composition.

Usage: build_plan.py plan.json edit.json [--aligned aligned.json] [--segments segments.json] [--job job.json]

Anchors (beat `at` / `until`, section `at`, any prop key `at` or ending in `At`, caption `span`):
  "Price band ₹143"                          first occurrence of these script words (start time)
  {"phrase": "poora OFS", "after": "issue size ₹852.18", "edge": "end", "offset": 0.2}
  "start" | "end" | 12.5 (seconds)
Brand values (palette, logo, layout, captions, compliance text) are copied from the brand pack, never from the plan.
Plan switches: "sound": false (no bed/effects, plain voice), "autoPunch": false (no automatic punch-ins).
Prints one line per cue plus warnings; exits 1 if any anchor or component is invalid.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402

CATALOG = kitcfg.load(os.path.join(kitcfg.PLUGIN_ROOT, "templates", "remotion", "components.json"))["components"]
errors, warns = [], []


def tok(x):
    return re.sub(r"[^a-z0-9]", "", x.lower())


class Words:
    def __init__(self, words, duration):
        self.w = words
        self.t = [tok(x["text"]) for x in words]
        self.duration = duration

    def find(self, phrase, after=-1.0, start_idx=0):
        p = [tok(x) for x in phrase.split() if tok(x)]
        hits = [i for i in range(start_idx, len(self.t) - len(p) + 1) if self.t[i : i + len(p)] == p and self.w[i]["t0"] > after]
        return hits, len(p)

    def at(self, a, where=""):
        if isinstance(a, (int, float)):
            return float(a)
        if a == "start":
            return 0.0
        if a == "end":
            return self.duration
        spec = a if isinstance(a, dict) else {"phrase": a}
        after = self.at(spec["after"], where) if "after" in spec else -1.0
        hits, n = self.find(spec["phrase"], after)
        if not hits:
            errors.append(f"{where}: phrase not found in script: {spec['phrase']!r}")
            return 0.0
        if len(hits) > 1 and "after" not in spec:
            warns.append(f"{where}: {spec['phrase']!r} occurs {len(hits)}x, used first ({self.w[hits[0]]['t0']:.2f}s); add \"after\" if wrong")
        i = hits[0]
        t = self.w[i + n - 1]["t1"] if spec.get("edge") == "end" else self.w[i]["t0"]
        return t + float(spec.get("offset", 0))


def resolve_props(x, W, lead, where):
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if (k == "at" or k.endswith("At")) and isinstance(v, (str, dict)):
                out[k] = round(max(0.0, W.at(v, f"{where}.{k}") - lead), 3)
            else:
                out[k] = resolve_props(v, W, lead, f"{where}.{k}")
        return out
    if isinstance(x, list):
        return [resolve_props(v, W, lead, f"{where}[{i}]") for i, v in enumerate(x)]
    return x


def nums(s):
    return {n.replace(",", "").rstrip("0").rstrip(".") if "." in n else n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--aligned")
    ap.add_argument("--segments")
    ap.add_argument("--job")
    a = ap.parse_args()
    plan = kitcfg.load(a.plan)
    job = kitcfg.load(a.job) if a.job else {}
    b = kitcfg.brand(plan.get("brand") or job.get("brand") or "")
    mo = {**b["motion"], **plan.get("timing", {})}  # plan "timing" may set cueLeadSec / itemLeadSec (0 for archived plans in seconds)
    layout = plan.get("layout", "card-top")
    fps = plan.get("fps") or round(job.get("fps") or b["canvas"]["fps"])

    segs = kitcfg.load(a.segments) if a.segments else []
    t = 0.0
    auto_punch = layout == "card-top" and plan.get("autoPunch", True)
    punch = [1.0] if auto_punch else (b["framing"]["alternatePunch"] if layout == "card-top" else [1.0])
    for i, s in enumerate(segs):
        s["out"] = round(t, 3)
        s["punch"] = punch[i % len(punch)]  # alternate framing hides jump cuts
        t += s["src1"] - s["src0"]
    duration = round(t, 3) if segs else float(plan["duration"])
    W = Words(kitcfg.load(a.aligned) if a.aligned else [], duration)

    beats = plan.get("beats", [])
    cues, talk = [], []
    for i, bt in enumerate(beats):
        where = f"beat {bt.get('id', i)}"
        start = W.at(bt["at"], where)
        if "until" in bt:
            end = W.at(bt["until"], where)
        else:
            end = W.at(beats[i + 1]["at"], where) if i + 1 < len(beats) else duration
        if not bt.get("component"):
            talk.append({"from": round(max(0.0, start - mo["cueLeadSec"]), 3), "framing": bt.get("framing", "WIDE")})
            continue
        comp = bt["component"]
        custom = bool(a.job) and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(a.job)), "custom", comp + ".tsx"))
        if custom:
            pass
        elif comp not in CATALOG:
            errors.append(f"{where}: unknown component {comp!r}")
            continue
        missing = [] if custom else [k for k in CATALOG[comp]["required"] if k not in bt.get("props", {})]
        if missing:
            errors.append(f"{where}: {comp} missing props {missing}")
        c0, c1 = max(0.0, start - mo["cueLeadSec"]), min(duration, end - mo["cueLeadSec"])
        if c1 - c0 < 1.0:
            warns.append(f"{where}: only {c1 - c0:.2f}s on screen")
        cues.append({"id": bt.get("id", f"b{i}"), "component": comp, "from": round(c0, 3), "to": round(c1, 3),
                     "source": bt.get("source"), "props": resolve_props(bt.get("props", {}), W, mo["itemLeadSec"], where)})
    for x in plan.get("talk", []):
        talk.append({"from": round(max(0.0, W.at(x["at"], "talk") - mo["cueLeadSec"]), 3), "framing": x.get("framing", "WIDE")})
    talk.sort(key=lambda x: x["from"])

    sections = [{"scene": s["scene"], "from": round(max(0.0, W.at(s["at"], "section") - mo["cueLeadSec"]), 3)} for s in plan.get("sections", [])]
    zooms = [{"from": round(W.at(z["at"], "zoom") - 0.1, 3), "to": round(W.at(z.get("until", "end"), "zoom"), 3), "scale": z.get("scale", b["framing"]["endZoom"])} for z in plan.get("zooms", [])]

    # Captions: English phrase per Hinglish span, matched in order through the script.
    caps, idx = [], 0
    for k, c in enumerate(plan.get("captions", [])):
        if "span" in c:
            hits, n = W.find(c["span"], start_idx=idx)
            if not hits:
                errors.append(f"caption {k}: span not found after word {idx}: {c['span']!r}")
                continue
            i = hits[0]
            if i > idx:
                warns.append(f"caption {k}: script words without caption before it: {' '.join(x['text'] for x in W.w[idx:i])!r}")
            caps.append({"from": W.w[i]["t0"], "to": W.w[i + n - 1]["t1"], "text": c["text"], "speech_to": W.w[i + n - 1]["t1"]})
            if nums(c["span"]) != nums(c["text"]):
                warns.append(f"caption {k}: numbers differ: {sorted(nums(c['span']))} vs {sorted(nums(c['text']))}")
            idx = i + n
        else:
            caps.append({"from": float(c["from"]), "to": float(c["to"]), "text": c["text"], "speech_to": float(c["to"])})
        if len(c["text"]) > b["captions"]["maxChars"] * 2:
            warns.append(f"caption {k}: {len(c['text'])} chars, over two lines")
    if W.w and plan.get("captions") and idx < len(W.w):
        warns.append(f"{len(W.w) - idx} script words after the last caption")
    for k in range(len(caps)):
        nxt = caps[k + 1]["from"] if k + 1 < len(caps) else duration
        sp = caps[k].pop("speech_to")
        caps[k]["to"] = round(nxt if nxt - caps[k]["to"] < 0.6 else caps[k]["to"] + 0.35, 3)
        caps[k]["from"] = round(caps[k]["from"], 3)
        # Word highlight times: English words share the Hinglish phrase's speaking time in proportion to their length.
        ws = caps[k]["text"].split(" ")
        wt = [len(x) + 2 for x in ws]
        t, starts = caps[k]["from"], []
        for x, wl in zip(ws, wt):
            starts.append(round(t, 3))
            t += (sp - caps[k]["from"]) * wl / sum(wt)
        caps[k]["starts"] = starts

    # Auto punch-ins (card-top layout): cut-style framing change at a sentence start every ~3-4.5 s, alternating wide / tight.
    punches = []
    if auto_punch and caps:
        pc = b.get("pacing", {})
        lo, hi = pc.get("punchMinHoldSec", 3.0), pc.get("punchMaxHoldSec", 4.5)
        # Candidates: every caption start (preferred when the previous caption ended a sentence) and every word start.
        cands = []
        for k, c in enumerate(caps):
            sentence = k > 0 and caps[k - 1]["text"].rstrip()[-1:] in ".?!:"
            for j, st in enumerate(c.get("starts", [c["from"]])):
                if st > 0.5:
                    cands.append((st, j == 0 and sentence))
        last, tight = 0.0, False
        for st, sentence in cands:
            gap = st - last
            if gap >= hi or (gap >= lo and sentence):
                tight = not tight
                punches.append({"from": round(st, 3), "scale": b["framing"]["punch"] if tight else 1.0})
                last = st

    channel = plan.get("channel") or job.get("channel") or "ipo-review"
    ch = b["channels"].get(channel, {})
    ra = plan.get("ra", {})
    ra_name, ra_date = ra.get("name") or job.get("raName", ""), ra.get("date") or job.get("raDate", "")
    end_card = None
    if plan.get("endCard"):
        if not ra_name or not ra_date:
            errors.append("endCard: RA name and RA date are required (plan.ra or job.json)")
        end_card = {"from": round(W.at(plan["endCard"]["at"], "endCard"), 3), "text": ch.get("disclaimer", ""),
                    "ra": b["compliance"]["raLine"].format(raName=ra_name, raDate=ra_date)}

    logo = dict(b["logo"])
    for k in ("onLight", "onDark", "icon"):
        logo[k] = "brand/" + os.path.basename(b["logo"][k])
    brand_props = {k: b[k] for k in ("name", "palette", "series", "tones", "fonts", "layout", "motion", "captions", "framing", "compliance")}
    brand_props["logo"] = logo
    pres = plan.get("presenter")
    edit = {
        "fps": fps, "width": b["canvas"]["width"], "height": b["canvas"]["height"], "duration": duration, "layout": layout,
        "brand": brand_props, "theme": b["themes"][plan.get("theme") or b["defaultTheme"]],
        "header": {"tag": ch.get("tag") if b.get("header", {}).get("show", True) else None, "topic": plan.get("header", {}).get("topic")},
        "presenter": {"src": pres["src"], "offset": pres.get("offset", 0)} if pres else None,
        "voice": plan.get("voice"), "mix": "mix.m4a" if plan.get("sound", True) else None, "punches": punches, "segments": segs, "sections": sections, "talk": talk, "cues": cues,
        "captions": caps, "zooms": zooms, "endCard": end_card,
    }
    for w in warns:
        print("warning:", w)
    if errors:
        for e in errors:
            print("ERROR:", e)
        sys.exit(1)
    kitcfg.save(edit, a.out, indent=1)
    for c in cues:
        print(f"{c['from']:7.2f}-{c['to']:7.2f}  {c['component']:13s} {c['id']}")
    print(f"{a.out}: {duration:.2f}s @ {fps}fps, layout {layout}, {len(cues)} cues, {len(sections)} sections, {len(caps)} captions, {len(punches)} punch-ins, {len(warns)} warnings")


if __name__ == "__main__":
    main()
