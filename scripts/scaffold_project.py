#!/usr/bin/env python3
"""Create a portable knowledge-motion project skeleton."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ASPECTS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--title", required=True)
    parser.add_argument("--aspect", choices=ASPECTS, default="9:16")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--fps", type=int, choices=(24, 30, 60), default=30)
    args = parser.parse_args()

    root = Path(args.project_dir).expanduser().resolve()
    width, height = ASPECTS[args.aspect]
    for rel in (
        "script",
        "storyboard",
        "assets/images",
        "assets/video",
        "assets/audio",
        "composition/compositions",
        "renders",
        "qc",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)

    brief = f"""# Brief\n\n- Title: {args.title}\n- Language: {args.language}\n- Aspect: {args.aspect}\n- Resolution: {width}x{height}\n- FPS: {args.fps}\n- Audience: TBD\n- Core message: TBD\n- Duration: TBD\n- Script mode: TBD\n- Voice source: TBD\n- Brand constraints: TBD\n- License constraints: TBD\n"""
    (root / "BRIEF.md").write_text(brief, encoding="utf-8")
    (root / "script/narration.md").write_text("# Narration\n\n", encoding="utf-8")
    (root / "storyboard/storyboard.md").write_text("# Storyboard\n\n", encoding="utf-8")

    scenes = {
        "version": 1,
        "project": {
            "title": args.title,
            "language": args.language,
            "width": width,
            "height": height,
            "fps": args.fps,
            "durationSec": 6.0,
            "captionSafeArea": {
                "x": round(width * 0.067),
                "y": round(height * 0.82),
                "width": round(width * 0.866),
                "height": round(height * 0.12),
            },
        },
        "design": {
            "background": "#11110F",
            "foreground": "#F5F1E8",
            "accent": "#F36B3D",
            "muted": "#8C887F",
            "displayFont": "Noto Sans SC",
            "bodyFont": "Noto Sans SC",
        },
        "scenes": [
            {
                "id": "s01",
                "startSec": 0,
                "durationSec": 6,
                "narration": "Replace this narration.",
                "keywords": [],
                "purpose": "hook",
                "semanticClass": "argument",
                "style": "swiss-sketch",
                "visualSubject": "A document becomes a visual system",
                "visualVerb": "unfold-and-connect",
                "layout": "split-left-copy-right-diagram",
                "camera": "slow-push-then-lock",
                "transitionIn": "hard-cut",
                "transitionOut": "hard-cut",
                "assets": [],
                "beats": [
                    {"atSec": 0.2, "action": "document draws in"},
                    {"atSec": 2.0, "action": "nodes connect"},
                    {"atSec": 4.8, "action": "system settles"},
                ],
                "finalState": "Resolved system holds for 1.2 seconds",
                "renderer": "hyperframes",
            }
        ],
    }
    (root / "storyboard/scenes.json").write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "assets/manifest.json").write_text(
        json.dumps({"version": 1, "assets": []}, indent=2) + "\n", encoding="utf-8"
    )
    (root / "DELIVERY.md").write_text("# Delivery\n\n", encoding="utf-8")
    print(root)


if __name__ == "__main__":
    main()
