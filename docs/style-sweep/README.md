# Style sweep — 同一段文案，15 条风格各渲一遍（v2.5）

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

15/15 全部渲染成功（各 7.6s，lint 0 error）。

## 逐条结论（拿到「陌生文案」时的成片质量）

| 风格 | 结论 | 观察 |
|---|---|---|
| **data-viz** | ✅ 直接可用 | 巨数卡 1750亿 + 大标题 + 口径行 + 来源行，四层结构完整；本版重做过 |
| **hand-sketch** | ✅ 可用 | 标题 + 手绘标注 + 红色圈注 + 照片位；文字用描边字，小字略糊但读得出来 |
| **collage-evidence** | ⚠️ 需素材 | 结构好（卡片 + 印章 + 箭头 + 图注），但没跑 `fetch_assets.py` 时全是 "photo slot" 占位 |
| **editorial-collage** | ⚠️ 需素材 | 同上，主图位空着；填一张真实照片就成立 |
| **generated-cinematic** | ⚠️ 需素材 | 没有视频素材时几乎是黑场 + 一个光点；必须配媒体 |
| **paper-fold / paper-diorama** | ✅ 可用 | 纸质层次很美，槽位已能填上标签；信息密度低，适合过渡句而非论点句 |
| **process-flow** | ✅ 可用 | 三节点 + 分支高亮 + 数据包；节点名已填（GPT-3 / 一千 / 参数量） |
| **timeline-history** | ✅ 可用 | 轴线 + 节点 + 卡片；年份槽位拿到 2020 就填上，拿不到退 01/02/03 |
| **whiteboard-tutorial** | ✅ 可用 | 手写笔画 + 下划线 + 圈注，槽位文字已上屏 |
| **kinetic-typography** | ⚠️ 信息稀 | 大字 + 色块，形是成立的，但一句文案只出得了一个词（POINT 槽），适合金句不适合数据 |
| **swiss-sketch** | ⚠️ 信息稀 | 版面留白极大，命中「一个论点」时很好，拿到长句会很空 |
| **character-concept-comic** | ⚠️ 信息稀 | 火柴人 + 台词气泡，缺少人物设定/表情资产时画面很干 |
| **map-geo** | ⚠️ 底图抽象 | 底图是形状化大陆块而非真实地理，地方叙事会显得不专业；真要做地理得接 GeoJSON |
| **ui-demo** | ⚠️ 需指定 | 浏览器框 + 焦点环 + 高亮，拿到非 UI 文案时刻意感强；只该用在产品操作场景 |

**结论**：auto 模式（任意文案自动选风格）目前的安全区是 **data-viz / hand-sketch /
process-flow / timeline-history / whiteboard-tutorial / paper-fold**；带素材的
collage/editorial/cinematic 需要先跑素材检索；kinetic/swiss/comic/map/ui-demo 更适合人工指定
场景，不宜交给自动路由。

这同时也是回归网：每条模板的组装路径（槽位命名空间、锚点重定时、lint、渲染）都被跑了一遍。

## 这一轮扫描逼出来的两个真修复

1. **槽位大面积留空**：`fill_slots` 原来只认 HEADLINE/POINT_1/POINT_2，其余槽位（TITLE /
   LINE_A/B / STEP_1..3 / EVENT_1..3 / NODE_A..C / PIN_1..3 / LAYER_*_LABEL / CAPTION /
   QUOTE / KEY_WORD / YEAR_1..3 / BRANCH_TAKEN / APP_TITLE / STEP_TEXT）一律填空串 —— 渲染出来
   就是一排空白占位框。现在按「关键词 → 数字 → 短子句」的有序候选逐槽分配，同一段内容不重复
   占两个槽；`{{ACCENT}}` 由风格调色板注入。
2. **`tile` 滤镜吃不了多路输入**：抽帧表最早用 `tile` 拼 15 张 PNG，报
   "More input link labels specified for filter 'tile' than it has inputs" —— 多图要用
   `xstack`；另外这台 ffmpeg 没编 `drawtext`（无 freetype），风格名改由 **libass** 覆盖层烧
   （和成片字幕同一条路径），不再依赖 drawtext。
