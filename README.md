# short-edit-kit-groww

A Claude Code plugin that turns **raw green-screen footage + a finished script** into an **edited vertical Short** (1080x1920).

It transcribes the narration, cuts retakes and extra spoken words so the audio matches the script, adds English captions (the spoken word lights up), keys and grades the presenter, builds animated infographics with Remotion, mixes a music bed and effects, and finishes with an independent QA check on numbers, captions, safe zones and loudness.

The brand pack in `brands/groww/` (logo, colours, guidelines) belongs to Groww. Swap in your own pack for other brands.

## What you need (once per laptop)

| Need | How to check | If missing |
|---|---|---|
| Mac with Claude Code | `claude --version` | Install Claude Code from https://claude.com/claude-code |
| Python 3 | `python3 --version` | macOS offers to install developer tools; accept |
| Node 18 or newer | `node --version` | Install from https://nodejs.org |
| About 2 GB free disk | | The speech model alone is 1.6 GB |

No admin password and no Homebrew needed.

## Install

Run in Terminal, in this order, once per laptop:

```bash
claude plugin marketplace add Preethzzzz/short-edit-kit-groww
```
```bash
claude plugin install short-edit-kit-groww@groww-video
```

Then open Claude Code and run:

```
/short-edit-kit-groww:setup
```

Setup installs or checks ffmpeg, a Python environment with faster-whisper, the Whisper large-v3-turbo model, and Remotion (all under `~/video-tools`), then renders a 10-second test video. The first run downloads about 1.6 GB and can take several minutes; if it stalls, run it again and it resumes. It ends with `setup PASSED`.

## Edit a Short

In Claude Code, from the folder where you want your jobs saved, say for example:

> Edit this Short. Footage: `/path/to/video.mp4`. Script: `/path/to/script.docx`

Inputs: vertical MP4 or MOV shot on a green screen, and the finished script as DOCX, PDF or text.
It asks once for the format, channel, RA name and RA date, and header topic. The finished video is `jobs/<name>/out/final.mp4`, with a short report of every cut, every place the audio differs from the script, and anything to check by ear.

| Format | Use for |
|---|---|
| `ipo-day-roundup` | 2 to 5 IPOs opening on the same day: hook, concept explainer, one card per company |
| `data-explainer` | One data finding from a report or study: talk lines plus full-screen data cards |

## Update

When a new version is published:

```bash
claude plugin marketplace update groww-video
```
```bash
claude plugin update short-edit-kit-groww@groww-video
```

## What is inside

| Skill | Purpose |
|---|---|
| `edit-short` | Full flow: job setup, keying, transcribe, cuts synced to the script, English captions, visual plan, render, QA |
| `format-ipo-day-roundup` | Rules for the IPO roundup format |
| `format-data-explainer` | Rules for the data explainer format |
| `setup` | Install or verify the tools and run the test render |

| Agent | Job |
|---|---|
| `content-strategist` | One visual per script line |
| `infographics` | Exact card data, anchors, sources and arithmetic checks |
| `motion-graphics` | Timing and pace pass; new designs when the library lacks one |
| `editor` | Takes, retakes, extra words, voice track, alignment, English captions |
| `qa-checker` | Independent check of numbers, captions, safe zones, brand, loudness |

## How it works

- `plan.json` (cards and captions tied to script phrases) -> `build_plan.py` -> `edit.json` (seconds and brand values) -> `render.py` -> `out/final.mp4`.
- Sound: an original synthesized music bed (ducked under speech) plus whoosh and pop effects, mixed to the brand loudness target. A brand pack can supply its own licensed track.
- Pacing: automatic punch-in cuts every 3 to 4.5 seconds; QA fails any stretch over 6 seconds with no change.
- Anchors in a plan: a verbatim script phrase, `{"phrase", "after", "edge", "offset"}`, `"start"`, `"end"` or seconds.
- Turn features off per video with `"sound": false` or `"autoPunch": false` in the plan.

## Brand packs

One folder per brand under `brands/`. The workflow reads every brand value from there (palette, tones, fonts, logo, safe zones, captions, disclaimers, grade, audio, loudness); nothing brand-specific is hard-coded. See `brands/README.md`. Select a pack with `SEK_BRAND=<name>` or `"brand"` in `~/.short-edit-kit/config.json`.

## Folders

- `scripts/` pipeline steps; each prints a short summary. `legacy/` holds the original per-video builders.
- `templates/remotion/` the generic video template and the component catalogue (`components.json`).
- `brands/groww/` brand pack. `formats/` format specs with worked example plans.

## Troubleshooting

| Problem | Fix |
|---|---|
| `marketplace add` says repository not found | Check the spelling `Preethzzzz` (three z's) and your internet connection |
| Setup shows `FAIL` on a line | That line names the missing tool; install it and run setup again |
| Model download stalls | Run `/short-edit-kit-groww:setup` again; it resumes |
| `node` not found or too old | Install Node 18+ from https://nodejs.org |
| Music too loud or effects annoying | Change `levelDb`, `popDb`, `whooshDb` in `brands/groww/brand.json` |
| QA fails a number | The number is not in the script or `facts.txt`; correct the plan or the script |

Footage, renders and models are never committed (`.gitignore`).
