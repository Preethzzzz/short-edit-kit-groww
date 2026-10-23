# Brand packs

One folder per brand. The workflow reads every brand value from here; nothing brand-specific is typed in scripts, templates or agents.

Required in `<name>/`:
- `brand.json` with the keys of `groww/brand.json`: `canvas`, `palette`, `series`, `tones` (profit / loss / note / neutral, each main/dark/tint), `themes`, `defaultTheme`, `fonts`, `logo` (onLight / onDark / icon paths + width/right/top), `layout` (header band, safe zone, card and caption positions), `header`, `channels` (tag + disclaimer per channel), `compliance` (opening lines, RA line template), `motion`, `captions`, `framing`, `presenterGrade` (ffmpeg filter string), `audio`, `video`.
- `BRAND_GUIDELINES.md` (human rules the agents read: pace, colour meaning, templates).
- `logo/` files referenced by `brand.json`.

Select a pack: `"brand": "<name>"` in `~/.short-edit-kit/config.json`, or `SEK_BRAND=<name or folder path>`.
For a public release, ship a neutral pack and remove `groww/`.
