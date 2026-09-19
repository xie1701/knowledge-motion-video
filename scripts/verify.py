#!/usr/bin/env python3
"""Verify a knowledge-motion project: manifest, master video, contact sheet.

Usage: python3 scripts/verify.py <project-dir>

Checks performed:

1. ``storyboard/scenes.json`` is re-validated via ``validate_scenes.validate``.
2. The visual master (``renders/visual-master.mp4`` by default, override with
   ``--visual``) is probed with ffprobe: must be a valid video whose duration
   matches ``project.durationSec`` (tolerance 0.5s) and whose dimensions match
   ``project.width``/``project.height``.
3. One frame is grabbed at the midpoint of every scene; all frames are tiled
   into ``verify/contact-sheet.jpg`` via ffmpeg's tile filter.

A ``verify/report.json`` is written with per-check PASS/FAIL entries. Exit
code is 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_scenes import validate  # noqa: E402

DURATION_TOLERANCE = 0.5


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
