"""Create a job folder from raw footage + a finished script (DOCX, PDF or text).

Usage: init_job.py FOOTAGE SCRIPT --name SLUG --format ipo-day-roundup|data-explainer [--channel ipo-review] [--root jobs]

Makes ROOT/SLUG/{inputs,work,work/images,public,out}, links the footage, extracts the script to
work/script_raw.txt (paragraphs in order, [IMAGE img_NN.ext] markers, tables as "a | b") and every
embedded image to work/images/, probes the footage, and writes job.json.
work/script.txt (spoken words only) is written afterwards by the editor from script_raw.txt.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402


def docx_extract(path, img_dir):
    import docx
    from docx.oxml.ns import qn

    d = docx.Document(path)
    lines, n = [], 0
    for el in d.element.body.iterchildren():
        if el.tag == qn("w:p"):
            text = "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()
            if text:
                lines.append(text)
            for blip in el.iter(qn("a:blip")):
                rid = blip.get(qn("r:embed"))
                part = d.part.related_parts.get(rid)
                if part is None:
                    continue
                n += 1
                ext = os.path.splitext(part.partname)[1] or ".png"
                name = f"img_{n:02d}{ext}"
                open(os.path.join(img_dir, name), "wb").write(part.blob)
                lines.append(f"[IMAGE {name}]")
        elif el.tag == qn("w:tbl"):
            for row in el.iter(qn("w:tr")):
                cells = ["".join(t.text or "" for t in c.iter(qn("w:t"))).strip() for c in row.iter(qn("w:tc"))]
                lines.append(" | ".join(cells))
    return lines, n


def pdf_extract(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("pypdf missing: run the setup skill (it installs pypdf into the venv)")
    lines = []
    for page in PdfReader(path).pages:
        # PDF text often comes one word per line: rebuild paragraphs (split on blank lines / sentence ends).
        text = " ".join((page.extract_text() or "").split())
        lines += [p.strip() for p in re.split(r"(?<=[.?!:])\s+(?=[A-Z₹0-9])", text) if p.strip()]
    return lines, 0


def probe(ff, path):
    import av

    with av.open(path) as c:
        v = c.streams.video[0]
        fps = float(v.average_rate)
        dur = float(c.duration / 1e6) if c.duration else float(v.duration * v.time_base)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", "1", "-i", path, "-frames:v", "1", tmp], check=True)
    from PIL import Image

    w, h = Image.open(tmp).size  # after autorotation, as ffmpeg will deliver it
    os.unlink(tmp)
    return w, h, fps, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("footage")
    ap.add_argument("script")
    ap.add_argument("--name", required=True)
    ap.add_argument("--format", required=True)
    ap.add_argument("--channel", default="ipo-review")
    ap.add_argument("--root", default="jobs")
    a = ap.parse_args()
    if not all(c.isalnum() or c in "-_" for c in a.name):
        sys.exit("--name: letters, digits, - and _ only")
    job = os.path.abspath(os.path.join(a.root, a.name))
    for sub in ("inputs", "work/images", "public", "out"):
        os.makedirs(os.path.join(job, sub), exist_ok=True)

    foot = os.path.abspath(a.footage)
    link = os.path.join(job, "inputs", "raw" + os.path.splitext(foot)[1].lower())
    if not os.path.exists(link):
        os.symlink(foot, link)
    src = os.path.join(job, "inputs", "script" + os.path.splitext(a.script)[1].lower())
    shutil.copyfile(a.script, src)

    ext = os.path.splitext(src)[1]
    if ext == ".docx":
        lines, nimg = docx_extract(src, os.path.join(job, "work", "images"))
    elif ext == ".pdf":
        lines, nimg = pdf_extract(src)
    else:
        lines, nimg = [l.strip() for l in open(src, encoding="utf-8") if l.strip()], 0
    open(os.path.join(job, "work", "script_raw.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    w, h, fps, dur = probe(kitcfg.ffmpeg(), link)
    b = kitcfg.brand()
    kitcfg.save({
        "name": a.name, "format": a.format, "channel": a.channel, "brand": b["_dir"],
        "footage": link, "script": src, "width": w, "height": h, "fps": round(fps, 3), "duration": round(dur, 2),
        "raName": "", "raDate": "",
    }, os.path.join(job, "job.json"), indent=1)
    words = sum(len(l.split()) for l in lines if not l.startswith("[IMAGE"))
    warn = "" if h > w else "  WARNING: footage is not vertical"
    print(f"{job}: footage {w}x{h} {fps:.2f}fps {dur:.1f}s; script {len(lines)} lines, {words} words, {nimg} images{warn}")


if __name__ == "__main__":
    main()
