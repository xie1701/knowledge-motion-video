#!/usr/bin/env python3
"""style_sweep.py — 同一段文案在全部风格里各渲一遍，出对比网格与抽帧表。

用途：风格路由选完主风格后，用同一段文案横向比一遍 15 条风格的真实成片效果
（不是看模板 HTML，是看渲染出来的片子），确认主风格选择、也方便给别人看风格差异。

做法：对每条风格跑一次 make_video.py（同一 copy / narration / transcript / data），
然后
  1) 从每条成片的 65% 时刻抽一帧，拼成 5×3 抽帧表（带风格名标注）
  2) 把 15 条短片按 5×3 并排压成一支对比片（各格带风格名）
产物：<out-dir>/sweep-contact-sheet.jpg、<out-dir>/sweep-grid.mp4、<out-dir>/sweep-report.json

用法：
  style_sweep.py --copy c.txt --narration n.mp3 --transcript t.json --out-dir q/
                  [--styles a,b,c] [--data d.json] [--fps 30] [--no-grid]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
CELL_W, CELL_H = 270, 480
COLS, ROWS = 5, 3


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Label,Helvetica,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,3,2,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def label_ass(labels: list[tuple[str, int, int]], grid_w: int, grid_h: int,
              path: Path) -> Path:
    """把风格名写进 ASS 覆盖层——这台 ffmpeg 没有 drawtext（未编 freetype），
    但 libass 一定在（烧录字幕走的就是它）。"""
    events = []
    for name, x, y in labels:
        events.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,Label,,0,0,0,,"
                      f"{{\\pos({x},{y})}}{name}")
    path.write_text(ASS_HEAD.format(w=grid_w, h=grid_h) + "\n".join(events) + "\n",
                    encoding="utf-8")
    return path


def run(cmd: list, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)


def probe_duration(path: Path) -> float:
    proc = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "csv=p=0", path])
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--copy", type=Path, required=True)
    ap.add_argument("--narration", type=Path, required=True)
    ap.add_argument("--transcript", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--styles", default="", help="逗号分隔，默认全部 15 条")
    ap.add_argument("--data", type=Path, help="图表数据 JSON（data-viz 用）")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--no-grid", action="store_true", help="只出抽帧表，不合成对比片")
    args = ap.parse_args()

    sys.path.insert(0, str(SCRIPTS))
    import make_video as mv  # noqa: E402

    styles = [s for s in args.styles.split(",") if s] or sorted(mv.STYLE_PALETTES)
    out_dir: Path = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    table: list[dict] = []
    clips: list[tuple[str, Path]] = []
    for i, style in enumerate(styles, 1):
        proj = out_dir / style
        proj.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, SCRIPTS / "make_video.py", "--copy", args.copy,
               "--project", proj, "--style", style, "--go",
               "--narration", args.narration, "--transcript", args.transcript,
               "--fps", str(args.fps)]
        if args.data:
            cmd += ["--data", args.data]
        print(f"[{i:02d}/{len(styles)}] {style} …", flush=True)
        proc = run(cmd)
        final = proj / "renders" / "final.mp4"
        ok = proc.returncode == 0 and final.exists()
        charts = proj / "storyboard" / "charts.json"
        entry = {"style": style, "ok": ok, "durationSec": round(probe_duration(final), 2)
                 if ok else 0.0}
        if charts.exists():
            entry["charts"] = [f"{c['scene']}:{c['mode']}" for c in
                               json.loads(charts.read_text(encoding="utf-8"))]
        if not ok:
            entry["error"] = (proc.stderr or proc.stdout or "")[-400:]
            print(f"    FAILED: {entry['error'].strip().splitlines()[-1][:120]}", file=sys.stderr)
        table.append(entry)
        if ok:
            clips.append((style, final))

    # 1) 抽帧表：每片 65% 处抽一帧，5×3 拼图 + 风格名
    if clips:
        frames_dir = out_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        frame_paths: list[Path] = []
        for style, final in clips:
            dur = probe_duration(final)
            out = frames_dir / f"{style}.png"
            run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{max(dur * 0.65, 0.1):.2f}",
                 "-i", final, "-frames:v", "1", "-update", "1", out])
            if out.exists():
                frame_paths.append(out)
        if frame_paths:
            inputs: list[str] = []
            for p in frame_paths:
                inputs += ["-i", str(p)]
            chain = []
            for i, p in enumerate(frame_paths):
                chain.append(
                    f"[{i}:v]scale={CELL_W}:{CELL_H}:force_original_aspect_ratio=decrease,"
                    f"pad={CELL_W}:{CELL_H}:(ow-iw)/2:(oh-ih)/2:color=#111111[v{i}]")
            tile = "".join(f"[v{i}]" for i in range(len(frame_paths)))
            positions = "|".join(
                f"{(i % COLS) * (CELL_W + 8)}_{(i // COLS) * (CELL_H + 8)}"
                for i in range(len(frame_paths)))
            chain.append(f"{tile}xstack=inputs={len(frame_paths)}:"
                         f"layout={positions}:fill=#222222[out]")
            grid_w = COLS * CELL_W + (COLS - 1) * 8
            grid_h = ROWS * CELL_H + (ROWS - 1) * 8
            labels = [(p.stem, (i % COLS) * (CELL_W + 8) + 16,
                       (i // COLS) * (CELL_H + 8) + 16)
                      for i, p in enumerate(frame_paths)]
            ass = label_ass(labels, grid_w, grid_h, out_dir / "labels.ass")
            chain.append(f"[out]ass={ass}[final]")   # 覆盖层必须并进同一条 filtergraph
            sheet = out_dir / "sweep-contact-sheet.jpg"
            proc = run(["ffmpeg", "-loglevel", "error", "-y", *inputs,
                        "-filter_complex", ";".join(chain), "-map", "[final]",
                        "-frames:v", "1", sheet])
            print(f"抽帧表：{sheet}" if proc.returncode == 0 else f"抽帧表失败: {proc.stderr[-300:]}")

    # 2) 对比片：15 条并排（xstack），各格标风格名
    if clips and not args.no_grid:
        shortest = min(probe_duration(f) for _, f in clips)
        inputs: list[str] = []
        for _, final in clips:
            inputs += ["-t", f"{shortest:.2f}", "-i", str(final)]
        chain, layout = [], []
        for i, (style, _) in enumerate(clips):
            chain.append(
                f"[{i}:v]scale={CELL_W}:{CELL_H}:force_original_aspect_ratio=decrease,"
                f"pad={CELL_W}:{CELL_H}:(ow-iw)/2:(oh-ih)/2:color=#111111,"
                f"fps={args.fps},setsar=1[v{i}]")
            layout.append(f"{(i % COLS) * CELL_W}_{(i // COLS) * CELL_H}")
        tile = "".join(f"[v{i}]" for i in range(len(clips)))
        chain.append(f"{tile}xstack=inputs={len(clips)}:layout={'|'.join(layout)}:"
                     "fill=#111111[stack]")
        labels = [(style, (i % COLS) * CELL_W + 16, (i // COLS) * CELL_H + 16)
                  for i, (style, _) in enumerate(clips)]
        ass = label_ass(labels, COLS * CELL_W, ROWS * CELL_H, out_dir / "labels-grid.ass")
        chain.append(f"[stack]ass={ass}[out]")
        grid = out_dir / "sweep-grid.mp4"
        proc = run(["ffmpeg", "-loglevel", "error", "-y", *inputs,
                    "-filter_complex", ";".join(chain), "-map", "[out]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", grid])
        print(f"对比片：{grid}" if proc.returncode == 0 else f"对比片失败: {proc.stderr[-300:]}")

    (out_dir / "sweep-report.json").write_text(
        json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok_n = sum(1 for t in table if t["ok"])
    print(f"\n完成 {ok_n}/{len(styles)} 条风格；报告：{out_dir / 'sweep-report.json'}")
    for t in table:
        flag = "✓" if t["ok"] else "✗"
        print(f"  {flag} {t['style']:24s} {t['durationSec']:>5}s  {','.join(t.get('charts', []))}")
    return 0 if ok_n == len(styles) else 1


if __name__ == "__main__":
    raise SystemExit(main())
