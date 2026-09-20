# Changelog

## v2.6.0 — 2026-09-20

**“把素材型风格接上自动检索”** —— collage-evidence / editorial-collage / generated-cinematic
三条风格的画面主体是真实照片，而此前自动档只会在槽位里填一个内联占位图：一条风格好不好用，
取决于人有没有手动去找图。这一版让管线自己去取图，并把取图当成一个有质量护栏的步骤。

### 素材检索进管线（`make_video.py` 新增 `step_assets`）

- 三条素材风格声明自己需要的槽位（`MATERIAL_PLANS`：槽位名 / 角色 / 类型优先序 / 限定修饰词），
  `step_assets` 在**分镜之后、组装 composition 之前**跑：合成检索词 → 调 `fetch_assets.py`
  下载 → 把「本场实际下到的文件」映射回模板写死的槽位名。
- **检索词合成**：新增 `assets/lexicon/visual-concepts.txt`（自撰，MIT，52 条）：中文概念 →
  英文检索短语，每条给 2–4 个同域备选。为什么要它：Pexels/Pixabay/Openverse/Wikimedia 对英文
  召回远好于中文（实测「智能手机芯片」取回路由器与麦克风照片）；而且一条风格同一场往往要 4 张
  素材，四张都拿同一个检索词必是同一张脸——现在按候选表顺位取第 1/2/3/4 名，四张各不相同又
  都在同一语义域。命中不了概念表就退中文关键词。
- 检索词打分：命中触发词按字数计分，若触发词还是该场关键词的一部分，按覆盖率加权 3 分；
  同分则先出现在文案里的胜。
- `--assets plan.json` 逐场覆写检索词（`{"s01":[{"slot":"photo-1","query":"…","pick":0}]}`）；
  `--local-dir` 本地素材库优先；`--no-fetch` 保留模板兜底。产物：`storyboard/assets-plan.json`。

### 取图质量护栏（`fetch_assets.py`）

- **标题相关性排序**：命中结果按「检索词有几个词出现在标题/描述/标签里」稳定排序。无密钥源的
  相关性很粗——实测 `model scale` 第一名是一张城堡模型照片——标题命中是最便宜有效的护栏。
- **尺寸护栏**：下载后用 ffprobe 量宽度，小于 900px 的换下一张（铺到 1080 宽会糊）。
- **本轮 URL 去重**：同一个源图不会同时填两个槽位。
- **检索词阶梯**：主检索词零命中时退到不带修饰词的裸概念（长短语在全文检索里命中率极低，
  `neural network architecture cinematic still` 实测 0 命中）。
- **文件名带检索词指纹**：`s01-photo-1-b4f2f9.jpg`——换检索词不会静默复用上一轮那张图。
- 接触表改 libass 打标（本机 ffmpeg 未编 drawtext），标签现在真的显示，且带检索词。

### 模板与槽位解析

- 路径修正：HyperFrames 的项目根就是 composition 目录，素材必须拷进
  `composition/assets/media/` 并以根相对路径引用；旧的 `../assets/media/` 会被 lint 判为
  `invalid_parent_traversal_in_asset_path`，而文件不在 composition 下又会报
  `missing_local_asset`（渲染时静默丢图）。
- collage-evidence：四张卡的兜底层不再是「photo-1 / 素材占位」，改为当前场关键词 + 槽位角色
  （主证据/对照/档案/细节）——没取到图时画面仍然是一张设计过的卡片。
- editorial-collage：新增右下副素材窗口（photo-2）。没取到图时整块在构建期移除
  （`data-hide-when-empty`），不会留下一个空框。
- generated-cinematic：容器里新增真实静帧 `<img>`（media-1），保留原有渐变+环层兜底；
  视频优先、照片兜底（无密钥的免费视频源基本只有 Wikimedia 的 webm）。

### 扫描

- `style_sweep.py` 透传 `--assets` / `--local-dir` / `--no-fetch`；三条素材风格在扫描里
  会各自取图，扫描因此同时是素材通路的端到端回归网。
- 重新横扫 15 条风格并更新 `docs/style-sweep/`：素材型三风格从「空占位框」变成有真实照片的
  成片；逐条结论重写（见 `docs/style-sweep/README.md`）。
- CI 增加 --no-fetch 的 15 模板组装关卡（不联网）。

## v2.5.0 — 2026-09-20

**“把自动档做成真正能看的成片”** —— 上一版的自动档能跑通，但片子本身站不住：动画和旁白不同步，
场景被拦腰切断，图表只是真实数据的示意图。这一版把三件事拆开重做。

### 节奏：动画挂在念出的字上（`@beats` 锚点）

- 模板在尾注声明五个编排锚点
  `// @beats enter=… build=… reveal=… peak=… settle=…`，`make_video.py` 把它们解到场景时间：
  `enter` = 场次头 +0.12s，`build` = 首个内容词前 0.7s 起势（柱子是「边说边长」的），
  `reveal` / `peak` 落在旁白念到的关键词上，`settle` 收势。锚点时间表写到
  `storyboard/beats.json`。
- 修掉真正的病根：旧版把模板整套编排（典型 0.1–3.5s）**线性拉满整个场景**，
  一场 10s 的片子就是 10s 慢动作，说完话画面还在动。现在动画在词上完成，其余时间静止可读。
- 15 条模板全部声明锚点（各自由编排语义决定，例如 hand-sketch 的 `reveal` = 证据照片钉入、
  process-flow 的 `peak` = 数据包走完）。未声明的模板仍然安全：锚点从位置参数分布自动推断。

### 结构：一场一句，字幕逐字照文案

- `group_clauses` 改为**按文案句子分场**：一句一场；超过 8.2s 的句子在其内部标点处切成 5–7.5s
  的段；尾场 <2.2s 并回上一场。此前的纯时长贪心会把句子拦腰截断（「涨到二十五万八千篇
  投稿量还在涨」把两个话题黏在一场）。
- 新增 `scripts/align_transcript.py`：**转写以文案为准**。ASR 的 ITN 与误字
  （过去十年→过去1年、arXiv→Aive、三分之二→3分之2）会同时污染字幕与关键词分词，而旁白
  本来就是照文案念的——用 difflib 把文案文字套回 ASR 时间戳（相似度 <0.55 则放弃并原样保留），
  原始转写留在 `script/transcript.raw.json`。
- 关键词抽取继续抬地板：中文数词串禁入（十年/十六/三分/一倍）、复合词可跨「的/之」
  （论文的数量 → 论文数量）、可带单字后缀（投稿|量、复现|率）、紧邻数字的候选加权
  （那个词就是这张图的类目名）；`derive_timing.find_keyword` 同步支持跳修饰助词定位 beat。
- furniture 移到 `data-track-index="3"`（实测 **track 0 不渲染**，而场景 clip 不透明，
  原先 furniture 一直被盖住），现在片头/片尾标记真的会显示。

### 画面：data-viz v2 与五种诚实版式

- 场景现在是**大标题 + 口径行 + 绘图区 + 数据来源**四层结构（此前只有一个 42px 小标题钉在
  左上角，与 furniture 规则线相撞）。
- 按语义自动选版式：`trend`（年份序列折线，pathLength 生长）/ `bars`（同一量纲零基线柱）/
  `cards`（量纲不同并列参照）/ `bignum`（单个数：1750亿、280倍）/ `statement`（没有可上屏的
  数字就上大字陈述，**绝不画假柱**）。轴顶标出 vmax + 单位，类目标签在基线下方，负向指标
  不用强调色。
- 折线修了两个真 bug：path 缺 `viewBox` 导致坐标被当作像素、整条线缩在左上角；末端数值
  标签居中溢出画面（改为两端留边 + nowrap）。`--data` 支持指定 `mode`，未给则自动判定。

### 新增：风格扫描与数据片示例

- `scripts/style_sweep.py`：同一段文案在 **15 条风格**里各渲一遍，输出
  5×3 抽帧表（`sweep-contact-sheet.jpg`）、15 格并排对比片（`sweep-grid.mp4`）与
  `sweep-report.json`。既用于风格选型，也是每条模板组装路径的端到端回归。
- `examples/demo-density/`：8 场 / 49.9s 数据片《数量在膨胀，密度在收缩》——旁白 + CC0 BGM +
  烧录字幕，全部数字可溯源（Stanford HAI AI Index 2025/2026、arXiv 年度报告、NeurIPS 2019、
  AAAI 2025、arXiv 2603.23640），每张图都带来源行。

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
