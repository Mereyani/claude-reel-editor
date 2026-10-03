#!/usr/bin/env python3
"""Turn word-level timestamps into a silence-trimmed edit (timing map).

Input  transcript.json: [{"text","start","end"}, ...]  or  {"words": [...]}
Output timing-map.json:
  ranges   - kept source ranges and where they land on the output timeline
  removed  - cut source ranges (dead air)
  words    - every word re-timed onto the output timeline (feed captions from this)

Usage:
  plan_cuts.py transcript.json -o timing-map.json [--gap 0.25] [--pad 0.08] [--fps 30] [--duration SRC_SECONDS]
  plan_cuts.py --selftest
"""
import argparse
import json
import math
import sys
from fractions import Fraction


def load_words(path):
    data = json.load(open(path, encoding="utf-8"))
    words = data["words"] if isinstance(data, dict) else data
    # zero-length words (whisper emits some) still need a caption: give them 10 ms
    words = [{**w, "end": max(w["end"], w["start"] + 0.01)} for w in words]
    if not words:
        sys.exit("plan_cuts: transcript has no timed words")
    return sorted(words, key=lambda w: w["start"])


def plan(words, gap=0.25, pad=0.08, fps=None, duration=None):
    """Keep speech, cut pauses longer than `gap`, leave `pad` of room around speech."""
    if duration is not None:  # whisper sometimes hallucinates words past the end of the media
        words = [w for w in words if w["start"] < duration]
    if not words:
        sys.exit("plan_cuts: no words inside the source duration")
    # group words into speech runs separated by pauses > gap
    runs = [[words[0]["start"], words[0]["end"]]]
    for w in words[1:]:
        if w["start"] - runs[-1][1] > gap:
            runs.append([w["start"], w["end"]])
        else:
            runs[-1][1] = max(runs[-1][1], w["end"])

    end_limit = duration if duration is not None else runs[-1][1] + pad
    snap_down = (lambda t: math.floor(t * fps + 1e-6) / fps) if fps else (lambda t: t)
    snap_up = (lambda t: math.ceil(t * fps - 1e-6) / fps) if fps else (lambda t: t)

    ranges = []
    for i, (s, e) in enumerate(runs):
        # padding never reaches past the midpoint of the pause, so ranges can't overlap
        lo = (s + runs[i - 1][1]) / 2 if i else 0.0
        hi = (e + runs[i + 1][0]) / 2 if i + 1 < len(runs) else end_limit
        start = max(snap_down(max(s - pad, lo)), ranges[-1]["src_end"] if ranges else 0.0)
        end = min(snap_up(min(e + pad, hi)), end_limit)
        if round(end, 4) > round(start, 4):  # --duration can swallow a run entirely
            ranges.append({"src_start": round(start, 4), "src_end": round(end, 4)})

    out = 0.0
    for r in ranges:
        r["duration"] = round(r["src_end"] - r["src_start"], 4)
        r["out_start"] = round(out, 4)
        out += r["duration"]
        r["out_end"] = round(out, 4)

    removed, prev = [], 0.0
    for r in ranges:
        if r["src_start"] > prev:
            removed.append([round(prev, 4), r["src_start"]])
        prev = r["src_end"]
    if duration is not None and duration > prev:
        removed.append([round(prev, 4), round(duration, 4)])

    timed, k = [], 0
    for w in words:
        if w["start"] >= ranges[-1]["src_end"]:
            continue
        while k + 1 < len(ranges) and w["start"] >= ranges[k]["src_end"]:
            k += 1
        j = k  # frame snapping can push a word's end into the next (contiguous) range
        while j + 1 < len(ranges) and w["end"] > ranges[j]["src_end"]:
            j += 1
        r, r2 = ranges[k], ranges[j]
        timed.append({**w,
                      "out_start": round(max(w["start"], r["src_start"]) + r["out_start"] - r["src_start"], 4),
                      "out_end": round(min(w["end"], r2["src_end"]) + r2["out_start"] - r2["src_start"], 4)})

    return {
        "params": {"gap": gap, "pad": pad, "fps": fps},
        "source_duration": duration,
        "output_duration": round(out, 4),
        "ranges": ranges,
        "removed": removed,
        "words": timed,
    }


def selftest():
    words = [
        {"text": "a", "start": 1.00, "end": 1.40},
        {"text": "b", "start": 1.50, "end": 1.90},   # 0.10 pause -> kept
        {"text": "c", "start": 3.00, "end": 3.50},   # 1.10 pause -> cut
        {"text": "d", "start": 3.60, "end": 3.65},   # 0.10 pause -> kept
    ]
    m = plan(words, gap=0.25, pad=0.08, duration=5.0)
    assert len(m["ranges"]) == 2, m["ranges"]
    r0, r1 = m["ranges"]
    assert (r0["src_start"], r0["src_end"]) == (0.92, 1.98), r0
    assert (r1["src_start"], r1["src_end"]) == (2.92, 3.73), r1
    assert r1["out_start"] == r0["out_end"]
    assert m["removed"] == [[0.0, 0.92], [1.98, 2.92], [3.73, 5.0]], m["removed"]
    c = next(w for w in m["words"] if w["text"] == "c")
    assert abs(c["out_start"] - (r1["out_start"] + 0.08)) < 1e-9, c
    # tiny gap + big pad: padding must stop at the pause midpoint (no overlap)
    m2 = plan([{"text": "x", "start": 0, "end": 1}, {"text": "y", "start": 1.3, "end": 2}],
              gap=0.25, pad=0.5)
    assert m2["ranges"][0]["src_end"] <= m2["ranges"][1]["src_start"]
    # frame snapping keeps every range on the frame grid
    m3 = plan(words, fps=30, duration=5.0)
    for r in m3["ranges"]:
        for t in (r["src_start"], r["src_end"]):
            assert abs(t * 30 - round(t * 30)) < 0.01, t  # 4-decimal rounding ~0.0015 frame
    # word past --duration is dropped instead of producing a negative range
    m4 = plan([{"text": "x", "start": 0.5, "end": 1}, {"text": "ghost", "start": 6, "end": 6.5}], duration=5.0)
    assert all(r["duration"] > 0 for r in m4["ranges"]) and len(m4["words"]) == 1, m4
    # tiny gap + fps snapping must not shrink a boundary word to a flash
    m5 = plan([{"text": "x", "start": 2.477, "end": 3.144}, {"text": "y", "start": 3.2, "end": 3.64}],
              gap=0.05, pad=0.08, fps=29.97)
    for w in m5["words"]:
        assert w["out_end"] - w["out_start"] > 0.4, w
    assert fps_arg("30000/1001") == 30000 / 1001
    print("plan_cuts selftest: OK")


def fps_arg(v):
    """Accept ffprobe's r_frame_rate as-is: 30, 29.97 or 30000/1001."""
    return float(Fraction(v))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", nargs="?")
    ap.add_argument("-o", "--out", default="timing-map.json")
    ap.add_argument("--gap", type=float, default=0.25, help="cut pauses longer than this (s)")
    ap.add_argument("--pad", type=float, default=0.08, help="room kept around speech (s)")
    ap.add_argument("--fps", type=fps_arg, help="snap cuts to this frame rate (30, 29.97 or 30000/1001)")
    ap.add_argument("--duration", type=float, help="source duration (s), from ffprobe")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.transcript:
        ap.error("transcript path required")
    m = plan(load_words(a.transcript), a.gap, a.pad, a.fps, a.duration)
    json.dump(m, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    src = a.duration or m["ranges"][-1]["src_end"]
    print(f"{len(m['ranges'])} ranges kept, {len(m['removed'])} cut, "
          f"{src:.2f}s -> {m['output_duration']:.2f}s  ->  {a.out}")


if __name__ == "__main__":
    main()
