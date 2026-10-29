# short-edit-kit-groww

A Claude Code plugin that turns **raw green-screen footage + a finished script** into an **edited vertical Short** (1080x1920).

It transcribes the narration, cuts retakes and extra spoken words so the audio matches the script, adds English captions (the spoken word lights up), keys and grades the presenter, builds animated infographics with Remotion, mixes a music bed and effects, and finishes with an independent QA check on numbers, captions, safe zones and loudness.

The brand pack in `brands/groww/` (logo, colours, guidelines, disclaimer and RA lines) belongs to Groww and is included for Groww's own team; the Groww name and logo are Groww's trademarks. Swap in your own pack for other brands (`brands/README.md`).

## Quick start

```bash
npx -y short-edit-kit-groww@latest
```

Run alone, it prints the manual (the whole workflow). Then, once per laptop:

```bash
npx -y short-edit-kit-groww@latest setup
```
```bash
npx -y short-edit-kit-groww@latest install-claude
```

`setup` installs or verifies ffmpeg, a Python venv with faster-whisper, the Whisper large-v3-turbo model (curl with resume, SHA-256 checked against Hugging Face) and Remotion, all under `~/video-tools` (`--tools-dir DIR` for another place), then renders a 10-second test video and ends with `setup PASSED`. Run it again any time: it only installs what is missing. `install-claude` adds the skills and agents below to Claude Code; restart Claude Code afterwards.

`@latest` always runs the newest published version, so fixes arrive without reinstalling.

## Requirements

| Need | How to check | If missing |
|---|---|---|
| Python 3.9+ | `python3 --version` | macOS offers to install developer tools; accept (or python.org) |
| Node 18+ | `node --version` | Install from https://nodejs.org |
| About 2.5 GB free disk | | The speech model alone is 1.6 GB; Remotion and the venv about 0.8 GB |
| Claude Code (for the agent workflow) | `claude --version` | https://claude.com/claude-code |

No admin password and no Homebrew needed. macOS and Linux.

## Commands

Every command prints a one-line summary; `npx -y short-edit-kit-groww@latest <command> --help` shows its arguments.

| Command | Does |
|---|---|
| `setup`, `install-claude`, `doctor` | install and verify; register with Claude Code; show the config |
| `init` | job folder from footage + script (DOCX, PDF or text) |
| `key` | green-screen key (`--greenness`, `--unmix` for yellow-green screens and long hair) or `--plain` grade |
| `transcribe` | Whisper word timings |
| `extra-words`, `cuts` | spoken words not in the script; kept segments |
| `audio`, `joins` | voice track; re-transcribe every join |
| `align`, `plan`, `captions` | script on the timeline; plan.json -> edit.json; English captions as SRT/VTT |
| `mix`, `render`, `stills`, `qa` | sound, Remotion render, contact sheet, deterministic QA |
| `openfilm` | only on request: also export the job as an OpenFilm project (the default output stays out/final.mp4) |

## Remotion license

Rendering uses [Remotion](https://www.remotion.dev). Remotion is free for individuals and companies with up to 3 employees; larger companies need a paid company license. See https://www.remotion.dev/license before using this kit at work.

## OpenFilm output (only on request)

The normal output is the Remotion render, `jobs/<name>/out/final.mp4`. The OpenFilm export is made only when you ask for OpenFilm. `openfilm JOB` writes `JOB/film/`: `film.html` with the logo, the presenter cut by the job's segments and a plain ground, the presenter baked onto the brand ground as H.264 with normalised audio, English captions as WebVTT with word timings, and shot templates. Open it with `npx -y openfilm@latest open JOB/film` and write one page per shot (`npx -y openfilm@latest` prints OpenFilm's manual).

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

The command line updates itself: `npx -y short-edit-kit-groww@latest` always fetches the newest version. To update the Claude Code skills and agents, run `install-claude` again (it updates an existing install), then restart Claude Code.

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
| `install-claude` says repository not found | Check the spelling `Preethzzzz` (three z's) and your internet connection |
| Setup shows `FAIL` on a line | That line names the missing tool; install it and run setup again |
| Model download stalls | Run `setup` again; it resumes |
| `node` not found or too old | Install Node 18+ from https://nodejs.org |
| Music too loud or effects annoying | Change `levelDb`, `popDb`, `whooshDb` in `brands/groww/brand.json` |
| QA fails a number | The number is not in the script or `facts.txt`; correct the plan or the script |

Footage, renders and models are never committed (`.gitignore`).
