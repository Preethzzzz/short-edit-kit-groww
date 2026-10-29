# Format: IPO Day Roundup

Vertical Short (1080x1920, about 2:00-2:20) covering several IPOs that open on the same day, presented to camera on green screen with animated brand-colour infographics. Approved reference: 4 IPOs opening 15 Oct 2026 (Zetwerk, Bonfiglioli, Tonbo, Sahajanand), approved 22 Oct 2026. Rebuilt plan: `reference/plan.json` (anchors are words of `reference/script.txt`). The brand pack overrides anything here that conflicts with it.

## When to use
- 2 to 5 IPOs opening on the same day (or week) in one Short.
- Script shape: hook with combined size -> one concept explainer (e.g. Fresh issue vs OFS) -> one block per company -> CTA.
- A single-IPO data update (e.g. Day 1 subscription) is still card-top layout: use BigNumber, Bars, Calculation, Timeline, NoteCard beats.

## Inputs
1. Raw green-screen footage (phone, vertical).
2. Script (DOCX/PDF/text) with one X card image per IPO, plus any RHP extracts (objects of the offer table). Map images by what they show, never by filename.

## Plan settings
`"layout": "card-top"`, `"channel": "ipo-review"`, theme `light-blue` unless the user asks otherwise.

## Beats (one per script block)
| Beat | Script cue | Component | Scene |
|---|---|---|---|
| Hook | opening line: number of IPOs + combined size | `StackedTotal`: total count-up, one bar segment per IPO appearing as it is named, BIDDING footer with dates | `market` |
| Concept | "Ek important baat..." | `FlowExplainer`: chip per IPO with its issue type, Fresh lane, OFS lane, "₹0 to the company" callout when OFS proceeds are explained | `market` |
| Company N | each company block | `EntityCard`: number, sector, name, icon, one-line business; price band and issue size appear exactly when spoken; lot size, min. investment (upper band), badge Fresh + OFS / OFS only, retail portion + dates footnote | sector scene |
| Fresh issue split | fresh vs OFS amounts | `SplitBar` (source: RHP) | same sector scene |
| Use of proceeds | objects of the offer | `AmountRows` with the RHP table image panned to its amounts column; never show an amount the RHP marks [●] | same sector scene |
| CTA | "Aise hi IPO updates..." | no card; presenter full frame with `zooms` 1.08; end card at the CTA | `market` |

Sector scenes: `factory` (manufacturing), `gears` (industrial, power transmission, energy), `radar` (defence, imaging), `medical` (healthcare, devices), `telecom` (telecom, digital), `market` (intro, CTA). A sector with no fitting scene: the motion-graphics agent adds one (job-local `custom/`), same vector style, no logos or photos.

## Numbers
- Badge text carries no number the script does not say ("OFS only", not "100% OFS" unless spoken).
- `checks` in the plan: lot x upper band = min. investment for every company; fresh + OFS = issue size; issue sizes add up to the stated total (`atLeast` for "se zyada").
- Lot size, min. investment and retail portion come from the X card images: write them to `work/facts.txt` with the image they came from.

## Edit rules
- Retakes: full-clip Whisper merges repeated takes; re-transcribe suspicious stretches with `transcribe.py --pieces`. Keep the last complete take.
- Extra words: `extra_words.py` against the script as written; cut genuine extras (fillers, lead-ins such as "No. 1 is" when the script does not have them) only after `check_joins.py` reads clean.
- Pauses over 0.40 s trimmed to 0.20 s (brand audio values). Alternate 1.00 / 1.06 framing per segment hides jump cuts (automatic in card-top layout).
- Green screen: `key.py sample` per shoot; `key.py test` 3 strengths on dark, face mask with no holes, then `key.py run`. The 4-IPO shoot used chromakey 0x95D623:0.11:0.05. No green screen (plain wall): `key.py run --plain`, layout `full` (talk stretches + full-screen cards); the Jio listing Short of 28 Oct 2026 was made this way.
- Captions: English, phrase by phrase, timed to the Hinglish phrase (see `reference/plan.json`).

## Checks before handover
Every on-screen number matches the script or facts.txt; captions follow what was actually said where the take differs (list the differences); stills across the render (cards, captions, face clear of graphics); report every cut with raw timestamps, names Whisper heard oddly, and every creative decision taken without instruction.
