"""Shot list for the Jio Day 1 'story' re-cut: one visual per sentence, three rotating shot types.

Usage: python build_story_jio.py aligned_words.json duration out_story.json
Each shot starts at the first word of its anchor phrase (minus a short lead) and runs to the next shot.
"""
import json
import re
import sys

words = json.load(open(sys.argv[1]))
duration = float(sys.argv[2])
toks = [re.sub(r"[^a-z0-9]", "", w["text"].lower()) for w in words]


def at(phrase: str, after: float = -1.0) -> float:
    p = [re.sub(r"[^a-z0-9]", "", x.lower()) for x in phrase.split()]
    for i in range(len(toks) - len(p) + 1):
        if toks[i : i + len(p)] == p and words[i]["t0"] > after:
            return words[i]["t0"]
    raise SystemExit(f"phrase not found: {phrase!r}")


LEAD = 0.15
plan = [
    ("title", "split", "India ka ab tak", {}),
    ("mc", "split", "Aur open hone", {}),
    ("clock", "chart", "subah ke 10:36", {}),
    ("times", "chart", "Day 1 ke ant tak", {}),
    ("talk1", "talk", "Chaliye category-wise", {}),
    ("qibbar", "chart", "QIB portion, anchor", {"v": "9.02 guna"}),
    ("circles", "chart", "jisme 44.22", {"res": "4.90 crore"}),
    ("nii", "split", "Non-institutional investors", {"v": "1.59 guna"}),
    ("donut", "chart", "Retail investors ka portion", {}),
    ("fill", "chart", "0.68 guna", {}),
    ("emp", "split", "Employees aur RIL", {"a": "1.30 aur", "b": "1.38 guna"}),
    ("dots", "chart", "Total mila kar", {"bid": "59.51 crore"}),
    ("talk2", "talk", "QIB bids mein", {}),
    ("qibsplit", "chart", "domestic financial", {"a": "domestic financial", "b": "FIIs ke 15.14", "c": "mutual funds ke"}),
    ("versus", "chart", "Institutions ne", {"retail": "lekin retail"}),
    ("cal", "split", "Ab nazar", {}),
    ("et", "split", "Isse pehle anchor", {}),
    ("price", "chart", "₹1,119 per share", {}),
    ("lot", "chart", "Retail investors kam se kam", {"res": "yaani upper band"}),
    ("timeline", "chart", "IPO 23 October tak", {"a": "23 October tak", "b": "basis of allotment", "c": "listing 28"}),
    ("talk3", "talk", "Ek important baat", {}),
    ("mind", "chart", "Valuation, company", {}),
    ("talk4", "talk", "Yeh video sirf", {}),
]
starts = [0.0 if i == 0 else round(at(ph) - LEAD, 3) for i, (_, _, ph, _) in enumerate(plan)]
shots = []
for i, (sid, kind, ph, params) in enumerate(plan):
    end = starts[i + 1] if i + 1 < len(plan) else duration
    shots.append({"id": sid, "kind": kind, "from": starts[i], "to": round(end, 3), "p": {k: round(at(v) - 0.1, 3) for k, v in params.items()}})

story = {"duration": duration, "shots": shots, "endCardAt": round(at("Yeh video sirf"), 3)}
json.dump(story, open(sys.argv[3], "w"), indent=1)
lens = [s["to"] - s["from"] for s in shots]
for s in shots:
    print(f"{s['from']:7.2f}-{s['to']:7.2f} ({s['to']-s['from']:4.1f}s) {s['kind']:5} {s['id']}")
print(f"{len(shots)} shots, average {sum(lens)/len(lens):.1f}s, longest {max(lens):.1f}s")
