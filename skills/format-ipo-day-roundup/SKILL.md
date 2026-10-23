---
name: format-ipo-day-roundup
description: Format rules for the "IPO Day Roundup" Short - several IPOs opening the same day, green-screen presenter over sector scenes, animated company cards. Load with edit-short when the script covers 2-5 IPOs (or a single-IPO data update in card-top layout).
---

# Format: IPO Day Roundup

Read `${CLAUDE_PLUGIN_ROOT}/formats/ipo-day-roundup/FORMAT.md` (beats, components, scenes, numbers, edit rules) and use `${CLAUDE_PLUGIN_ROOT}/formats/ipo-day-roundup/reference/plan.json` as the worked example: copy its shape, never its numbers.

Plan defaults: `"layout": "card-top"`, `"channel": "ipo-review"`, `"theme": "light-blue"`, sections switch scene at each company, `zooms` 1.08 and `endCard` at the CTA line.

Must-haves:
- One `EntityCard` per company; price band and issue size `at` the exact spoken phrase; badge text without numbers the script does not say.
- `checks`: lot × upper band = min. investment per company; fresh + OFS = issue size; sizes add up to the stated total.
- Lot size, min. investment, retail portion: from the X card images, recorded in `work/facts.txt`.
- Objects-of-the-offer table: show only amounts the RHP gives (never a [●] amount), `source` = "<Company> Limited RHP".
