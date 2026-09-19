#!/usr/bin/env python3
"""Narration TTS via the edge-tts package (optional dependency).

Synthesizes an MP3 plus a word-level timing JSON built from edge-tts
``WordBoundary`` events:

    {"text": "...", "startSec": 0.0, "endSec": 0.21, "duration": 3.42}

Requires the third-party ``edge_tts`` package. If it is not installed the
script prints a hint and exits with code 3 (it is NEVER installed here).

Usage:
    python3 scripts/tts_edge.py --text "你好世界" --out-dir assets/audio
    python3 scripts/tts_edge.py --text-file script/narration.md --voice zh-CN-XiaoxiaoNeural
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--text", help="text to synthesize")
    parser.add_argument("--text-file", type=Path, help="read the text from this file instead")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="edge-tts voice name")
    parser.add_argument("--rate", default="+0%", help="speaking rate, e.g. +10%% (default +0%%)")
    parser.add_argument("--out-dir", type=Path, default=Path("assets/audio"),
                        help="output directory (default assets/audio)")
    parser.add_argument("--prefix", default="narration", help="output basename (default narration)")
    args = parser.parse_args()

    if importlib.util.find_spec("edge_tts") is None:
        print(
            "edge-tts is not installed.\n"
            "  This script requires the optional `edge_tts` package.\n"
            "  Install it manually if you want it:  pip install edge-tts\n"
            "  Alternative: use `coli tts` or provide narration.mp3 directly.",
            file=sys.stderr,
        )
        raise SystemExit(3)

    if bool(args.text) == bool(args.text_file):
        die("pass exactly one of --text or --text-file")

    text = args.text or args.text_file.read_text(encoding="utf-8").strip()
    if not text:
        die("text is empty")
    if len(text) > 2000:
        die(f"text is {len(text)} chars; edge-tts accepts at most ~2000 per request")

    import edge_tts  # deferred: only imported when the package exists

    async def synthesize() -> None:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        mp3_path = args.out_dir / f"{args.prefix}.mp3"
        words_path = args.out_dir / f"{args.prefix}.words.json"

        words: list[dict] = []
        duration = 0.0
        communicate = edge_tts.Communicate(text, args.voice, rate=args.rate)
        with mp3_path.open("wb") as audio:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 1e7  # 100ns ticks -> seconds
                    end = start + chunk["duration"] / 1e7
                    words.append({
                        "text": chunk["text"],
                        "startSec": round(start, 3),
                        "endSec": round(end, 3),
                    })
                    duration = max(duration, end)

        if not audio_tell_ok(mp3_path):
            die("no audio was produced; edge-tts service may be unreachable")

        payload = {
            "text": text,
            "voice": args.voice,
            "duration": round(duration, 3),
            "tokens": [w["text"] for w in words],
            "timestamps": [[w["startSec"], w["endSec"]] for w in words],
        }
        words_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"voice: {args.voice}")
        print(f"  {mp3_path}  ({duration:.2f}s, {len(words)} word boundaries)")
        print(f"  {words_path}")

    def audio_tell_ok(path: Path) -> bool:
        return path.exists() and path.stat().st_size > 0

    try:
        asyncio.run(synthesize())
    except Exception as exc:  # network errors etc.
        die(f"edge-tts synthesis failed: {exc}", 1)


if __name__ == "__main__":
    main()
