# Gemini prompts: background photo and AI clips

The content strategist writes these into `visual_plan.md`. The user runs them in Gemini (image for the background, video for the clips) and drops the files into the job: `public/bg.jpg`, `public/clips/ai_1.mp4` ... `ai_3.mp4`.

## Rules for every prompt
- **Picture only, no text.** AI garbles letters, so ask for no text, numbers, logos, signboards, tickers or screens with readable content. Every number and name on screen comes from our own graphics.
- **No real brands, people or places by name.** No company logos, no real company names, no lookalikes of real people, no exchange building names. A generic "Indian coaching institute classroom" is fine; a named institute is not. (SEBI rule: no third-party brand analogies.)
- **Nothing that reads as advice or a promise.** No money raining, no rocket charts, no celebrating traders, no "profit" imagery.
- **Indian setting, real-looking, calm.** Natural light, realistic people and clothes, muted colours (it must sit next to Groww blue/green cards without clashing).
- **Vertical 9:16, about 8 s, one slow camera move** (slow push-in, slow pan or locked-off with gentle motion). No fast cuts, no whip pans, no morphing, no dialogue. Audio is muted in the edit anyway.
- **Subject in the middle third** so a centre crop still works if Gemini returns 16:9.
- **Ask for one shot, not a sequence.** We use 2-4 s of it.

## Clip prompt template
```
Vertical 9:16 video, 8 seconds, photorealistic, one continuous shot.
Scene: <what the line means, in plain words, in an Indian setting>.
Action: <one small, natural movement>.
Camera: <slow push-in | slow pan left to right | locked-off>, eye level, shallow depth of field.
Light and colour: soft natural daylight, muted calm palette, slightly cool whites.
Keep the main subject in the centre third of the frame.
No text, no numbers, no logos, no brand names, no signboards, no readable screens, no recognisable real people. No dialogue, no fast motion, no morphing.
```

## How to choose the 2-3 lines
Choose the lines where a viewer needs to *see* the real world to understand, and where our graphics cannot show it:
1. **What the business is**: the first time the company's work is described (e.g. a commerce-coaching classroom).
2. **The event in the world**: listing day, a factory starting, a store opening, shown generically (e.g. a stock exchange trading screen glow on a calm face, with nothing readable).
3. (Optional) **The consequence for a person**: an investor checking a demat app at home, with the screen not readable.

Never use AI clips for numbers, rules or documents: those are graphics or source cards.

## Background photo prompt (only if the user wants a new one)
The standing background is `brands/groww/backgrounds/white-room.jpg`. Write this prompt only when the user asks for a different background.

```
Vertical 9:16 photograph, photorealistic, 1080x1920 or larger.
An empty, modern Indian home-office / study corner: a light wooden shelf with a few books and a small plant, a soft warm table lamp turned on, a large window just out of frame on the <LEFT|RIGHT> letting in soft daylight.
Camera at chest height, about 2 metres from the back wall, straight on. The centre of the frame, from the middle down, is a calm, uncluttered wall where a person will be placed later.
The top-right corner of the frame is plain wall with nothing in it.
Shallow depth of field, background gently out of focus. Muted neutral palette (warm white, light wood, soft grey) with one small touch of green from the plant.
No people, no text, no logos, no posters, no screens, no clocks, no reflections of people.
```
Set `<LEFT|RIGHT>` to the side her key light comes from in the footage (look at which cheek is brighter). If she is lit warm, keep the lamp; if she is lit cool and flat, change "warm table lamp turned on" to "lamp off, cool daylight only".

## Worked example: "How JK shah listed without an IPO?"
1. On "J.K. Shah Commerce Education ... commerce coaching":
   `Vertical 9:16 video, 8 seconds, photorealistic, one continuous shot. Scene: an Indian commerce coaching classroom, a teacher at a whiteboard covered in simple accounting tables (not readable), students in the front rows taking notes. Action: the teacher turns from the board to the class and gestures. Camera: slow push-in from the back of the room, eye level, shallow depth of field. Light and colour: soft natural daylight, muted calm palette. Keep the teacher in the centre third. No text, no numbers, no logos, no brand names, no readable writing, no recognisable real people. No dialogue, no fast motion.`
2. On "the stock debuted on 18 November":
   `Vertical 9:16 video, 8 seconds, photorealistic, one continuous shot. Scene: a calm Indian investor in their 30s at home in the evening, looking at a phone; soft glow of a market chart on the screen, not readable. Action: they scroll once and look up thoughtfully. Camera: locked-off, eye level, shallow depth of field. Light and colour: warm room light, muted palette. Keep the person in the centre third. No text, no numbers, no logos, no readable screens, no recognisable real people. No dialogue.`
