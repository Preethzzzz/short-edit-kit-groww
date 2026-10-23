"""Whisper word timestamps for a clip, or for pieces of it (retake checks).

Usage:
  transcribe.py MEDIA OUT_words.json [--lang hi] [--prompt "names, terms"] [--clip A-B]
  transcribe.py MEDIA --pieces A-B,C-D,...   # each piece transcribed on its own; one line per piece

Hindi-heavy audio: keep --lang hi and pass NO English --prompt (Whisper otherwise translates).
Full-clip runs merge repeated takes; re-check suspicious stretches with --pieces.
Writes OUT_words.json (+ OUT_words.txt with segment lines). Prints a one-line summary only.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402

SR = 16000


def span(s):
    a, b = s.split("-")
    return float(a), float(b)


def run(model, audio, lang, prompt, offset=0.0):
    segs, _ = model.transcribe(audio, language=lang, word_timestamps=True, initial_prompt=prompt or None, vad_filter=False, beam_size=5)
    words, lines = [], []
    for s in segs:
        for w in s.words:
            words.append({"start": round(w.start + offset, 2), "end": round(w.end + offset, 2), "word": w.word.strip(), "p": round(w.probability, 2)})
        lines.append(f"[{s.start + offset:7.2f}-{s.end + offset:7.2f}] {s.text.strip()}")
    return words, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--lang", default="hi")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--clip", type=span)
    ap.add_argument("--pieces")
    a = ap.parse_args()
    if a.prompt and a.lang == "hi" and all(ord(c) < 128 for c in a.prompt):
        print("warning: English prompt with --lang hi can make Whisper translate; drop it if output looks translated")

    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio

    model = WhisperModel(kitcfg.cfg()["model"], device="cpu", compute_type="int8")
    audio = decode_audio(a.media, sampling_rate=SR)

    if a.pieces:
        for p in a.pieces.split(","):
            s0, s1 = span(p)
            _, lines = run(model, audio[int(s0 * SR) : int(s1 * SR)], a.lang, a.prompt, s0)
            text = " ".join(l.split("] ", 1)[1] for l in lines)
            print(f"{s0:7.2f}-{s1:7.2f}  {text}")
        return

    if not a.out:
        sys.exit("OUT_words.json required (or use --pieces)")
    off = 0.0
    if a.clip:
        off = a.clip[0]
        audio = audio[int(a.clip[0] * SR) : int(a.clip[1] * SR)]
    words, lines = run(model, audio, a.lang, a.prompt, off)
    kitcfg.save(words, a.out, indent=0)
    txt = os.path.splitext(a.out)[0] + ".txt"
    open(txt, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    low = sum(w["p"] < 0.5 for w in words)
    dur = len(audio) / SR
    print(f"{a.out}: {len(words)} words, {len(lines)} segments, {dur:.1f}s audio, {low} low-confidence words; text in {txt}")


if __name__ == "__main__":
    main()
