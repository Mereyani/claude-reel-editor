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
if command -v ffmpeg >/dev/null; then
  v=$(ffmpeg -version | head -1 | sed -E 's/^ffmpeg version n?([0-9]+)\.([0-9]+).*/\1 \2/')
  set -- $v
  if [ "${1:-99}" -lt 5 ] 2>/dev/null; then warn "ffmpeg $1.$2" "works (plan_cuts falls back to -vsync) but 5.1+ is recommended"; fi
fi
command -v yt-dlp >/dev/null && ok "yt-dlp" || warn "yt-dlp" "only for copying a reference reel's style: pip install yt-dlp"

command -v python3 >/dev/null && ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)" || bad "python3" "https://python.org"

# the shell's python3 may not be the one with faster-whisper (e.g. conda not on PATH in a new session)
fw=""
for py in python3 ~/.venvs/reel/bin/python3 ~/miniconda3/bin/python3 ~/anaconda3/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  "$py" -c 'import faster_whisper' 2>/dev/null && fw=$(command -v "$py" 2>/dev/null || echo "$py") && break
done
if [ -n "$fw" ]; then ok "faster-whisper  (use: $fw)"
else bad "faster-whisper" "python3 -m pip install faster-whisper  (\"externally-managed-environment\"? use: python3 -m venv ~/.venvs/reel && ~/.venvs/reel/bin/pip install faster-whisper)  — first run downloads the large-v3 model (~3 GB)"; fi

# optional: free local decisions for quick mode
if command -v ollama >/dev/null; then ok "ollama (quick mode can run free: scripts/local_assist.py)"
else warn "ollama" "optional — free local highlights/corrections in quick mode: https://ollama.com"; fi

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
