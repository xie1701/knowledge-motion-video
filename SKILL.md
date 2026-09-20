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

## One-shot pipeline (`make_video.py`, v2.6)

For a straight copy-to-film run, the orchestrator chains recommendation → confirmation gate →
auto storyboard → template assembly → render → finalize → verify:

```bash
# 1. recommend (prints the full auditable trace, then STOPS at the gate)
python3 scripts/make_video.py --copy copy.txt --project outdir
# 2. confirm (human or agent) and finish
python3 scripts/make_video.py --copy copy.txt --project outdir --go \
    [--style <name>] [--narration audio.mp3] [--corrections "一只=一支"] [--bgm music.mp3] \
    [--data charts.json] [--assets plan.json] [--local-dir DIR] [--no-fetch]
```

- The gate is non-interactive by design: default behavior is STOP after printing the decision
  trace and writing `storyboard/style-decision.json`; `--go` (or an explicit `--style`) proceeds.
- **Scenes follow the copy's own sentences (v2.5)**: one sentence = one scene; a sentence longer
  than 8.2s is split at its internal punctuation into 5–7.5s chunks; a trailing scene under 2.2s
  merges back. Time-only greedy grouping used to saw sentences in half ("涨到二十五万八千篇投稿量
  还在涨" — the tail of one topic glued to the head of the next).
- **Transcripts are corrected against the copy (v2.5)**: `scripts/align_transcript.py` aligns the
  ASR characters to the authoritative copy text with difflib and keeps the ASR timestamps
  (`script/transcript.raw.json` keeps the raw pass). ASR ITN and mishearings (过去十年→过去1年,
  arXiv→Aive) otherwise poison both captions and keyword segmentation. Similarity below 0.55
  aborts the alignment rather than forcing it.
- Keywords: maximum-probability segmentation over a bundled lexicon
  (`assets/lexicon/zh-words.txt`, jieba-derived, MIT) — content words plus adjacent-word
  compounds, across a single 「的/之」 (论文的数量 → 论文数量) and with single-char suffixes
  (投稿|量, 复现|率); numeral runs (十年/十六/三分) are banned outright, and candidates that sit
  right in front of a number get a bonus (that word is the chart's category label).
- **Animation is anchored to the spoken word (v2.5)**: every template declares
  `// @beats enter=… build=… reveal=… peak=… settle=…` in its trailing comment, and
  `make_video.py` solves those five choreography moments onto scene time — `build` starts 0.7s
  before the first content word, `reveal`/`peak` land on the spoken keywords, `settle` winds down
  (see `storyboard/beats.json`). Previously the whole choreography was stretched linearly across
  the scene, so a 3.5s move played in slow motion over 10s. Templates without `@beats` still
  work: anchors are inferred from the position-parameter distribution.
- Composition assembly instantiates the style template per scene (ids namespaced, furniture on
  `data-track-index="3"` — track 0 does not render, and scenes' opaque clips would cover anything
  below them). data-viz picks one of five honest layouts per scene from `--data` or from
  unit-bearing tokens in the copy: `trend` (year series), `bars` (one unit), `cards` (mixed
  units), `bignum` (a single number), `statement` (no numbers — big type, never fake bars).
  Bar heights are zero-based linear; category labels sit below the baseline; the axis max is
  labelled; every chart carries a `数据来源` line. Auto mode is the floor, not the ceiling.
- **Material styles fetch their own photos (v2.6)**: when the chosen style is collage-evidence,
  editorial-collage or generated-cinematic, the run inserts an asset step between the storyboard
  and the composition: queries are synthesized from the scene's concepts, photos are downloaded
  and mapped onto the template's slots, and `storyboard/assets-plan.json` +
  `assets/media/manifest.json` record what was used (see the asset section below). `--no-fetch`
  keeps the template fallback instead.
- Narration: pass `--narration` (agent-generated TTS) or let edge_tts synthesize if installed;
  without either the tool exits 3 with guidance.

## Style sweep (`style_sweep.py`, v2.6)

To see what each of the 15 styles actually looks like on the same copy (not the template HTML —
the rendered film), sweep one short excerpt across every style:

```bash
python3 scripts/style_sweep.py --copy excerpt.txt --narration excerpt.m4a \
    --transcript excerpt.json --out-dir q/ [--data one-chart.json] [--styles a,b]
```

It renders each style into `q/<style>/`, writes `sweep-contact-sheet.jpg` (5×3 frames at 65% of
each clip, labelled), `sweep-grid.mp4` (the 15 clips side by side) and `sweep-report.json`
(duration, chart modes, failures). Material styles fetch their own photos here too, so the sweep
doubles as the end-to-end net for the asset path (`--assets` / `--local-dir` / `--no-fetch` pass
through). Use it to sanity-check a style choice or to show someone the difference — and as a
regression net: it exercises every template's assembly path end to end.

## Production gates

Pause for approval at expensive boundaries:

1. **Narrative lock** — approve spoken script before TTS and timing.
2. **Storyboard lock** — approve scene intent and routing before asset generation.
3. **Pilot** — render 20–30 seconds spanning at least two styles before full production.
4. **Final preview** — render delivery only after the assembled preview is approved.

Explicitly autonomous requests may skip pauses, but the same artifacts are still produced.

## Style routing: film-level first (v2.3)

Style is a **whole-film decision**, not a per-scene mix. Analyze the entire copy's semantics —
subject matter, persuasive structure, and real-asset availability — then commit the whole film
to one visual grammar (reference video's four styles are complete film grammars, not scene
filters). Record the choice as `project.style`; the validator then enforces that every scene
uses it. Per-scene routing remains available only for intentionally mixed long-form chapters.

Film-level decision table:

Run the analysis with `python3 scripts/recommend_style.py --file copy.txt` — it prints the full
auditable decision trace (text stats → semantic signals with quoted evidence → decision-table hit
→ per-style scores → primary + runner-up). Details: `docs/style-recommendation.md`.

- methods, tutorials, arguments, processes → **hand-sketch** or swiss-sketch (the pen leads attention; the process itself persuades)
- history, events, people, real archives available → **collage-evidence** or editorial-collage
- systems, engineering, nature, structures → **paper-fold** or paper-diorama
- psychology, workplace, relationships, ethics → character-concept-comic
- numbers, trends, rankings → data-viz

Confirm the choice (with the user or in the storyboard notes) **before** writing the storyboard.

## Scene routing (within the chosen grammar)

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
(`coli asr -j`, edge-tts WordBoundary, WhisperX, or supplied). 4. **Derive scene boundaries and
keyword beats with `scripts/derive_timing.py`** — scene cuts land on pause midpoints between
clauses, beats land exactly on the spoken keyword's token time. Never hand-author beat times
when word timestamps exist; hand-tuned beats are the #1 cause of perceived A/V desync. 5. Land
visual payoffs on spoken keywords (±0.3s). 6. Hold the resolved state ≥0.8s
(1–1.5s for dense diagrams). 7. Subtitles go on the topmost layer, applied last in FFmpeg.

When the pipeline assembles a template automatically, step 4–5 become the `@beats` anchor solve:
the template's own choreography moments (`enter/build/reveal/peak/settle`) are pinned to scene
time with `build` = first content word − 0.7s and `reveal`/`peak` on the spoken keywords.
Hand-authored projects should keep the same shape: intro in ≤0.2s, the data move on the word,
then a still hold.

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

1. `python3 scripts/fetch_assets.py --project <dir> [--sheet]` — searches Pexels (set `PEXELS_API_KEY`),
   Pixabay (`PIXABAY_API_KEY`), then keyless Openverse and Wikimedia Commons; downloads to
   `assets/media/`, backfills `local`/`attribution`/`license`, and writes
   `assets/media/manifest.json` (the license record you ship). Resume-safe; bundled SFX pack
   matches `audio-sfx` queries locally. `--sheet` renders a contact sheet of downloaded photos.
2. **Asset gate**: view the contact sheet (or the files) before rendering; judge match against
   the asset's rich `description`, not just the query. Reject → rewrite the query and re-fetch
   (at most two rounds per slot).
3. Templates reference `{{assets.<id>}}` placeholders; a missing asset degrades to the
   template's CSS fallback instead of an empty frame.
4. `python3 scripts/mix_audio.py --scenes ... --narration ... --out audio/mix.wav` — mixes the
   narration with per-scene SFX at `startSec + atSec` (SFX sit at -12dB with fades; default to
   **no SFX** and let BGM carry cohesion unless an effect is explicitly authored).
5. **BGM**: prefer a local `assets/bgm/` track, else fetch CC0/CC-BY music via the Openverse
   audio API (keyless), trim with fade-in/out, and mix via `finalize.py --bgm` (0.18 under the
   narration). Record attribution in the asset manifest.

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
