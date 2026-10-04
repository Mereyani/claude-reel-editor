# HyperFrames field notes

Things learned from real runs that the docs don't put in one place. HyperFrames' own skills stay authoritative; these are the traps.

## Setup problems

| Symptom | Fix |
|---|---|
| `brew install ffmpeg` fails asking for `sudo chown` (or "Tier 3 configuration" on Intel Macs with new macOS) | No-sudo route: `~/miniconda3/bin/conda create -y -n ffmpeg -c conda-forge ffmpeg`, then symlink `ffmpeg`/`ffprobe` from `~/miniconda3/envs/ffmpeg/bin/` into a PATH dir such as `~/.local/bin`. Verify `libx264` and `aac` in `ffmpeg -encoders`. |
| `hyperframes doctor` says Chrome timed out / `browser ensure` hangs | The headless shell is usually already downloaded under `~/.cache/hyperframes/chrome/chrome-headless-shell/`; its first launch is just slow (Gatekeeper). Run it once with `--version`, stop the hung `ensure`, re-run `doctor`. |
| Plugin install warns about Git LFS pointer files | Only example media; skills work. `git -C ~/.claude/plugins/marketplaces/hyperframes lfs pull` if you need them. |
| Transcription comes back in English | The CLI default `small.en` translates. Always pass `--model <multilingual> --language <code>`. |
| Whisper `initial_prompt` output repeats the prompt instead of the speech | Prompt-echo hallucination on short or unclear clips. Retry without a prompt and with different `beam_size`/`temperature`; prefer comparing several decodes over priming. |
| `ModuleNotFoundError: faster_whisper` in a new session | The session's `python3` isn't the env you installed into (conda not on PATH). `preflight.sh` prints the interpreter that has it — call that one by full path. |
| A forced `--cut` at the head removes a word's caption | Whisper glued the first word to camera-handling noise. `plan_cuts.py` now moves the text onto the surviving speech burst of the same word. |
| Whisper word spans are seconds long | Words absorb neighbouring pauses (and sometimes a missed word). Pass `--silences` (ffmpeg `silencedetect` output) to `plan_cuts.py`; it splits such spans into speech bursts so pauses get cut and no speech is lost. |

## Measuring audio from the shell

- `ffmpeg -ss X -t D -i file -af astats` can print nothing for short windows; use `-af "atrim=X:Y,astats=metadata=0"` instead.
- In zsh, `set -- $w` does not split a string into words; use `a=(${=w})`.
- astats prints per-channel blocks then `Overall`; take values after the `Overall` line. "Noise floor dB" (overall, whole file) is the right denoise reference — detected "pauses" often hold breaths or camera handling.

## Source footage

- Phone / WhatsApp video is usually variable frame rate (`r_frame_rate` ≠ `avg_frame_rate`) and WhatsApp re-encodes to ~480p. Bake a CFR A-roll (`plan_cuts.py --bake`), which resamples *before* trimming so every cut lands on an exact frame and audio stays in sync to the millisecond.
- Phone voice is typically −25 to −30 LUFS. `--bake` normalises to −14 LUFS / −1 dBTP by default.
- 30 fps output renders twice as fast as 60 and is what social platforms deliver.

## Lint / check findings that matter

| Code | Meaning | Fix |
|---|---|---|
| `gsap_css_transform_conflict` | CSS sets `transform` on something GSAP also transforms | remove the CSS transform; `tl.set(...)` the initial state at 0 |
| `gsap_non_transform_motion` | tweening `left/top/width/height` — stutters in frame capture | animate `x/y/scale` (give the element its final box and express the small state as a transform with `transform-origin: 0 0`) |
| `multiple_root_compositions` | another HTML file with `data-composition-id` in the project root (e.g. a template) | keep only `index.html` in the root |
| `content_overlap` | two text blocks collide (Arabic ascenders are tall) | give each its own zone |
| `escaped_container` / `container_overflow` on a crop wrapper or scrolling image | intentional | `data-layout-allow-overflow` on that element |
| contrast < 3:1 | e.g. bright orange text on paper | use the darker accent for text; keep the bright one for fills |
| `nested_structure_needs_subcomposition` (warning) | a timed `<section>` with children in the root | acceptable for small reels; move scenes to sub-compositions when the project grows or the user will edit in Studio |

A lint **error** switches off the layout and contrast audits — "0 samples" then means nothing ran.

## Fonts

- Bundled families render offline with no setup. Google Fonts names are fetched once at *build* time and cached (`~/.cache/hyperframes/fonts`) — acceptable for Latin fallbacks like Montserrat; for the main Arabic face prefer a local `@font-face` file (`rtl-and-fonts.md`), which never depends on the network. Locally installed families are auto-captured in local renders but **not** in cloud/Lambda renders.
- For Arabic, a local `@font-face` file is the reliable path. On macOS, `SF Arabic` (`/System/Library/Fonts/SFArabic.ttf`, variable weight) is always present and looks good; copy it into `assets/` for local renders (it's licensed for use on Apple hardware — don't redistribute the file).
- Latin words inside Arabic (product names) can use a bundled family such as Montserrat via a `.lat` class with `direction: ltr; unicode-bidi: isolate`.

## Commands worth remembering

```bash
npx hyperframes init <dir> --non-interactive --example=blank --skill=general-video
npx hyperframes lint                       # fast, after structural changes
npx hyperframes check                      # final gate: lint + runtime + layout + motion + contrast
npx hyperframes snapshot --at 0.05,4.4,…   # PNGs + contact sheets in snapshots/
npx hyperframes preview --background       # Studio; --status prints state, URL is in the log
npx hyperframes render -o out.mp4 -f 30 -q looks
npx hyperframes timeline --json            # what's on the timeline without reading HTML
```
