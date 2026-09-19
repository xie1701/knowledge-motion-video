#!/usr/bin/env python3
"""Assemble the final video: visual master + narration + bgm + burned captions.

- narration is the primary audio (volume 1.0); bgm sits underneath (volume 0.18).
- loudness normalization (single-pass loudnorm, -16 LUFS) is on by default;
  disable with --no-loudnorm.
- captions are always burned last in the filter chain (ass -> ass filter,
  srt -> subtitles filter).
- with no narration/bgm/captions/normalization the master is stream-copied.

After encoding, ffprobe re-reads the output and a JSON summary is printed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

BGM_VOLUME = 0.18
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def ffprobe_json(path: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        die(f"ffprobe failed for {path}: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def summarize(probe: dict) -> dict:
    video = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)
    return {
        "durationSec": float(probe.get("format", {}).get("duration") or 0.0),
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "videoCodec": video.get("codec_name") if video else None,
        "audioCodec": audio.get("codec_name") if audio else None,
        "hasAudio": audio is not None,
    }


def escape_filter_path(path: str) -> str:
    """Escape a filename for use inside an ffmpeg filter argument."""
    return re.sub(r"([\\':,])", r"\\\1", path)


def caption_filter(captions: Path) -> str:
    suffix = captions.suffix.lower()
    escaped = escape_filter_path(str(captions.resolve()))
    if suffix == ".ass":
        return f"ass={escaped}"
    if suffix == ".srt":
        return f"subtitles={escaped}"
    die(f"unsupported caption format {suffix!r} (use .ass or .srt)")


def build_command(args: argparse.Namespace, source: dict) -> tuple[list[str], bool]:
    """Return (ffmpeg argv, video_is_copied)."""
    has_audio_source = bool(args.narration or args.bgm)
    duration = source["durationSec"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(args.visual)]
    if args.narration:
        cmd += ["-i", str(args.narration)]
    if args.bgm:
        cmd += ["-i", str(args.bgm)]

    # Fast path: nothing to do at all.
    if not has_audio_source and not args.captions and not (args.loudnorm and source["hasAudio"]):
        cmd += ["-c", "copy"]
        if duration > 0:
            cmd += ["-t", f"{duration:.3f}"]
        cmd += [str(args.out)]
        return cmd, True

    filters: list[str] = []
    maps: list[str] = []

    # --- video ---
    if args.captions:
        filters.append(f"[0:v]{caption_filter(args.captions)}[vout]")
        maps += ["-map", "[vout]"]
    else:
        maps += ["-map", "0:v:0"]

    # --- audio ---
    sources: list[str] = []
    if args.narration:
        filters.append("[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                       f"volume=1.0[nar]")
        sources.append("[nar]")
    if args.bgm:
        bgm_label_in = "[2:a]" if args.narration else "[1:a]"
        filters.append(f"{bgm_label_in}aformat=sample_fmts=fltp:sample_rates=48000:"
                       f"channel_layouts=stereo,volume={BGM_VOLUME}[bgm]")
        sources.append("[bgm]")

    if sources and not args.narration and source["hasAudio"]:
        # No narration: keep the master's own audio underneath the bgm.
        filters.append("[0:a]aformat=sample_fmts=fltp:sample_rates=48000:"
                       "channel_layouts=stereo[master]")
        sources.insert(0, "[master]")

    if len(sources) > 1:
        filters.append(
            "".join(sources)
            + f"amix=inputs={len(sources)}:duration=longest:normalize=0[mix]"
        )
    elif sources:
        filters.append(f"{sources[0]}anull[mix]")
    else:
        filters.append("[0:a]anull[mix]")

    if args.loudnorm:
        filters.append("[mix]" + LOUDNORM + ",aresample=48000[aout]")
    else:
        filters.append("[mix]anull[aout]")
    maps += ["-map", "[aout]"]

    cmd += ["-filter_complex", ";".join(filters), *maps]
    if duration > 0:
        cmd += ["-t", f"{duration:.3f}"]
    if args.captions:
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(args.out)]
    return cmd, not args.captions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--visual", type=Path, required=True, help="visual master mp4")
    parser.add_argument("--narration", type=Path, help="narration wav/mp3 (optional)")
    parser.add_argument("--bgm", type=Path, help="background music (optional, volume 0.18)")
    parser.add_argument("--captions", type=Path, help="caption file to burn (.ass or .srt)")
    parser.add_argument("--out", type=Path, required=True, help="output mp4")
    parser.add_argument("--loudnorm", action=argparse.BooleanOptionalAction, default=True,
                        help="single-pass loudness normalization to -16 LUFS (default: on)")
    args = parser.parse_args()

    for label, path in (("--visual", args.visual), ("--narration", args.narration),
                        ("--bgm", args.bgm), ("--captions", args.captions)):
        if path and not path.exists():
            die(f"{label} not found: {path}")
    if shutil.which("ffmpeg") is None:
        die("ffmpeg not found on PATH")

    source = summarize(ffprobe_json(args.visual))
    cmd, video_copied = build_command(args, source)
    print("+ " + " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        die(f"ffmpeg failed:\n{proc.stderr.strip()}")

    result = summarize(ffprobe_json(args.out))
    result.update(
        {
            "out": str(args.out),
            "videoCopied": video_copied,
            "loudnorm": args.loudnorm,
            "narration": str(args.narration) if args.narration else None,
            "bgm": str(args.bgm) if args.bgm else None,
            "captions": str(args.captions) if args.captions else None,
            "sourceDurationSec": source["durationSec"],
            "durationDeltaSec": round(result["durationSec"] - source["durationSec"], 3),
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if abs(result["durationDeltaSec"]) > 1.0:
        die(f"output duration differs from source by {result['durationDeltaSec']}s", 1)


if __name__ == "__main__":
    main()
