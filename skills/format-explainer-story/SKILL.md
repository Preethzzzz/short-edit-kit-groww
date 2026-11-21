---
name: format-explainer-story
description: Format rules for the "Explainer Story" Short - one "how did this happen?" story told by the presenter keyed onto a single realistic photo background, with source-quote cards above her, clean diagrams and 2-3 Gemini AI b-roll clips; modelled on "How JK shah listed without an IPO?" with its errors fixed. Load with edit-short for story / mechanism scripts (listing without an IPO, demerger, rule change).
---

# Format: Explainer Story

Read `${CLAUDE_PLUGIN_ROOT}/formats/explainer-story/FORMAT.md` (structure, background, presenter matching, rhythm, reference errors) and `${CLAUDE_PLUGIN_ROOT}/formats/explainer-story/PROMPTS.md` (Gemini prompt rules, clip template, background prompt, worked example).

Plan defaults: `"layout": "card-top"`, one section `{"scene": "photo"}`, `"background": {"src": "bg.jpg", "blur": 4, "dim": 0.0}` with `bg.jpg` copied from `brands/groww/backgrounds/white-room.jpg`, `"sebi": {"position": "bottom", "openingSeconds": 3, "closingSeconds": 3}`, `presenter.look` tuned on a full-size still, fps = footage fps.

Must-haves:
- One background photo for the whole video. Her colour, brightness and rim light are matched to it on a test still before the full render.
- 2-3 `Clip` beats (2-4 s, labelled "AI-generated visual"), never two in a row; the Gemini prompts go to the user as soon as the visual plan exists.
- Quote/source cards cropped to the highlighted lines, under 6 s, presenter stays on screen (55%+ of runtime).
- SEBI lines only in the first 3 s and last 3 s, bottom centre; punch-in max 1.2x.
