#!/usr/bin/env bash
# Check everything the reel-editor workflow needs. Exit 1 if a hard requirement is missing.
miss=0
ok()   { printf '  ok       %s\n' "$1"; }
bad()  { printf '  MISSING  %s  ->  %s\n' "$1" "$2"; miss=1; }
warn() { printf '  warn     %s  ->  %s\n' "$1" "$2"; }

echo "reel-editor preflight"

if command -v node >/dev/null; then
  major=$(node -p 'process.versions.node.split(".")[0]')
  [ "$major" -ge 22 ] && ok "node $(node -v)" || bad "node $(node -v) (need 22+)" "https://nodejs.org or: nvm install 22"
else bad "node" "https://nodejs.org (22+)"; fi

for t in ffmpeg ffprobe; do
  command -v $t >/dev/null && ok "$t" || bad "$t" "macOS: brew install ffmpeg (no sudo? conda create -n ffmpeg -c conda-forge ffmpeg) | Windows: winget install ffmpeg | Linux: apt install ffmpeg"
done

command -v python3 >/dev/null && ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)" || bad "python3" "https://python.org"

if python3 -c 'import faster_whisper' 2>/dev/null; then ok "faster-whisper"
else warn "faster-whisper" "pip install faster-whisper (only needed if HyperFrames /media-use transcription is unavailable)"; fi

# HyperFrames skills: plugin install or standalone skills folder
found=0
for g in ~/.claude/plugins/cache/*/hyperframes* ~/.claude/skills/hyperframes* \
         .claude/skills/hyperframes* ../.claude/skills/hyperframes* ~/.agents/skills/hyperframes*; do
  compgen -G "$g" >/dev/null && found=1 && break
done
if [ $found -eq 1 ]; then
  ok "HyperFrames skills"
else
  bad "HyperFrames skills" "claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes   (or: npx hyperframes skills update)"
fi

# headless Chrome HyperFrames renders with (first launch can be slow; not fatal)
chrome=$(ls -d ~/.cache/hyperframes/chrome/chrome-headless-shell/*/*/chrome-headless-shell 2>/dev/null | tail -1)
[ -n "$chrome" ] && ok "headless Chrome" || warn "headless Chrome" "npx hyperframes browser ensure"

[ $miss -eq 0 ] && echo "ready." || echo "fix the MISSING items, then re-run."
exit $miss
