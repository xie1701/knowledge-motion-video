#!/usr/bin/env python3
"""Verify a knowledge-motion project: manifest, master video, contact sheet, motion.

Usage: python3 scripts/verify.py <project-dir>

Checks performed:

1. ``storyboard/scenes.json`` is re-validated via ``validate_scenes.validate``.
2. The visual master (``renders/visual-master.mp4`` by default, override with
   ``--visual``) is probed with ffprobe: must be a valid video whose duration
   matches ``project.durationSec`` (tolerance 0.5s) and whose dimensions match
   ``project.width``/``project.height``.
3. One frame is grabbed at the midpoint of every scene; all frames are tiled
   into ``verify/contact-sheet.jpg`` via ffmpeg's tile filter.
4. Motion: the master is sampled at 8 fps and compared against itself one second earlier
   (ffmpeg ``blend=difference`` + ``signalstats``), because that is the scale at which a slow
   drift stops reading as "frozen" while a genuine hold still measures zero. Every scene must
   keep changing: no run longer than ``MAX_FROZEN_SEC`` where the frame does not change at all,
   and the whole-film mean must clear ``MIN_MEAN_DIFF``. This is how "the picture is stiff"
   becomes a failing test instead of a matter of taste.

A ``verify/report.json`` is written with per-check PASS/FAIL entries. Exit
code is 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_scenes import validate  # noqa: E402

DURATION_TOLERANCE = 0.5
SAMPLE_FPS = 8            # 运动采样率
MOTION_LAG_SEC = 1.0      # 比较「一秒前的同一位置」——比 125ms 尺度接近「看着没动」的直觉
FROZEN_DIFF = 0.4         # 一秒前后帧间平均差低于此值 = 这一秒画面没变
MAX_FROZEN_SEC = 1.2      # 单段「没变」的上限（默认 1.2s）
MIN_MEAN_DIFF = 0.4       # 全集一秒尺度平均运动的下限


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, (proc.stderr or proc.stdout or "").strip()


def ffprobe_json(path: Path) -> dict:
    code, out = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ])
    if code != 0:
        raise RuntimeError(f"ffprobe failed: {out}")
    return json.loads(out)


def motion_profile(visual: Path) -> tuple[list[float], int]:
    """逐采样点的「跟 MOTION_LAG_SEC 秒前比，画面变了多少」（平均亮度差）。

    为什么是「一秒前」而不是「上一帧」：低幅持续运动（比如 3% 的镜头推近）在 125ms 尺度上
    每帧只挪不到一个像素，逐帧比会判成「没动」，但它在一秒里是看得见的。反过来，真正的
    停住（画面逐像素不动）在哪个尺度上都是 0。所以这条门禁问的是「这一秒画面变了没有」。
    """
    lag = max(1, int(round(MOTION_LAG_SEC * SAMPLE_FPS)))
    graph = (f"[0:v]fps={SAMPLE_FPS},scale=270:480,split=2[a][b];"
             f"[b]trim=start_frame={lag},setpts=PTS-STARTPTS[bb];"
             f"[a]setpts=PTS-STARTPTS[aa];[aa][bb]blend=all_mode=difference,"
             "signalstats,metadata=print:key=lavfi.signalstats.YAVG")
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "info", "-i", str(visual),
         "-filter_complex", graph, "-f", "null", "-"],
        capture_output=True, text=True)
    vals = [float(x) for x in re.findall(r"YAVG=([0-9.]+)", proc.stderr or "")]
    # vals[k] 对应「第 k+lag 个采样点 vs 第 k 个采样点」，即影片时间 (k+lag)/FPS 处的变化量。
    # 把 lag 一起返回，调用方才能把采样下标对齐回场景窗口（不要在前面补零——补零会把
    # 后面所有窗口整体错开 1 秒，看起来就像每场开场都「没变」）。
    return vals, lag


def frozen_runs(diffs: list[float]) -> list[tuple[float, float]]:
    """返回 [(开始秒, 时长秒)]：所有低于 FROZEN_DIFF 的连续段（至少一秒长才算）。"""
    runs: list[tuple[float, float]] = []
    start: int | None = None
    for i, v in enumerate(diffs):
        if v < FROZEN_DIFF:
            start = i if start is None else start
        elif start is not None:
            runs.append((start / SAMPLE_FPS, (i - start) / SAMPLE_FPS))
            start = None
    if start is not None:
        runs.append((start / SAMPLE_FPS, (len(diffs) - start) / SAMPLE_FPS))
    return runs


def motion_check(visual: Path, scenes: list[dict]) -> dict:
    """把「呆板」量一量：每场最长冻帧 + 全集平均运动。"""
    diffs, lag = motion_profile(visual)
    if len(diffs) < 2:
        return {"name": "motion", "status": "FAIL", "detail": "no samples"}
    mean = sum(diffs) / len(diffs)
    per_scene: list[dict] = []
    worst = ("", 0.0)
    for scene in scenes:
        start = float(scene["startSec"])
        end = start + float(scene["durationSec"])
        lo = max(0, int(round(start * SAMPLE_FPS)) - lag)
        hi = max(lo + 1, int(round(end * SAMPLE_FPS)) - lag)
        window = diffs[lo:hi]
        if not window:
            continue
        runs = [(s + lo / SAMPLE_FPS, d) for s, d in frozen_runs(window)]
        longest = max((d for _, d in runs), default=0.0)
        per_scene.append({"scene": scene["id"], "longestFrozenSec": round(longest, 2),
                          "meanDiff": round(sum(window) / len(window), 2)})
        if longest > worst[1]:
            worst = (scene["id"], longest)
    problems: list[str] = []
    if mean < MIN_MEAN_DIFF:
        problems.append(f"mean diff {mean:.2f} < {MIN_MEAN_DIFF}（一秒尺度上全片太平）")
    if worst[1] > MAX_FROZEN_SEC:
        problems.append(f"{worst[0]} 连续 {worst[1]:.2f}s 画面没变 > {MAX_FROZEN_SEC}s")
    return {
        "name": "motion",
        "status": "PASS" if not problems else "FAIL",
        "detail": problems or {
            "meanDiff": round(mean, 2),
            "longestFrozenSec": round(worst[1], 2),
            "worstScene": worst[0],
            "thresholds": {"sampleFps": SAMPLE_FPS, "lagSec": MOTION_LAG_SEC,
                           "frozenDiff": FROZEN_DIFF, "maxFrozenSec": MAX_FROZEN_SEC,
                           "minMeanDiff": MIN_MEAN_DIFF},
            "scenes": per_scene,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project", type=Path, help="knowledge-motion project directory")
    parser.add_argument("--visual", type=Path, help="master video (default renders/visual-master.mp4)")
    args = parser.parse_args()

    project_dir = args.project
    manifest_path = project_dir / "storyboard" / "scenes.json"
    out_dir = project_dir / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, object]] = []
    manifest: dict = {}

    # --- 1. manifest validation ---
    if not manifest_path.exists():
        checks.append({"name": "manifest", "status": "FAIL", "detail": f"missing {manifest_path}"})
    else:
        errors = validate(manifest_path)
        checks.append({
            "name": "manifest",
            "status": "PASS" if not errors else "FAIL",
            "detail": errors or f"{manifest_path} is valid",
        })
        if not errors:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    project = manifest.get("project", {})
    scenes = manifest.get("scenes", [])

    # --- 2. video probe ---
    visual = args.visual or project_dir / "renders" / "visual-master.mp4"
    video_check: dict[str, object]
    streams: dict = {}
    if not visual.exists():
        video_check = {"name": "video", "status": "FAIL", "detail": f"missing {visual}"}
    else:
        try:
            probe = ffprobe_json(visual)
            vstream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
            streams = probe
            if vstream is None:
                video_check = {"name": "video", "status": "FAIL", "detail": "no video stream"}
            else:
                problems = []
                duration = float(probe.get("format", {}).get("duration") or 0.0)
                declared = float(project.get("durationSec") or 0.0)
                if declared and abs(duration - declared) > DURATION_TOLERANCE:
                    problems.append(
                        f"duration {duration:.2f}s differs from project.durationSec {declared}s "
                        f"(tolerance {DURATION_TOLERANCE}s)"
                    )
                width, height = int(vstream.get("width", 0)), int(vstream.get("height", 0))
                if project.get("width") and width != int(project["width"]):
                    problems.append(f"width {width} != project.width {project['width']}")
                if project.get("height") and height != int(project["height"]):
                    problems.append(f"height {height} != project.height {project['height']}")
                video_check = {
                    "name": "video",
                    "status": "PASS" if not problems else "FAIL",
                    "detail": problems or {
                        "durationSec": round(duration, 3),
                        "width": width,
                        "height": height,
                        "codec": vstream.get("codec_name"),
                    },
                }
        except RuntimeError as exc:
            video_check = {"name": "video", "status": "FAIL", "detail": str(exc)}
    checks.append(video_check)

    # --- 3. contact sheet: one frame per scene midpoint ---
    sheet_check: dict[str, object]
    sheet_path = out_dir / "contact-sheet.jpg"
    if not scenes or not visual.exists():
        sheet_check = {
            "name": "contact-sheet",
            "status": "FAIL",
            "detail": "skipped: no scenes or no master video",
        }
    else:
        midpoints = [
            (scene["id"], float(scene["startSec"]) + float(scene["durationSec"]) / 2.0)
            for scene in scenes
        ]
        width = int(project.get("width", 1080)) // 2  # tile-friendly preview width
        width = max(width, 360)
        frame_files: list[Path] = []
        failed_frames: list[str] = []
        for index, (scene_id, mid) in enumerate(midpoints):
            frame = out_dir / f".frame-{index:02d}-{scene_id}.jpg"
            code, detail = run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", f"{mid:.3f}", "-i", str(visual),
                "-frames:v", "1", "-vf", f"scale={width}:-1", str(frame),
            ])
            if code != 0 or not frame.exists():
                failed_frames.append(f"{scene_id}@{mid:.2f}s: {detail}")
            else:
                frame_files.append(frame)
        if failed_frames:
            sheet_check = {"name": "contact-sheet", "status": "FAIL", "detail": failed_frames}
        elif not frame_files:
            sheet_check = {"name": "contact-sheet", "status": "FAIL", "detail": "no frames extracted"}
        else:
            # Pad with a black frame so the frame count is tileable by 3 columns.
            cols = 3
            rows = -(-len(frame_files) // cols)  # ceil division
            height = int(project.get("height", 1920)) // 2
            height = max(height, 360)
            if len(frame_files) < rows * cols:
                pad = out_dir / ".frame-pad.jpg"
                run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                     "-f", "lavfi", "-i", f"color=black:s={width}x{height}",
                     "-frames:v", "1", str(pad)])
                frame_files += [pad] * (rows * cols - len(frame_files))
            inputs: list[str] = []
            for frame in frame_files:
                inputs += ["-i", str(frame)]
            code, detail = run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                *inputs,
                "-filter_complex",
                f"concat=n={len(frame_files)}:v=1:a=0,tile={cols}x{rows},scale=iw/2:-1",
                "-frames:v", "1", "-q:v", "3", str(sheet_path),
            ])
            for frame in frame_files:
                if frame.name.startswith(".frame-"):
                    frame.unlink(missing_ok=True)
            if code != 0:
                sheet_check = {"name": "contact-sheet", "status": "FAIL", "detail": detail}
            else:
                sheet_check = {
                    "name": "contact-sheet",
                    "status": "PASS",
                    "detail": {"frames": [f"{scene_id}@{mid:.2f}s" for scene_id, mid in midpoints],
                               "path": str(sheet_path)},
                }
    checks.append(sheet_check)

    # --- 4. motion: 每一场都得在动 ---
    if scenes and visual.exists():
        checks.append(motion_check(visual, scenes))
    else:
        checks.append({"name": "motion", "status": "FAIL",
                       "detail": "skipped: no scenes or no master video"})

    all_pass = all(c["status"] == "PASS" for c in checks)
    report = {
        "project": str(project_dir),
        "verdict": "PASS" if all_pass else "FAIL",
        "checks": checks,
    }
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for check in checks:
        print(f"[{check['status']}] {check['name']}: {check['detail']}")
    print(f"verdict: {report['verdict']}  (report: {report_path})")
    raise SystemExit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
