#!/usr/bin/env python3
"""Free/offline decisions for QUICK mode via a local Ollama model.

Asks the model for two small, checkable things and validates both, so a small model can't break
the edit:
  highlights.json            words to highlight (kept only if they really occur in the transcript)
  corrections.proposed.json  likely misrecognitions ("OBS" -> "Opus") - proposed, never auto-applied

Usage:
  local_assist.py --timing-map timing-map.json --out-dir edit [--model qwen3:8b] [--max 10]
  local_assist.py --selftest
Needs `ollama serve` running (default http://localhost:11434, override with OLLAMA_HOST).
"""
import argparse
import json
import os
import re
import sys
import urllib.request

PUNCT = ".,!?\u061f\u060c\u061b:\"'()"
PROMPT = """You help edit a short social video. Below is its transcript (it may be Arabic dialect mixed with English names).
Return ONLY a JSON object with two keys:
"highlights": up to {n} single words, copied EXACTLY as written in the transcript, that carry the key meaning (names, the main idea, numbers). Prefer nouns. No duplicates.
"corrections": a list of {{"wrong": "...", "right": "..."}} ONLY for obvious speech-recognition errors in product or brand names or English terms (for example a product name the recognizer turned into a similar-sounding common word or wrong letters). Use [] if unsure.

Transcript:
{text}"""


def norm(w):
    return w.strip(PUNCT)


def validate(raw, words, n):
    """Keep only answers that are grounded in the transcript."""
    vocab = {norm(w): w for w in words}
    hl, seen = [], set()
    for h in raw.get("highlights", []) or []:
        k = norm(str(h))
        if k in vocab and k not in seen and len(hl) < n:
            hl.append(vocab[k]); seen.add(k)
    fixes = [c for c in (raw.get("corrections", []) or [])
             if isinstance(c, dict) and norm(str(c.get("wrong", ""))) in vocab
             and str(c.get("right", "")).strip() and norm(str(c["right"])) != norm(str(c["wrong"]))]
    return hl, fixes


def ask(model, prompt, host):
    body = json.dumps({"model": model, "stream": False, "format": "json", "options": {"temperature": 0},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        content = json.load(r)["message"]["content"]
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S)   # reasoning models
    return json.loads(content)


def selftest():
    words = ["نموذج", "Claude", "الجديد", "OBS", "5.5.", "المونتاج", "الفكرة،"]
    raw = {"highlights": ["Claude", "المونتاج", "الفكرة", "invented", "Claude"],
           "corrections": [{"wrong": "OBS", "right": "Opus"}, {"wrong": "ghost", "right": "x"},
                           {"wrong": "Claude", "right": "Claude"}]}
    hl, fixes = validate(raw, words, 10)
    assert hl == ["Claude", "المونتاج", "الفكرة،"], hl          # grounded, deduped, original spelling
    assert fixes == [{"wrong": "OBS", "right": "Opus"}], fixes  # hallucinated / no-op fixes dropped
    assert validate({"highlights": ["Claude", "المونتاج"]}, words, 1)[0] == ["Claude"]
    print("local_assist selftest: OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timing-map")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "qwen3:8b"))
    ap.add_argument("--max", type=int, default=10, help="max highlighted words")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.timing_map:
        ap.error("--timing-map required")
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if not host.startswith("http"):
        host = "http://" + host
    words = [w["text"] for w in json.load(open(a.timing_map, encoding="utf-8"))["words"] if w["text"].strip()]
    try:
        raw = ask(a.model, PROMPT.format(n=a.max, text=" ".join(words)), host)
    except Exception as e:  # noqa: BLE001 - surface any connection/model problem plainly
        sys.exit(f"local_assist: could not get an answer from Ollama model '{a.model}' at {host}: {e}\n"
                 f"  start it with `ollama serve`, and pull the model with `ollama pull {a.model}`")
    hl, fixes = validate(raw, words, a.max)
    json.dump(hl, open(os.path.join(a.out_dir, "highlights.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(fixes, open(os.path.join(a.out_dir, "corrections.proposed.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"{len(hl)} highlights, {len(fixes)} proposed corrections ({a.model}) -> {a.out_dir}")


if __name__ == "__main__":
    main()
