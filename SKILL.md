---
name: knowledge-motion-video
description: >
  Turn any script, article, lesson, product explanation, or industry analysis into a narrated
  knowledge-animation video. Use when the user asks for 文案转动画、知识视频、科普动画、自动分镜、讲解视频、
  explainer video, motion graphics, data-viz video, kinetic typography, whiteboard tutorial,
  or a reusable script-to-video workflow. Segments content into 6–8 second semantic beats, routes
  each beat to the visual grammar that explains it best, builds a timed storyboard, generates or
  sources assets, renders deterministic animation (HyperFrames by default, built-in headless-Chrome
  renderer as fallback), and assembles voiceover, subtitles, music, and credits with FFmpeg.
---

# Knowledge Motion Video

Turn authored ideas into legible motion. The script is source truth, audio is the clock, the
storyboard is the production contract, and the renderer is replaceable infrastructure. This skill
is renderer-neutral by design: every scene contract can be produced by HyperFrames, another
engine, or the bundled headless-Chrome fallback renderer.

## Read first

- `references/pipeline.md` — the full production pipeline and gates. Read before starting a project.
- `references/scene-schema.md` — the `scenes.json` contract. Read before writing a storyboard.
- `references/style-router.md` — route selection across 12 visual grammars. Read before choosing styles.
- `references/motion-language.md` — motion verbs, narration sync, camera. Read before implementing scenes.
- `references/series-furniture.md` — branding layers independent of scene style.
- `references/open-source-stack.md` — engine and license notes.
- Installed `hyperframes*` skills — read before authoring or rendering HyperFrames compositions.

## Operating model

`source → narrative lock → voice timing → semantic beats → style routing → scene manifest →
assets → deterministic animation → audio/subtitles → QC → render`

The core unit is a **6–8 second semantic beat** — not a sentence, not a slide. Merge fragments
sharing one visual idea; split a sentence when its explanation changes subject, relation, or
visual verb.

## Tooling

Run `python3 scripts/doctor.py` first. Then:

| Need | Command |
|---|---|
| Scaffold a project | `python3 scripts/scaffold_project.py <dir> --title "..." --aspect 9:16` |
| Validate a manifest | `python3 scripts/validate_scenes.py <dir>/storyboard/scenes.json` |
| Build captions from transcript | `python3 scripts/build_captions.py --transcript t.json --scenes scenes.json --out-dir captions/` |
| Mix audio + burn captions | `python3 scripts/finalize.py --visual master.mp4 --narration vo.wav --captions subs.ass --out final.mp4` |
| Render via HyperFrames | `npx hyperframes check` then `npx hyperframes render` |
| Render without HyperFrames | `node scripts/render-browser.mjs composition/index.html --fps 30 --output renders/out.mp4` |
| Verify a project | `python3 scripts/verify.py <dir>` |

The bundled `render-browser.mjs` renders HyperFrames-style compositions (data-duration clips +
registered GSAP timelines) through headless Chrome and FFmpeg with zero additional dependencies
beyond puppeteer-core. Use it when the HyperFrames CLI is unavailable, and for CI.

## Intake

Infer what is known; ask only for decisions that cannot be safely inferred: source text, aspect
ratio and platform, target duration, whether wording is locked, voice source (existing audio /
TTS / none), and any brand constraints. Never make the viewer choose among all styles — analyze
the content, recommend a primary and secondary route, and justify in one sentence.

## Production gates

Pause for approval at expensive boundaries:

1. **Narrative lock** — approve spoken script before TTS and timing.
2. **Storyboard lock** — approve scene intent and routing before asset generation.
3. **Pilot** — render 20–30 seconds spanning at least two styles before full production.
4. **Final preview** — render delivery only after the assembled preview is approved.

Explicitly autonomous requests may skip pauses, but the same artifacts are still produced.

## Scene routing

Classify each beat by its explanatory job, then route it (details in `style-router.md`):

- **editorial-collage** — evidence, history, people, documents, news.
- **character-concept-comic** — cognition, emotion, workplace tension, ethics, recurring dilemmas.
- **paper-diorama** — mechanisms, engineering, ecology, physical systems, chronology.
- **swiss-sketch** — arguments, comparisons, methods, business/social commentary.
- **ui-demo** — exact product operation, when screen behavior is the evidence.
- **generated-cinematic** — atmosphere or impossible scenes; sparingly.
- **data-viz** — numbers, trends, rankings, distributions.
- **kinetic-typography** — punchlines, manifestos, pure textual emphasis.
- **whiteboard-tutorial** — teaching derivations, pen-led explanations.
- **timeline-history** — chronology, milestones, evolution.
- **process-flow** — pipelines, architectures, cause-effect chains.
- **map-geo** — geography, spatial distribution, movement.
- **collage-evidence** — material-style collage: real photos/footage pinned as torn-paper evidence cards with captions and license tags. Best when real-world proof drives the argument.
- **hand-sketch** — material-style hand-drawn: SVG strokes draw themselves with a moving pen tip; embeds one photo as evidence. Best for arguments and methods with warmth.
- **paper-fold** — material-style origami/paper-craft: CSS 3D folds stand a flat sheet into a layered diorama with crease lines, thickness, and paper texture.

A film may mix styles; a chapter should normally keep one dominant grammar. Do not imitate a
living creator frame-for-frame — reuse principles, never protected frames, characters, or logos.

## Timing contract

1. Lock narration. 2. Generate or import voice audio. 3. Obtain word/phrase timestamps
(`coli asr -j`, edge-tts WordBoundary, WhisperX, or supplied). 4. Derive beats from semantic
changes and pauses. 5. Land visual payoffs on spoken keywords. 6. Hold the resolved state ≥0.8s
(1–1.5s for dense diagrams). 7. Subtitles go on the topmost layer, applied last in FFmpeg.

Never hard-code final frame numbers before voice timing; estimates are for pilots only.

## Real-asset pipeline (optional but recommended)

For material-style scenes, declare per-scene `assets` in `scenes.json` (see `scene-schema.md`):

```jsonc
"assets": [
  { "id": "photo-1", "type": "photo", "query": "vintage typewriter" },
  { "id": "broll-1", "type": "video", "query": "timelapse city" },
  { "id": "sfx-1", "type": "audio-sfx", "query": "paper", "atSec": 0.6 }
]
```

Then:

1. `python3 scripts/fetch_assets.py --project <dir>` — searches Pexels (set `PEXELS_API_KEY`),
   Pixabay (`PIXABAY_API_KEY`), then keyless Openverse and Wikimedia Commons; downloads to
   `assets/media/`, backfills `local`/`attribution`/`license`, and writes
   `assets/media/manifest.json` (the license record you ship). Resume-safe; bundled SFX pack
   matches `audio-sfx` queries locally.
2. Templates reference `{{assets.<id>}}` placeholders; a missing asset degrades to the
   template's CSS fallback instead of an empty frame.
3. `python3 scripts/mix_audio.py --scenes ... --narration ... --out audio/mix.wav` — mixes the
   narration with per-scene SFX at `startSec + atSec`.

License notes: Pexels/Pixabay content licenses allow modification and redistribution inside a
larger work; Openverse/Wikimedia return CC/PD content — record attribution in the manifest and
show credits. Generated media (FLUX.1-schnell / Qwen-Image, both Apache-2.0) may serve as a
fallback; do not bundle non-commercial model weights.

## Rendering

HyperFrames is the default deterministic renderer. Route a scene elsewhere only on clear advantage:
Manim (math), Lottie/Rive (licensed prebuilt vector), Three.js (true depth/shaders), image/video
generation (illustrative assets). Non-HyperFrames clips are normalized to the project's codec,
resolution, FPS, and pixel format before assembly. FFmpeg owns final assembly, loudness, subtitle
burn-in (always last), and encoding. All render-critical motion must be seek-safe and deterministic.

## Project layout

```text
<project>/
├── BRIEF.md  script/ (narration.md, transcript.json, subtitles)  storyboard/ (scenes.json, storyboard.md)
├── assets/ (manifest.json, images/, video/, audio/)  composition/ (index.html, compositions/)
├── captions/  renders/  qc/  DELIVERY.md
```

## Quality gate

Before delivery: manifest validated; `npx hyperframes check --snapshots` (or fallback-render
snapshots) reviewed — first frame, every scene midpoint, every transition, final frame; no empty
frame, clipped text, hidden subtitle, duplicate ID, missing media, or unintended reset; every
scene has one dominant idea and at least one non-text visual subject; audio below clipping with
intelligible speech; duration/resolution/FPS/codec verified with ffprobe; sources and licenses in
`assets/manifest.json` and `DELIVERY.md`.

## Failure handling

- Generated assets fail → code-drawn diagrams or licensed stills with camera treatment.
- HyperFrames CLI unavailable → `scripts/render-browser.mjs`.
- Advanced renderer fails → SVG/DOM motion under the same scene contract.
- Word timestamps unavailable → phrase-level alignment from measured audio, marked approximate.
- Unclear license → omit the asset. Discoverability is not permission.
- Style route drifts → preserve layout and motion grammar; simplify imagery before changing the chapter.
