"""Shared matching helpers: Devanagari transliteration, fuzzy word similarity, DP alignment."""
import re
from difflib import SequenceMatcher

CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h", "ड़": "d", "ढ़": "dh", "क़": "k", "ख़": "kh", "ग़": "g", "ज़": "z", "फ़": "f",
}
VOW = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऋ": "ri"}
MATRA = {"ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ृ": "ri"}


def translit(x: str) -> str:
    """Rough Devanagari -> Roman Hinglish (with final-schwa deletion), enough for fuzzy matching."""
    if not re.search(r"[ऀ-ॿ]", x):
        return x
    import unicodedata
    x = unicodedata.normalize("NFC", x)
    out, i = [], 0
    while i < len(x):
        ch = x[i]
        two = x[i : i + 2]
        if two in CONS:
            ch, i = two, i + 1
        if ch in CONS:
            out.append(CONS[ch])
            nxt = x[i + 1] if i + 1 < len(x) else ""
            if nxt == "़":
                i += 1
                nxt = x[i + 1] if i + 1 < len(x) else ""
            if nxt in MATRA:
                out.append(MATRA[nxt])
                i += 1
            elif nxt == "्":
                i += 1
            elif nxt and (nxt in CONS or nxt in VOW or nxt in "ंँ"):
                out.append("a")
            elif not nxt:
                pass  # final schwa dropped
            else:
                out.append("a")
        elif ch in VOW:
            out.append(VOW[ch])
        elif ch in "ंँ":
            out.append("n")
        elif ch in MATRA:
            out.append(MATRA[ch])
        elif ch not in "्ः़":
            out.append(ch)
        i += 1
    return "".join(out)


def norm(x: str) -> str:
    x = translit(x)
    x = x.lower().replace("₹", "").replace(",", "")
    x = re.sub(r"[^a-z0-9.%]", "", x).strip(".")
    # Collapse common Hinglish spelling variants so "guna"/"goona", "hissa"/"hisa" match.
    x = re.sub(r"(.)\1+", r"\1", x)
    x = x.replace("oo", "u").replace("ee", "i").replace("aa", "a").replace("w", "v").replace("z", "j")
    return x


def sim(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def dp_align(script_words, trans_words, gap=-0.4, min_sim=0.45):
    """Needleman-Wunsch alignment. Returns {script_index: transcript_index} for confident matches."""
    n, m = len(script_words), len(trans_words)
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = i * gap
        back[i][0] = 1
    for j in range(1, m + 1):
        score[0][j] = j * gap
        back[0][j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = sim(script_words[i - 1], trans_words[j - 1])
            diag = score[i - 1][j - 1] + (s * 2 - 0.8)
            up = score[i - 1][j] + gap
            left = score[i][j - 1] + gap
            best = max(diag, up, left)
            score[i][j] = best
            back[i][j] = 0 if best == diag else (1 if best == up else 2)
    pairs = {}
    i, j = n, m
    while i > 0 or j > 0:
        b = back[i][j]
        if i > 0 and j > 0 and b == 0:
            if sim(script_words[i - 1], trans_words[j - 1]) >= min_sim:
                pairs[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif i > 0 and (j == 0 or b == 1):
            i -= 1
        else:
            j -= 1
    return pairs
