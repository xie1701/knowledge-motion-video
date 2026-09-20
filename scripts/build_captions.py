#!/usr/bin/env python3
"""Build SRT + ASS captions from word-level timings and a scene manifest.

Word timings come from either:

- ``--transcript``  JSON produced by ``coli asr -j`` (fields ``tokens``,
  ``timestamps``, ``duration``), or
- ``--words-json``  a custom ``[{"text": ..., "startSec": ..., "endSec": ...}]`` file.

Words are assigned to scenes from ``storyboard/scenes.json`` by their midpoint.
Cues split on CJK punctuation (，。！？、；：) or when they exceed ``--max-chars``
Chinese characters, and never cross a scene boundary. The ASS style is derived
from the manifest's ``design`` block and ``project.captionSafeArea``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PUNCTUATION = "，。！？、；：！？；"
DEFAULT_MAX_CHARS = 16
FALLBACK_WORD_SEC = 0.35


def err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def clamp_positive(value: float) -> float:
    return value if value > 0 else FALLBACK_WORD_SEC


def load_words_from_transcript(path: Path) -> list[dict]:
    """Convert coli asr tokens/timestamps into [{text,startSec,endSec}]."""
    data = json.loads(path.read_text(encoding="utf-8"))
    tokens = data.get("tokens")
    timestamps = data.get("timestamps")
    if not isinstance(tokens, list) or not isinstance(timestamps, list):
        raise ValueError("transcript must contain 'tokens' and 'timestamps' arrays")
    if len(tokens) != len(timestamps):
        raise ValueError(
            f"tokens ({len(tokens)}) and timestamps ({len(timestamps)}) lengths differ"
        )

    # Support both scalar start times and [start, end] pairs.
    if timestamps and isinstance(timestamps[0], (list, tuple)):
        return [
            {"text": tok, "startSec": float(span[0]), "endSec": float(span[-1])}
            for tok, span in zip(tokens, timestamps)
        ]

    starts = [float(t) for t in timestamps]
    duration = float(data.get("duration") or 0.0)
    words = []
    for i, tok in enumerate(tokens):
        start = starts[i]
        if i + 1 < len(starts):
            end = starts[i + 1]
        else:
            end = duration if duration > start else start + FALLBACK_WORD_SEC
        words.append({"text": tok, "startSec": start, "endSec": max(end, start)})
    return words


def load_words_json(path: Path) -> list[dict]:
    words = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for i, entry in enumerate(words):
        try:
            out.append(
                {
                    "text": str(entry["text"]),
                    "startSec": float(entry["startSec"]),
                    "endSec": float(entry["endSec"]),
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"words-json entry {i} is malformed: {exc}") from exc
    return out


def assign_words_to_scenes(words: list[dict], scenes: list[dict]) -> dict[str, list[dict]]:
    """Group words by the scene containing their midpoint."""
    buckets: dict[str, list[dict]] = {scene["id"]: [] for scene in scenes}
    dropped = 0
    for word in words:
        mid = (word["startSec"] + word["endSec"]) / 2.0
        for scene in scenes:
            start = float(scene["startSec"])
            if start <= mid < start + float(scene["durationSec"]):
                buckets[scene["id"]].append(word)
                break
        else:
            dropped += 1
    if dropped:
        print(f"note: {dropped} word(s) fall outside every scene and are skipped", file=sys.stderr)
    return buckets


def join_text(left: str, right_token: str) -> str:
    """Join ASR tokens preserving the spacing embedded in the tokens.

    sensevoice-style tokens are either single CJK characters (no spaces) or
    latin fragments that already carry their own leading spaces (e.g.
    ' an' + 'imate' -> ' animate'). Plain concatenation therefore reproduces
    the ASR text exactly; adding our own spaces corrupts words like 'skill'.
    """
    return left + right_token


def cue_length(text: str) -> int:
    return len(text.replace(" ", ""))


def build_cues(scene_words: list[dict], scene: dict, max_chars: int) -> list[dict]:
    cues: list[dict] = []
    scene_start = float(scene["startSec"])
    scene_end = scene_start + float(scene["durationSec"])
    text = ""
    start = 0.0
    end = 0.0
    for word in scene_words:
        if not text:
            start = word["startSec"]
        text = join_text(text, word["text"])
        end = max(end, word["endSec"])
        must_break = bool(word["text"]) and word["text"][-1] in PUNCTUATION
        over_limit = cue_length(text) >= max_chars
        if must_break or over_limit:
            clean = text.lstrip("，。？！、；：,.?")
            if clean:
                cues.append(
                    {
                        "text": clean,
                        "startSec": max(start, scene_start),
                        "endSec": min(max(end, start + 0.1), scene_end),
                    }
                )
            text, end = "", 0.0
    if text:
        clean = text.lstrip("，。？！、；：,.?")
        if clean:
            cues.append(
                {
                    "text": clean,
                    "startSec": max(start, scene_start),
                    "endSec": min(max(end, start + 0.1), scene_end),
                }
            )
    # Merge flash cues (<0.8s) into their successor so no caption blinks by
    # unreadably fast; the last cue may absorb into its predecessor instead.
    merged: list[dict] = []
    for cue in cues:
        if merged and (cue["endSec"] - cue["startSec"]) < 0.8:
            prev = merged[-1]
            prev["endSec"] = cue["endSec"]
            prev["text"] += cue["text"]
        elif (
            merged
            and (merged[-1]["endSec"] - merged[-1]["startSec"]) < 0.8
            and cue_length(merged[-1]["text"] + cue["text"]) <= max_chars
        ):
            prev = merged[-1]
            prev["endSec"] = cue["endSec"]
            prev["text"] += cue["text"]
        else:
            merged.append(cue)
    return merged


def srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def ass_time(seconds: float) -> str:
    centis = int(round(seconds * 100))
    hours, centis = divmod(centis, 360_000)
    minutes, centis = divmod(centis, 6_000)
    secs, centis = divmod(centis, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"


def ass_color(hex_color: str, alpha: str = "00") -> str:
    """Convert #RRGGBB to ASS &HAABBGGRR."""
    value = hex_color.lstrip("#")
    if len(value) != 6:
        value = "000000"
    rr, gg, bb = value[0:2], value[2:4], value[4:6]
    return f"&H{alpha}{bb}{gg}{rr}".upper()


def build_ass_header(manifest: dict) -> str:
    project = manifest.get("project", {})
    design = manifest.get("design", {})
    safe = project.get("captionSafeArea", {})
    width = int(project.get("width", 1080))
    height = int(project.get("height", 1920))
    font = design.get("displayFont") or design.get("bodyFont") or "sans-serif"
    safe_x = int(safe.get("x", round(width * 0.07)))
    safe_w = int(safe.get("width", width - 2 * safe_x))
    safe_h = int(safe.get("height", round(height * 0.1)))
    margin_l = safe_x
    margin_r = max(0, width - safe_x - safe_w)
    margin_v = max(0, height - (int(safe.get("y", 0)) + safe_h))
    fontsize = max(20, round(safe_h * 0.42))

    foreground = ass_color(design.get("foreground", "#FFFFFF"))
    accent = ass_color(design.get("accent", foreground))
    background = ass_color(design.get("background", "#000000"))
    return "\n".join(
        [
            "[Script Info]",
            f"; Title: {project.get('title', 'captions')}",
            "; ScriptType: v4.00+",
            f"PlayResX: {width}",
            f"PlayResY: {height}",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            (
                f"Style: Caption,{font},{fontsize},{foreground},{accent},{background},"
                f"{background},0,0,0,0,100,100,0,0,1,2,0,2,{margin_l},{margin_r},{margin_v},1"
            ),
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
    )


def write_srt(cues: list[dict], path: Path) -> None:
    lines = []
    for i, cue in enumerate(cues, start=1):
        lines.append(str(i))
        lines.append(f"{srt_time(cue['startSec'])} --> {srt_time(cue['endSec'])}")
        lines.append(cue["text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_ass(cues: list[dict], header: str, path: Path) -> None:
    events = [
        f"Dialogue: 0,{ass_time(c['startSec'])},{ass_time(c['endSec'])},Caption,,0,0,0,,{c['text']}"
        for c in cues
    ]
    path.write_text("\n".join([header, *events, ""]) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--transcript", type=Path, help="coli asr -j transcript JSON")
    parser.add_argument("--words-json", type=Path, help="custom [{text,startSec,endSec}] JSON")
    parser.add_argument("--scenes", type=Path, required=True, help="storyboard/scenes.json")
    parser.add_argument("--out-dir", type=Path, required=True, help="output directory for captions")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                        help=f"max characters per cue (default {DEFAULT_MAX_CHARS})")
    parser.add_argument("--prefix", default="captions", help="output file basename (default: captions)")
    parser.add_argument("--preview", type=int, default=3, help="print the first N cues (default 3)")
    args = parser.parse_args()

    if bool(args.transcript) == bool(args.words_json):
        err("pass exactly one of --transcript or --words-json")
        raise SystemExit(2)

    try:
        words = (
            load_words_from_transcript(args.transcript)
            if args.transcript
            else load_words_json(args.words_json)
        )
        manifest = json.loads(args.scenes.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        err(str(exc))
        raise SystemExit(2)

    scenes = manifest.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        err(f"{args.scenes} contains no scenes array")
        raise SystemExit(2)

    buckets = assign_words_to_scenes(words, scenes)
    cues: list[dict] = []
    for scene in scenes:
        cues.extend(build_cues(buckets.get(scene["id"], []), scene, args.max_chars))
    cues.sort(key=lambda c: c["startSec"])

    if not cues:
        err("no cues produced: word timings and scene time ranges do not overlap")
        raise SystemExit(1)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    srt_path = args.out_dir / f"{args.prefix}.srt"
    ass_path = args.out_dir / f"{args.prefix}.ass"
    write_srt(cues, srt_path)
    write_ass(cues, build_ass_header(manifest), ass_path)

    print(f"wrote {len(cues)} cues from {len(words)} words")
    print(f"  {srt_path}")
    print(f"  {ass_path}")
    for cue in cues[: max(args.preview, 0)]:
        print(f"  [{cue['startSec']:7.2f} -> {cue['endSec']:7.2f}] {cue['text']}")


if __name__ == "__main__":
    main()
