# short-edit-kit-groww

Claude Code plugin that edits raw green-screen footage + a finished script into a branded vertical Short.
Repo: https://github.com/Preethzzzz/short-edit-kit-groww. The `brands/groww/` pack (logo, brand guidelines) belongs to Groww; swap in your own pack for other brands.

## Install (each laptop, once)
```bash
claude plugin marketplace add Preethzzzz/short-edit-kit-groww
```
```bash
claude plugin install short-edit-kit-groww@groww-video
```
Then in Claude Code run `/short-edit-kit-groww:setup`. It installs or verifies the tools without admin rights (ffmpeg, a Python venv with faster-whisper, the Whisper large-v3-turbo model, about 1.6 GB, and Remotion) under `~/video-tools`, and ends with a 10-second test render. Needs macOS with `python3` and Node 18+.

## Update (after a new push)
```bash
claude plugin marketplace update groww-video
```
```bash
claude plugin update short-edit-kit-groww@groww-video
```

Footage, renders and models are never committed (`.gitignore`).

## Use
"Edit this Short: footage `<path>`, script `<path>`" -> skill `edit-short` runs the flow and asks once for format, channel, RA name/date and header topic.

| Skill | Purpose |
|---|---|
| `edit-short` | full flow: job, key, transcribe, cuts synced to the script, English captions, visual plan, render, QA |
| `format-ipo-day-roundup` | several IPOs on one day, card-top layout, sector scenes |
| `format-data-explainer` | data finding with talk + full-screen cards (mutual-fund reference) |
| `setup` | ffmpeg, venv + faster-whisper, Whisper large-v3-turbo (curl resume + SHA-256), Remotion; test render |

| Agent | Model | Job |
|---|---|---|
| `content-strategist` | Opus | one visual per script line -> `visual_plan.md` |
| `infographics` | Sonnet | exact props, anchors, sources, arithmetic checks -> `plan.json` |
| `motion-graphics` | Sonnet (Opus for new designs) | job-local components/scenes, timing and pace pass |
| `editor` | Sonnet | takes, retakes, extra words, segments, voice, alignment, join checks, English captions, render |
| `qa-checker` | Sonnet | independent: numbers vs script, captions vs fresh transcript, safe zones, brand, compliance |

## Layout
- Sound: `build_mix.py` + `synth_audio.py` make an original synthesized music bed (no samples, no licences) with whoosh/pop effects, ducked under speech, mixed to the brand loudness target. A brand pack can point `audio.bed.file` at its own licensed track.
- `scripts/` pipeline (short summaries on stdout): `init_job`, `build_mix`, `synth_audio`, `transcribe` (`--pieces` for retakes), `make_segments`, `extra_words`, `build_audio`, `check_joins`, `align`/`align_core`, `key` (+ `greenness_key`), `reflow`, `build_plan`, `render`, `stills`, `qa_check`, `setup`. `legacy/` = the original per-video builders, kept for reference.
- `templates/remotion/` generic `Short` composition driven by `edit.json`; component catalogue `components.json`; `test_plan.json` -> `src/sample.json` (setup test).
- `brands/groww/` swappable brand pack: `brand.json` (palette, tones, themes, fonts, logo placement, layout/safe zones, captions, motion, compliance text, presenter grade, audio targets), `BRAND_GUIDELINES.md`, `logo/`, `source/`. Another brand = another folder with the same keys; select with `SEK_BRAND=<name>` or `"brand"` in `~/.short-edit-kit/config.json`.
- `formats/<format>/FORMAT.md` + `reference/plan.json` worked examples.

## Plan -> video
`plan.json` (script phrases) --`build_plan.py`--> `edit.json` (seconds + brand values) --`render.py`--> `out/final.mp4`.
Anchors: any `at` / `...At` / `until` is a verbatim script phrase, `{"phrase", "after", "edge", "offset"}`, `"start"`, `"end"` or seconds.
