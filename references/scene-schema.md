# Scene manifest schema

`storyboard/scenes.json` is a JSON object:

```json
{
  "version": 1,
  "project": {
    "title": "Why tools do not equal a workflow",
    "language": "zh-CN",
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "durationSec": 28.4,
    "captionSafeArea": {"x": 72, "y": 1570, "width": 936, "height": 230}
  },
  "design": {
    "background": "#11110F",
    "foreground": "#F5F1E8",
    "accent": "#F36B3D",
    "muted": "#8C887F",
    "displayFont": "Noto Sans SC",
    "bodyFont": "Noto Sans SC"
  },
  "scenes": []
}
```

Each scene requires:

```json
{
  "id": "s01",
  "startSec": 0,
  "durationSec": 6.4,
  "narration": "文案写完，只是起点。",
  "keywords": [{"text": "起点", "atSec": 2.1}],
  "purpose": "hook",
  "semanticClass": "argument",
  "style": "swiss-sketch",
  "visualSubject": "A document unfolds into a broken production chain",
  "visualVerb": "unfold-and-fracture",
  "layout": "split-left-copy-right-diagram",
  "camera": "slow-push-then-lock",
  "transitionIn": "hard-cut",
  "transitionOut": "match-cut-document",
  "assets": [],
  "beats": [
    {"atSec": 0.2, "action": "document draws in"},
    {"atSec": 2.1, "action": "chain fractures on spoken keyword"},
    {"atSec": 4.8, "action": "pieces settle and hold"}
  ],
  "finalState": "Broken chain remains readable for 1.2 seconds",
  "renderer": "hyperframes"
}
```

## Validation invariants

- IDs are unique and match `^[a-z][a-z0-9-]*$`.
- Scenes begin at or after zero, have positive duration, and do not overlap.
- The first scene starts at zero; gaps over 0.15 seconds are rejected.
- `style` is one of the fifteen routes in `style-router.md`: editorial-collage, character-concept-comic, paper-diorama, swiss-sketch, ui-demo, generated-cinematic, data-viz, kinetic-typography, whiteboard-tutorial, timeline-history, process-flow, map-geo, collage-evidence, hand-sketch, paper-fold.
- `renderer` is `hyperframes`, `manim`, `lottie`, `three`, `generated-video`, or `still`.
- Every scene names one visual subject, one visual verb, at least one beat, and a final state.
- Every beat lies inside the scene; `beats[].atSec` and `keywords[].atSec` are scene-relative (seconds from the scene's own start), while scene `startSec` values tile the film timeline.
- Text-only scenes are allowed only for chapter cards or intentional kinetic typography.
- Every external asset ID resolves in `assets/media/manifest.json` (written by `scripts/fetch_assets.py`).

## assets[] (optional, per scene)

Declares real-world media for material-style scenes. `fetch_assets.py` fills `local`,
`attribution`, and `license` automatically; templates read `{{assets.<id>}}`.

```jsonc
"assets": [
  { "id": "photo-1", "type": "photo", "query": "vintage typewriter" },
  { "id": "broll-1", "type": "video", "query": "timelapse city" },
  { "id": "sfx-1", "type": "audio-sfx", "query": "paper", "atSec": 0.6 }
]
```

- `type`: `photo` | `video` | `audio-sfx`.
- `query`: search phrase for the asset sources; for `audio-sfx` it fuzzy-matches the bundled
  SFX pack filenames.
- `atSec`: scene-relative second for SFX placement (used by `scripts/mix_audio.py`).
- Sources are tried in order: Pexels (`PEXELS_API_KEY`) → Pixabay (`PIXABAY_API_KEY`) →
  Openverse → Wikimedia Commons (both keyless) → local library (`--local-dir`) → bundled SFX.
- Missing assets never break rendering: templates fall back to CSS materials, and `mix_audio.py`
  skips unmatched SFX with a warning.

The manifest describes intent, not renderer-specific implementation. This keeps style routing and timing stable when a scene changes engines.
