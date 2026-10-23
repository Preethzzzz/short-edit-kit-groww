# Format: Data Explainer

Vertical Short (1080x1920, about 1:30-2:00) that explains one finding from a study, report or dataset: presenter on green screen for talk lines, full-screen data cards for the numbers. Approved reference: mutual-fund video "Should you stop looking at returns?" (22 Oct 2026, FundsIndia report data). Rebuilt plan: `reference/plan.json`. The brand pack overrides anything here that conflicts with it.

## When to use
- One question answered with data ("does last 5 years' top fund stay on top?"), any channel.
- Not for multi-company IPO lists (use IPO Day Roundup).

## Plan settings
`"layout": "full"` (cards replace the A-roll full-screen), `"channel"` per the video (`mutual-funds` or `ipo-review`), theme `light-blue` (light ground + dot grid). fps = the footage fps (the reference was 25).

## Structure
| Beat | On screen |
|---|---|
| Hook question (0-5 s) | talk MCU, then `KineticLine` with the question, one accent phrase |
| Headline finding | `TileDrop` ("4 of 5 lose the spot") or `DotGrid` ("only 4 of 100") or `BigNumber` |
| Source / method | `DocCard`: report name, date, what it covered (pills) |
| Key numbers | `Bars` (2-5 values), `ImageCallout` on the source chart with boxes on the rows being discussed |
| Why | `KineticLine` with the reason, then `RowsReveal` / `Ranking` |
| Caveat | `Ranking` note or `NoteCard` (yellow = note) |
| What to do instead | `Checklist` |
| Close | talk WIDE, end card with the channel disclaimer + RA line |

## Rhythm (brand)
- Talk stretches: beats without a component, `"framing": "MCU"` on emphasis/number lines, `"WIDE"` on setup lines; switch every 1-3 sentences.
- Change something visual every 2-4 s; no static hold over 5 s (cards push in slowly by themselves).
- Every borrowed number has `"source"` on its beat (shown top-right under the logo).
- Profit/loss colours only where the data is good/bad (stayed on top = profit, dropped = loss); everything else neutral or accent.

## Checks before handover
Same as every format: on-screen numbers vs script, captions vs audio, safe zones, end card + RA, report of cuts and differences.
