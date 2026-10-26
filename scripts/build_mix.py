"""Mix voice + music bed + sound effects into one loudness-normalised track.

Usage: build_mix.py JOB_DIR [--edit work/edit.json] [--out public/mix.m4a] [--no-voice]

Reads the brand pack (audio.bed, audio.sfx, audio.lufs...). Bed is ducked under speech. Effects follow edit.json:
whoosh at each card entry and scene change, pop at each item that appears, soft pop at the end card.
Final two-pass loudnorm to the brand target. Prints one line with the measured result.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402
import numpy as np  # noqa: E402
import synth_audio as sa  # noqa: E402

SR = sa.SR


def read_voice(ff, path, n):
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    v = np.frombuffer(r.stdout, np.float32).reshape(-1, 2)
    out = np.zeros((n, 2), np.float32)
    out[: min(n, len(v))] = v[:n]
    return out


def item_times(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if (k == "at" or k.endswith("At")) and isinstance(v, (int, float)):
                yield float(v)
            else:
                yield from item_times(v)
    elif isinstance(x, list):
        for v in x:
            yield from item_times(v)


def duck_gain(voice, depth_db, thresh_db=-45.0, attack=0.05, release=0.45):
    win = int(0.02 * SR)
    m = np.abs(voice).mean(axis=1)
    k = len(m) // win
    rms = np.sqrt((m[: k * win].reshape(k, win) ** 2).mean(axis=1) + 1e-12)
    speech = (20 * np.log10(rms) > thresh_db).astype(np.float32)
    g = np.zeros(k, np.float32)
    ca, cr = np.exp(-0.02 / attack), np.exp(-0.02 / release)
    s = 0.0
    for i in range(k):
        s = ca * s + (1 - ca) * speech[i] if speech[i] > s else cr * s + (1 - cr) * speech[i]
        g[i] = s
    gain = 1 - (1 - 10 ** (depth_db / 20)) * g
    full = np.repeat(gain, win)
    return np.concatenate([full, np.full(len(m) - len(full), gain[-1] if k else 1.0, np.float32)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--edit", default="work/edit.json")
    ap.add_argument("--out", default="public/mix.m4a")
    ap.add_argument("--no-voice", action="store_true")
    a = ap.parse_args()
    job = os.path.abspath(a.job)
    edit = kitcfg.load(a.edit if os.path.isabs(a.edit) else os.path.join(job, a.edit))
    jobj = kitcfg.load(os.path.join(job, "job.json")) if os.path.exists(os.path.join(job, "job.json")) else {}
    b = kitcfg.brand(jobj.get("brand", ""))
    au = b["audio"]
    bed_cfg, sfx = au.get("bed", {}), au.get("sfx", {})
    ff = kitcfg.ffmpeg()
    dur = float(edit["duration"])
    n = int(dur * SR)

    voice_path = os.path.join(job, "public", edit["voice"]) if edit.get("voice") and not a.no_voice else None
    voice = read_voice(ff, voice_path, n) if voice_path and os.path.exists(voice_path) else np.zeros((n, 2), np.float32)
    has_voice = bool(np.abs(voice).max() > 0)

    mix = voice.copy()
    if bed_cfg.get("enabled", True):
        if bed_cfg.get("file"):
            tmp = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-stream_loop", "-1", "-i", os.path.join(b["_dir"], bed_cfg["file"]), "-t", f"{dur:.3f}",
                                  "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
            bed = np.frombuffer(tmp, np.float32).reshape(-1, 2)
            bed = np.vstack([bed, np.zeros((max(0, n - len(bed)), 2), np.float32)])[:n]
        else:
            bed = sa.bed(dur, bpm=bed_cfg.get("bpm", 92), level_db=bed_cfg.get("levelDb", -34.0))
            bed = np.vstack([bed, np.zeros((max(0, n - len(bed)), 2), np.float32)])[:n]
        if has_voice:
            bed = bed * duck_gain(voice, bed_cfg.get("duckDb", -8.0))[:, None]
        mix += bed

    ev = []  # (time, kind)
    if sfx.get("enabled", True):
        for c in edit["cues"]:
            ev.append((c["from"] - 0.05, "whoosh"))
            ev += [(t, "pop") for t in item_times(c["props"]) if c["from"] < t < c["to"]]
        ev += [(s["from"], "whoosh_soft") for s in edit.get("sections", [])[1:]]
        if edit.get("endCard"):
            ev.append((edit["endCard"]["from"], "pop"))
        lib = {"whoosh": (sa.whoosh(), sfx.get("whooshDb", -17.0)), "whoosh_soft": (sa.whoosh(0.4, 5), sfx.get("whooshDb", -17.0) - 5),
               "pop": (sa.pop(), sfx.get("popDb", -21.0)), "pop2": (sa.pop(1046.5), sfx.get("popDb", -21.0))}
        last, count = {}, 0
        for t, kind in sorted(ev):
            if t < 0 or t >= dur:
                continue
            fam = "whoosh" if kind.startswith("whoosh") else "pop"
            if t - last.get(fam, -9) < (0.5 if fam == "whoosh" else sfx.get("minGapSec", 0.35)):
                continue
            last[fam] = t
            snd, db = lib[kind if kind != "pop" or count % 2 == 0 else "pop2"]
            if kind == "pop":
                count += 1
            a0 = int(t * SR)
            seg = snd[: n - a0] * (10 ** (db / 20))
            mix[a0 : a0 + len(seg)] += seg

    # two-pass loudnorm via ffmpeg (linear mode keeps dynamics)
    wav = os.path.join(job, "work", "_mix_raw.wav") if os.path.isdir(os.path.join(job, "work")) else os.path.join(job, "_mix_raw.wav")
    import wave

    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    tgt = f"I={au['lufs']}:TP={au['truePeak'] - 0.5}:LRA={au['lra']}"  # AAC encoding adds ~0.3 dB of peak
    meas = subprocess.run([ff, "-hide_banner", "-i", wav, "-af", f"loudnorm={tgt}:print_format=json", "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    m = json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", meas)[-1])
    ln = (f"loudnorm={tgt}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = os.path.join(job, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-af", ln + f",aresample={au['sampleRate']}", "-c:a", "aac", "-b:a", au["bitrate"], out], check=True)
    os.unlink(wav)
    nsfx = len([1 for _ in ev])
    print(f"{out}: {dur:.1f}s, voice {'yes' if has_voice else 'no'}, bed {'on' if bed_cfg.get('enabled', True) else 'off'}, {nsfx} sfx candidates, {m['input_i']} LUFS -> {au['lufs']} LUFS")


if __name__ == "__main__":
    main()
