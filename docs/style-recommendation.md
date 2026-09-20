# 语义风格推荐：决策过程（v2.3）

输入任意文案 → 自动分析并推荐整片视频风格，全过程可审计。
工具：`scripts/recommend_style.py`（`--text` / `--file` / stdin，`--json` 输出机器可读结果）。

## 决策过程（工具执行的四步）

1. **文本统计** — 字数、句数、平均句长、疑问句、数字密度 → 节奏提示（快冲击 vs 边画边讲）。
2. **语义信号提取** — 12 类语义轴（方法流程 / 论证观点 / 历史档案 / 真实证据 / 系统结构 /
   科普自然 / 心理人性 / 数据 / 时间演进 / 地理空间 / 软件操作 / 金句定义），
   每类列出**命中的原文词**（证据）与强度 0/1/2（≥2 个强信号 = 2）。
3. **整片决策表命中** — 按强度最高的语义轴查整片决策表（style-router.md）得主风格组；
   双轴并存时套融合规则（如 论证+方法 → hand-sketch，历史+证据 → collage-evidence）。
4. **风格评分与推荐** — 15 条风格按支撑轴加权打分（含负向反证，如出现数据词时压制
   generated-cinematic），Top3 展示；若信号榜头名与决策表组不一致会显式提示人工复核。

风格是**整片决策**：主风格写入 `project.style`，校验器强制全片一致；分镜阶段不再换风格。

## 示例 trace

输入（showcase 同款文案）：

> 一篇文案，怎么变成一支让人看完的知识视频？先读懂文案，找到它真正的论证结构。
> 再把文案切成六到八秒的语义分镜。说服力来自结构，而不是特效。

输出：

```
== 1. 文本统计 ==
  92 字 / 4 句 / 平均句长 23 字 / 疑问句 1 / 数字 0 处
  节奏提示：中长句，节奏留出呼吸，适合边画边讲

== 2. 语义信号（强度 0-2，附原文证据）==
  argument_opinion   强度 2  证据：论证、说服、结构×2、而不是
  method_process     强度 1  证据：怎么、怎么变

== 3. 整片决策表命中 ==
  主导轴：argument_opinion
  主风格组：hand-sketch / swiss-sketch
  理由：论证+方法双主导：笔尖过程承载论证，比纯排版更有说服的温度

== 4. 风格评分（信号加权 Top3）==
  1. swiss-sketch     4.0  (argument_opinion=2, method_process=1)
  2. hand-sketch      3.5  (method_process=1, argument_opinion=2)
  3. whiteboard-tutorial 1.5

== 5. 推荐 ==
  主风格：hand-sketch
  备选：swiss-sketch
```

## 更多验证用例（2026-09-20 实测）

| 文案类型 | 主导轴 | 推荐 |
|---|---|---|
| 方法+论证（showcase） | argument+method 融合 | hand-sketch ✓（与已交付成片一致） |
| 历史档案（莱特兄弟/老照片） | real_evidence | collage-evidence ✓ |
| 数据趋势（电动车占比） | data_numbers | data-viz ✓（融合规则避开 data/timeline 混搭） |
| 职场心理（周一焦虑） | psychology_human | character-concept-comic ✓ |
| 软件操作（三步设置） | software_ui | ui-demo ✓ |

## 边界与原则

- 打分是**启发式预判**：词典/正则覆盖常见语义，但最终确认按 SKILL.md 走
  （与用户确认或人工复核）；工具的价值是把依据摆在明面上，而不是替代判断。
- clean-room 原则：本工具是自研实现，借鉴的是"证据可审计的检索与匹配"这一思路
  （见 `research/openmontage-report.md`），未使用其任何代码。
- 无强语义轴时回退 swiss-sketch/hand-sketch 并标注原因（style-router.md 打分细则第 4 条）。
