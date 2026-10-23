"""Build Remotion edit.json: captions from aligned script words, cards anchored to script phrases.

Usage: python build_edit.py aligned_words.json segments.json out_edit.json
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
    """Start time of the first occurrence of `phrase` (script words) starting after `after` seconds."""
    p = [re.sub(r"[^a-z0-9]", "", x.lower()) for x in phrase.split()]
    for i in range(len(toks) - len(p) + 1):
        if toks[i : i + len(p)] == p and words[i]["t0"] > after:
            return words[i]["t0"]
    raise SystemExit(f"phrase not found in script: {phrase!r}")


LEAD = 0.25  # cards land a beat before the words they illustrate
NEVER = 9999

def cue(type_, start, end, **p):
    return {"type": type_, "from": round(max(0.0, start - LEAD), 3), "to": round(end - LEAD, 3), "p": {k: round(v - 0.1, 3) for k, v in p.items()}}


b = {
    "open": at("Aur open hone"),
    "day1": at("Day 1 ke ant tak"),
    "chaliye": at("Chaliye category-wise"),
    "jisme": at("jisme 44.22"),
    "nii": at("Non-institutional investors"),
    "retail": at("Retail investors ka portion"),
    "emp": at("Employees aur RIL"),
    "total": at("Total mila kar"),
    "qibbids": at("QIB bids mein"),
    "inst": at("Institutions ne"),
    "anchor": at("Isse pehle anchor"),
    "lot": at("Retail investors kam se kam"),
    "dates": at("IPO 23 October tak"),
    "note": at("Ek important baat"),
    "disc": at("Yeh video sirf"),
}

cues = [
    {"type": "issue", "from": 0.0, "to": round(b["open"] - LEAD, 3), "p": {}},
    cue("fully1036", b["open"], b["day1"], clip=at("10:36")),
    cue("total", b["day1"], b["chaliye"]),
    cue("bars", b["chaliye"], b["jisme"], qib=at("9.02 guna"), nii=NEVER, retail=NEVER, emp=NEVER, ril=NEVER),
    cue("qibBids", b["jisme"], b["nii"]),
    cue("bars", b["nii"], b["retail"], qib=b["nii"] - 9, nii=at("1.59 guna"), retail=NEVER, emp=NEVER, ril=NEVER),
    cue("retail", b["retail"], b["emp"], meter=at("0.68 guna")),
    cue("bars", b["emp"], b["total"], qib=b["emp"] - 9, nii=b["emp"] - 9, retail=b["emp"] - 9, emp=at("1.30 aur"), ril=at("1.38 guna")),
    cue("totalBids", b["total"], b["qibbids"]),
    cue("qibSplit", b["qibbids"], b["inst"], dfi=at("domestic financial"), fii=at("FIIs ke 15.14"), mf=at("mutual funds ke")),
    cue("versus", b["inst"], b["anchor"], next=at("Ab nazar")),
    cue("anchor", b["anchor"], b["lot"], price=at("₹1,119 per share")),
    cue("lot", b["lot"], b["dates"], result=at("yaani upper band")),
    cue("dates", b["dates"], b["note"], close=at("23 October tak"), allot=at("basis of allotment"), list=at("listing 28")),
    cue("note", b["note"], b["disc"], chips=at("Valuation")),
]

# Captions: script wording, punctuation trimmed for display, break hints kept.
# Where the take differs from the script, captions follow what is actually said.
SPOKEN = {"karoge?": "karenge?"}
cap = []
for w in words:
    t = w["text"]
    brk = bool(re.search(r"[.?!,]$", t))
    shown = re.sub(r"(?<!\d)[,.](?!\d)", "", t).rstrip(",.")
    shown = SPOKEN.get(shown, shown)
    cap.append({"t0": w["t0"], "t1": w["t1"], "text": shown, "brk": brk})

zooms = [
    {"from": round(at("Kya aap") - 0.1, 3), "to": duration, "scale": 1.1},
    {"from": round(b["disc"] - 0.1, 3), "to": round(at("Kya aap") - 0.15, 3), "scale": 1.04},
]

edit = {"duration": duration, "segments": segs, "cues": cues, "words": cap, "zooms": zooms, "endCardAt": round(b["disc"], 3)}
json.dump(edit, open(out_path, "w"), ensure_ascii=False, indent=1)
for c in cues:
    print(f"{c['from']:7.2f}-{c['to']:7.2f}  {c['type']}")
print("duration", duration, "end card at", edit["endCardAt"])
