"""Render a job with the plugin's Remotion template library.

Usage: render.py JOB_DIR [--edit work/edit.json] [--out out/final.mp4] [--frames A-B] [--test]

Syncs templates/remotion/src into <remotion_dir>/src/sek (the Remotion project only supplies node_modules),
copies the brand logos into JOB/public/brand/, and renders composition "Short" with --props=edit.json and
--public-dir=JOB/public. Full log in JOB/out/render.log; prints a one-line summary.
JOB/custom/*.tsx (job-local components / Scene* scenes) are compiled in too.
--test renders the built-in sample (no footage) into JOB/out/test.mp4.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitcfg  # noqa: E402


def sync_templates(remotion_dir):
    src = os.path.join(kitcfg.PLUGIN_ROOT, "templates", "remotion", "src")
    dst = os.path.join(remotion_dir, "src", "sek")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return os.path.join("src", "sek", "index.ts")


def sync_custom(job, remotion_dir):
    """JOB/custom/<Name>.tsx -> component <Name>; JOB/custom/Scene<Name>.tsx -> scene "<name>"."""
    cdir = os.path.join(job, "custom")
    if not os.path.isdir(cdir):
        return 0
    dst = os.path.join(remotion_dir, "src", "sek", "custom")
    names = sorted(f[:-4] for f in os.listdir(cdir) if f.endswith(".tsx") and f[:-4].isidentifier())
    for n in names:
        shutil.copyfile(os.path.join(cdir, n + ".tsx"), os.path.join(dst, n + ".tsx"))
    lines = ["import type React from 'react';"] + [f"import {n} from './{n}';" for n in names]
    comps = [n for n in names if not n.startswith("Scene")]
    scenes = [n for n in names if n.startswith("Scene")]
    lines.append("export const CUSTOM: Record<string, React.FC<any>> = {" + ", ".join(comps) + "};")
    lines.append("export const CUSTOM_SCENES: Record<string, React.FC> = {" + ", ".join(f"{n[5:].lower()}: {n}" for n in scenes) + "};")
    open(os.path.join(dst, "index.ts"), "w").write("\n".join(lines) + "\n")
    return len(names)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--edit", default="work/edit.json")
    ap.add_argument("--out", default="")
    ap.add_argument("--frames", default="")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--concurrency", default="6")
    a = ap.parse_args()
    c = kitcfg.cfg()
    job = os.path.abspath(a.job)
    os.makedirs(os.path.join(job, "out"), exist_ok=True)
    pub = os.path.join(job, "public")
    os.makedirs(os.path.join(pub, "brand"), exist_ok=True)
    edit = os.path.join(kitcfg.PLUGIN_ROOT, "templates", "remotion", "src", "sample.json") if a.test else os.path.join(job, a.edit)
    b = kitcfg.brand(kitcfg.load(os.path.join(job, "job.json")).get("brand", "") if os.path.exists(os.path.join(job, "job.json")) else "")
    for k in ("onLight", "onDark", "icon"):
        shutil.copyfile(os.path.join(b["_dir"], b["logo"][k]), os.path.join(pub, "brand", os.path.basename(b["logo"][k])))

    # Remotion copies public/ into its bundle and does not follow symlinks: turn them into hard links (or copies).
    for f in os.listdir(pub):
        p = os.path.join(pub, f)
        if os.path.islink(p):
            real = os.path.realpath(p)
            os.unlink(p)
            try:
                os.link(real, p)
            except OSError:
                shutil.copyfile(real, p)

    # Sound: mix voice + bed + effects when the edit asks for it (scripts/build_mix.py).
    mix_name = kitcfg.load(edit).get("mix")
    if mix_name:
        r = subprocess.run([c["python"], "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_mix.py"), job, "--edit", edit, "--out", os.path.join("public", mix_name)],
                           capture_output=True, text=True)
        if r.returncode:
            print("MIX FAILED:\n" + (r.stdout + r.stderr)[-600:])
            sys.exit(1)
        print(r.stdout.strip().splitlines()[-1])

    entry = sync_templates(c["remotion_dir"])
    ncustom = 0 if a.test else sync_custom(job, c["remotion_dir"])
    out = os.path.abspath(a.out) if a.out else os.path.join(job, "out", "test.mp4" if a.test else "final.mp4")
    cmd = ["npx", "remotion", "render", entry, "Short", out, f"--props={edit}", f"--public-dir={pub}", "--codec=h264",
           f"--crf={b['video']['crf']}", f"--audio-bitrate={b['audio']['bitrate']}", f"--concurrency={a.concurrency}", "--log=info"]
    if a.frames:
        cmd.append(f"--frames={a.frames}")
    env = dict(os.environ, PATH=os.path.dirname(c["ffmpeg"]) + os.pathsep + os.environ.get("PATH", ""))
    log = os.path.join(job, "out", "render.log")
    t0 = time.time()
    with open(log, "w") as fh:
        r = subprocess.run(cmd, cwd=c["remotion_dir"], stdout=fh, stderr=subprocess.STDOUT, env=env)
    if r.returncode:
        tail = open(log).read().splitlines()[-15:]
        print("RENDER FAILED, last log lines:\n" + "\n".join(tail))
        sys.exit(1)
    mb = os.path.getsize(out) / 1e6
    print(f"{out}: {mb:.1f} MB, rendered in {time.time() - t0:.0f}s, {ncustom} custom components (log {log})")


if __name__ == "__main__":
    main()
