---
name: reel-editor
description: Edit raw talking-head footage into a finished, publish-ready short video (Reels / TikTok / Shorts, or 16:9) — silence removal, jump cuts, punch-in reframes, word-timed captions, full-screen motion-graphic interludes, audio leveling, preview, render — built as code with HyperFrames. Use this whenever the user drops a raw recording and wants it edited, "montaged", cut, captioned, turned into a reel, or "made ready to post", even if they never say HyperFrames. Strong on Arabic/RTL captions (مونتاج، ريلز، شيل الصمت، كابشنز). Not for generating video from nothing with no footage (use the HyperFrames router), and not for editing an existing NLE project (Premiere/Resolve/CapCut files).
---

# Reel Editor

Turn one raw recording into a directed short video. The edit is a HyperFrames project (HTML + seekable animation, rendered by ffmpeg), so every caption, cut and graphic stays editable after the first pass — the user can ask for "change the word on frame 140" instead of regenerating the whole video.

This skill is the **director layer**. HyperFrames' own skills know *how* to write valid compositions; this skill decides *what* the edit should be and enforces the quality gates. Lean on their skills for syntax; lean on this one for editorial judgment.

## Step 0 — Preflight

Run `bash <this-skill>/scripts/preflight.sh`. It checks Node 22+, ffmpeg/ffprobe, Python, faster-whisper and the HyperFrames skills, and prints the install command for anything missing. Install what is missing (ask first if it needs sudo or a system package manager). If HyperFrames skills are absent:

```bash
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
# or standalone: npx hyperframes skills update
```

Then read `/hyperframes` (the router). It will point at the domain skills you need: `hyperframes-core`, `hyperframes-animation`, `hyperframes-keyframes`, `hyperframes-creative`, `media-use`, `hyperframes-audio`, `hyperframes-registry`, `hyperframes-cli`. The closest creation workflow is `/talking-head-recut` (graphics over talking head); use `/embedded-captions` patterns for the caption layer and `/general-video` as the fallback.

## Step 1 — Intake (one round of questions at most)

Find the inputs in the working folder:

| Input | Required | How to find it |
|---|---|---|
| Raw footage | yes | the video file(s) in the folder; if several and it's unclear which is the A-roll, ask |
| `fonts/` | no | custom font files to use for captions and titles |
| `logos/`, `broll/`, `music/` | no | only use what's supplied; never pull random media from the web |
| `brand.md` | no | colors, fonts, tone; overrides the style preset |

Settle the brief with sensible defaults, and confirm it in **one** message only if something is genuinely ambiguous:

- **Mode** — `full` (default): cuts + captions + reframes + graphic interludes. `quick`: cuts + captions + reframes only — several times faster and cheaper, good for daily posting.
- **Format** — 1080×1920 (9:16) unless the source or user says otherwise; 1920×1080 for YouTube long-form.
- **Language** — detect from the audio. Arabic, Hebrew, Persian, Urdu → read `references/rtl-and-fonts.md` before any typography.
- **Style** — `references/style-editorial-paper.md` (default), or the user's `brand.md`, or a style they describe/link. If they reference a creator's style, describe it as concrete rules (crop scale, caption size/position, palette, cut rhythm) rather than "like X".

Work in a new child folder (e.g. `reel-edit/`). Never modify or overwrite the source footage.

## Step 2 — Understand the footage before designing

1. `ffprobe` the source: duration, resolution, fps, codecs, audio rate/channels. Keep the native fps when practical.
2. Contact sheet at 1 fps (`ffmpeg -i src -vf "fps=1,scale=270:-1,tile=6x5" sheet_%02d.jpg`) and actually look at it: where are the face, eyes and hands, how much headroom, is there usable negative space, does the framing drift.
3. Silence map: `ffmpeg -i src -af silencedetect=noise=-35dB:d=0.25 -f null - 2>&1 | grep silence_`. Treat it as a hint only.
4. Word-level transcript → `transcript.json` (`[{"text","start","end"}]`). Prefer HyperFrames `/media-use` transcription; otherwise faster-whisper with `word_timestamps=True` (model `large-v3` for Arabic/dialects, `small` is fine for clean English).
5. **Correct the transcript by hand.** Whisper mangles product names, English terms inside Arabic speech, and dialect. Fix them now: every caption and every graphic is derived from this file, so an error here is published. If parts stay uncertain, say so — don't animate guesses.

Write `source-analysis.md`: metadata, what the speaker is saying in 3–6 beats, framing notes, anything problematic (noise, bad lighting, phone in shot).

## Step 3 — Cut plan

```bash
python3 <this-skill>/scripts/plan_cuts.py transcript.json -o timing-map.json --fps <source fps> --duration <source seconds>
```

`--fps` accepts ffprobe's `r_frame_rate` as-is (`30000/1001`). Zero-length words are kept (10 ms) and words past `--duration` are dropped.

It keeps speech, cuts pauses longer than `--gap` (default 0.25 s) while leaving `--pad` (0.08 s) of breathing room, snaps cuts to the frame grid, and re-times every word onto the output timeline (`words[].out_start/out_end`) — use those times for captions, never the source times. Doing this arithmetic by hand is where edits drift out of sync, which is why it's a script.

Then sanity-check against the picture: a cut that lands mid-gesture or mid-breath-laugh should move or go. Retakes (the speaker repeating a sentence) are not silences — find them in the transcript and keep only the best take, then re-run the script on the edited word list. See `references/editing-rules.md` → *Cuts*.

## Step 4 — Storyboard

Split the narration into semantic beats and assign each a treatment using `references/editing-rules.md` (beat types, A-roll/graphic ratio, crop states, caption rules). Write `STORYBOARD.md`: for each scene, the exact transcript phrase that drives it, output start/end, treatment (talking head + crop state, or graphic interlude + its central visual metaphor), and caption plan.

In `quick` mode the storyboard is just crop changes and caption emphasis words.

## Step 5 — Build

Build the HyperFrames project following their core contract. The parts that most often go wrong:

- Each kept source range is its own media clip: `data-media-start` = `src_start`, `data-duration` = `duration`, `data-start` = `out_start` from `timing-map.json`. If audio is separate, it uses the identical ranges.
- Dialogue continues uninterrupted under graphic interludes.
- Reframes/punch-ins animate an inner wrapper, never the timed `.clip` element itself.
- Every graphic scene is its own sub-composition; timelines are paused, seekable, deterministic (no `Date.now()`, unseeded random, timers, or network fetches at render).
- Fonts load locally and are verified before use (`references/rtl-and-fonts.md`).
- Search the HyperFrames registry before hand-building a named effect or transition.

## Step 6 — Verify, then stop for approval

1. `npx hyperframes lint` after the first structural pass; `npx hyperframes check` at the end with zero unresolved errors.
2. Snapshot and look at: the first frame, the opening push-in, ±1 frame around every cut, the middle and end of every graphic scene, the final frame. Look for black flashes, missing-font boxes, broken RTL shaping, captions over the face or under platform UI, and lip-sync drift.
3. Open HyperFrames Studio preview and give the user the URL. **This is the approval gate**: rendering is slow and the user's taste is the final judge. Apply their notes, re-check, and only render after a yes.

## Step 7 — Render and report

Render to `final.mp4` (H.264 + AAC), then `ffprobe` it: resolution, fps, codecs, non-zero size, duration matching the composition. Report briefly: original → final duration, number of cuts, scenes, A-roll/graphic ratio, fonts used, anything you were unsure about.

## Stop and say so instead of faking success when

- the footage can't be decoded or there's no clear A-roll;
- the transcript is still materially uncertain after review;
- no installed font renders the script correctly;
- a graphic would require inventing facts, screenshots or numbers you don't have;
- `hyperframes check` keeps failing.

## Expectations to set with the user

A 20–40 s reel in `full` mode typically takes 20–40 minutes of agent time and a noticeable share of a usage window; `quick` is much lighter. Output is strong for talking-head content, weaker for multi-camera, cinematic or heavily b-roll-driven edits. Always review before posting.
