---
name: setup
description: Install or verify the Short editing toolchain (ffmpeg, Python venv with faster-whisper, Whisper large-v3-turbo model, Remotion) without admin rights, write ~/.short-edit-kit/config.json, and run a 10-second test render. Use on first install, on a new Mac, or when an edit-short step fails on a missing tool.
---

# Setup

Run (it reuses existing installs under `~/video-tools`; pass `--tools-dir` for another location):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
```

It prints one line per check (`OK` / `INSTALLED` / `FAIL`) and ends with `setup PASSED` after a 10 s 1080x1920 test render (`~/.short-edit-kit/selftest/out/test.mp4`). Run it in the background if it has to download the model (1.6 GB).

What it does, in order:
- **python**: `TOOLS/venv`; creates it and pip-installs any missing package (faster-whisper, python-docx, pillow, numpy, av, pypdf, imageio-ffmpeg). Retries with `~/corporate-ca.pem` on TLS errors.
- **ffmpeg**: `TOOLS/bin/ffmpeg`, else ffmpeg on PATH, else links the static build from imageio-ffmpeg. Needs libx264, libvpx-vp9, aac. No Homebrew, no admin.
- **model**: `TOOLS/models/large-v3-turbo` from `mobiuslabsgmbh/faster-whisper-large-v3-turbo`. Downloads stall on this network, so it uses `curl -C -` with retries, checks every file size and model.bin's SHA-256 against Hugging Face, and saves `SHA256SUMS.json` for offline re-checks.
- **remotion**: `TOOLS/remotion` npm project (remotion + @remotion/cli 4.0.537, react 19.3.1); needs Node 18+.
- **brand**: the pack in `brands/<name>/` exists. Writes `~/.short-edit-kit/config.json`.

On FAIL: report the failing line to the user with the fix it suggests; do not work around a missing tool silently.
