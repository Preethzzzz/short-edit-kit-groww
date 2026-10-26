"""Original, royalty-free audio generated in code (numpy only): a soft music bed plus whoosh / pop / tick effects.

No samples, no third-party music. A brand pack can instead point audio.bed.file at its own licensed track.
Deterministic: same parameters give the same sound. All functions return float32 arrays at SR, shape (n, 2).
"""
import numpy as np

SR = 48000
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave - 4) - 9) / 12)


def _env(n, attack, release, sr=SR):
    e = np.ones(n, np.float32)
    a, r = min(n, int(attack * sr)), min(n, int(release * sr))
    if a:
        e[:a] = np.linspace(0, 1, a, dtype=np.float32) ** 2
    if r:
        e[-r:] *= np.linspace(1, 0, r, dtype=np.float32) ** 2
    return e


def _pad(freqs, dur, detune=0.003):
    t = np.arange(int(dur * SR), dtype=np.float32) / SR
    out = np.zeros_like(t)
    for f in freqs:
        for d in (-detune, 0.0, detune):
            ph = 2 * np.pi * f * (1 + d) * t
            out += np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    return out / (len(freqs) * 3)


def bed(duration, bpm=92, key=("A", "minor"), seed=7, level_db=-34.0):
    """Ambient pad + soft pluck arpeggio + gentle pulse and shaker. Chords Am F C G, two bars each."""
    rng = np.random.RandomState(seed)
    n = int((duration + 1.0) * SR)
    beat = 60.0 / bpm
    prog = [("A", 3, [0, 3, 7]), ("F", 3, [0, 4, 7]), ("C", 3, [0, 4, 7]), ("G", 3, [0, 4, 7])]
    chord_len = 8 * beat
    mono = np.zeros(n, np.float32)
    t0, ci = 0.0, 0
    while t0 < duration + 1.0:
        root, octv, iv = prog[ci % 4]
        base = hz(root, octv)
        freqs = [base * 2 ** (i / 12) for i in iv] + [base / 2]
        seg = _pad(freqs, chord_len + 1.0) * _env(int((chord_len + 1.0) * SR), 1.2, 1.2)
        s = int(t0 * SR)
        e = min(n, s + len(seg))
        mono[s:e] += seg[: e - s] * 0.9
        # pluck arpeggio on eighth notes
        notes = [base * 2 ** (i / 12) * 2 for i in iv] + [base * 4]
        for k in range(16):
            tt = t0 + k * beat / 2
            f = notes[[0, 1, 2, 3, 2, 1, 2, 1][k % 8]]
            m = int(0.5 * SR)
            x = np.arange(m, dtype=np.float32) / SR
            pl = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 7.0)
            a = int(tt * SR)
            b = min(n, a + m)
            if a < n:
                mono[a:b] += pl[: b - a] * 0.16 * (1.0 if k % 2 == 0 else 0.7)
        t0 += chord_len
        ci += 1
    # soft kick on beats 1 and 3, shaker on off-beats
    nb = int((duration + 1.0) / beat) + 1
    for b in range(nb):
        a = int(b * beat * SR)
        if a >= n:
            break
        if b % 2 == 0:
            m = int(0.35 * SR)
            x = np.arange(m, dtype=np.float32) / SR
            f = 45 + 55 * np.exp(-x * 18)
            k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9)
            mono[a : min(n, a + m)] += k[: min(n, a + m) - a] * 0.32
        else:
            m = int(0.06 * SR)
            sh = rng.randn(m).astype(np.float32)
            sh = np.diff(sh, prepend=0)  # crude high-pass
            sh *= np.exp(-np.arange(m, dtype=np.float32) / SR * 70)
            mono[a : min(n, a + m)] += sh[: min(n, a + m) - a] * 0.05
    mono = mono[: int(duration * SR)]
    rms = float(np.sqrt(np.mean(mono ** 2)) + 1e-9)
    mono *= (10 ** (level_db / 20)) / rms
    mono *= _env(len(mono), 1.0, 2.0)
    # slight stereo width: small delay on one side
    d = int(0.012 * SR)
    left = mono
    right = np.concatenate([np.zeros(d, np.float32), mono[:-d]]) if d else mono
    return np.stack([left, right], axis=1).astype(np.float32)


def whoosh(dur=0.55, seed=3):
    """Noise sweep that brightens then fades: slide / card entry."""
    rng = np.random.RandomState(seed)
    n = int(dur * SR)
    noise = rng.randn(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    chunk = 480
    for i in range(0, n, chunk):
        p = i / n
        width = int(max(6, 220 * (1 - p) ** 2 + 6))  # shorter box filter = brighter
        k = np.ones(width, np.float32) / width
        seg = np.convolve(noise[max(0, i - width) : i + chunk], k, mode="same")[-min(chunk, n - i) :]
        out[i : i + len(seg)] = seg
    p = np.linspace(0, 1, n, dtype=np.float32)
    env = np.sin(np.pi * np.clip(p * 1.15, 0, 1)) ** 2 * (1 - p) ** 0.5
    tone = np.sin(2 * np.pi * np.cumsum(300 + 700 * p ** 2) / SR) * 0.12
    mono = (out * 5.0 + tone) * env
    mono /= np.max(np.abs(mono)) + 1e-9
    return np.stack([mono, mono], axis=1).astype(np.float32)


def pop(freq=880.0, dur=0.12):
    n = int(dur * SR)
    x = np.arange(n, dtype=np.float32) / SR
    f = freq * (1 + 0.6 * np.exp(-x * 60))
    mono = (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)) * np.exp(-x * 38)
    mono /= np.max(np.abs(mono)) + 1e-9
    return np.stack([mono, mono], axis=1).astype(np.float32)


def tick(dur=0.05):
    n = int(dur * SR)
    x = np.arange(n, dtype=np.float32) / SR
    mono = np.sin(2 * np.pi * 2200 * x) * np.exp(-x * 120)
    return np.stack([mono, mono], axis=1).astype(np.float32)
