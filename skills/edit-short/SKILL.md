---
name: edit-short
description: Edit raw green-screen footage plus a finished script (DOCX, PDF or text) into a branded vertical Short. Runs the full flow - job setup, keying, transcription, retake and extra-word cuts synced to the script, English captions, visual plan, Remotion render, independent QA. Use when the user gives footage + script and asks for an edited Short / reel / video.
---

# Edit a Short

Input: raw vertical footage (MP4/MOV) + finished script. Output: `JOB/out/final.mp4` + a report.
Editing only: never write or rewrite the script itself.

`K=${CLAUDE_PLUGIN_ROOT}` · `PY="<python from ~/.short-edit-kit/config.json> -I"` (run every script as `$PY $K/scripts/<name>.py`).
Scripts print one-line summaries; read detail files (`*.txt`, `qa_checks.md`) only when needed. Run anything over ~2 min in the background (transcribe, key run, render).

## Rules (standing, from the user)
- Brand comes from the brand pack (`$K/brands/<brand>/brand.json` + `BRAND_GUIDELINES.md`). Never type a colour, font, logo path or disclaimer anywhere else.
- Captions in English, translated phrase by phrase from the Hinglish narration: exact meaning, no added claims, no dropped qualifiers ("kam se kam" = "at least", "lagbhag" = "about"), every number and name unchanged; each caption timed to the Hinglish phrase it translates.
- Narration must match the script: cut spoken words not in the script (fillers, added lead-ins, retakes) when the cut is clean; verify every cut by re-transcribing the joined audio (`check_joins.py`). Not extra: Whisper-split numbers, "rupees" for ₹, split hyphenated words, Hindi spellings of English words.
- Hindi-heavy audio: Whisper `--lang hi`, no English `--prompt` (it translates otherwise). Full-clip runs merge repeated takes: re-check suspicious stretches with `--pieces`.
- Every on-screen number matches the script (or `work/facts.txt`, read off the script's images). Logo top-right whole video with nothing around it, not even footage background marks (logo clear zone: canvas x 740-1080, y 0-360; paint out with `key.py --plain --clean`), header band y 0-220 kept clear, source credit top-right under the logo. Ease-out only, no bounce, no progress bar.
- Sound and rhythm come from the brand pack, automatically: an original synthesized music bed (ducked under speech) plus whoosh/pop effects on card entries and items, mixed to the loudness target (`build_mix.py`, run by `render.py`; `"sound": false` in the plan turns it off, `brands/<name>/brand.json` audio.bed.file swaps in a licensed track). Captions highlight the spoken word. Automatic punch-in cuts keep the presenter changing every 3-4.5 s (`"autoPunch": false` turns off). QA fails any stretch over 6 s with no change, and fails a final render outside 1 LU of the loudness target.
- Green screen: sample the colour per shoot; chromakey on clean screens, `--greenness 6 16 GARBAGE_Y` on dull/uneven ones, add `--unmix` (try `2 18`) for yellow-green screens with long hair (olive fringe); face mask must have no holes. Grade and audio targets come from the brand pack.
- Cost: keep context small. Agents pass work through files in `JOB/work/`, not chat; every agent prompt is just `K=<plugin root> JOB=<job path>` plus the task. All agents run on Opus.

## Steps
0. **Preflight.** If `~/.short-edit-kit/config.json` is missing, run the `setup` skill first. Ask the user, in ONE batched question: format (if not obvious: `ipo-day-roundup` or `data-explainer`, see the format skills), channel (`ipo-review` / `mutual-funds`), RA name and RA date, header topic text, job name. Load the matching format skill.
1. **Job.** `$PY $K/scripts/init_job.py FOOTAGE SCRIPT --name SLUG --format F --channel C --root jobs` (jobs live in the current project folder). Put RA name/date into `job.json`.
2. **Script + images.** Read `work/script_raw.txt`. View every image in `work/images/` and map it by what it shows (never by filename). Write `work/script.txt`: the spoken words only, exactly as written (no headings, `[IMAGE]` markers, source lines, RA block). Write `work/facts.txt`: numbers read off images, one per line with the image name. Copy images that will appear on screen into `public/` (crop/reflow with `reflow.py` as needed).
3. **Key (background).** `key.py sample inputs/raw.*` -> `key.py test ... work/key_test.png` with the suggested keyer; view the sheet, pick the strength with ~0% holes -> `key.py run inputs/raw.* public/presenter.webm ...` in the background. Use `--trim A-B` only to drop long dead footage (offset is recorded in `presenter.json`; put it in plan.presenter.offset). No green screen (sample says `--plain`): `key.py run inputs/raw.* public/presenter.mp4 --plain` (graded, opaque) and use layout `full` whatever the format (card-top needs a keyed presenter); keep the presenter on screen 35%+ of the runtime (build_plan warns under 30%).
4. **Transcribe (background).** `transcribe.py inputs/raw.* work/words_raw.json --lang hi`.
5. **Editor agent** (`editor`, Opus): takes, cuts, `segments.json`, `public/voice.m4a`, `aligned.json`, joins check, English captions into `work/plan.json`, `work/edit_report.md`.
6. **Content strategist agent** (`content-strategist`, Opus): `work/visual_plan.md` (one visual per script line) - can start as soon as step 2 is done, in parallel with 3-5.
7. **Infographics agent** (`infographics`, Opus): turns the visual plan into `beats`, `sections`, `checks` in `work/plan.json`. If the plan needs a component or scene the library lacks, spawn **motion-graphics** for that design; otherwise motion-graphics does the timing/motion pass.
8. **Assemble.** `build_plan.py work/plan.json work/edit.json --aligned work/aligned.json --segments work/segments.json --job job.json` (fix every ERROR; read warnings). Preview: `render.py JOB --frames 0-299 --out out/preview.mp4`, then `stills.py`; fix, then full `render.py JOB` in the background, then `stills.py out/final.mp4 out/sheet.png --edit work/edit.json`.
8b. **OpenFilm output (optional, only when the user asks for OpenFilm / Studio).** After step 8, `openfilm_export.py JOB` makes `JOB/film/` (film.html with logo, presenter cut by segments, ground; baked presenter.mp4 + English presenter.vtt; shot templates). Read the OpenFilm manual (`npx -y openfilm@latest`), open the project (`npx -y openfilm@latest open JOB/film`), write one page per shot from `visual_plan.md`, check with `look`. Studio draws subtitles at ~72% height: keep y 1300-1460 free.
9. **QA agent** (`qa-checker`, Opus, fresh context, give it only the job path). It writes `work/qa_report.md` with PASS/FAIL. On FAIL send the items to the owner agent (numbers/props: infographics; cuts/captions/audio: editor; motion/layout: motion-graphics), rebuild, re-render, re-run QA until PASS.
10. **Report to the user** (short): output path; every removed word/retake with raw timestamps; every place she said something different from the script (e.g. "4" for "chaar"); names Whisper heard oddly (check by ear); creative decisions taken without instruction; anything unverified.

## Files (JOB/)
`job.json` · `inputs/raw.*`, `inputs/script.*` · `work/`: `script_raw.txt`, `images/`, `script.txt`, `facts.txt`, `words_raw.json(.txt)`, `segments.json`, `aligned.json`, `visual_plan.md`, `plan.json`, `edit.json`, `edit_report.md`, `qa_checks.md`, `qa_report.md` · `public/`: `presenter.webm`, `voice.m4a`, on-screen images, `brand/` · `custom/`: job-local components · `out/`: `final.mp4`, `sheet.png`, `render.log`. `public/mix.m4a` is the finished soundtrack (made at render time).

Plan schema: `$K/templates/remotion/components.json` (components, props, scenes) and the header of `$K/scripts/build_plan.py` (anchors). Worked examples: `$K/formats/*/reference/plan.json`.
