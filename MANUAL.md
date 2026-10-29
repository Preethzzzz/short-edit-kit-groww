# short-edit-kit-groww

You edit raw presenter footage (green screen or a plain wall) plus a finished script into a branded vertical Short (1080x1920): cut retakes and words that are not in the script, English captions, Groww infographics, music bed and effects, Remotion render, independent QA. Ships with the Groww brand pack. Editing only: the script is never rewritten.

## Once

    npx -y short-edit-kit-groww@latest setup            # ffmpeg, Python venv + faster-whisper, Whisper large-v3-turbo (1.6 GB, SHA-256 checked), Remotion; 10 s test render
    npx -y short-edit-kit-groww@latest install-claude   # skills + agents into Claude Code; restart Claude Code after

No admin rights needed. Tools go to ~/video-tools (`setup --tools-dir DIR` for another place); the config to ~/.short-edit-kit/config.json. Run `setup` again any time: it verifies and only installs what is missing.

## With Claude Code (the usual way)

In a project folder, give Claude Code the footage and the script: "edit this into a Short". The `edit-short` skill runs the whole flow with five agents (editor, content-strategist, infographics, motion-graphics, qa-checker) and reports every removed word with its timestamp and every place the narration differs from the script.

## By hand: one command per step

Run in the project folder; JOB = jobs/<slug>. Every command prints a one-line summary; `<command> --help` shows its arguments.

    npx -y short-edit-kit-groww@latest init FOOTAGE SCRIPT --name SLUG --format ipo-day-roundup   # or data-explainer
    npx -y short-edit-kit-groww@latest key sample JOB/inputs/raw.mov                               # screen colour, which keyer
    npx -y short-edit-kit-groww@latest key test JOB/inputs/raw.mov JOB/work/key_test.png --greenness 6 16 200
    npx -y short-edit-kit-groww@latest key run JOB/inputs/raw.mov JOB/public/presenter.webm --greenness 6 16 200   # --plain: no green screen
    npx -y short-edit-kit-groww@latest transcribe JOB/inputs/raw.mov JOB/work/words_raw.json --lang hi
    npx -y short-edit-kit-groww@latest extra-words JOB/work/words_raw.json JOB/work/script.txt           # fillers, lead-ins, retakes
    npx -y short-edit-kit-groww@latest cuts JOB/work/words_raw.json JOB/work/segments.json --keep A-B --cut C-D
    npx -y short-edit-kit-groww@latest audio JOB/inputs/raw.mov JOB/work/segments.json JOB/public/voice.m4a
    npx -y short-edit-kit-groww@latest joins JOB/public/voice.m4a JOB/work/segments.json                # every cut re-transcribed
    npx -y short-edit-kit-groww@latest align JOB/work/words_raw.json JOB/work/segments.json JOB/work/script.txt JOB/work/aligned.json
    npx -y short-edit-kit-groww@latest plan JOB/work/plan.json JOB/work/edit.json --aligned JOB/work/aligned.json --segments JOB/work/segments.json --job JOB/job.json
    npx -y short-edit-kit-groww@latest captions JOB                                                     # out/captions.srt + .vtt
    npx -y short-edit-kit-groww@latest mix JOB                                                          # bed + effects + voice
    npx -y short-edit-kit-groww@latest render JOB                                                       # out/final.mp4 (--frames 0-299 to preview)
    npx -y short-edit-kit-groww@latest stills JOB/out/final.mp4 JOB/out/sheet.png --edit JOB/work/edit.json
    npx -y short-edit-kit-groww@latest qa JOB                                                           # work/qa_checks.md, PASS/FAIL

`plan.json` holds the English captions (phrase by phrase, timed to the Hinglish span they translate) and the visual beats, anchored to script phrases, not seconds. Schema: templates/remotion/components.json; worked examples: formats/*/reference/plan.json.

## OpenFilm instead of Remotion (optional)

    npx -y short-edit-kit-groww@latest openfilm JOB      # JOB/film: film.html, presenter cut by the segments, English VTT, shot templates
    npx -y openfilm@latest open JOB/film                 # then write one page per shot; `npx -y openfilm@latest` is its manual

## Rules the kit enforces

- Brand from the brand pack only (brands/groww): palette, fonts, logo top-right for the whole video with nothing around it (x 740-1080, y 0-360, footage marks painted out), disclaimer and RA end card.
- Every on-screen number matches the script character for character; no GMP, no buy/sell/apply advice.
- Captions in English with the exact meaning: no added claims, no dropped qualifiers, numbers and names unchanged.
- Narration matches the script: extra spoken words are cut only where the join re-transcribes clean.

Remotion is free for individuals and small teams; larger companies need a paid Remotion company license (remotion.dev/license).
