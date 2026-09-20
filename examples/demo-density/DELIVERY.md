# Delivery — Demo「数量在膨胀，密度在收缩」(data-viz, 49.9s)

一条 8 场数据叙事片，用来验证 v2.5 的自动流水线能不能直接出「真正能看的成片」：
文案进 → 风格推荐 → 自动分镜 → 图表数据化 → 锚点编排 → 渲染 → 烧字幕 → 校验。

- 规格：1080×1920 · 30fps · H.264 + AAC · **49.9s** · 8 场
- 风格：data-viz（整片单一语法；`storyboard/style-decision.json` 记录了决策链）
- 旁白：解说小明（ListenHub TTS，48.9s）→ `coli asr` 词级时间戳 → **以文案校正**
  （`script/transcript.raw.json` 是原始 ASR，`script/transcript.json` 是校正后的）
- BGM：CC0 钢琴循环（复用 showcase 的 Openverse CC0 音源），0.18 音量 + 淡入淡出
- 成片：`renders/final-density.mp4`；抽帧：`renders/contact-sheet.jpg`

## 数据来源（每条都能点回原文）

| 场次 | 图表 | 数字 | 来源 |
|---|---|---|---|
| s01 | trend | 10.2万 → 24.2万 → 25.8万 篇/年（2013/2023/2024） | Stanford HAI, AI Index 2025/2026（Scopus 口径） |
| s02 | bars | 24.4万 → 28.4万 篇（2024→2025，+16%） | arXiv 2024/2025 年度报告 |
| s03 | bars | 63.5% / 50% 复现成功率 | NeurIPS 2019（255 篇）/ AAAI 2025（22 篇高被引） |
| s04 | bignum | GPT-3 1750 亿参数（2020） | OpenAI, GPT-3 技术报告（NeurIPS 2020） |
| s05 | statement | 参数规模不再公开 | OpenAI, GPT-4 Technical Report（2023） |
| s06 | bars | 23.7 / 10.4 tokens/s（同一 15 亿参数模型，4-bit） | arXiv 2603.23640（连续推理热稳定态） |
| s07 | bignum | 推理成本 18 个月降 280 倍（$20 → $0.07 / 百万 tokens） | Stanford HAI, AI Index 2025 |
| s08 | statement | 数量在膨胀，密度在收缩 | 结论卡（无数据） |

口径与出处写在 `storyboard/data.json`；每张图底部有 `数据来源` 署名行，没有来源就不写。

## 编排同步（锚点挂在念出的字上）

`storyboard/beats.json` 是程序解出的编排时间表；`beats` 写回了 `storyboard/scenes.json`：

| 场 | 起势 build | 数据落地 reveal | 强调 peak | 收势 settle | 该场关键词 |
|---|---|---|---|---|---|
| s01 | 论文数量 | 论文数量 | 论文数量 | 十/二十五万 | 论文数量 |
| s02 | arXiv | arXiv | 投稿 | | arXiv、投稿 |
| s03 | 复现研究 | 复现研究 | 复现研究 | | 复现研究 |
| s04 | GPT-3 | 参数量 | 参数量 | | GPT-3、参数量 |
| s05 | 参数规模 | 参数规模 | 公开 | | 参数规模、公开 |
| s06 | 小模型 | 小模型 | 三星 | | 小模型、三星 |
| s07 | 推理成本 | 推理成本 | 推理成本 | | 推理成本 |
| s08 | 膨胀 | 膨胀 | 密度 | | 膨胀、密度 |

规则：`build` = 首个内容词前 0.7s（柱子边说边长）、`reveal` = 该词后 0.35s、`peak` = 末个内容词
后 0.3s、`settle` = peak + 1.4s（不超过场尾保留 1.5s 的静止阅读区）。

## 复现

```bash
python3 scripts/make_video.py \
  --copy examples/demo-density/script/copy.txt \
  --project /tmp/demo-density --go --style data-viz \
  --narration examples/demo-density/audio/narration.mp3 \
  --data examples/demo-density/storyboard/data.json \
  --bgm examples/demo-density/audio/bgm.wav
python3 scripts/verify.py /tmp/demo-density        # verdict: PASS
```

## 已知边界

- `data.json` 是**人给的真数据**。自动档从文案里抽到的是「十万篇 / 二十五万八千篇 / 二十八万篇」
  这类原文数字，能画但不能替你判断口径是否可比 —— 交片前应像本案例一样备一份 `--data`。
- s06 的两个数取自同一篇论文的热稳定态；不同设备/框架/量化之间不能等同比较，图上已注明来源，
  但这类「同一模型跨设备」的比较仍应视为趋势而非基准。
- 旁白 ASR 原始输出有误字（过去十年→过去1年、arXiv→Aive），由 `align_transcript.py` 用文案
  校正回时间戳；若换旁白，需重跑该步并复核 `align_ratio`。
