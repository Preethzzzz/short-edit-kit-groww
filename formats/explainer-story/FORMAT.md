# Format: Explainer Story

Vertical Short (1080x1920, about 1:00-1:40) that tells one "how did this happen?" story: the presenter, keyed onto ONE realistic photo background, explains a single event or mechanism (a listing without an IPO, a demerger, a rule change), with source-quote cards above her, a few clean diagrams, and 2-3 short AI-generated b-roll clips. Modelled on "How JK shah listed without an IPO?" (IPO Review by Groww, 20 Nov 2026), keeping what worked there and fixing its errors (see the end of this file). The brand pack overrides anything here that conflicts with it.

## When to use
- One story or mechanism explained end to end ("how", "why", "what changed"), any channel.
- Not for multi-company lists (IPO Day Roundup) or number-heavy report findings (Data Explainer).

## Plan settings
- `"layout": "card-top"` (cards in the top area, presenter stays on screen and drops a little while a card is up).
- One section for the whole video: `"sections": [{"scene": "photo", "at": "<first words>"}]`.
- `"background": {"src": "bg.jpg", "blur": 4, "dim": 0.0, "drift": 0.03, "dark": false}`. Standing background: copy `brands/groww/backgrounds/white-room.jpg` to `public/bg.jpg` (bright white room, window light from the left, plant lower left; chosen by the user 21 Nov 2026). `dark: true` when the photo is dark enough that the white-text logo reads better (it also switches header and SEBI lines to white).
- `"presenter": {"src": "presenter.webm", "offset": 0, "look": {...}}`. See "Matching the presenter to the background".
- `"sebi": {"position": "bottom", "openingSeconds": 3, "closingSeconds": 3}`: the SEBI lines show **only** in the first 3 s and the last 3 s, bottom centre (just above the Shorts UI, on a small dark backing so they read over her hands). User rule, 21 Nov 2026.
- fps = footage fps. Theme: default light theme for the cards.

## The background (one photo, whole video)
- Exactly one background photo for the whole Short. Never switch rooms between shots (the reference jumped from a dark room to a light room and back).
- Use the channel's standing background (`brands/groww/backgrounds/white-room.jpg`; its uncropped source is `white-room_source.jpg`). Use another only if the user asks; otherwise ask the user for one, made with the background prompt in `formats/explainer-story/PROMPTS.md`, or for a real photo of the shoot location. Never use a web photo.
- What the photo must have:
  - 9:16 at 1080x1920 or larger.
  - Eye level at about chest height.
  - Light coming from the same side as her key light.
  - Nothing busy behind her head.
  - The top-right logo zone (x 740-1080, y 0-360) plain.
  - No text, logos, screens with content, or people.
- The template adds a 4 px blur (depth of field: she is sharp, the room is not), an 8% dim and a very slow 3% drift so the frame never freezes.

## Matching the presenter to the background
The reference's main error: she looked pasted on, with brighter, warmer light than the room, the room sharper than her, and hard edges. Fix it every time:
1. Key with the usual keyer (`key.py`). Keep about 0% holes and a clean hair edge, with no green fringe (despill on).
2. Render one test still at a talk moment (`npx remotion still ... --frame=N`) and view it at full size.
3. Set `presenter.look` until she sits in the room:
   - `brightness` 0.92-1.06 to match the room's exposure on her face.
   - `contrast` 0.95-1.05.
   - `saturate` 0.9-1.0: keyed skin is usually too saturated against a calm room.
   - `hue` -4 to 4 degrees, only for a clear colour cast.
   - `rim` is the room's dominant light colour at 0.25-0.4 alpha (e.g. `"rgba(240,210,160,0.35)"` for a warm lamp room), with `rimPx` 10-16. This wraps the room's light around her edges.
4. Framing: her eyes at about y 1000-1150 when no card is up. Never punch in past 1.2x: the reference's 72 s zoom went soft and blocky.
5. QA checks that same still against the edge (no halo or fringe), the light direction, and her colour vs the room.

## Structure
| Beat | On screen |
|---|---|
| Hook (0-4 s) | Her face, MCU, asking the question. SEBI lines bottom centre for the first 3 s. |
| What is missing / different | `CrossList` ("Price band ✕, Lot size ✕, Allotment ✕") as each item is said |
| Name the subject | `KineticLine` with the name in serif accent, or `EntityCard` |
| AI clip 1 (2-4 s) | `Clip`: what the business is (from the Gemini prompts) |
| The mechanism | `KineticLine` keyword in serif ("*Demerger*"), then `FlowExplainer` or `Timeline` |
| Proof | `ImageCard` with the highlighted line of the press release, RHP or exchange filing, cropped to 3-6 lines. Under 6 s per card. Source tag on the beat. |
| Key numbers | Quote card with the number highlighted, or `BigNumber` / `Calculation` |
| AI clip 2 (2-4 s) | `Clip` on the "market / listing day" line |
| Why it is allowed / what it means | `FlowExplainer` (parent company → scheme approved → NSE/BSE listing) built big and readable, not a thin flowchart |
| Close | Talk MCU, end card with disclaimer + RA line, Like/Subscribe if the script says it |

## Rhythm
- Something changes every 2-4 s. Nothing is held over 5 s without a new element.
- Presenter on screen at least 55% of the runtime: the story is told by her, and cards support her.
- Cards and quote boxes go in the top area. Never a full-screen screenshot with a tiny presenter thumbnail: the reference held a 23 s press-release page with a 100 px face.
- AI clips: **2 or 3 per Short, 2-4 s each, never two in a row**. Each one must show what the line says (not generic "office" footage). Every AI clip keeps the `AI-generated visual` corner label.
- Colour meaning as always: red only for "not / loss / risk", green only for good outcomes, yellow for notes, blue neutral.

## Gemini clip prompts (content strategist)
The content strategist picks the 2-3 lines that most need a real-world picture and writes one Gemini prompt for each in `visual_plan.md` (rules and template in `PROMPTS.md`). The user generates the clips and drops them in `public/clips/` as `ai_1.mp4`, `ai_2.mp4`, `ai_3.mp4`. If a clip is missing at render time, that beat falls back to a talk stretch (MCU), never to a stock or web clip.

## Errors in the reference, and the rule that fixes each
| Time | Error | Rule |
|---|---|---|
| 0:00-0:07, 1:03 | Background switched rooms (dark, light, dark) | One background photo for the whole video |
| whole video | Presenter brighter and warmer than the room, room sharper than her | `presenter.look` + blurred background + rim light, checked on a still |
| 0:00-0:04 | SEBI lines low in the frame, under the Shorts UI, unreadable | SEBI lines bottom centre above the Shorts UI on a dark backing, first 3 s and last 3 s only |
| 0:22-0:45 | 23 s of full press-release text with a tiny face thumbnail | Crop to the highlighted 3-6 lines, under 6 s, presenter stays on |
| 0:10-0:20, 1:09-1:20 | About 20 s of generic AI b-roll (classroom, books, trading floor, certificate) | 2-3 clips, 2-4 s each, each tied to one line |
| 1:12 | Punch-in so far her face went soft | Max 1.2x |
| 1:27-end | Thin, small flowchart as the last frame, no clear end | Big `FlowExplainer`, then her close + end card |

What to keep from it:
- The cold open on her face with a question.
- The ✕ pills.
- Serif keyword titles.
- The highlighted quote boxes above her (0:48-1:00), the best pattern in it.

## Checks before handover
Same as every format, plus:
- One background for the whole video.
- SEBI lines visible (and readable) in the first 3 s and the last 3 s, nowhere else.
- A full-size still of the presenter on the background, checked for edges, light and colour.
- 2-3 AI clips, each labelled.
- No quote card over 6 s.
- Presenter on screen at least 55% of the runtime.
