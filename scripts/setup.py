"""Verify (and where missing, install) everything the kit needs, then run a 10-second test render.

Usage: python3 setup.py [--tools-dir ~/video-tools] [--skip-render] [--brand groww]

No admin rights or Homebrew needed. Reuses existing installs under the tools dir:
  ffmpeg    TOOLS/bin/ffmpeg (else the static build pinned in the venv by imageio-ffmpeg, else ffmpeg on PATH)
  python    TOOLS/venv with faster-whisper, python-docx, pillow, numpy, av, pypdf
  model     TOOLS/models/large-v3-turbo (curl with resume + size and SHA-256 check against Hugging Face)
  remotion  TOOLS/remotion (npm project with remotion + @remotion/cli) + Chrome Headless Shell (curl with resume)
Writes ~/.short-edit-kit/config.json. One line per check; exit 1 on any failure.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
CONFIG = os.path.expanduser(os.environ.get("SEK_CONFIG", "~/.short-edit-kit/config.json"))
HF_REPO = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
MODEL_FILES = ["config.json", "model.bin", "preprocessor_config.json", "tokenizer.json", "vocabulary.json"]
PY_PKGS = {"faster_whisper": "faster-whisper", "docx": "python-docx", "PIL": "pillow", "numpy": "numpy", "av": "av", "pypdf": "pypdf", "imageio_ffmpeg": "imageio-ffmpeg"}
NPM_PKGS = ["remotion@4.0.537", "@remotion/cli@4.0.537", "react@19.3.1", "react-dom@19.3.1"]
fails = []


def say(status, what, detail=""):
    print(f"{status:9s} {what:9s} {detail}")
    if status == "FAIL":
        fails.append(what)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def pip_install(py, pkgs):
    cmd = [py, "-m", "pip", "install", "--quiet", *pkgs]
    r = run(cmd)
    ca = os.path.expanduser("~/corporate-ca.pem")
    if r.returncode and "SSL" in r.stderr and os.path.exists(ca):
        r = run(cmd + ["--cert", ca])  # corporate TLS inspection
    return r


def check_python(tools):
    venv = os.path.join(tools, "venv")
    py = os.path.join(venv, "bin", "python")
    if not os.path.exists(py):
        r = run([sys.executable, "-m", "venv", venv])
        if r.returncode:
            say("FAIL", "python", f"could not create venv: {r.stderr.strip()[:200]}")
            return None
        say("INSTALLED", "python", f"new venv {venv}")
    missing = [pip for mod, pip in PY_PKGS.items() if run([py, "-I", "-c", f"import {mod}"]).returncode]
    if missing:
        r = pip_install(py, missing)
        if r.returncode:
            say("FAIL", "python", f"pip install {' '.join(missing)} failed: {r.stderr.strip()[-300:]}")
            return py
        say("INSTALLED", "python", ", ".join(missing))
    v = run([py, "-I", "-c", "import faster_whisper,sys;print(sys.version.split()[0], faster_whisper.__version__)"]).stdout.split()
    say("OK", "python", f"{py} (Python {v[0]}, faster-whisper {v[1]})")
    return py


def audio_chain_ok(ff):
    """The mix's last pass on a 1 s plain stereo WAV (written like build_mix.py writes it): two-pass loudnorm ->
    48 kHz AAC. Some PATH builds (ffmpeg-static 6.0) cannot pick a channel layout there and fail."""
    import math
    import struct
    import tempfile
    import wave
    with tempfile.TemporaryDirectory() as d:
        wav, m4a = os.path.join(d, "t.wav"), os.path.join(d, "t.m4a")
        with wave.open(wav, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(48000)
            tone = [int(3000 * math.sin(2 * math.pi * 440 * i / 48000)) for i in range(48000)]
            w.writeframes(struct.pack(f"<{2 * len(tone)}h", *(v for x in tone for v in (x, x))))
        r = run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-af",
                 "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=-30:measured_TP=-15:measured_LRA=4:measured_thresh=-40:offset=0.5:linear=true,aresample=48000",
                 "-c:a", "aac", "-b:a", "192k", m4a])
        return r.returncode == 0


def check_ffmpeg(tools, py):
    """Order: TOOLS/bin/ffmpeg, the static build pinned in the venv (imageio-ffmpeg), any ffmpeg on PATH.
    The first with libx264, libvpx-vp9, aac and a working audio chain is linked to TOOLS/bin/ffmpeg."""
    target = os.path.join(tools, "bin", "ffmpeg")
    cands = [target]
    if py:
        r = run([py, "-I", "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"])
        if r.returncode == 0:
            cands.append(r.stdout.strip())
    cands.append(shutil.which("ffmpeg") or "")
    rejected = []
    for ff in (c for c in cands if c and os.path.exists(c)):
        enc = run([ff, "-hide_banner", "-encoders"]).stdout
        need = [e for e in ("libx264", "libvpx-vp9", "aac") if e not in enc]
        if need or not audio_chain_ok(ff):
            rejected.append(f"{ff} ({'lacks ' + ', '.join(need) if need else 'loudnorm/aac chain fails'})")
            continue
        if ff != target:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if os.path.lexists(target):
                if not os.path.islink(target):  # a real binary someone put there: leave it, say so
                    say("FAIL", "ffmpeg", f"{target} fails the checks; move it away and rerun")
                    return None
                os.unlink(target)
            os.symlink(ff, target)
            say("INSTALLED", "ffmpeg", f"linked {ff}")
        ver = run([target, "-version"]).stdout.split("\n")[0].split(" ")[2]
        say("OK", "ffmpeg", f"{target} ({ver}; libx264, libvpx-vp9, aac, loudnorm)")
        return target
    say("FAIL", "ffmpeg", "no usable ffmpeg" + (f"; rejected: {'; '.join(rejected)}" if rejected else "; install imageio-ffmpeg into the venv and rerun"))
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def hf_listing():
    try:
        with urllib.request.urlopen(f"https://huggingface.co/api/models/{HF_REPO}/tree/main", timeout=30) as r:
            return {f["path"]: f for f in json.load(r)}
    except Exception:  # offline or blocked: fall back to the saved SHA256SUMS
        return None


def check_model(tools):
    d = os.path.join(tools, "models", "large-v3-turbo")
    os.makedirs(d, exist_ok=True)
    sums_path = os.path.join(d, "SHA256SUMS.json")
    saved = json.load(open(sums_path)) if os.path.exists(sums_path) else {}
    listing = hf_listing()
    for name in MODEL_FILES:
        p = os.path.join(d, name)
        want = (listing or {}).get(name, {}).get("size") or saved.get(name, {}).get("size")
        if os.path.exists(p) and (not want or os.path.getsize(p) == want):
            continue
        if listing is None:
            say("FAIL", "model", f"{name} missing/incomplete and Hugging Face unreachable")
            return None
        # HF downloads stall on this network: curl with resume, retried.
        url = f"https://huggingface.co/{HF_REPO}/resolve/main/{name}"
        for _ in range(20):
            run(["curl", "-L", "-C", "-", "--retry", "5", "--retry-delay", "3", "-sS", "-o", p, url])
            if os.path.exists(p) and os.path.getsize(p) == want:
                break
        if not os.path.exists(p) or os.path.getsize(p) != want:
            say("FAIL", "model", f"{name}: download incomplete")
            return None
        say("INSTALLED", "model", name)
    oid = (listing or {}).get("model.bin", {}).get("lfs", {}).get("oid") or saved.get("model.bin", {}).get("sha256")
    got = sha256(os.path.join(d, "model.bin"))
    if oid and got != oid:
        say("FAIL", "model", f"model.bin SHA-256 mismatch ({got[:12]} != {oid[:12]}); delete it and rerun")
        return None
    json.dump({n: {"size": os.path.getsize(os.path.join(d, n)), **({"sha256": got} if n == "model.bin" else {})} for n in MODEL_FILES}, open(sums_path, "w"), indent=1)
    say("OK", "model", f"{d} (SHA-256 {'verified' if oid else 'recorded, unverified offline'})")
    return d


def check_remotion(tools):
    d = os.path.join(tools, "remotion")
    node = shutil.which("node")
    if not node:
        say("FAIL", "remotion", "node not found (install Node 18+ from nodejs.org without admin: use the macOS .tar.gz into ~/)")
        return None
    if not os.path.exists(os.path.join(d, "node_modules", "@remotion", "cli")):
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(os.path.join(d, "package.json")):
            run(["npm", "init", "-y"], cwd=d)
        r = run(["npm", "install", "--no-fund", "--no-audit", *NPM_PKGS], cwd=d)
        if r.returncode:
            say("FAIL", "remotion", f"npm install failed: {r.stderr.strip()[-300:]}")
            return None
        say("INSTALLED", "remotion", " ".join(NPM_PKGS))
    v = json.load(open(os.path.join(d, "node_modules", "remotion", "package.json")))["version"]
    say("OK", "remotion", f"{d} (remotion {v}, node {run([node, '-v']).stdout.strip()})")
    return d


BROWSER_JS = r"""
const path = require('path');
const d = path.dirname(require.resolve('@remotion/renderer/package.json')) + '/dist/browser/';
const f = require(d + 'BrowserFetcher.js'), u = require(d + 'get-chrome-download-url.js');
const m = 'headless-shell', p = f.getPlatform();
console.log(JSON.stringify({ platform: p, url: u.getChromeDownloadUrl({ platform: p, version: null, chromeMode: m }),
  want: f.getExpectedVersion({ version: null, chromeMode: m, platform: p }), have: f.readVersionFile(m), ...f.getRevisionInfo(m) }));
"""


def check_browser(rem):
    """Chrome Headless Shell for Remotion, fetched with curl resume (Remotion's own downloader cannot resume and
    stalls on slow networks), unpacked where Remotion looks for it, with its VERSION marker."""
    r = run(["node", "-e", BROWSER_JS], cwd=rem)
    if r.returncode:
        say("FAIL", "browser", f"could not read Remotion's browser info: {r.stderr.strip()[-200:]}")
        return None
    b = json.loads(r.stdout)
    exe, folder, plat = b["executablePath"], b["folderPath"], b["platform"]
    if b["have"] == b["want"] and os.path.exists(exe):
        say("OK", "browser", f"Chrome Headless Shell {b['want']}")
        return exe
    downloads = os.path.dirname(folder)
    os.makedirs(downloads, exist_ok=True)
    part = os.path.join(downloads, "headless-shell.zip.part")
    for _ in range(30):
        c = run(["curl", "-L", "-C", "-", "--retry", "5", "--retry-delay", "3", "--speed-limit", "20000", "--speed-time", "30",
                 "-sS", "-o", part, b["url"]])
        if c.returncode == 0:
            break
    import zipfile
    if not zipfile.is_zipfile(part):
        say("FAIL", "browser", f"download incomplete ({b['url']}); run setup again, it resumes")
        return None
    shutil.rmtree(folder, ignore_errors=True)
    x = run(["ditto", "-x", "-k", part, folder] if sys.platform == "darwin" else ["unzip", "-q", part, "-d", folder])
    if x.returncode:
        say("FAIL", "browser", f"unpack failed: {x.stderr.strip()[-200:]}")
        return None
    for sub in ("chrome-linux", "chrome-headless-shell-linux64"):  # Linux archives: Remotion's own renames
        src = os.path.join(folder, sub)
        if os.path.exists(os.path.join(src, "chrome")):
            os.rename(os.path.join(src, "chrome"), os.path.join(src, "chrome-headless-shell"))
        dst = os.path.join(folder, f"chrome-headless-shell-{plat}")
        if os.path.exists(src) and src != dst:
            os.rename(src, dst)
    if not os.path.exists(exe):
        say("FAIL", "browser", f"{exe} missing after unpack")
        return None
    os.chmod(exe, 0o755)
    open(os.path.join(downloads, "VERSION"), "w").write(b["want"])
    os.remove(part)
    say("INSTALLED", "browser", f"Chrome Headless Shell {b['want']}")
    return exe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools-dir", default=os.path.expanduser("~/video-tools"))
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--brand", default="groww")
    a = ap.parse_args()
    tools = os.path.abspath(os.path.expanduser(a.tools_dir))
    py = check_python(tools)
    ff = check_ffmpeg(tools, py)
    model = check_model(tools)
    rem = check_remotion(tools)
    if rem and not check_browser(rem):
        rem = None
    brand_ok = os.path.exists(os.path.join(PLUGIN_ROOT, "brands", a.brand, "brand.json"))
    say("OK" if brand_ok else "FAIL", "brand", os.path.join(PLUGIN_ROOT, "brands", a.brand))
    if fails:
        sys.exit(f"setup FAILED: {', '.join(fails)}")
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    json.dump({"tools_dir": tools, "ffmpeg": ff, "python": py, "model": model, "remotion_dir": rem, "brand": a.brand}, open(CONFIG, "w"), indent=1)
    say("OK", "config", CONFIG)
    if a.skip_render:
        return
    job = os.path.join(os.path.dirname(CONFIG), "selftest")
    os.makedirs(job, exist_ok=True)
    r = run([py, "-I", os.path.join(HERE, "render.py"), job, "--test"])
    out = os.path.join(job, "out", "test.mp4")
    if r.returncode or not os.path.exists(out):
        say("FAIL", "render", (r.stdout + r.stderr).strip()[-400:])
        sys.exit("setup FAILED: render")
    dur = run([py, "-I", "-c", f"import av;c=av.open({out!r});print(round(c.duration/1e6,2), c.streams.video[0].codec_context.width, c.streams.video[0].codec_context.height)"]).stdout.split()
    ok = abs(float(dur[0]) - 10) < 0.2 and dur[1:] == ["1080", "1920"]
    say("OK" if ok else "FAIL", "render", f"{out} ({dur[0]}s, {dur[1]}x{dur[2]})")
    if not ok:
        sys.exit("setup FAILED: render output wrong")
    print("setup PASSED")


if __name__ == "__main__":
    main()
