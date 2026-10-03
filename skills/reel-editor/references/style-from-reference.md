# Style from a reference reel

The user sends a reel they like ("edit mine like this") — a link or a file. The goal is to reproduce its **editing grammar and visual language**, not its content or assets.

## 1. Get it and measure it

```bash
yt-dlp -f "bv*+ba/b" --merge-output-format mp4 -o "reference/ref.%(ext)s" --write-info-json "<url>"   # Instagram/TikTok/YouTube
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of compact reference/ref.mp4
ffmpeg -i reference/ref.mp4 -vf "select='gt(scene,0.28)',showinfo" -f null - 2>&1 | grep -o "pts_time:[0-9.]*"   # hard cuts
ffmpeg -i reference/ref.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | grep "Input Integrated"
ffmpeg -i reference/ref.mp4 -vf "fps=2,scale=200:-1,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=9x5" reference/sheet_%02d.jpg
```

Then **look at the sheets** — 2 fps is the minimum to see how text arrives and how transitions move. Scene detection undercounts moves that aren't hard cuts (whips, pushes, blur transitions); the sheet is the truth.

## 2. Distill it into a rule table

Write `reference/STYLE.md` with concrete, checkable rules — never "make it like X":

| Axis | What to write down |
|---|---|
| Presence | talking head / faceless / mixed; how much of the frame the speaker gets |
| Worlds | backgrounds and how many distinct "worlds" (e.g. deep-red gradient act → white act) and where the switch happens |
| Characters / visuals | photos, flat illustration, silhouettes, UI, memes, generated paintings; their palette |
| Text | word-by-word accumulating sentence vs. 1–4-word captions vs. big keywords; position; size; colour; glow/shadow; how it exits |
| Motion | constant push-ins? punch zooms? static? |
| Transitions | hard cut / whip-pan with motion blur / blur dissolve / slide; how often |
| Rhythm | average scene length; when scenes change (on meaning? on a beat?) |
| Narrative devices | thought bubbles, "?!" marks, stamps, metaphors (puppet strings, scales…) |
| Ending | CTA card, fade to dark, hard stop |
| Audio | voice only / music bed / SFX; loudness |

## 3. Rebuild it with your own material

- Map every device to the user's *meaning*: a thought bubble for what someone thinks, a balance scale for a comparison, puppet strings for "depends on", a stamp for a verdict.
- Draw characters and objects yourself (SVG symbols reused with `<use>`) or use the user's assets. **Never copy the reference's illustrations, memes, music or footage** — they belong to someone else; reproduce the *style*, not the files.
- Before hand-building a transition the reference uses, search the registry (`npx hyperframes catalog --query "whip pan motion blur"`): `whip-pan-cut` exists; reuse its recipe (one `power3.inOut` move, horizontal SVG blur capped at 16 px, peaking mid-move).
- Keep the user's voice/footage authoritative; the reference decides look and rhythm, not content.
- Report what was matched and what was approximated (e.g. "flat SVG silhouettes instead of hand-drawn illustrations").

## Pitfalls met in practice

- Colours on SVG `<symbol>` content used via `<use>`: class selectors like `.red .body` don't reach into the use-tree. Set colours with CSS custom properties (`--body`, `--head`) on the scene and `fill: var(--body)` inside the symbol.
- `<symbol viewBox>` clips anything outside it (a thought cloud's lobe): size the viewBox to the art or set `overflow: visible`.
- Whip transitions: put the scene background on the **moving** layer, not on the static scene box — otherwise the incoming scene's background covers the outgoing one and the whip shows a single scene.
- Incoming scene content must already be on screen during the whip; start its build at the cut, not after the move.
