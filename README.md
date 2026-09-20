# Knowledge Motion Video

<!-- GitHub 徽章：仓库创建后把 <owner>/<repo> 替换为实际路径，例如 your-name/knowledge-motion-video -->
[![ci](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

**文案进，知识动画视频出。** A renderer-neutral, open-source agent skill that turns scripts,
articles, lessons, and analyses into narrated knowledge-animation videos — segmented into
semantic beats, routed per beat to the visual grammar that explains it best, rendered
deterministically, and assembled end-to-end with voiceover, captions, and music.

> Inspirations include Vox-style collage, Kurzgesagt-style explainers, and creator workflows
> such as the "badcat-animate" demo. All templates and code here are original. Principles are
> learned; no protected frames, characters, or assets are reproduced.

## Why

Knowledge videos are hard not because any single piece is hard, but because the work is
fragmented: finding assets, planning camera moves, timing captions, generating media,
downloading, and assembling. This skill collapses that pipeline into one recoverable,
auditable production contract — and generalizes beyond any single creator's style pack:

- **Semantic beats, not slides.** Content is segmented into 6–8 second beats driven by meaning
  and the audio clock.
- **Routing, not templates.** Twelve visual grammars — collage, comic, paper diorama, Swiss
  sketch, UI demo, data-viz, kinetic type, whiteboard, timeline, process flow, map, cinematic —
  compete to explain each beat.
- **Renderer-neutral contracts.** `storyboard/scenes.json` describes intent; HyperFrames,
  Manim, Lottie, Three.js, or the bundled headless-Chrome fallback renderer can execute it.
- **Audio-first timing.** Narration is locked first; word timestamps drive visual payoffs.
- **Deterministic and resumable.** Fixed seeds, seek-safe motion, manifests for scenes and
  assets, JSON verification reports.

## Quick start

```bash
# 1. Check the environment
python3 scripts/doctor.py

# 2. Scaffold a project
python3 scripts/scaffold_project.py ~/Videos/my-explainer --title "为什么天空是蓝色" --aspect 9:16

# 3. Edit storyboard/scenes.json (schema: references/scene-schema.md)
python3 scripts/validate_scenes.py ~/Videos/my-explainer/storyboard/scenes.json

# 4. Build the composition, then render either way:
npx hyperframes render                              # HyperFrames (default)
node scripts/render-browser.mjs composition/index.html --fps 30   # bundled fallback

# 5. Captions, mix, and finalize
python3 scripts/build_captions.py --transcript transcript.json \
  --scenes storyboard/scenes.json --out-dir captions/
python3 scripts/finalize.py --visual renders/visual-master.mp4 \
  --narration assets/audio/vo.wav --captions captions/subtitles.ass \
  --out renders/final.mp4

# 6. Verify
python3 scripts/verify.py ~/Videos/my-explainer
```

A complete worked example — script → storyboard → composition → narration → captions →
final MP4, all verified — lives in [`examples/sample-project/`](examples/sample-project/).

## From a long document to a 5-minute film（v2.8）

用一份 44,484 字的研报（`TOC瓶颈理论从入门到精通.md`）跑出来的真实案例：

- **先算预算再动笔**：这个音色实测 ≈3.35 字/秒，5 分钟 ≈ 1,050 字。4.4 万字压到 5 分钟是
  **42:1** 的重写，不是朗读——脊柱比目录重要（案例命 6 幕：反直觉开场 → 概念翻转 →
  五步法 → 为什么难 → 来历 → 判断）。
- **旁白分段生成 + 逐段体检**：TTS 会**静默丢句**——实测两次各留下 41.3s / 58.5s 的纯静音，
  不看波形根本发现不了（后果是时间轴错位或 `durationSec must be > 0`）。
  `python3 scripts/check_narration.py audio/*.mp3` 已进管线，见
  [`docs/document-to-film.md`](docs/document-to-film.md)。
- **55 场 / 5 套版面**：同一部片里按句子形状逐场换（巨数字 / 一句话大片 / 对照 / 步骤进度 /
  论证），最长同版面连续 2 场；「第 N 步」句自动拿到进度条 + 巨号步序。

## Showcase（完整素材化案例）

[`examples/showcase-project/`](examples/showcase-project/) 是全链路案例（32.3s，1080×1920）：

- **整片单一风格**：全片文案语义分析 → 整片 hand-sketch 语法（风格路由是整片决策，见 SKILL.md）
- **旁白 + BGM + 烧录字幕**：场景边界与关键词 beat 全部由词级 ASR 时间戳推导
  （`derive_timing.py`），每个视觉动作卡在语音关键词落点 ±0.3s 内
- **真实素材**：一张语义匹配的 CC 授权真实照片（复古胶片相机），由 `fetch_assets.py` 检索
  下载并经素材目检关卡，许可证与署名记录在 `assets/media/manifest.json`
- **BGM**：Openverse 无密钥获取的 CC0 钢琴循环，0.18 音量垫底 + 淡入淡出
- 成片：`renders/final-showcase.mp4`

复现：`python3 scripts/fetch_assets.py --project examples/showcase-project --sheet` → 目检素材 →
渲染 → `python3 scripts/derive_timing.py …` 重建时间轴 → `finalize.py --bgm …`。

## Data film（数据片示例，v2.5）

[`examples/demo-density/`](examples/demo-density/) 是一条 8 场 / 49.9s 的数据叙事片
《数量在膨胀，密度在收缩》（1080×1920，旁白 + CC0 BGM + 烧录字幕）：

- **每个数字都能点回来源**：Stanford HAI AI Index 2025/2026、arXiv 年度报告、NeurIPS 2019、
  AAAI 2025、arXiv 2603.23640；每张图底部署名，没来源就不写。
- **五种版式按语义自动选**：趋势线（10.2万→24.2万→25.8万）→ 柱状图（arXiv 投稿量）→
  柱状图（两项独立复现实验 63.5% / 50%）→ 巨数（GPT-3 1750 亿）→ 大字陈述（参数不再公开）→
  柱状图（同一 15 亿模型的速度）→ 巨数（推理成本 280 倍）→ 大字陈述（结论）。
- **动画挂在念出的字上**：模板的 `@beats` 锚点被解到旁白关键词的词级时间戳，
  柱子是边说边长、数值在词后落地（`storyboard/beats.json` 可核）。
- 成片：`renders/final-density.mp4`；数据源与口径记在 `storyboard/data.json`。

复现：`python3 scripts/make_video.py --copy examples/demo-density/script/copy.txt \
  --project /tmp/demo --go --style data-viz --narration examples/demo-density/audio/narration.mp3 \
  --data examples/demo-density/storyboard/data.json --bgm examples/demo-density/audio/bgm.wav`

## Style gallery

Four design presets × four routes, same 10-second script, rendered at 1080×1920.
These are **silent style loops** for comparing visual grammars — for a full narrated,
material-driven case see the Showcase above:

| Preset | Route | Sample |
|---|---|---|
| clean-education | whiteboard-tutorial | [`examples/style-samples/clean-education/`](examples/style-samples/clean-education/) |
| dark-technical | data-viz | [`examples/style-samples/dark-technical/`](examples/style-samples/dark-technical/) |
| warm-editorial | editorial-collage | [`examples/style-samples/warm-editorial/`](examples/style-samples/warm-editorial/) |
| bold-social | kinetic-typography | [`examples/style-samples/bold-social/`](examples/style-samples/bold-social/) |

A side-by-side comparison GIF is at [`docs/style-comparison.gif`](docs/style-comparison.gif);
per-style loops live next to each sample under `renders/`. Each sample contains the full
`composition/` + `storyboard/scenes.json` pair, so you can re-render or remix any of them.

### Sweep all 15 styles on one excerpt

`scripts/style_sweep.py` renders the *same* excerpt through **every** route and builds a review
sheet, so you can see what each grammar actually does to your copy:

```bash
python3 scripts/style_sweep.py --copy excerpt.txt --narration excerpt.m4a \
    --transcript excerpt.json --out-dir q/
# → q/sweep-contact-sheet.jpg（5×3 抽帧表）
#   q/sweep-grid.mp4（15 格并排对比片）
#   q/sweep-report.json（每格时长 / 版式 / 失败原因）
```

Renderings of the 15 routes on one sentence are in [`docs/style-sweep/`](docs/style-sweep/).
It doubles as an end-to-end regression net: every template's assembly path gets exercised.

### Material styles fetch their own photos (v2.6)

Three routes put **real photographs** on screen — `collage-evidence` (torn-paper evidence wall),
`editorial-collage` (main + secondary photo window), `generated-cinematic` (a cinematic still).
The pipeline now sources those photos itself instead of leaving placeholder boxes:

```bash
python3 scripts/make_video.py --copy copy.txt --project outdir --go --style collage-evidence \
    --narration vo.mp3 --transcript asr.json
# → 素材检索（collage-evidence）：4/4 就绪 → outdir/assets/media
#   outdir/storyboard/assets-plan.json    每场的检索词与来源
#   outdir/assets/media/contact-sheet.jpg 渲染前目检（标签带检索词）
#   outdir/assets/media/manifest.json     许可证与署名清单（发布要留）
```

Queries are synthesized from each scene's own concepts via
[`assets/lexicon/visual-concepts.txt`](assets/lexicon/visual-concepts.txt) (Chinese concept →
English phrase, 2–4 alternatives each, so four slots in one scene get four different images).
English recall is far better than Chinese on every source. Override per scene with
`--assets plan.json`, prefer your own library with `--local-dir`, or opt out with `--no-fetch`.

Keyless sources are noisy, so fetching carries guards: results are re-ranked by title/description
overlap, images narrower than 900px are rejected, **paper material is rejected** (a white, low-
saturation first frame means a paper figure, a flowchart, or a matplotlib screenshot — 7 of the 29
images in our first material cut were exactly that), no source URL is used twice in a run, and a
query ladder retries both the bare concept and the scene's other concept candidates. The concept
table itself follows one hard rule: **the first alternative has to be something a camera can
photograph** — abstract nouns (`inference`, `algorithm`, `efficiency`) only ever match paper
figures on keyless sources, which the guard then rejects, so the slot comes back empty. Fixing that
rule alone took material readiness from 28/32 to 32/32.

**Layout follows the material.** A scene that came back with three photos instead of four does not
leave an empty box on screen: the new `choose_variant` step picks a layout that fits the count
(`wall` / `cascade` / `hero` / `pair` / `single`), never repeating the previous scene's layout, and
a slot with no material removes its whole card. `storyboard/layouts.json` records what was chosen
and why per scene.

**Relevance is still roughly 3-in-4** — view `contact-sheet.jpg` before rendering and fix the
off-topic slot by editing its query or shifting the hit (`"pick": 1`). Set `PEXELS_API_KEY` /
`PIXABAY_API_KEY` for much better material; Openverse and Wikimedia need no key.

## Motion is a gate, not a taste (v2.7)

"The picture is stiff" is measurable. `verify.py` samples the master at 8 fps and compares every
frame **to the same frame one second earlier** (`blend=difference` + `signalstats`) — the scale at
which a slow drift reads as visible while a genuine hold still measures zero. It fails when

- any scene has a run of **more than 1.2 s where the picture does not change at all**, or
- the whole-film mean drops below 0.4.

```bash
python3 scripts/verify.py outdir
# [PASS] motion: {'meanDiff': 3.72, 'longestFrozenSec': 0.12, 'worstScene': 's01', …}
```

The first run of this gate failed both shipped films (1.75 s with nothing changing in one scene of
the collage film, 1.50 s in the data film; 24–27% of all samples under the floor) — entrance
animations are over by the middle of a scene, and the rest was literally the same pixels. Two
engine features fix it, and both are declared in the template rather than composed by hand:

- **Ambient layer** — every scene gets a slow 3–4.5% camera push on the clip itself (no template
  work needed, and pushing *in* means the overflow is clipped rather than exposing an edge), plus
  per-template detail: `data-km-drift="20"` on a decorative layer (drifts ±20 px over the whole
  scene) and `data-km-push="4"` on a photo (a Ken Burns move). Decorative layers sit at
  `inset:-8%` so a few pixels of drift never expose a seam. Opt out with `data-km-ambient="off"`.
- **A second development beat** — the `@beats` anchor set grew a `mid`, solved to the middle of the
  reveal→peak span. That's where a scene changes *state* (in `collage-evidence`: the hero card
  pushes in while the others get shoved aside and dimmed) instead of just adding another entrance.

Per-template guidance: entrances belong in the first third, one visible re-layout or emphasis
belongs at `mid` or `peak`, and the tail is carried by the ambient layer. Fixing a failing scene is
usually "the animation is over too early" — move a beat later or add ambient life, don't shorten
the threshold.

## Requirements

- Python 3.10+ (standard library only)
- Node.js 22+ (for rendering; `puppeteer-core` installed via npm)
- FFmpeg + FFprobe on PATH
- Google Chrome / Edge / Chromium (for the fallback renderer)
- Optional: HyperFrames CLI (`npx hyperframes`), `coli asr` for offline transcription,
  edge-tts / Kokoro / commercial TTS for narration

## Repository layout

```text
SKILL.md                  the agent-facing workflow
references/               pipeline, scene schema, style router, motion language, stack notes
scripts/                  scaffold, validate, captions, finalize, verify, fetch-assets, mix-audio, render, doctor
assets/templates/         per-route scene fragments + series furniture
assets/styles/            design token presets
examples/                 complete runnable projects
```

## Install as a skill

```bash
./install.sh   # symlinks into ~/.cola/skills/knowledge-motion-video
```

## License

MIT — see [LICENSE](LICENSE). Third-party components and any assets you generate or import are
governed by their own licenses; record provenance in `assets/manifest.json`.

Bundled third-party data: `assets/lexicon/zh-words.txt` is derived from jieba's `dict.txt`
(MIT License, Copyright (c) 2013 Sun Junyi) — trimmed and extended with project-authored
vocabulary; provenance notes are in the file header.
