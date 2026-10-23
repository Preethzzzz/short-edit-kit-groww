---
name: format-data-explainer
description: Format rules for the "Data Explainer" Short - one data-backed finding (study, report, dataset) with presenter talk lines and full-screen data cards, modelled on the approved mutual-fund video "Should you stop looking at returns?". Load with edit-short for explainer scripts built around numbers from a report.
---

# Format: Data Explainer

Read `${CLAUDE_PLUGIN_ROOT}/formats/data-explainer/FORMAT.md` and use `${CLAUDE_PLUGIN_ROOT}/formats/data-explainer/reference/plan.json` as the worked example (that archived plan uses seconds; a new job uses script phrases as anchors and drops its `timing` block).

Plan defaults: `"layout": "full"`, `"theme": "light-blue"`, channel per video, fps = footage fps.

Must-haves:
- Talk stretches are beats without a component: `"framing": "MCU"` on emphasis/number lines, `"WIDE"` on setup lines, switching every 1-3 sentences.
- Every borrowed number has `"source"` on its beat.
- Profit/loss tones only where the data itself is good/bad; caveats in yellow (`NoteCard` or `Ranking.note`).
- No visual held over 5 s without a new element; something changes every 2-4 s.
