# Style sweep — 同一段文案，15 条风格各渲一遍（v2.7）

**目的**：不是看模板 HTML，而是看**渲染出来的成片**。同一段旁白、同一份图表数据，横跑全部 15
条风格，用一张抽帧表判断「这条语法拿到任意文案时到底成不成」。

- 素材：`examples/demo-density/sweep/`（文案一句「2020 年，GPT-3 的参数量是一千七百五十亿。」+
  该句旁白 6.6s + 单场景图表数据）
- 产物：`sweep-contact-sheet.jpg`（5×3 抽帧，65% 时刻）、`sweep-grid.mp4`（15 格并排 7.6s）、
  `sweep-report.json`（每格时长 / 版式 / 失败原因）
- 命令：

```bash
python3 scripts/style_sweep.py \
  --copy examples/demo-density/sweep/copy.txt \
  --narration examples/demo-density/sweep/narration.m4a \
  --transcript examples/demo-density/sweep/transcript.json \
  --data examples/demo-density/sweep/data.json \
  --out-dir docs/style-sweep
```

v2.6 起三条素材型风格（collage-evidence / editorial-collage / generated-cinematic）在扫描里
**各自去检索真实照片**（`--assets` / `--local-dir` / `--no-fetch` 可透传）。

**v2.7 本次结果：15/15 全部渲染成功**（各 7.6s，lint 0 error），素材型三条全部取到素材；
其中 **motion 门禁 11 条通过、4 条仍告警**（下表的 motion 列）。告警不等于渲坏了——
是「这一场后半段画面在一秒尺度上量不出变化」，修法是给这几条各做一次中段发屏。

## 逐条结论（拿到「陌生文案」时的成片质量）

| 风格 | 结论 | motion | 观察 |
|---|---|---|---|
| **data-viz** | ✅ 直接可用 | ✓ | 巨数卡 / 柱状 / 趋势 / 大字陈述四种诚实版式；本版重做过 |
| **hand-sketch** | ✅ 可用 | ✓ | 标题 + 手绘标注 + 红色圈注 + 照片位；文字用描边字，小字略糊但读得出来 |
| **collage-evidence** | ✅ 可用（v2.7 重做） | ✓ | 不再八场一个样：**版面逐场换**（wall / cascade / hero / pair / single，按本场实际素材数 + 内容挑），中段焦点收拢（主卡推近 + 其余挤开压暗），peak 在图注条下画出下划线 + 贴出角色芯片；缺素材整卡消失不留灰框 |
| **editorial-collage** | ✅ 可用（v2.6） | ✓ | 主窗口真实照片 + 右下副窗口；没取到图时副窗口在构建期整块移除，不留空框 |
| **generated-cinematic** | ⚠️ 能看但看命 | ✓ | 自动取回的是论文插图/机柜照，压暗调色后叠加句清楚可读——「电影感」取决于素材本身：正解是自己拍的镜头或生成的静帧（`--local-dir`） |
| **paper-fold / paper-diorama** | ✅ 可用 | ✓ | 纸质层次很美；信息密度低，适合过渡句而非论点句 |
| **process-flow** | ✅ 可用 | ! 1.25s | 三节点 + 分支高亮 + 数据包；节点名已填。画面大面积平色，通用推近量不出变化 |
| **timeline-history** | ✅ 可用 | ! 1.88s | 轴线 + 节点 + 卡片；年份槽位拿到 2020 就填上 |
| **whiteboard-tutorial** | ✅ 可用 | ✓ | 手写笔画 + 下划线 + 圈注，槽位文字已上屏 |
| **ui-demo** | ⚠️ 需指定 | ✓ | 浏览器框 + 焦点环 + 高亮，拿到非 UI 文案时刻意感强 |
| **kinetic-typography** | ⚠️ 信息稀 | ! 1.25s | 大字 + 色块，形是成立的，但一句文案只出得了一个词，适合金句不适合数据 |
| **swiss-sketch** | ⚠️ 信息稀 | ✓ | 版面留白极大，命中「一个论点」时很好，拿到长句会很空 |
| **character-concept-comic** | ⚠️ 信息稀 | ✓ | 火柴人 + 台词气泡，缺少人物设定/表情资产时画面很干 |
| **map-geo** | ⚠️ 底图抽象 | ! 2.00s | 底图是形状化大陆块而非真实地理；而且大片平色+推近=量不出变化，地方叙事会显得不专业，真做地理得接 GeoJSON |
**结论（v2.7）**：auto 模式的安全区是 **data-viz / hand-sketch / process-flow /
timeline-history / whiteboard-tutorial / paper-fold / paper-diorama / collage-evidence /
editorial-collage / swiss-sketch / character-concept-comic / ui-demo**（12 条渲染与运动都站得住）。
generated-cinematic 仍是「素材决定上限」；kinetic-typography 一句文案只出得了一个词，
最适合人工指定场景。

**motion 列的 4 条告警怎么读**：这四条的共同特征是版面大面积平色（map-geo 的底图、
process-flow 的白底方块、kinetic 的色块、timeline 的白底轴线）——通用镜头推近在这种画面上
「推了但没有可看的细节在动」，一秒尺度上量出的变化接近 0。这不是门禁误判，而是**可感知的
呆板**：正解是给它们各做一次中段发屏（像 collage-evidence 的「焦点收拢」），还没做。

**素材相关度**：无密钥源（Openverse / Wikimedia）大约 **三张里有两到三张明确对题**，其余是
「同域但构图一般」。所以取图后有一个人工/agent 关卡：看
`assets/media/contact-sheet.jpg`（标签带检索词），不对题的槽位改检索词（`--assets`）或换一张
（`"pick": 1`）。设了 `PEXELS_API_KEY` / `PIXABAY_API_KEY` 会明显更好。

这同时也是回归网：每条模板的组装路径（槽位命名空间、锚点重定时、lint、渲染）都被跑了一遍。
素材型三条还会把检索—下载—槽位映射—拷贝进 composition 这条链路走通。

**一条经验**：别把渲染挂在会退出的父 shell 后面（`cmd &` 然后脚本退出）。HyperFrames 渲染器
会检测父进程，实测出现 `render_cancelled_parent_exited`（同一条风格重跑就过）。扫描要放前台跑。

## v2.7 这一轮扫描逼出来的四个真修复

1. **motion 门禁把 12 条模板挡在门外 → 通用镜头推近**：以前只有声明了环境微动的模板才有
   尾段运动。现在引擎对每一场的 `<section class="clip">` 都铺一条 3–4.5% 的慢推（朝内推，
   超出部分被裁掉，不会露边），模板一个字都不用改；模板自己的 `data-km-drift`/`data-km-push`
   仍然生效，`data-km-ambient="off"` 可关。一次改动让门禁通过数从 3/15 涨到 11/15。
2. **`generated-cinematic` 把 `.webm` 塞进了 `<img>`**：`types: ["video","photo"]` 配上
   `<img>` 槽位，lint 直接判 `media_src_kind_mismatch`（嵌套 `<video>` 又不能确定性 seek）。
   现在该槽位只收照片，并且 `resolve_asset_srcs` 遇到「视频填进 img 槽」会 fail-closed 退回
   占位图而不是交出一个坏 composition。
3. **`hand-sketch` 的 JS 又被散文行顶坏**：`parse_template` 的「含中文即当散文丢掉」规则在
   修「行内尾注吃掉代码行」时被放松过头，纯中文说明行（如 `注意: helper 内 ...`）被当代码留下，
   `Unexpected identifier '内'`。现在只在**行内有 `//` 且代码段不含中文**时才保留代码段。
4. **门禁的尺度选错了**：一开始拿「上一帧 vs 这一帧」比，125ms 里 3% 的慢推挪不到一个像素，
   于是把明明在动的画面判成「没动」。改成**跟一秒前的同一位置比**之后，旧成片照样挂
   （collage 1.75s、数据片 1.50s），而慢推被正确地算成运动。指标量错了，比没有指标更糟。

## v2.6 这一轮扫描逼出来的三个真修复

1. **kinetic-typography 两行叠字**：这条模板把重点词用强调色**叠在行首**（`left:0;top:0`）来
   实现「高亮第一个词」——前提是第一行必须以重点词开头。填槽器原来给的第一行是关键词 A、
   重点词是关键词 B，渲染出来就是两个词叠在一起。现在第一行从首个关键词起算，两层严丝合缝。
2. **generated-cinematic 文字压不住画面**：渐变暗角只到 40%，叠加句压在插图线条上几乎读不出。
   现在加了冷色调色层（multiply）并把素材压暗去饱和——任何素材拉进同一种语气，文字始终可读。
3. **素材型风格的空占位**：见上一节（管线的素材检索）。取不到图时，卡片兜底层显示该场关键词 +
   槽位角色，`data-hide-when-empty` 的副窗口整块移除。

## 上一轮（v2.5）扫描逼出来的两个真修复

1. **槽位大面积留空**：`fill_slots` 原来只认 HEADLINE/POINT_1/POINT_2，其余槽位（TITLE /
   LINE_A/B / STEP_1..3 / EVENT_1..3 / NODE_A..C / PIN_1..3 / LAYER_*_LABEL / CAPTION /
   QUOTE / KEY_WORD / YEAR_1..3 / BRANCH_TAKEN / APP_TITLE / STEP_TEXT）一律填空串 —— 渲染出来
   就是一排空白占位框。现在按「关键词 → 数字 → 短子句」的有序候选逐槽分配，同一段内容不重复
   占两个槽；`{{ACCENT}}` 由风格调色板注入。
2. **`tile` 滤镜吃不了多路输入**：抽帧表最早用 `tile` 拼 15 张 PNG，报
   "More input link labels specified for filter 'tile' than it has inputs" —— 多图要用
   `xstack`；另外这台 ffmpeg 没编 `drawtext`（无 freetype），风格名改由 **libass** 覆盖层烧
   （和成片字幕同一条路径），不再依赖 drawtext。
