#!/usr/bin/env python3
"""Validate the renderer-neutral knowledge-motion scene manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STYLES = {
    "editorial-collage",
    "character-concept-comic",
    "paper-diorama",
    "swiss-sketch",
    "ui-demo",
    "generated-cinematic",
    "data-viz",
    "kinetic-typography",
    "whiteboard-tutorial",
    "timeline-history",
    "process-flow",
    "map-geo",
    "collage-evidence",
    "hand-sketch",
    "paper-fold",
}
RENDERERS = {"hyperframes", "manim", "lottie", "three", "generated-video", "still"}
ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON: {exc}"]

    if data.get("version") != 1:
        fail(errors, "version must be 1")
    project = data.get("project")
    if not isinstance(project, dict):
        return errors + ["project must be an object"]
    for key in ("title", "language", "width", "height", "fps", "durationSec", "captionSafeArea"):
        if key not in project:
            fail(errors, f"project.{key} is required")
    for key in ("width", "height", "fps", "durationSec"):
        if key in project and (not isinstance(project[key], (int, float)) or project[key] <= 0):
            fail(errors, f"project.{key} must be positive")

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return errors + ["scenes must be a non-empty array"]

    ids: set[str] = set()
    previous_end = 0.0
    for index, scene in enumerate(scenes):
        label = f"scenes[{index}]"
        if not isinstance(scene, dict):
            fail(errors, f"{label} must be an object")
            continue
        required = (
            "id", "startSec", "durationSec", "narration", "purpose", "semanticClass",
            "style", "visualSubject", "visualVerb", "layout", "camera", "transitionIn",
            "transitionOut", "assets", "beats", "finalState", "renderer",
        )
        for key in required:
            if key not in scene:
                fail(errors, f"{label}.{key} is required")
        scene_id = scene.get("id")
        if not isinstance(scene_id, str) or not ID_RE.match(scene_id):
            fail(errors, f"{label}.id must match {ID_RE.pattern}")
        elif scene_id in ids:
            fail(errors, f"duplicate scene id: {scene_id}")
        else:
            ids.add(scene_id)
        start = scene.get("startSec")
        duration = scene.get("durationSec")
        if not isinstance(start, (int, float)) or start < 0:
            fail(errors, f"{label}.startSec must be >= 0")
            continue
        if not isinstance(duration, (int, float)) or duration <= 0:
            fail(errors, f"{label}.durationSec must be > 0")
            continue
        if index == 0 and abs(start) > 0.001:
            fail(errors, "first scene must start at 0")
        if start < previous_end - 0.001:
            fail(errors, f"{label} overlaps the previous scene")
        if start - previous_end > 0.15:
            fail(errors, f"{label} leaves a gap of {start - previous_end:.3f}s")
        previous_end = start + duration
        if scene.get("style") not in STYLES:
            fail(errors, f"{label}.style is unsupported: {scene.get('style')!r}")
        if scene.get("renderer") not in RENDERERS:
            fail(errors, f"{label}.renderer is unsupported: {scene.get('renderer')!r}")
        for key in ("visualSubject", "visualVerb", "finalState"):
            if not isinstance(scene.get(key), str) or not scene[key].strip():
                fail(errors, f"{label}.{key} must be non-empty")
        beats = scene.get("beats")
        if not isinstance(beats, list) or not beats:
            fail(errors, f"{label}.beats must be non-empty")
        else:
            for beat_index, beat in enumerate(beats):
                beat_label = f"{label}.beats[{beat_index}]"
                if not isinstance(beat, dict) or not isinstance(beat.get("atSec"), (int, float)):
                    fail(errors, f"{beat_label}.atSec must be numeric")
                    continue
                if beat["atSec"] < 0 or beat["atSec"] > duration:
                    fail(errors, f"{beat_label}.atSec must lie within scene duration")
                if not isinstance(beat.get("action"), str) or not beat["action"].strip():
                    fail(errors, f"{beat_label}.action must be non-empty")

    declared = project.get("durationSec")
    if isinstance(declared, (int, float)) and abs(declared - previous_end) > 0.15:
        fail(errors, f"project.durationSec ({declared}) differs from scene end ({previous_end:.3f})")
    # v2.3 整片风格约束：project.style 设置后，所有 scene.style 必须一致
    proj_style = (data.get("project") or {}).get("style")
    if proj_style:
        for scene in data.get("scenes", []):
            if scene.get("style") != proj_style:
                fail(errors,
                     f"scenes[{scene.get('id')}].style {scene.get('style')!r} conflicts with "
                     f"project.style {proj_style!r} (film-level style routing: one style per film)")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = validate(args.manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"OK: {args.manifest}")


if __name__ == "__main__":
    main()
