"""List narration words that are not in the script (ad-libs, fillers, added lead-ins).

Usage: extra_words.py words.json script.txt [--json out.json]
words.json: Whisper words (raw or edited timeline). script.txt: the spoken script exactly as written.
One line per run of unmatched words with its time span and the script context.
Known false positives to ignore: numbers split by Whisper ("5 ,012 .33"), "rupees" for ₹,
hyphenated words split in two, Hindi spellings of English words.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_core as al  # noqa: E402
import kitcfg  # noqa: E402

if len([x for x in sys.argv[1:] if not x.startswith("--")]) < 2:
    sys.exit(__doc__)
words = kitcfg.load(sys.argv[1])
script = open(sys.argv[2], encoding="utf-8").read().split()
pairs = al.dp_align(script, [w["word"] for w in words])
matched_t = set(pairs.values())

runs, cur = [], []
for j in range(len(words)):
    if j not in matched_t:
        cur.append(j)
    elif cur:
        runs.append(cur)
        cur = []
if cur:
    runs.append(cur)

inv = {v: k for k, v in pairs.items()}
found = []
for r in runs:
    a, b = r[0], r[-1]
    before = max([inv[j] for j in inv if j < a], default=-1)
    after = min([inv[j] for j in inv if j > b], default=len(script))
    ctx = " ".join(script[max(0, before - 3) : before + 1]) + " [ ... ] " + " ".join(script[after : after + 3])
    text = " ".join(words[j]["word"] for j in r)
    found.append({"start": words[a]["start"], "end": words[b]["end"], "extra": text, "context": ctx})
    print(f"{words[a]['start']:7.2f}-{words[b]['end']:7.2f}  EXTRA: {text:40s} | script: {ctx}")
print(f"{len(found)} extra runs, {sum(len(r) for r in runs)} words")
if "--json" in sys.argv:
    kitcfg.save(found, sys.argv[sys.argv.index("--json") + 1], indent=1)
