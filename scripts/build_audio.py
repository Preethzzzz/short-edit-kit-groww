"""Cut the voice track to the kept segments and loudness-normalise it.

Usage: build_audio.py raw.mp4 segments.json voice.m4a [--brand groww]
Fades at every cut and the two-pass loudnorm target come from the brand pack (audio.*).
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402

if len([x for x in sys.argv[1:] if not x.startswith("--")]) < 3:
    sys.exit(__doc__)
args = [x for x in sys.argv[1:] if not x.startswith("--")]
raw, seg_path, out = args[:3]
brand = sys.argv[sys.argv.index("--brand") + 1] if "--brand" in sys.argv else ""
au = kitcfg.brand(brand)["audio"]
FF = kitcfg.ffmpeg()
segs = kitcfg.load(seg_path)
fade = au["fadeMs"] / 1000

parts, labels = [], []
for i, s in enumerate(segs):
    d = s["src1"] - s["src0"]
    parts.append(
        f"[0:a]atrim={s['src0']:.3f}:{s['src1']:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:d={fade}," f"afade=t=out:st={max(0, d - fade):.3f}:d={fade}[a{i}]"
    )
    labels.append(f"[a{i}]")
graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=0:a=1[cat]"
target = f"I={au['lufs']}:TP={au['truePeak']}:LRA={au['lra']}"

measure = subprocess.run(
    [FF, "-hide_banner", "-i", raw, "-filter_complex", graph + f";[cat]loudnorm={target}:print_format=json[o]", "-map", "[o]", "-f", "null", "-"],
    capture_output=True, text=True, check=True,
).stderr
m = json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", measure)[-1])

# Pass 2 in linear mode keeps the delivery natural.
ln = (
    f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
)
subprocess.run(
    [FF, "-hide_banner", "-loglevel", "error", "-y", "-i", raw, "-filter_complex", graph + f";[cat]{ln},aresample={au['sampleRate']}[o]",
     "-map", "[o]", "-c:a", "aac", "-b:a", au["bitrate"], out],
    check=True,
)
total = sum(s["src1"] - s["src0"] for s in segs)
print(f"{out}: {len(segs)} segments, {total:.2f}s, {m['input_i']} LUFS -> {au['lufs']} LUFS")
