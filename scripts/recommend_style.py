#!/usr/bin/env python3
"""Film-level style recommender: analyze a copy, recommend one visual style.

v2.3 风格路由的深挖版：输入任意文案，输出**可审计的决策过程**——
1. 文本统计（句长、疑问句、数字密度）；
2. 语义信号提取（每类信号列出命中的原文词，强度 0/1/2）；
3. 15 条风格路由逐一打分（证据加权，含负分反证）；
4. 最终推荐（主风格 + 备选 + 何时该换 + 素材可得性提示）。

打分是启发式的：它把 style-router.md 的整片决策表和打分细则程序化，
用于快速预判和展示依据；最终确认仍按 SKILL.md 走（与用户确认或人工复核）。

Usage:
    python3 scripts/recommend_style.py --text "一篇文案，怎么变成……"
    python3 scripts/recommend_style.py --file copy.txt
    cat copy.txt | python3 scripts/recommend_style.py
    python3 scripts/recommend_style.py --file copy.txt --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 语义信号词典：category -> (信号词, 权重)
# 权重：1 = 相关，2 = 强信号（出现即几乎确定该语义轴成立）
# ---------------------------------------------------------------------------

SIGNALS: dict[str, dict[str, int]] = {
    "method_process": {
        "方法": 2, "步骤": 2, "教程": 2, "流程": 2, "指南": 1, "攻略": 1,
        "教你": 2, "怎么办": 2, "怎么做": 2, "如何": 1, "怎么": 1,
        "怎么变": 2, "一遍": 1, "打法": 1, "拆解": 1, "上手": 1, "实操": 2,
        "how to": 2, "tutorial": 2,
    },
    "argument_opinion": {
        "观点": 1, "论证": 2, "说服": 2, "本质": 1, "结构": 1, "结论": 1,
        "应该": 1, "为什么": 1, "误解": 1, "真相": 1, "逻辑": 2, "对比": 1,
        "而不是": 2, "不是…而是": 2, "关键在于": 2,
    },
    "history_archive": {
        "历史": 2, "年代": 1, "世纪": 2, "朝代": 2, "战争": 1, "事件": 1,
        "起源": 2, "演变": 1, "大事记": 2, "复盘": 1, "当年": 1, "古人": 1,
        "档案": 2, "遗迹": 1, "文明": 1,
    },
    "real_evidence": {
        "真实": 2, "照片": 2, "录像": 2, "现场": 1, "证据": 2, "老照片": 2,
        "记录": 1, "实拍": 2, " footage": 1, "影像": 1, "档案": 1,
    },
    "system_structure": {
        "系统": 2, "原理": 2, "机制": 2, "架构": 2, "工程": 1, "组成": 1,
        "内部": 1, "运转": 1, "运作": 2, "生态系统": 2, "产业链": 2,
        "分子": 1, "细胞": 1, "引擎": 1, "物理": 1,
    },
    "science_nature": {
        "宇宙": 2, "自然": 1, "生物": 2, "化学": 2, "量子": 2, "进化": 2,
        "地球": 1, "气候": 2, "动物": 1, "植物": 1, "大脑": 1, "基因": 2,
    },
    "psychology_human": {
        "心理": 2, "职场": 2, "情绪": 2, "焦虑": 2, "内耗": 2, "沟通": 1,
        "人性": 2, "关系": 1, "领导": 1, "团队": 1, "伦理": 2, "困境": 1,
        "两难": 2, "自尊": 2, "共情": 2, "边界感": 2,
    },
    "data_numbers": {
        "数据": 2, "增长": 2, "占比": 2, "排名": 2, "趋势": 2, "调查": 1,
        "统计": 2, "份额": 2, "翻倍": 2, "飙升": 1, "跌": 1, "指数": 2,
        "%": 1, "百分之": 2,
    },
    "timeline_sequence": {
        "最初": 2, "后来": 2, "之后": 1, "随后": 1, "最终": 1, "演进": 2,
        "里程碑": 2, "从…到": 2, "发展史": 2, "元年": 2,
    },
    "geography_space": {
        "地理": 2, "地图": 2, "分布": 2, "位于": 2, "区域": 1, "城市": 1,
        "国家": 1, "迁移": 2, "扩散": 2, "选址": 2, "路线": 1,
    },
    "software_ui": {
        "软件": 1, "app": 2, "App": 2, "点击": 2, "界面": 2, "操作": 2,
        "设置": 1, "功能": 1, "快捷键": 2, "菜单": 2, "屏幕": 1, "安装": 2,
    },
    "quote_definition": {
        "定义": 2, "就是": 1, "一句话": 2, "记住": 1, "核心是": 2, "本质上": 2,
        "一句话讲清": 2,
    },
}

# 负向反证：这些信号出现时，对应风格要扣分
ANTI_SIGNALS: dict[str, dict[str, int]] = {
    "generated_cinematic": {"数据": -2, "教程": -2, "步骤": -1, "统计": -2},
}

# 数字 / 年份等正则信号（独立于词典）
_REGEX_SIGNALS = [
    ("data_numbers", re.compile(r"\d+(\.\d+)?\s*[%％]|\d+\s*万|\d+\s*亿|\d+\s*倍"), 2, "数字+单位"),
    ("timeline_sequence", re.compile(r"(19|20)\d{2}\s*年|\d+\s*世纪"), 2, "年份/世纪"),
    ("quote_definition", re.compile(r"[^。！？\n]{2,12}，?就是[^。！？\n]{2,20}[。！？]"), 1, "『…就是…』句式"),
]

# 整片语义 -> 主风格组（style-router.md 整片决策表）
FILM_DECISION_TABLE: list[tuple[str, list[str], str]] = [
    ("method_process", ["hand-sketch", "swiss-sketch", "whiteboard-tutorial"], "方法/教程/流程/论证：笔尖引导注意，过程即说服"),
    ("history_archive", ["collage-evidence", "editorial-collage", "timeline-history"], "历史/事件/档案：真实证据是说服力本体"),
    ("real_evidence", ["collage-evidence", "editorial-collage"], "需要真实照片/视频证据的叙事"),
    ("system_structure", ["paper-fold", "paper-diorama", "process-flow"], "系统/工程/结构原理：空间装配感承载系统语义"),
    ("science_nature", ["paper-diorama", "paper-fold"], "科普/自然机制：分层纸雕承载机制拆解"),
    ("psychology_human", ["character-concept-comic"], "心理/职场/关系/伦理：固定角色承载隐喻"),
    ("data_numbers", ["data-viz"], "数据/排名/趋势：图表即主角"),
    ("geography_space", ["map-geo"], "地理/空间分布：地图即主角"),
    ("software_ui", ["ui-demo"], "软件操作：屏幕行为本身就是论据"),
    ("timeline_sequence", ["timeline-history"], "明确时间先后/演进：主轴线承载先后"),
    ("quote_definition", ["kinetic-typography"], "金句/定义/强观点：文字冲击即内容"),
    ("argument_opinion", ["swiss-sketch", "hand-sketch"], "抽象命题/对比/评论：网格线描承载论证"),
]

# 双轴融合规则：当强度最高的轴与第二轴同时成立时的特判
# (主导轴, 第二轴) -> (主风格, 理由)
BLEND_RULES: dict[tuple[str, str], tuple[str, str]] = {
    ("argument_opinion", "method_process"):
        ("hand-sketch", "论证+方法双主导：笔尖过程承载论证，比纯排版更有说服的温度"),
    ("history_archive", "real_evidence"):
        ("collage-evidence", "历史+真实证据双主导：档案照片是叙事本体"),
    ("data_numbers", "timeline_sequence"):
        ("data-viz", "数据+时间演进：趋势图天然承载时间轴，不必拆两套语法"),
}

STYLE_AXES: dict[str, list[str]] = {
    # style -> 支撑它的信号轴（顺序即权重优先级）
    "hand-sketch": ["method_process", "argument_opinion"],
    "swiss-sketch": ["argument_opinion", "method_process"],
    "whiteboard-tutorial": ["method_process", "quote_definition"],
    "collage-evidence": ["real_evidence", "history_archive"],
    "editorial-collage": ["history_archive", "real_evidence"],
    "timeline-history": ["timeline_sequence", "history_archive"],
    "paper-fold": ["system_structure", "science_nature"],
    "paper-diorama": ["system_structure", "science_nature"],
    "process-flow": ["system_structure", "method_process"],
    "character-concept-comic": ["psychology_human"],
    "data-viz": ["data_numbers"],
    "map-geo": ["geography_space"],
    "ui-demo": ["software_ui"],
    "kinetic-typography": ["quote_definition"],
    "generated-cinematic": [],
}

STYLE_NOTES: dict[str, str] = {
    "hand-sketch": "SVG 描边自绘 + 笔尖沿路径，手作温度适合观点/方法论证",
    "swiss-sketch": "网格大字黑红米白，适合冷静的对比与评论",
    "whiteboard-tutorial": "手写笔迹逐步推导，适合分步教学与算式演示",
    "collage-evidence": "真实照片/视频 + 撕纸拼贴证据墙，可信度即说服力",
    "editorial-collage": "编辑拼贴 + 档案标签，适合事件复盘与人物历史",
    "timeline-history": "主轴线 + 节点依次点亮，适合年表与演进",
    "paper-fold": "CSS 3D 折纸立体书，适合科普与结构演示",
    "paper-diorama": "层叠纸雕逐件装配，适合机制与生态",
    "process-flow": "节点连线逐段点亮，适合流程与分支",
    "character-concept-comic": "贯穿角色 + 分格漫画，适合心理与两难",
    "data-viz": "图表即主角，数值直接标注，适合数据叙事",
    "map-geo": "简化地图 + pin 与扩散圈，适合空间叙事",
    "ui-demo": "真实界面 + 光标走位，适合操作证据",
    "kinetic-typography": "超大字逐词入场，适合金句与宣言",
    "generated-cinematic": "生成式镜头，只做情绪点缀（默认不推荐作整片主风格）",
}


def extract_signals(text: str) -> tuple[dict[str, list[dict]], dict[str, int]]:
    """Return ({category: [{evidence, weight, source}]}, {category: strength})."""
    hits: dict[str, list[dict]] = {}
    strength: dict[str, int] = {}
    lower = text.lower()
    for cat, words in SIGNALS.items():
        for word, weight in words.items():
            count = lower.count(word.lower())
            if count:
                hits.setdefault(cat, []).append(
                    {"evidence": word, "weight": weight, "count": count, "source": "lexicon"}
                )
    for cat, pattern, weight, label in _REGEX_SIGNALS:
        matches = pattern.findall(text)
        if matches:
            shown = [m if isinstance(m, str) else m[0] for m in matches][:3]
            hits.setdefault(cat, []).append(
                {"evidence": "、".join(shown), "weight": weight, "count": len(matches), "source": label}
            )
    for cat, items in hits.items():
        # 强度：出现 ≥2 个强信号(权重2) → 2；1 个强信号或多个弱信号 → 1
        strong = sum(1 for h in items if h["weight"] == 2)
        strength[cat] = 2 if strong >= 2 else (1 if items else 0)
        if strong >= 1 and strength[cat] != 2:
            strength[cat] = max(strength[cat], 1)
    return hits, strength


def text_stats(text: str) -> dict:
    sentences = [s for s in re.split(r"[。！？!?\n]+", text) if s.strip()]
    questions = len(re.findall(r"[？？?]", text))
    numbers = len(re.findall(r"\d+", text))
    chars = len(re.sub(r"\s", "", text))
    avg_len = round(chars / max(len(sentences), 1), 1)
    return {
        "chars": chars,
        "sentences": len(sentences),
        "avg_sentence_chars": avg_len,
        "questions": questions,
        "numbers": numbers,
        "pacing_hint": (
            "短句多，节奏可快，适合逐词/逐句冲击"
            if avg_len <= 14
            else "中长句，节奏留出呼吸，适合边画边讲" if avg_len <= 30 else "长句多，需要更克制的视觉密度"
        ),
    }


def score_styles(strength: dict[str, int], text: str) -> list[dict]:
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for style, axes in STYLE_AXES.items():
        score, why = 0.0, []
        for axis in axes:
            s = strength.get(axis, 0)
            if s:
                score += s * (1.5 if axis == axes[0] else 1.0)
                why.append(f"{axis}={s}")
        scores[style] = score
        reasons[style] = why
    # 负向反证
    for style, penalty_map in ANTI_SIGNALS.items():
        for word, penalty in penalty_map.items():
            if word.lower() in text.lower():
                scores[style] = scores.get(style, 0) + penalty
                reasons.setdefault(style, []).append(f"反证：『{word}』{penalty}")
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {"style": style, "score": round(score, 2), "signals": reasons[style]}
        for style, score in ranked
        if score > 0
    ]


def recommend(text: str) -> dict:
    stats = text_stats(text)
    hits, strength = extract_signals(text)
    ranked = score_styles(strength, text)
    # 整片决策表：取强度最高且 >=1 的语义轴对应的主风格组
    axis_rank = sorted(strength.items(), key=lambda kv: kv[1], reverse=True)
    film_group, film_reason = [], ""
    for axis, s in axis_rank:
        if s < 1:
            continue
        for table_axis, styles, reason in FILM_DECISION_TABLE:
            if table_axis == axis:
                film_group, film_reason = styles, reason
                break
        if film_group:
            break
    if not film_group:
        film_group, film_reason = ["swiss-sketch", "hand-sketch"], "无强语义轴，回退到论证主导风格（swiss/hand-sketch）"
    # 双轴融合特判：主导轴+第二轴同时成立时按 BLEND_RULES 覆盖主风格
    blend = None
    if len(axis_rank) >= 2 and axis_rank[0][1] >= 1 and axis_rank[1][1] >= 1:
        rule = BLEND_RULES.get((axis_rank[0][0], axis_rank[1][0]))
        if rule:
            primary_blend, why_blend = rule
            if primary_blend in film_group:
                film_group = [primary_blend] + [s for s in film_group if s != primary_blend]
                film_reason = why_blend
                blend = True
    # 最终推荐 = 决策表主风格组 ∩ 信号评分榜的头部
    primary, runner_up = film_group[0], None
    if ranked:
        top_scored = ranked[0]["style"]
        if top_scored not in film_group:
            # 信号榜头名不在决策表组内：仍然给决策表风格，但标注竞争者
            runner_up = top_scored
        else:
            second = ranked[1]["style"] if len(ranked) > 1 else None
            runner_up = second if second and second not in film_group else (
                film_group[1] if len(film_group) > 1 else None)
    else:
        runner_up = film_group[1] if len(film_group) > 1 else None
    top3 = ranked[:3]
    evidence = {
        axis: [h["evidence"] + (f"×{h['count']}" if h["count"] > 1 else "")
               for h in items]
        for axis, items in hits.items()
    }
    return {
        "text_stats": stats,
        "semantic_signals": {
            axis: {"strength": strength[axis], "evidence": evidence.get(axis, [])}
            for axis, _ in axis_rank
        },
        "film_decision_table_hit": {"semantic_axis": axis_rank[0][0] if axis_rank else None,
                                    "group": film_group, "reason": film_reason,
                                    "blend_applied": bool(blend)},
        "style_scores": top3,
        "recommendation": {
            "primary": primary,
            "runner_up": runner_up,
            "why": STYLE_NOTES.get(primary, ""),
            "film_reason": film_reason,
            "note": (
                f"注意：信号评分头名 {runner_up} 与决策表组不一致，若该轴确为叙事核心，考虑以其为主风格"
                if runner_up and ranked and runner_up == ranked[0]["style"] else ""
            ),
        },
    }


def render_report(rec: dict) -> str:
    lines: list[str] = []
    stats = rec["text_stats"]
    lines.append("== 1. 文本统计 ==")
    lines.append(
        f"  {stats['chars']} 字 / {stats['sentences']} 句 / 平均句长 {stats['avg_sentence_chars']} 字"
        f" / 疑问句 {stats['questions']} / 数字 {stats['numbers']} 处"
    )
    lines.append(f"  节奏提示：{stats['pacing_hint']}")
    lines.append("")
    lines.append("== 2. 语义信号（强度 0-2，附原文证据）==")
    for axis, info in rec["semantic_signals"].items():
        ev = "、".join(info["evidence"][:6]) or "-"
        lines.append(f"  {axis:<18} 强度 {info['strength']}  证据：{ev}")
    lines.append("")
    hit = rec["film_decision_table_hit"]
    lines.append("== 3. 整片决策表命中 ==")
    lines.append(f"  主导轴：{hit['semantic_axis']}")
    lines.append(f"  主风格组：{' / '.join(hit['group'])}")
    lines.append(f"  理由：{hit['reason']}")
    lines.append("")
    lines.append("== 4. 风格评分（信号加权 Top3）==")
    for i, row in enumerate(rec["style_scores"], 1):
        sig = ", ".join(row["signals"]) or "-"
        lines.append(f"  {i}. {row['style']:<24} {row['score']:>5}  ({sig})")
    lines.append("")
    r = rec["recommendation"]
    lines.append("== 5. 推荐 ==")
    lines.append(f"  主风格：{r['primary']} —— {r['why']}")
    lines.append(f"  备选：{r['runner_up'] or '（无——文案语义高度单一，不需要备选）'}")
    if r["note"]:
        lines.append(f"  ⚠ {r['note']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--text", help="copy text inline")
    parser.add_argument("--file", type=Path, help="path to a .txt copy")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of report")
    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.file:
        text = args.file.read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.error("pass --text, --file, or pipe text on stdin")
        return 2

    text = text.strip()
    if len(text) < 10:
        print("ERROR: text too short to analyze (<10 chars)", file=sys.stderr)
        return 1

    rec = recommend(text)
    if args.json:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
    else:
        print(render_report(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
