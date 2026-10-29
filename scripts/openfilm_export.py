"""Export a job as an OpenFilm project: the optional output path instead of the Remotion render.
Usage: openfilm_export.py JOB_DIR [--out film] [--edit work/edit.json] [--brand groww]
Makes JOB/film/ with:
  film.html          logo track, an empty graphics track, the presenter cut by the job's segments, a plain ground
  assets/presenter.mp4  the presenter from JOB/public (a keyed alpha webm is baked onto the brand ground as H.264),
                     whole take, with the raw audio loudness-normalised to the brand target
  assets/presenter.vtt  the English captions from edit.json, mapped back to presenter-file seconds, a tag per word
  assets/logo.png, shared.css, shot.js, background.html, shot-example.html (templates/openfilm)
Then: `npx -y openfilm@latest open JOB/film`, write one page per shot (shot-example.html), check with `look`.
Breakout Short lessons: clip position goes in inline style (classes are ignored for left/top/width); Studio draws
subtitles at ~72% of the height (keep y 1300-1460 free); VP9 alpha loses its matte in some renders, hence the bake.
Prints one summary line.
"""
import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(kitcfg.PLUGIN_ROOT, "templates", "openfilm")


def ts(sec: float) -> str:
    ms = int(round(max(sec, 0) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}"


def to_file_time(t: float, segs: list, offset: float, end_seg=None):
    """Edited-timeline second -> presenter-file second, through the segment that holds it."""
    for i, s in enumerate(segs):
        if s["out"] <= t <= s["out"] + (s["src1"] - s["src0"]) + 1e-6:
            if end_seg is not None and i != end_seg:  # caption runs over a cut: end it at its own segment's end
                return segs[end_seg]["src1"] - offset, end_seg, True
            return s["src0"] + (t - s["out"]) - offset, i, False
    return None, None, False


def vtt(captions: list, segs: list, offset: float):
    lines, clamped = ["WEBVTT", ""], 0
    for n, c in enumerate(captions, 1):
        a, i, _ = to_file_time(c["from"], segs, offset)
        if a is None:
            continue
        b, _, cut = to_file_time(c["to"], segs, offset, end_seg=i)
        clamped += cut
        words, starts = c["text"].split(), c.get("starts") or []
        text = c["text"]
        if len(starts) == len(words):
            text = words[0] + "".join(f" <{ts(to_file_time(st, segs, offset, end_seg=i)[0] or a)}>{w}" for st, w in zip(starts[1:], words[1:]))
        lines += [str(n), f"{ts(a)} --> {ts(b if b is not None else a + 1)}", text, ""]
    return "\n".join(lines), clamped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--out", default="film")
    ap.add_argument("--edit", default="work/edit.json")
    ap.add_argument("--brand", default="")
    a = ap.parse_args()
    job = os.path.abspath(a.job)
    edit = kitcfg.load(os.path.join(job, a.edit))
    info = kitcfg.load(os.path.join(job, "job.json"))
    b = kitcfg.brand(a.brand or info.get("brand", ""))
    ff = kitcfg.ffmpeg()
    out = os.path.join(job, a.out)
    os.makedirs(os.path.join(out, "assets"), exist_ok=True)

    ground = b["palette"]["ground"]
    pres = edit["presenter"]
    src = os.path.join(job, "public", pres["src"])
    offset = float(pres.get("offset", 0))
    dst = os.path.join(out, "assets", "presenter.mp4")
    au = b.get("audio", {})
    loud = f"loudnorm=I={au.get('lufs', -14)}:TP={au.get('truePeak', -1)}:LRA={au.get('lra', 11)},aresample={au.get('sampleRate', 48000)}"
    audio_in = ["-ss", f"{offset}", "-i", info["footage"]]
    bt709 = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    if src.endswith(".webm"):  # keyed: bake onto the ground (alpha needs the libvpx decoder)
        fps = edit.get("fps", 30)
        cmd = [ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={ground}:s=1080x1920:r={fps}",
               "-c:v", "libvpx-vp9", "-i", src, *audio_in,
               "-filter_complex", "[1:v]scale=1080:1920[p];[0:v][p]overlay=shortest=1:format=auto,scale=out_color_matrix=bt709,format=yuv420p[v]",
               "-map", "[v]", "-map", "2:a", "-af", loud, "-c:v", "libx264", "-crf", "18", "-preset", "medium", *bt709,
               "-c:a", "aac", "-b:a", au.get("bitrate", "192k"), "-movflags", "+faststart", "-shortest", dst]
        kind = f"keyed, baked on {ground}"
    else:  # plain footage: keep the graded picture, add the normalised audio
        cmd = [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", src, *audio_in, "-map", "0:v", "-map", "1:a", "-af", loud,
               "-c:v", "copy", "-c:a", "aac", "-b:a", au.get("bitrate", "192k"), "-movflags", "+faststart", "-shortest", dst]
        kind = "plain"
    subprocess.run(cmd, check=True)

    segs = edit["segments"]
    text, clamped = vtt(edit.get("captions", []), segs, offset)
    open(os.path.join(out, "assets", "presenter.vtt"), "w", encoding="utf-8").write(text)

    logo = b["logo"]
    shutil.copy(os.path.join(b["_dir"], logo["onLight"]), os.path.join(out, "assets", "logo.png"))
    for name in ("shared.css", "shot.js", "shot-example.html"):
        shutil.copy(os.path.join(TEMPLATES, name), os.path.join(out, name))
    bg = open(os.path.join(TEMPLATES, "background.html"), encoding="utf-8").read().replace("{{GROUND}}", ground)
    open(os.path.join(out, "background.html"), "w", encoding="utf-8").write(bg)

    dur = round(edit["duration"], 2)
    clips = "\n".join(
        f'  <video id="seg{i + 1}" src="assets/presenter.mp4#t={s["src0"] - offset:.2f},{s["src1"] - offset:.2f}" at="{s["out"]:.2f}" '
        f'style="left: 0px; top: 0px; width: 1080px"></video>'
        for i, s in enumerate(segs))
    film = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1080, height=1920">
</head>
<body>
<section>
  <img id="logo" src="assets/logo.png#t=0,{dur}" style="left: {1080 - logo['right'] - logo['width']}px; top: {logo['top']}px; width: {logo['width']}px">
</section>
<section>
</section>
<section>
{clips}
</section>
<section>
  <iframe id="ground" src="background.html#t=0,{dur}"></iframe>
</section>
</body>
</html>
"""
    open(os.path.join(out, "film.html"), "w", encoding="utf-8").write(film)
    print(f"{out}: OpenFilm project, {dur}s, {len(segs)} presenter clips ({kind}), {len(edit.get('captions', []))} captions"
          f"{f' ({clamped} ended at a cut)' if clamped else ''}; next: npx -y openfilm@latest open {out}")


if __name__ == "__main__":
    main()
