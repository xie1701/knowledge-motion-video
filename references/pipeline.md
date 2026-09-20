# Production pipeline

## 0. Doctor

Run `python3 scripts/doctor.py` to confirm ffmpeg/ffprobe, Node, Chrome, and optional engines (HyperFrames CLI, coli, edge-tts). Missing optional tools degrade specific steps, not the project.

## 1. Establish the brief

Write `BRIEF.md` with audience, message, destination, duration, language, aspect ratio, script-lock status, voice choice, brand, licensing constraints, and approval mode.

## 2. Lock narration

Separate spoken language from visual directions. Keep one argument per paragraph. Preserve the author's point of view; the skill improves structure but does not invent the thesis.

Useful Chinese speaking-density starting point: 4–5.5 characters/second after pauses. Measure the actual voice instead of trusting estimates.

## 3. Build the audio clock

Generate or import narration, then obtain timestamps. Preferred order: supplied word timings; edge-tts WordBoundary (`scripts/tts_edge.py`); offline ASR (`coli asr -j`); phrase boundaries from measured audio (mark approximate). Store immutable timing in `script/transcript.json`.

## 4. Segment semantic beats

Target 6–8 seconds, but allow 4–12 seconds when comprehension requires it. Split on a change of subject, relation, proof, or visual verb. Do not split merely because punctuation appears.

## 5. Route styles (film-level decision)

First choose **one primary style for the whole film** from the copy's semantics (subject,
persuasive structure, asset availability) — see `style-router.md` film-level table — and record
it as `project.style` plus the one-line rationale. Then assign each beat its semantic class,
visual subject, camera treatment, transition, and asset strategy **inside that grammar**.
Per-scene style changes are for intentionally mixed long-form chapters only, never a default.

## 6. Approve the storyboard

Write both human-readable `storyboard.md` and machine-readable `scenes.json`. The JSON is canonical for implementation; Markdown is canonical for review.

## 7. Produce assets

Prefer, in order:

1. code-drawn SVG/DOM diagrams;
2. original local drawings or generated images;
3. permissively licensed assets with provenance;
4. generated video only when motion semantics cannot be expressed economically in code.

Every external asset gets source URL, creator, license, local path, and usage in `assets/manifest.json`.

## 8. Build a pilot

Implement 20–30 seconds spanning at least two scene types. Verify type scale, subtitle band, camera energy, voice speed, and transitions before scaling production.

## 9. Build in parallel

Group adjacent scenes by shared visual grammar and assets. Each worker receives the same scene schema, design tokens, subtitle safe area, and final-frame requirement. Never let workers independently invent global palettes or typography.

## 10. Assemble and verify

Run static validation, renderer checks or fallback-render snapshots, draft render, visual inspection, audio checks, then final render. `scripts/finalize.py` mixes narration and BGM and burns subtitles last; `scripts/verify.py` produces a PASS/FAIL report and a contact sheet. Rendering options: `npx hyperframes render` (default) or `node scripts/render-browser.mjs` when the CLI is unavailable.

## Artifacts are checkpoints

Do not hide reasoning only in chat. `BRIEF.md`, narration, transcript, storyboard, scene manifest, asset manifest, checks, and delivery notes make the production resumable and debuggable.
