#!/usr/bin/env python3
"""mix_audio.py — 把旁白与音效混成主音轨。

音效来自 scenes.json 中 type=audio-sfx 的 assets（fetch_assets.py 已下载到
assets/media/），字段 `atSec`（场景内相对秒）决定混入时刻，绝对时刻 =
scene.startSec + atSec。音效默认 -6dB（约 0.5 倍音量），不压过旁白。

用法：
  python3 mix_audio.py --scenes <project>/storyboard/scenes.json \
      --narration <project>/audio/narration.mp3 --out <project>/audio/mix.wav

依赖 ffmpeg。退出码：0 成功 / 1 参数或数据错误。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SFX_GAIN = 0.25  # 约 -12dB，避免音效压过旁白或突兀


def main() -> int:
    ap = argparse.ArgumentParser(description="旁白 + 音效 → 混音主轨")
    ap.add_argument("--scenes", required=True)
    ap.add_argument("--narration", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sfx-gain", type=float, default=SFX_GAIN)
    args = ap.parse_args()

    scenes_path = Path(args.scenes)
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    narration = Path(args.narration).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg 不可用", file=sys.stderr)
        return 1

    base_dir = scenes_path.parent.parent  # <project>
    events: list[tuple[float, Path]] = []
    for sc in doc.get("scenes", []):
        for asset in sc.get("assets", []) or []:
            if asset.get("type") != "audio-sfx":
                continue
            local = asset.get("local")
            if not local:
                print(f"WARN: audio-sfx {asset.get('id')} 缺少 local（先跑 fetch_assets.py），跳过")
                continue
            f = base_dir / local
            if not f.is_file():
                print(f"WARN: 音效文件不存在 {f}，跳过")
                continue
            at = float(sc.get("startSec", 0)) + float(asset.get("atSec", 0) or 0)
            events.append((round(at, 3), f))
    events.sort()

    # 构造 filter_complex：旁白 + 每个音效 adelay 后 amix
    parts = ["[0:a]aformat=sample_rates=48000:channel_layouts=mono[n]"]
    labels = ["n"]
    dur = float(doc.get("project", {}).get("durationSec", 0)) or None
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", str(narration)]
    for i, (at, f) in enumerate(events):
        ms = int(at * 1000)
        cmd += ["-i", str(f)]
        # 音效淡入淡出（30ms/120ms）消除突兀感；长度用 ffprobe 实测
        try:
            fdur = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(f)], check=True, capture_output=True, text=True
            ).stdout.strip())
        except Exception:  # noqa: BLE001
            fdur = 0.0
        fade_out = f",afade=t=out:st={max(0.0, fdur - 0.12):.3f}:d=0.12" if fdur > 0.2 else ""
        parts.append(f"[{i + 1}:a]aformat=sample_rates=48000:channel_layouts=mono,"
                     f"volume={args.sfx_gain},afade=t=in:d=0.03{fade_out},"
                     f"adelay={ms}|{ms}[s{i}]")
        labels.append(f"s{i}")
    amix_in = "".join(f"[{l}]" for l in labels)
    fc = ";".join(parts) + f";{amix_in}amix=inputs={len(labels)}:duration=longest:normalize=0"
    if dur:
        fc += f",apad,atrim=0:{dur}"
    cmd += ["-filter_complex", fc, "-c:a", "pcm_s16le", str(out)]
    subprocess.run(cmd, check=True)
    print(f"混音完成: {out}  （旁白 + {len(events)} 条音效）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
