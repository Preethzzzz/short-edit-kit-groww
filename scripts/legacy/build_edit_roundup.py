"""Build Remotion edit.json for the 4-IPO Short: cues, background sections, captions, cut segments.

Usage: python build_edit4.py aligned_words.json segments.json out_edit.json
"""
import json
import re
import sys

words = json.load(open(sys.argv[1]))
segs = json.load(open(sys.argv[2]))
out_path = sys.argv[3]
t = 0.0
for i, s in enumerate(segs):
    s["out"] = round(t, 3)
    s["punch"] = 1.0 if i % 2 == 0 else 1.06  # alternate framing hides jump cuts
    t += s["src1"] - s["src0"]
duration = round(t, 3)
toks = [re.sub(r"[^a-z0-9]", "", w["text"].lower()) for w in words]


def at(phrase: str, after: float = -1.0) -> float:
    p = [re.sub(r"[^a-z0-9]", "", x.lower()) for x in phrase.split()]
    for i in range(len(toks) - len(p) + 1):
        if toks[i : i + len(p)] == p and words[i]["t0"] > after:
            return words[i]["t0"]
    raise SystemExit(f"phrase not found in script: {phrase!r}")


LEAD = 0.25


def cue(type_, start, end, raw=None, **p):
    c = {"type": type_, "from": round(max(0.0, start - LEAD), 3), "to": round(end - LEAD, 3), "p": {k: round(v - 0.1, 3) for k, v in p.items()}}
    c["p"].update(raw or {})
    return c


b = {
    "ofs": at("Ek important baat"),
    "c1": at("No. 1 is"),
    "isme": at("Isme ₹2,830"),
    "fresh": at("Fresh issue se"),
    "c2": at("Second is"),
    "c3": at("Third is"),
    "c4": at("Fourth is"),
    "cta": at("Aise hi IPO"),
}
s3 = at("issue size ₹852.18")
s4 = at("issue size ₹475.48")

cues = [
    {"type": "hook", "from": 0.0, "to": round(b["ofs"] - LEAD, 3), "p": {k: round(v - 0.1, 3) for k, v in {
        "n1": at("Zetwerk, Bonfiglioli"), "n2": at("Bonfiglioli Transmissions,"), "n3": at("Tonbo Imaging India aur"),
        "n4": at("Sahajanand Medical Technologies ke"), "dates": at("19 October")}.items()}},
    cue("ofs", b["ofs"], b["c1"], chips=at("Zetwerk ko chhodkar"), ofs=at("OFS yaani"), zero=at("kuch nahi milta"), zet=at("Zetwerk mein fresh")),
    cue("company", b["c1"], b["isme"], raw={"n": 1}, price=at("Price band ₹143"), size=at("issue size ₹5,012.33"), type=at("issue size ₹5,012.33") + 1.2),
    cue("zetSplit", b["isme"], b["fresh"], ofs=at("₹2,182.33 crore")),
    cue("zetObjects", b["fresh"], b["c2"], a1=at("₹1,300 crore"), a2=at("₹860 crore"), a3=at("baaki acquisitions"), table=at("₹1,300 crore")),
    cue("company", b["c2"], b["c3"], raw={"n": 2}, price=at("Price band ₹558"), size=at("issue size ₹2,533.66"), type=at("poora OFS hai")),
    cue("company", b["c3"], b["c4"], raw={"n": 3}, price=at("Price band ₹665"), size=s3, type=at("poora OFS", after=s3)),
    cue("company", b["c4"], b["cta"], raw={"n": 4}, price=at("Price band ₹327"), size=s4, type=at("poora OFS", after=s4)),
]

sections = [
    {"scene": "market", "from": 0.0},
    {"scene": "factory", "from": round(b["c1"] - LEAD, 3)},
    {"scene": "gears", "from": round(b["c2"] - LEAD, 3)},
    {"scene": "radar", "from": round(b["c3"] - LEAD, 3)},
    {"scene": "medical", "from": round(b["c4"] - LEAD, 3)},
    {"scene": "market", "from": round(b["cta"] - LEAD, 3)},
]

cap = []
for w in words:
    t_ = w["text"]
    brk = bool(re.search(r"[.?!,:]$", t_))
    shown = re.sub(r"(?<!\d)[,.:](?!\d)", "", t_).rstrip(",.:")
    cap.append({"t0": w["t0"], "t1": w["t1"], "text": shown, "brk": brk})

zooms = [{"from": round(b["cta"] - 0.1, 3), "to": duration, "scale": 1.08}]

edit = {"duration": duration, "segments": segs, "cues": cues, "sections": sections, "words": cap, "zooms": zooms, "endCardAt": round(b["cta"], 3)}
json.dump(edit, open(out_path, "w"), ensure_ascii=False, indent=1)
for c in cues:
    print(f"{c['from']:7.2f}-{c['to']:7.2f}  {c['type']} {c['p'].get('n', '')}")
print("sections", [(s["scene"], s["from"]) for s in sections])
print("duration", duration, "end card at", edit["endCardAt"])
