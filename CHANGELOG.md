# Changelog

## v2.4.3 — 2026-09-20

- **Zero-based bar scale**: bar heights were `18% + 70%·v/vmax` — a non-zero baseline, so 12 and
  130 rendered as roughly 1:5 instead of 1:11. Bars now use a pure linear scale from the axis
  (`h = 82%·v/vmax`, 2.5% floor). Measured on the rendered frame: 79 / 302 / 878 px for 12 / 45 /
  130 → ratios 0.090 / 0.344 / 1.000 against the theoretical 0.092 / 0.346 / 1.000.
- **Chart slot geometry**: bars were laid out as `left = 4% + j·(84/n)%`, which only fills 72% of
  the plot at n=2 (the chart looked left-shifted and the second category label drifted away from
  its bar). Bar centres are now distributed evenly across `[4 + w/2, 96 − w/2]` with `w = 60/n`.
- **Labels below the axis**: category labels sat at `bottom: 16%` *inside* the plot, so any bar
  taller than 16% painted over its own label — a white label on a white bar is invisible (the
  middle scene lost 「不可复现」). Labels now sit under the baseline (`top: calc(100% + 16px)`),
  which is also the standard chart grammar.

## v2.4.2 — 2026-09-20

- **data-viz honesty fix — no cross-unit axes**: 3倍 (a multiplier) and 三成 (a share) used to
  share one bar axis, so 3 rendered shorter than 30 — visually false. Charts now carry a `mode`:
  `bars` when every value shares a unit family, `cards` (metric callouts: value + label, no axis)
  when units differ, `fallback` when the copy carries no unit-bearing numbers. Chart category
  labels switched from muted gray to foreground at 0.78 opacity (dark palettes were unreadable).
- **Keyword extraction rebuilt on real word segmentation**: the old 2–4 char sliding window
  was boundary-blind — it happily returned fragments like「正能复现」or「果不到」. `make_video.py`
  now segments Chinese by **maximum-probability path** (Σ log word-frequency + length bonus −
  single-char penalty) using a bundled lexicon, then picks keywords among *content words*,
  preferring compounds of adjacent words (人工|智能 → 人工智能, 论文|数量 → 论文数量,
  小|模型 → 小模型). No shared-bigram duplicates (风格推荐 vs 推荐风格), no generic filler
  (变成/结果/开始), and chart category labels anchor to the nearest real content word
  (3倍 → 增长, 三成 → 复现). Segments like 在/手机/上, 人工/智能, 复现 now come out right.
  Compounds never span clause boundaries (交付|业主 across a comma used to swallow the whole
  scene's keywords, since per-clause keyword mapping found no match).
- **Lexicon**: `assets/lexicon/zh-words.txt` — 83k words derived from jieba `dict.txt`
  (MIT License, Copyright (c) 2013 Sun Junyi), trimmed to multi-char freq ≥ 15 / single-char
  freq ≥ 400, plus a project-authored domain supplement (AI / content creation / home-renovation
  vocabulary: 大模型, 分镜, 边界感, 增项…). Attribution is in the file header.

## v2.4.1 — 2026-09-20

- **data-viz charts carry real numbers (auto pipeline)**: the one-shot orchestrator used to
  blank every chart slot — no title, no values, hard-coded placeholder bar heights identical
  across scenes. New `{{BARS}}` contract: unit-bearing tokens are extracted from the copy
  (3倍 / 三成 / 千亿 / 2021年; bare unitless digits are deliberately not fabricated into bars),
  bar heights scale from the real magnitudes, the key bar takes the accent color, and each
  scene's chart lands in `storyboard/charts.json` (fallback scenes are honestly marked).
  `--data <json>` accepts a per-scene `{title, unit, labels, values, key}` array for exact
  control. Template colors now come from the wrapper palette (`--bg/--fg/--accent`) instead
  of non-existent `--km-*` vars that silently fell back to light-theme inks on dark films.
  Chart titles clip at clause boundaries, never mid-word.
- **Caption breaks**: unbreakable bigram and dangling-tail sets extended (结果/复现/手机/千亿…;
  从/在 bind forward), verb-initial heads favored — no more 结|果 or 手|机 splits; showcase
  captions byte-identical after the change (regression-checked).

## v2.4 — 2026-09-20

- **One-shot pipeline** (`scripts/make_video.py`): copy in → style recommendation with a full
  auditable decision trace → non-interactive confirmation gate (`--go`/`--style` passes) →
  auto storyboard (punctuation clause grouping 6–8s, keyword extraction, word-level ASR
  timing via derive_timing) → per-scene template assembly (id namespacing, timeline position
  remapping, slot filling, SVG placeholder for missing photo slots) → lint → render →
  finalize → verify. 15/15 styles assemble with zero lint errors. Auto mode is documented as
  the floor; agent-authored scenes remain the ceiling.

## v2.3.1 — 2026-09-20

- **Narration voice & prosody**: showcase re-voiced with a narration-grade male TTS
  (解说小明); the copy itself gained punctuation so pauses land on semantic boundaries —
  prosody, not a speed parameter, is what fixes "unnatural pacing". Film is now 46.43s.
- **Caption layout engine**: `build_captions.py` rewritten — hard ≤9 glyphs/line limit
  (fontsize 97 in a 936px text area), cues longer than two lines re-chunked recursively,
  scene assignment by word start (a word straddling a boundary no longer splits mid-word,
  e.g. 跑|完), and a readability score for break points: unbreakable bigrams (怎么/变成/一支…),
  no trailing 的/每/这 at line end, no leading 的 at line start, verb-initial breaks favored.
  No more flash cues like「频，」; no more edge-clipped lines.
- **Style recommender**: new `scripts/recommend_style.py` — any copy in, auditable decision
  trace out: text stats → 12 semantic axes with quoted evidence → film decision-table hit
  (incl. two-axis blend rules) → per-style scores with anti-evidence → primary + runner-up.
  Docs: `docs/style-recommendation.md`.
- **Fix (SVG filter region)**: a lone horizontal stroke in its own filtered `<g>` has a
  zero-height objectBoundingBox, so the default filter region clips the output to nothing —
  the s05 progress underline vanished from renders while being provably correct in the DOM.
  Fixed with `filterUnits="userSpaceOnUse"` full-canvas regions.

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
