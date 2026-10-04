#!/usr/bin/env python3
"""Turn word-level timestamps into a silence-trimmed edit (timing map).

Input  transcript.json: [{"text","start","end"}, ...]  or  {"words": [...]}
Output timing-map.json:
  ranges   - kept source ranges and where they land on the output timeline
  removed  - cut source ranges (dead air)
  words    - every word re-timed onto the output timeline (feed captions from this)
Optional:
  --silences silences.txt     ffmpeg silencedetect output; trims word boundaries that swallowed
                              pauses (whisper often stretches a word across the silence after it)
  --cut 22.7-22.98,55-60      source ranges to remove no matter what (retakes, stutters, spoken
                              "cut this" cues); padding never leaks back into them
  --srt captions.srt          short caption cues (1-4 words) on the output timeline
  --bake src.mp4 aroll.mp4    render the cuts into one constant-frame-rate A-roll with ffmpeg
                              (use for phone/WhatsApp VFR footage or many cuts; needs --fps)
  --clean                     with --bake: conservative voice cleanup before loudness
                              (rumble cut, denoise profiled from the longest pause, mud cut,
                              presence lift, gentle compression)

Usage:
  plan_cuts.py transcript.json -o timing-map.json [--gap 0.25] [--pad 0.08] [--fps 30] [--duration SRC_SECONDS]
               [--srt captions.srt] [--bake raw.mp4 aroll.mp4]
  plan_cuts.py --selftest
"""
import argparse
import json
import math
import re
import subprocess
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


def load_silences(path):
    """Parse `silence_start: x` / `silence_end: y` pairs from ffmpeg silencedetect output."""
    text = open(path, encoding="utf-8").read()
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", text)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", text)]
    return list(zip(starts, ends))


def trim_to_speech(words, silences, gap):
    """Remove pauses > gap that a word's span swallowed, without ever dropping sound.

    Whisper stretches words across silences (and sometimes merges a missed word into a
    neighbour), so a "word" can hold several bursts of speech. Split it into those bursts:
    the longest burst carries the text; the others stay as untitled speech so the cut
    planner keeps their audio but captions ignore them.
    """
    long = sorted((a, b) for a, b in silences if b - a > gap)
    out = []
    for g, w in enumerate(words):
        pieces = [(w["start"], w["end"])]
        for s0, s1 in long:
            nxt = []
            for a, b in pieces:
                if s1 <= a or s0 >= b:
                    nxt.append((a, b))
                    continue
                nxt += [p for p in ((a, min(b, s0)), (max(a, s1), b)) if p[1] - p[0] > 0.04]
            pieces = nxt
        if not pieces:  # all silence by the detector's account: trust whisper
            out.append(w)
            continue
        main = max(pieces, key=lambda p: p[1] - p[0])
        for a, b in pieces:
            out.append({**w, "start": round(a, 4), "end": round(b, 4), "group": g} if (a, b) == main
                       else {"text": "", "start": round(a, 4), "end": round(b, 4), "untitled": True,
                             "group": g, "orig_text": w["text"]})
    return sorted(out, key=lambda w: w["start"])


def subtract(ranges, cuts):
    """Remove forced-cut intervals from kept ranges."""
    for c0, c1 in sorted(cuts):
        nxt = []
        for r in ranges:
            a, b = r["src_start"], r["src_end"]
            if c1 <= a or c0 >= b:
                nxt.append(r)
                continue
            nxt += [{"src_start": x, "src_end": y} for x, y in ((a, c0), (c1, b)) if y - x > 0.02]
        ranges = nxt
    return ranges


def plan(words, gap=0.25, pad=0.08, fps=None, duration=None, cuts=()):
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

    if cuts:
        snap = (lambda t: round(t * fps) / fps) if fps else (lambda t: t)
        ranges = subtract(ranges, [(round(snap(a), 4), round(snap(b), 4)) for a, b in cuts])
        inside = lambda t: any(r["src_start"] <= t < r["src_end"] for r in ranges)
        kept = [w for w in words if inside((w["start"] + w["end"]) / 2)]
        # a forced cut can remove the burst that carried a word's text (e.g. whisper glued the
        # word to camera-handling noise) while its real speech survives: move the text there
        alive = {w.get("group") for w in kept if w["text"]}
        for w in sorted(kept, key=lambda w: w["start"] - w["end"]):  # longest first
            g = w.get("group")
            if w.get("untitled") and g is not None and g not in alive:
                w["text"] = w.pop("orig_text")
                w.pop("untitled")
                alive.add(g)
        words = kept

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
        while (j + 1 < len(ranges) and w["end"] > ranges[j]["src_end"]
               and ranges[j + 1]["src_start"] <= ranges[j]["src_end"] + 1e-6):
            j += 1
        r, r2 = ranges[k], ranges[j]
        timed.append({**w,
                      "out_start": round(max(w["start"], r["src_start"]) + r["out_start"] - r["src_start"], 4),
                      "out_end": round(min(w["end"], r2["src_end"]) + r2["out_start"] - r2["src_start"], 4)})

    return {
        "params": {"gap": gap, "pad": pad, "fps": fps, "cuts": [list(c) for c in cuts]},
        "source_duration": duration,
        "output_duration": round(out, 4),
        "ranges": ranges,
        "removed": removed,
        "words": timed,
    }


def srt_cues(words, max_words=4, max_gap=0.4):
    """Group re-timed words into short cues; break on punctuation, pauses and max_words."""
    cues, cur = [], []
    for w in (w for w in words if w["text"].strip()):
        if cur and (len(cur) >= max_words or w["out_start"] - cur[-1]["out_end"] > max_gap):
            cues.append(cur)
            cur = []
        cur.append(w)
        if w["text"].rstrip().endswith((".", "!", "?", "؟", "،", ",", "؛")):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    return [(c[0]["out_start"], c[-1]["out_end"], " ".join(w["text"].strip() for w in c)) for c in cues]


def write_srt(cues, path):
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, text) in enumerate(cues, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n\n")


def bake_filter(ranges, fps=30, fade=0.01):
    """ffmpeg filtergraph: resample to CFR first (VFR phone footage would otherwise gain or lose
    a frame per cut and drift out of sync), trim every kept range, 10 ms audio fades, concat."""
    n = len(ranges)
    parts = [f"[0:v]fps={fps:.6g},split={n}" + "".join(f"[sv{i}]" for i in range(n)),
             f"[0:a]asplit={n}" + "".join(f"[sa{i}]" for i in range(n))]
    labels = []
    for i, r in enumerate(ranges):
        a, b, d = r["src_start"], r["src_end"], r["duration"]
        parts.append(f"[sv{i}]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[sa{i}]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={fade},afade=t=out:st={max(d - fade, 0):.4f}:d={fade}[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    parts.append(f"{''.join(labels)}concat=n={len(ranges)}:v=1:a=1[v][a]")
    return ";".join(parts)


def noise_floor(src):
    """Room/hiss level to denoise against: astats' overall "Noise floor dB" (the quietest
    windowed RMS in the whole file). Detected "pauses" are a poor proxy - they often hold
    breaths or camera handling."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-vn", "-af", "astats=metadata=0", "-f", "null", "-"],
                       capture_output=True, text=True)
    vals = re.findall(r"Noise floor dB:\s*(-?[0-9.]+)", r.stderr)
    v = float(vals[-1]) if vals else -50.0  # last match = "Overall"
    return max(-70.0, min(-25.0, v))


def clean_chain(nf):
    """Conservative speech cleanup. Denoise by ~12 dB against the measured floor; no gating, so
    breaths and word tails survive (aggressive settings sound robotic)."""
    return (f"highpass=f=80,afftdn=nr=12:nf={nf:.0f}:tn=1,"
            "equalizer=f=300:t=q:w=1.0:g=-2,equalizer=f=3500:t=q:w=1.2:g=2,"
            "acompressor=threshold=-22dB:ratio=2.5:attack=10:release=160:makeup=1")


def ffmpeg_version():
    """(major, minor) of the ffmpeg on PATH; (99, 0) for git/unknown builds."""
    r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    m = re.search(r"ffmpeg version n?(\d+)\.(\d+)", r.stdout)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 0)


def bake(m, src, out, fps, lufs=-14.0, clean=None):
    graph = bake_filter(m["ranges"], fps)
    if clean is not None:
        graph = graph.replace("[0:a]asplit", f"[0:a]{clean_chain(clean)},asplit", 1)
    if lufs is not None:  # phone voice is usually far too quiet for social (-14 LUFS, -1 dBTP)
        graph = graph.replace("[v][a]", f"[v][a0];[a0]loudnorm=I={lufs}:TP=-1.5:LRA=11[a]")
    cfr = ["-fps_mode", "cfr"] if ffmpeg_version() >= (5, 1) else ["-vsync", "cfr"]  # -fps_mode is 5.1+
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", graph,
           "-map", "[v]", "-map", "[a]", "-r", f"{fps:.6g}", *cfr,
           "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-g", str(max(1, round(fps))),  # keyframe every second: fast, exact seeking in preview
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)


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
    # captions: 1-4 words, split on pauses and Arabic punctuation
    cw = [{"text": t, "out_start": i * 0.3, "out_end": i * 0.3 + 0.25} for i, t in enumerate("a b c d e".split())]
    cw[1]["text"] = "b\u060c"
    assert [c[2] for c in srt_cues(cw)] == ["a b\u060c", "c d e"], srt_cues(cw)
    # a word stretched across a long pause is trimmed back to its speech
    tw = trim_to_speech([{"text": "x", "start": 25.26, "end": 28.7}], [(26.99, 27.95), (25.03, 25.25)], 0.25)
    assert [(t["text"], t["start"], t["end"]) for t in tw] == [("x", 25.26, 26.99), ("", 27.95, 28.7)], tw
    # forced cut removes a stutter even though padding would have kept part of it
    mc = plan(words, gap=0.25, pad=0.08, duration=5.0, cuts=[(1.45, 1.95)])
    assert [w["text"] for w in mc["words"]] == ["a", "c", "d"], mc["words"]
    assert all(not (r["src_start"] < 1.9 and r["src_end"] > 1.5) for r in mc["ranges"]), mc["ranges"]
    # cut removes the burst holding the text; the surviving speech burst inherits it
    tw2 = trim_to_speech([{"text": "hi", "start": 0.0, "end": 2.4}], [(0.54, 0.77), (0.8, 2.03)], 0.2)
    mh = plan(tw2, gap=0.25, pad=0.08, duration=3.0, cuts=[(0, 2.0)])
    assert [w["text"] for w in mh["words"]] == ["hi"], mh["words"]
    assert clean_chain(-48).startswith("highpass") and "nf=-48" in clean_chain(-48)
    assert "concat=n=2" in bake_filter(m["ranges"]) and "atrim=start=2.92:end=3.73" in bake_filter(m["ranges"])
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
    ap.add_argument("--cut", default="", help="force-remove source ranges: 12.3-14,20-21.5")
    ap.add_argument("--silences", help="ffmpeg silencedetect output to tighten word boundaries")
    ap.add_argument("--srt", help="also write caption cues (output timeline) to this .srt")
    ap.add_argument("--bake", nargs=2, metavar=("SRC", "OUT"), help="render the cut A-roll with ffmpeg")
    ap.add_argument("--clean", action="store_true", help="with --bake: denoise/EQ/compress the voice")
    ap.add_argument("--lufs", type=float, default=-14.0, help="loudness target for --bake (use 'nan' to skip)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.transcript:
        ap.error("transcript path required")
    words = load_words(a.transcript)
    if a.silences:
        words = trim_to_speech(words, load_silences(a.silences), a.gap)
    cuts = [tuple(map(float, c.split("-"))) for c in a.cut.split(",") if c.strip()]
    m = plan(words, a.gap, a.pad, a.fps, a.duration, cuts)
    json.dump(m, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    src = a.duration or m["ranges"][-1]["src_end"]
    print(f"{len(m['ranges'])} ranges kept, {len(m['removed'])} cut, "
          f"{src:.2f}s -> {m['output_duration']:.2f}s  ->  {a.out}")
    if a.srt:
        write_srt(srt_cues(m["words"]), a.srt)
        print(f"captions -> {a.srt}")
    if a.bake:
        if not a.fps:
            ap.error("--bake needs --fps (the constant output frame rate)")
        nf = noise_floor(a.bake[0]) if a.clean else None
        if nf is not None:
            print(f"voice cleanup: noise floor {nf:.1f} dBFS")
        bake(m, *a.bake, a.fps, None if math.isnan(a.lufs) else a.lufs, nf)
        print(f"A-roll ({a.fps:.6g} fps CFR, cuts baked) -> {a.bake[1]}")


if __name__ == "__main__":
    main()
