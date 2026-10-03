# Editing rules

Editorial defaults for short-form talking-head edits. They are starting points, not laws: when the content argues for something else (an emotional moment, a joke that needs a pause), follow the content and note why in `STORYBOARD.md`.

The overarching idea: energy comes from **meaningful changes** — a cut on a claim, a crop change on a contrast, a graphic on a concept — not from constant motion. Viewers feel random movement as noise and motivated movement as direction.

## Cuts

- Remove dead air at the head and tail completely.
- Inside the take, cut pauses longer than ~0.25 s but keep 2–4 frames of room so speech doesn't sound clipped (`plan_cuts.py` defaults do this).
- Keep some breaths and micro-pauses; removing every one makes the speaker sound robotic and breathless.
- Never cut inside a syllable or truncate a hand gesture that completes the sentence.
- Retakes and false starts: keep the cleanest take; remove the rest even if there's no silence between them.
- Hard cuts between kept ranges. Dissolves on jump cuts look like a mistake.
- Camera still settling under the first word (the speaker started talking while sitting back from the phone): don't cut the word — hold the first clean frame as a still over the audio for those few hundred ms (`<img class="clip">` on a track above the A-roll, inside the camera wrapper so the opening push still applies). Same trick at the tail if the hand reaches for the phone during the last word.

## Two visual worlds (full mode)

**A — talking head.** The speaker is the credibility. Use three crop states and change between them only when the thought changes (new claim, contrast, punchline, CTA), not every sentence:

| State | Scale | Use |
|---|---|---|
| base | 1.00× | context, neutral explanation |
| emphasis | ~1.08× | a new point, a contrast |
| close | ~1.14–1.17× | punchline, strong claim, CTA |

Mostly hard punches between states; a short smooth push is reserved for the opening. Derive the crop's x/y from the contact sheet — faces are rarely perfectly centered — and keep eyes, chin and active hands inside the frame. Natural color only: no orange skin, crushed blacks or oversharpening.

**B — full-screen graphic interludes.** Designed scenes that *replace* the speaker while their voice continues. Each one has: one central visual metaphor taken from what is being said, one dominant keyword in large type plus a smaller supporting line, and a build that lands in sync with the spoken words, then a clear hold and a decisive cut out.

Pick the metaphor from the transcript, and don't reuse the same one twice:

| Spoken idea | Metaphor ideas |
|---|---|
| process / automation | path, timeline assembling, connected modules |
| decision / thinking | branching tree, network |
| problem / warning | cracked card, barrier, downward line |
| result / growth | completed frame, rising route, finished output card |
| list of steps / features | stacked numbered blocks, revealed one at a time |
| comment / follow CTA | oversized keyword + speech-bubble outline |

Avoid the generic-AI look: robots, glowing brains, circuit boards, HUDs, particle fields, unrelated stock clips. If something can be drawn honestly with HTML/CSS/SVG, draw it.

## Ratio and pacing

- Overall roughly half talking head, half graphics for a full-mode reel; adapt to content. Keep the speaker on screen for personal, emotional or credibility-critical lines.
- Graphic scene length: 1.8–2.5 s short, 2.8–4 s normal, ≤ ~4.5 s for the longest list scene.
- About 4–6 semantic scenes for 20–35 s. Group sentences into beats; one scene per sentence feels like a slideshow.
- Boundaries come from meaning, never from a fixed timer.

## Beat types and the default arc

1. **Hook** — open on the speaker (~0.7–1.2 s) with a fast push-in (1.00 → ~1.10–1.13× over ~0.6–0.8 s, strong ease-out, no bounce back). First caption appears during the push. Cut to the first graphic on the strongest word of the hook — usually within the first 1–2 s. Never open on a logo, black, or a slow fade.
2. **Context / what I did** — back to the speaker for the personal statement; cut to a process graphic (input → tool → output) when the inputs are named.
3. **List / transformation** — the longest graphic scene; build 3–5 items one at a time, active item enlarged in the accent color, finished items settle to neutral.
4. **Payoff** — speaker again, medium crop or a slight punch-out for resolution; caption emphasis on the result phrase.
5. **CTA** — speaker visible for the setup; on the CTA keyword, punch in or cut to a final card (keyword + simple outline icon + one short instruction). Hold it 12–18 frames after the last word. Don't end on black.

In `quick` mode use only the crop changes and caption emphasis — no interludes.

## Captions

- Times come from `timing-map.json` → `words[].out_start/out_end`.
- 1–4 words on screen at a time, never full subtitle sentences.
- Position around 64–70% of frame height (over the torso), never over the face, and above the bottom ~15% where platform UI sits.
- Bold/semibold, tight line height, no background pill by default; good contrast via color or a soft shadow.
- Highlight at most one important word per group with the main accent; the secondary accent is rarer. Accent-coloured *text* fails contrast over bright walls — when the footage is light, put the highlighted word on an accent pill with cream text instead (it reads over anything).
- A caption never overlaps a full-screen scene: if a cue starts inside a scene, start it at the cut back; if it runs into one, end it at the cut.
- Motion: a 2–4 frame fade/rise or a clean hard swap. No bouncing karaoke, per-letter wobble or overshoot on every word.
- During graphic interludes, no extra subtitle layer — the scene's typography *is* the caption, revealed on the spoken moment. Keep every factual claim, invent none.

## Motion

- 2–4 motion ideas per graphic scene: masked word/line rise, short stagger, scale settle, line/path draw, small object turn, restrained drift, shared-element handoff between scenes.
- Timing at project fps: entrance 6–12 frames, stagger 2–5 frames, readable hold 10–20 frames.
- One focal object and one dominant phrase at a time.
- Avoid: random continuous motion, glitch (unless the content is about errors), liquid morphs, chrome 3D text, heavy parallax, spinning logos, a different transition for every cut, animations that snap back to their start state at the end.

## Audio

- Original dialogue is the master. Light denoise only if needed; no aggressive gating.
- Loudness about −14 LUFS integrated, true peak ≤ −1 dBTP.
- No music unless the user supplies or approves it — voice-only beats unlicensed music.
- SFX only for meaningful moments (graphic cut, list item lands, CTA), well under the voice.

## Safe zones (9:16, 1080×1920)

Essential text within roughly x 80–1000 and y 140–1650; CTA comfortably above the bottom controls.
