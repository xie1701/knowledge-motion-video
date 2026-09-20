#!/usr/bin/env python3
"""check_narration.py — 旁白体检：时长、超长停顿、削波。

用法：
  python3 scripts/check_narration.py audio/narration.mp3 [more.mp3 ...]
  python3 scripts/check_narration.py --min-gap 3.0 --json audio/*.mp3

为什么需要：ListenHub 这类 TTS 会**静默丢句**——实测两次生成各出现一段 41s / 58s 的
纯静音，而 ASR 的 token 时间戳会直接跨过那段静音跳到下一句。后果是：切场时出现
「某一小段时长 0.00s」、或者整片时间轴与画面对不上，而且不看波形根本发现不了。
所以「拿到旁白音频 → 先体检 → 再进管线」应当是一次固定动作。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def probe(path: Path) -> dict:
    """时长 + 超长停顿 + 电平。返回 dict（全部为量出来的数字，不做猜测）。"""
    out: dict = {"file": str(path), "duration": None, "gaps": [], "meanDb": None,
                 "maxDb": None, "clipped": False}
    if shutil.which("ffprobe"):
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True)
        if p.returncode == 0 and p.stdout.strip():
            out["duration"] = round(float(p.stdout.strip()), 3)
    if not shutil.which("ffmpeg"):
        return out
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path),
                        "-af", "volumedetect", "-f", "null", "/dev/null"],
                       capture_output=True, text=True)
    log = (p.stderr or "")
    for key, field in (("mean_volume", "meanDb"), ("max_volume", "maxDb")):
        m = re.search(rf"{key}: (-?[\d.]+) dB", log)
        if m:
            out[field] = float(m.group(1))
    out["clipped"] = bool(re.search(r"max_volume: 0\.0 dB", log))
    return out


def silence_gaps(path: Path, min_gap: float = 3.0, noise_db: float = -45.0) -> list:
    if not shutil.which("ffmpeg"):
        return []
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                        f"silencedetect=noise={noise_db}dB:d={min_gap}", "-f", "null",
                        "/dev/null"], capture_output=True, text=True)
    gaps, start = [], None
    for m in re.finditer(r"silence_(start|end): ([\d.]+)", p.stderr or ""):
        if m.group(1) == "start":
            start = float(m.group(2))
        elif start is not None:
            gaps.append((round(start, 2), round(float(m.group(2)), 2)))
            start = None
    return gaps


def main() -> int:
    ap = argparse.ArgumentParser(description="旁白体检：时长 / 超长停顿 / 削波")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--min-gap", type=float, default=3.0,
                    help="多长的静音算「可能丢句」（默认 3s；中文叙述里 3s 以上很不寻常）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows, bad = [], 0
    for path in args.files:
        if not path.exists():
            print(f"ERROR: 找不到 {path}", file=sys.stderr)
            return 2
        info = probe(path)
        info["gaps"] = silence_gaps(path, args.min_gap)
        rows.append(info)
        if info["gaps"] or info["clipped"]:
            bad += 1
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            flag = "  <-- 检查" if (r["gaps"] or r["clipped"]) else ""
            print(f"{Path(r['file']).name}: {r['duration']}s  "
                  f"mean {r['meanDb']}dB / max {r['maxDb']}dB{flag}")
            for a, b in r["gaps"]:
                print(f"    ! 静音 {a}s → {b}s（{b - a:.1f}s）：TTS 很可能把那一句丢了")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
