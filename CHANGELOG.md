# Changelog

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
