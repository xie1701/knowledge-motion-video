# Changelog

## v2.3 — 2026-09-20

- **Film-level style routing**: style is a whole-film decision recorded as `project.style`
  (validator enforces one style per film); film-level decision table added to `style-router.md`;
  per-scene mixing demoted to intentional long-form chapters. Fixes the v2.2 mistake of mixing
  three grammars inside one 37.5s film.
- **Narration-clock hard constraint**: new `scripts/derive_timing.py` derives scene boundaries
  (pause midpoints) and keyword beats (exact ASR token times) from word-level transcripts —
  hand-authored beats were measured up to 2.06s off the voice in v2.2.
- **BGM**: keyless CC0/CC-BY music sourcing via the Openverse audio API; BGM mixed at 0.18
  under narration with fade-in/out (finalize.py `--bgm`).
- **Asset matching**: rich `description` field as the primary handle for the render-front asset
  gate; `fetch_assets.py --sheet` renders a contact sheet for agent/human visual review.
- **SFX restraint**: default no SFX; when used, effects sit at -12dB with 30ms/120ms fades
  (v2.2's full-volume noise bursts read as jarring).
- **Showcase rebuilt**: `examples/showcase-project/` — 32.3s single-grammar (hand-sketch)
  film with narration, burned captions, CC0 piano BGM, and one semantically matched real photo;
  every visual payoff lands on its spoken keyword within ±0.3s. Replaces the v2.2
  mixed-style showcase.
- `build_captions.py`: strip leading punctuation and drop punctuation-only cues.

## v2.2 — 2026-09-20

- **Real-asset pipeline**: `scripts/fetch_assets.py` — per-scene semantic asset search and
  download (Pexels / Pixabay via optional keys, keyless Openverse + Wikimedia Commons, local
  library, bundled SFX), auto-backfills `local`/`attribution`/`license` into `scenes.json` and
  writes a shippable license manifest; resume-safe.
- **Audio**: `scripts/mix_audio.py` (narration + per-scene SFX at `startSec + atSec`) and
  `scripts/make_sfx.py` (synthesized bundled SFX pack: paper, page, pen, click, whoosh).
- **Material-style routes**: three new routes (15 total) — `collage-evidence` (torn-paper
  evidence wall), `hand-sketch` (self-drawing SVG strokes + pen tip along path),
  `paper-fold` (CSS 3D origami pop-up with crease lines, thickness, texture). Upgraded
  `editorial-collage` and `paper-diorama` with torn edges, thickness, texture, and asset slots.
- **Showcase case**: `examples/showcase-project/` — 37.5s fully narrated, caption-burned,
  real-footage case (5 scenes, 5 photos + 1 real timelapse video + 6 SFX, all licensed and
  recorded), covering the three material-style routes.
- Schema/docs: optional per-scene `assets[]` contract (scene-schema.md), style-router table
  updated, showcase docs and CI coverage.

## v2.1 — 2026-09-19

- Style gallery: four 10-second sample renders (clean-education × whiteboard-tutorial,
  dark-technical × data-viz, warm-editorial × editorial-collage, bold-social × kinetic-typography)
  under `examples/style-samples/`, plus a side-by-side comparison GIF.
- Added GitHub Actions CI (compile, doctor, storyboard validation, sample caption build).
- Fixed `doctor.py` coli probe (uses `--help`; older builds rejected `--version`).
- Fixed caption word-joining for ASR tokens (`build_captions.py`) and short-cue merging.
- Fixed in-scene caption vs. burned subtitle collision in the sample project (caption-safe
  area rule now enforced in the furniture spec).

## v2 — 2026-09-19

- Generalized beyond the reference video's four styles: 12-route style router
  (data-viz, kinetic-typography, whiteboard-tutorial, timeline-history, process-flow,
  map-geo added).
- Added bundled fallback renderer `scripts/render-browser.mjs` (headless Chrome + FFmpeg,
  no HyperFrames CLI dependency).
- Added pipeline scripts: `doctor.py`, `build_captions.py`, `finalize.py`, `verify.py`,
  optional `tts_edge.py` adapter.
- Added series furniture layer (branding independent of scene style).
- Added design token presets and per-route scene templates.
- Open-source engineering: MIT license, README, CONTRIBUTING, install script, gitignore.
- Example project: Swiss-sketch portrait composition with motion assertions.

## v1 — 2026-09-19

- Initial MVP: SKILL.md, scene schema + validator, 6-route router, HyperFrames demo
  composition, open-source research report, video analysis report.
