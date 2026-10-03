---
name: reel-editor
description: Edit raw talking-head footage into a finished, publish-ready short video (Reels / TikTok / Shorts, or 16:9) — silence removal, jump cuts, punch-in reframes, word-timed captions, full-screen motion-graphic interludes, split screens, audio leveling, preview, render — built as code with HyperFrames. Also executes editing directions the speaker says out loud in the recording ("cut this shot", "zoom on my face here", "show my website here"). Use this whenever the user drops a raw recording and wants it edited, "montaged", cut, captioned, turned into a reel, or "made ready to post", even if they never say HyperFrames. Strong on Arabic/RTL captions (مونتاج، ريلز، شيل الصمت، كابشنز، قص، زوم). Not for generating video from nothing with no footage (use the HyperFrames router), and not for editing an existing NLE project (Premiere/Resolve/CapCut files).
---

# Reel Editor

Turn one raw recording into a directed short video. The edit is a HyperFrames project (HTML + seekable animation, rendered by headless Chrome + ffmpeg), so every caption, cut and graphic stays editable — the user can later say "change the word at 0:12" instead of regenerating everything.

This skill is the **director layer**. HyperFrames' own skills own the technical contract (valid compositions, lint, render); this skill decides *what* the edit is and enforces the quality gates. When the two disagree on syntax, HyperFrames wins; on editorial taste, this skill wins.

Work through the steps in order. Each produces an inspectable artifact in the project, so a later session (or the user) can resume from files instead of from memory.

## Step 0 — Environment

1. `bash <this-skill>/scripts/preflight.sh` — Node 22+, ffmpeg/ffprobe, Python, faster-whisper, HyperFrames skills. Install what's missing; read `references/hyperframes-notes.md` → *Setup problems* for machines where the normal install fails (no sudo for Homebrew, Intel Macs, Chrome timeouts).
2. `npx hyperframes doctor` — ffmpeg, Chrome and disk as HyperFrames sees them.
3. `npx hyperframes usage --json` — note the usage window; a full-mode reel is expensive. Re-check before rendering.
4. Read `/hyperframes` (router), then `/general-video` (a footage remix — cuts, reframes, captions, interludes — is a custom edit and routes there), then `/hyperframes-core` before writing any HTML. Load `/hyperframes-keyframes` for zooms/punches, `/hyperframes-animation` for scene motion, `/hyperframes-creative` → `typography.md` for fonts, `/media-use` for icons/images/SFX, `/hyperframes-audio` for loudness, `/hyperframes-registry` before hand-building any named effect, `/hyperframes-cli` for commands. Read them; don't reconstruct them from memory.

## Step 1 — Intake (one round of questions at most)

| Input | Required | Notes |
|---|---|---|
| Raw footage | yes | any video in the folder; ask only if several and the A-roll is unclear. Never modify the original. |
| `fonts/` | no | font files for captions/titles |
| `logos/`, `images/`, `broll/`, `music/` | no | use only what's supplied or what the speaker explicitly names (e.g. "my website") |
| `brand.md` | no | colors, fonts, tone — overrides the style preset |

Defaults, confirmed in **one** message only if genuinely ambiguous:

- **Mode** — `full` (default): cuts + captions + reframes + graphic interludes. `quick`: cuts + captions + reframes only; several times cheaper, good for daily posting. `faceless`: the speaker never appears — their voice plays over continuous motion graphics (see `editing-rules.md` → *Faceless mode*). Users ask for it as "without my face", "بدون وجهي", "voice only", "صوت وجرافيك فقط".
- **Format** — 1080×1920 @ 30 fps unless the user wants otherwise. 30 fps renders twice as fast as 60 and is what Reels/TikTok deliver anyway.
- **Language** — detect from audio. Arabic/Hebrew/Persian/Urdu → read `references/rtl-and-fonts.md` before any typography.
- **Style** — `references/style-editorial-paper.md`, or `brand.md`, or a described style turned into concrete rules.

Scaffold a child project and write `BRIEF.md` there (HyperFrames' router reads it, and it stops later sessions from re-asking):

```bash
npx hyperframes init "<project>/edit" --non-interactive --example=blank --skill=general-video
```

## Step 2 — Understand the source

1. `ffprobe` → `source-analysis.md`: duration, resolution, `r_frame_rate` **and** `avg_frame_rate`, codecs, audio rate/channels. If they differ the file is variable-frame-rate (phones, WhatsApp, screen recorders) — plan to bake a CFR A-roll in Step 4. If the resolution is far below 1080 wide (WhatsApp re-encodes to ~480p), say so and suggest the user send the camera original next time; continue with what you have.
2. Contact sheet with timestamps, then **look at it**:
   `ffmpeg -i src -vf "fps=1,scale=240:-1,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x5" sheet_%02d.jpg`
   Note: camera-setup/teardown frames at head and tail, where the face sits (for crop math), headroom, gestures, and **where the speaker points** when they say "here".
3. Transcribe with word timestamps → `transcript.json` (`[{"text","start","end"}]`):
   - faster-whisper `large-v3`, `language=<code>`, `word_timestamps=True`, `condition_on_previous_text=False`; or `npx hyperframes transcribe <src> --model large-v3 --language <code>`.
   - Never use a `.en` model or the CLI default (`small.en`) for non-English speech — it silently *translates* to English.
   - Re-run unclear stretches with `clip_timestamps=[a,b]` and an `initial_prompt` containing the names/terms you expect; compare.
4. **Correct the transcript** (product names, English terms in Arabic speech, dialect). Everything visible is derived from it. Mark what stays uncertain; don't animate guesses.
5. Find **spoken edit cues** — read `references/spoken-cues.md`. List each cue with its time, its literal words, your interpretation, and how you'll execute it, in `source-analysis.md`.

## Step 3 — Cut plan

```bash
python3 <this-skill>/scripts/plan_cuts.py transcript.json -o timing-map.json \
  --fps 30 --duration <source seconds> --srt captions.srt
```

Keeps speech, cuts pauses > `--gap` (0.25 s) leaving `--pad` (0.08 s) of room, snaps to the frame grid, writes `removed` ranges, re-times every word onto the output timeline (`words[].out_start/out_end` — captions use these, never source times), and writes short caption cues. Arithmetic by hand is where edits drift out of sync; use the script.

Before running it, remove from the word list: head/tail camera-handling, retakes and false starts (keep the best take), and any cue that says to cut something (`references/spoken-cues.md`). Then sanity-check cuts against the contact sheet — don't cut through a gesture that completes a sentence.

## Step 4 — A-roll

Pick one, and record which in `BRIEF.md`:

- **Baked A-roll** (default for phone/VFR sources, or more than ~10 cuts): `plan_cuts.py … --bake raw.mp4 edit/assets/aroll.mp4` renders the kept ranges into one constant-frame-rate H.264 file with 10 ms audio fades at every cut and a keyframe every second. The composition then has a single `<video>` from 0 to `output_duration`, which seeks exactly, renders fastest, and can't drift.
- **Clip-per-range** (CFR sources, few cuts, user wants to re-trim cuts in Studio): one `<video>` per kept range — `data-media-start`=`src_start`, `data-duration`=`duration`, `data-start`=`out_start`, `data-has-audio="true"`, unique `id` on each (`/hyperframes-core` → `creator-editing-recipes.md`).

In `faceless` mode the A-roll is used only for its audio: extract it (`ffmpeg -i aroll.mp4 -vn -c:a copy voice.m4a`) and place it as an `<audio id="voice">` track; no `<video>` at all, so the face can never leak into a frame.

## Step 5 — Storyboard

Split narration into semantic beats (`references/editing-rules.md`: beat types, A-roll/graphic ratio, crop states, captions). Execute spoken cues at the moments they describe. For sources longer than ~40 s, scale up: roughly one graphic scene per 6–10 s of speech, never one per sentence. If the content would clearly be stronger shorter, offer a cut-down — don't silently drop the speaker's points.

Write `STORYBOARD.md` with one `## Frame N` block per scene (HyperFrames' dispatch format): exact transcript phrase, output start/end, treatment (talking head + crop state, split screen, or graphic interlude + its central metaphor), motion rules cited from `/hyperframes-animation`'s `blueprints-index.md` / `rules-index.md`, and the caption plan. `quick` mode: crop changes and caption emphasis only.

## Step 6 — Build

Follow `/hyperframes-core`. The details that most often break (see `references/hyperframes-notes.md` for the lint codes):

- Reframes/zooms animate an **inner wrapper** around the video, never the timed `.clip`; derive scale origin from the face position you measured.
- Split screen = the same A-roll wrapper re-cropped into the bottom half (face kept in frame) plus content in the top half; the dialogue never stops.
- Graphic scenes are sub-compositions; timelines are paused, registered on `window.__timelines`, seekable; no clocks, unseeded random, timers or render-time network.
- Fonts: a local `@font-face` file for anything non-bundled (`references/rtl-and-fonts.md`).
- External visuals the speaker asks for (their website, their logo): capture or copy them once into `assets/` before building; never fetch at render time. A website screenshot: `chrome-headless-shell --headless --screenshot=site.png --window-size=540,2400 --force-device-scale-factor=2 --hide-scrollbars <url>` (the binary lives under `~/.cache/hyperframes/chrome/`).
- Search `npx hyperframes catalog --query "<look>" --json` before hand-building a named effect or transition.

## Step 7 — Verify, then stop for approval

1. `npx hyperframes lint` after the first structural pass; `npx hyperframes check` at the end with **zero** findings (a lint error disables the layout/contrast audits, so "0 samples" means nothing ran).
2. `npx hyperframes snapshot --at <t1,t2,…>` and look at: first frame; 25/50/75/100 % of the opening push; ±1 frame at every cut and scene boundary; middle and end of every graphic scene and every list state; every spoken-cue moment; the final hold and last frame. Hunt for black flashes, missing-font boxes, broken Arabic joining, captions over the face or under platform UI, lingering scenes, and lip-sync drift.
3. For multi-scene work run `/hyperframes-animation`'s `scripts/animation-map.mjs` and read it.
4. `npx hyperframes preview --background` and give the user the Studio URL. **This is the approval gate** — render only after a yes. Apply notes, re-check, re-preview.

## Step 8 — Render and report

`npx hyperframes render` → `final.mp4`; `ffprobe` it: 1080×1920, expected fps, H.264 + AAC, non-zero size, duration = composition duration. Loudness target about −14 LUFS / −1 dBTP (`/hyperframes-audio`).

Report briefly: original → final duration, removed ranges, spoken cues and how each was executed, scene count, A-roll/graphic ratio, fonts and weights, external assets and where they came from, validation status, anything still uncertain.

## Stop and say so instead of faking success when

- the footage can't be decoded or there's no clear A-roll;
- the transcript stays materially uncertain after review;
- a spoken cue is ambiguous in a way that changes the edit (ask, with your best guess);
- no available font renders the script correctly;
- a graphic would require inventing facts, screenshots or numbers you don't have;
- `hyperframes check` keeps failing.

## Expectations to set with the user

A 30 s reel in `full` mode is roughly 20–40 minutes of agent time plus render time (slower on Intel Macs); `quick` is much lighter. Strong for talking-head content; weak for multi-camera, cinematic or b-roll-driven work. Always review before posting.
