#!/usr/bin/env python3
"""make_video.py — 全流程编排器：任意文案 → 风格推荐（可审计决策链）→ 确认门 →
自动组装选定风格的 composition → 渲染 → 成片。

流程（对应 SKILL.md 生产管线）：
  1. recommend_style.recommend() 分析文案，打印完整决策链，写 storyboard/style-decision.json
  2. 确认门：无 --go 且无 --style 时停下（非交互默认 STOP，由 agent/用户确认后续跑）
  3. 旁白：--narration 优先；否则 edge_tts 可用时调 tts_edge.py；否则 exit 3 给出指引
  4. ASR：coli asr -j（或 --transcript 直供）+ --corrections 词级纠错
  5. 自动分镜：按标点切子句 → 6–8s 贪心归组 → 关键词滑窗提取 → derive_timing 落 beat
  6. 组装 composition：模板实例化（槽位填充 / id 命名空间 / 时间重映射）→ hyperframes lint
  7. 渲染 + 字幕 + final 合成 + verify（--no-render 可只到 lint）

Usage:
    python3 scripts/make_video.py --copy copy.txt --project outdir [--go] [--style hand-sketch]
        [--narration vo.mp3] [--transcript t.json] [--corrections "一只=一支"]
        [--aspect 9:16] [--fps 30] [--bgm music.mp3] [--speaker-hint "..."]
        [--no-render] [--keep-work]
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from recommend_style import recommend, render_report  # noqa: E402
from derive_timing import split_clauses, PUNCT  # noqa: E402
import validate_scenes  # noqa: E402

ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}
FPS_CHOICES = (24, 30, 60)

# 关键词滑窗禁用字（出自任务约定的停用字集）
STOPWORDS = set("的了是在和与或但就也把被将为到从对让使向往按据而且并还又再最很太更一个这那")
# 边缘字：量词/指代类字作首尾字时关键词不可读（如「次开会前」），直接排除
EDGE_CHARS = set("次件个位名篇帧轮步们某每各本该此之乎者呀吧吗呢")
CJK_RE = re.compile(r"[\u4e00-\u9fff]+")

# 整片调色板：15 种风格各一组 bg/fg/accent/muted（hand-sketch 为 showcase 实测值）
STYLE_PALETTES: dict[str, dict[str, str]] = {
    "hand-sketch":            {"background": "#F4EFE6", "foreground": "#11110F", "accent": "#E34234", "muted": "#8C887F"},
    "swiss-sketch":           {"background": "#F7F4EC", "foreground": "#11110F", "accent": "#D8341F", "muted": "#8C887F"},
    "whiteboard-tutorial":    {"background": "#FFFFFF", "foreground": "#1A1A1A", "accent": "#2F6FED", "muted": "#9AA0A6"},
    "collage-evidence":       {"background": "#EFE9DD", "foreground": "#1E1B16", "accent": "#C0392B", "muted": "#8A8375"},
    "editorial-collage":      {"background": "#F2EEE6", "foreground": "#17150F", "accent": "#B4552D", "muted": "#8C887F"},
    "timeline-history":       {"background": "#101418", "foreground": "#EDE7DA", "accent": "#E0A83A", "muted": "#6E7681"},
    "paper-fold":             {"background": "#F6F1E7", "foreground": "#26221C", "accent": "#D9683A", "muted": "#A89F8D"},
    "paper-diorama":          {"background": "#F3EDE2", "foreground": "#2A2620", "accent": "#3E8E5A", "muted": "#A79E8C"},
    "process-flow":           {"background": "#0F1216", "foreground": "#E8ECF1", "accent": "#37B3FF", "muted": "#6C7683"},
    "character-concept-comic": {"background": "#FFF8EC", "foreground": "#14120E", "accent": "#F25C3B", "muted": "#9C948A"},
    "data-viz":               {"background": "#0E1116", "foreground": "#EDF1F7", "accent": "#4CC38A", "muted": "#6B7684"},
    "map-geo":                {"background": "#EAF2F0", "foreground": "#16302B", "accent": "#E2703A", "muted": "#7C8F8A"},
    "ui-demo":                {"background": "#FFFFFF", "foreground": "#16181D", "accent": "#2F6FED", "muted": "#98A0AB"},
    "kinetic-typography":     {"background": "#0B0B0C", "foreground": "#F5F2EA", "accent": "#FF3B30", "muted": "#6E6E73"},
    "generated-cinematic":    {"background": "#101014", "foreground": "#ECECF0", "accent": "#C9A227", "muted": "#5E5E66"},
}

# 每种风格的通用 visualSubject 一句话（自动分镜缺省值）
STYLE_SUBJECTS: dict[str, str] = {
    "hand-sketch": "Hand-drawn strokes draw the core idea with a moving pen tip",
    "swiss-sketch": "Grid-typed headline and line-drawn argument on paper",
    "whiteboard-tutorial": "Whiteboard strokes derive the idea step by step",
    "collage-evidence": "Torn-paper evidence cards pin real photos with captions",
    "editorial-collage": "Editorial collage of archive clippings and labels",
    "timeline-history": "A milestone axis lights up node by node",
    "paper-fold": "A flat sheet folds into a layered paper diorama",
    "paper-diorama": "Layered paper-cut parts assemble into the mechanism",
    "process-flow": "Nodes and connectors light up along the pipeline",
    "character-concept-comic": "A recurring character enacts the tension in comic panels",
    "data-viz": "Bars and values rise into the key chart",
    "map-geo": "A simplified map places pins and ripple circles",
    "ui-demo": "A product screen demonstrates the operation with a cursor",
    "kinetic-typography": "Oversized words snap in one by one",
    "generated-cinematic": "A cinematic still holds atmosphere for the beat",
}

DEFAULT_VOICE = "zh-CN-YunjianNeural"

# 素材槽位（assets/media/photo-N.jpg）缺失时的内联占位（确定性、免外部文件、lint 干净）
PLACEHOLDER_SRC = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='320' height='420'>"
    "<rect width='100%25' height='100%25' fill='%23D8D2C4'/>"
    "<text x='50%25' y='50%25' font-family='monospace' font-size='22' fill='%238C887F' "
    "text-anchor='middle'>photo slot</text></svg>"
)


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print("+ " + " ".join(str(c) for c in cmd), file=sys.stderr)
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)


# ---------------------------------------------------------------------------
# 关键词提取：词边界模型（功能字不作词首/词尾）+ 边界强度 + 复现频率 + 词缀去重
# 目标：只要完整词与语义单元，不要「正能复现」这种跨词碎片
# ---------------------------------------------------------------------------

# 不能作词首的字：副词 / 连词 / 介词 / 能愿动词 / 代词指代
_CANNOT_START = set("的了地在得着过们呢吗吧啊嗯而且并或与和及以于在为对向从把被将让使给"
                    "能会要想要需可就是都也还很太更最又再才只仅既因如若虽其实正真已曾未不没别"
                    "好难却竟倒尤皆均亦尚仍另每这那某各个该此些何谁怎哪多")
# 不能作词尾的字：虚词 / 副词（名词短语不会以它们收尾）
_CANNOT_END = set("的了地在得着过们呢吗吧啊嗯而且并或与和及以于在为对向从把被将让使给"
                  "可很太更最都也就才只仅如若虽则不")
# 词内绝不允许出现的字：结构助词 / 语气词
_NEVER_INTERNAL = set("的了地得着过们呢吗吧啊嗯")
_FUNC_BOUNDARY = _CANNOT_START | _CANNOT_END  # 邻字为功能字 → 软词边界信号
# 单字修饰语：可与后词组成复合词（小+模型 → 小模型）
_MODIFIER_CHARS = set("大小新老微总高低温软硬云端单双多少前后内外长短")
# 数字/时间量词：不参与复合词（成本|三年 → 成本三年 这种语义歪接）
_TIME_CHARS = set("年月日周天倍成分秒")


def _shares_bigram(a: str, b: str) -> bool:
    """共享任意二字片段 → 语义重复（风格推荐 / 推荐风格）。"""
    if len(a) < 2 or len(b) < 2:
        return a in b or b in a
    grams = {a[i:i + 2] for i in range(len(a) - 1)}
    return any(b[i:i + 2] in grams for i in range(len(b) - 1))
# 泛义词：出现频率高但撑不起一个场景的关键词
_GENERIC_KW = {"开始", "结果", "时候", "东西", "什么", "怎么", "变成", "这些", "那些", "这样", "那样",
               "一个", "一种", "非常", "真正", "已经", "可以", "需要", "进行", "出现", "成为",
               "不是", "没有", "就是", "还是", "这个", "那个", "我们", "他们", "大家", "自己",
               "然后", "因为", "所以", "但是", "如果", "虽然", "同时", "目前", "现在", "过去",
               "未来", "以及", "或者", "并且", "因此", "于是", "其实", "只是", "全球", "更加"}
_LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]*")
_CJK_CHAR = re.compile(r"[\u4e00-\u9fff]")
LEXICON_PATH = ROOT / "assets" / "lexicon" / "zh-words.txt"
_LEX_CACHE: dict[str, int] | None = None


def load_lexicon() -> dict[str, int]:
    """词表（jieba dict.txt 裁剪 + 领域补充，MIT）。缺失时返回空 dict → 退化字符级启发式。"""
    global _LEX_CACHE
    if _LEX_CACHE is None:
        lex: dict[str, int] = {}
        if LEXICON_PATH.exists():
            for line in LEXICON_PATH.open(encoding="utf-8"):
                if line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) == 2:
                    try:
                        lex[parts[0]] = int(parts[1])
                    except ValueError:
                        pass
        _LEX_CACHE = lex
    return _LEX_CACHE


_ASCII_RUN_RE = re.compile(r"[A-Za-z0-9+#.\-]")
_SINGLE_CHAR_PENALTY = 8.0   # 单字词代价：避免「小/模/型」式碎切（与最长匹配等价地偏好完整词）
_LEN_BONUS = 1.2


def segment(text: str) -> list[tuple[str, int, int]]:
    """最大概率路径分词 → [(词, 起, 终)]：路径得分 = Σ(log(词频+1) + 长度奖励 − 单字罚)。
    非汉字串（AI / 2024 / c++）整体作一个 token。"""
    lex = load_lexicon()
    n = len(text)
    if not lex:
        return [(text[i:i + 1], i, i + 1) for i in range(n)]
    best = [0.0] * (n + 1)
    choice = [1] * n
    for i in range(n - 1, -1, -1):
        bscore, blen = None, 1
        if _ASCII_RUN_RE.match(text[i]):
            j = i
            while j < n and _ASCII_RUN_RE.match(text[j]):
                j += 1
            bscore, blen = math.log(80) + best[j], j - i
        else:
            for w in (4, 3, 2, 1):
                if i + w <= n and text[i:i + w] in lex:
                    sc = (math.log(lex[text[i:i + w]] + 1) + _LEN_BONUS * (w - 1)
                          - (_SINGLE_CHAR_PENALTY if w == 1 else 0) + best[i + w])
                    if bscore is None or sc > bscore:
                        bscore, blen = sc, w
            if bscore is None:
                bscore, blen = best[i + 1] - _SINGLE_CHAR_PENALTY, 1
        best[i] = bscore
        choice[i] = blen
    out: list[tuple[str, int, int]] = []
    i = 0
    while i < n:
        L = choice[i]
        out.append((text[i:i + L], i, i + L))
        i += L
    return out


def _is_content_word(word: str, lex: dict[str, int]) -> bool:
    if len(word) < 2 or not CJK_RE.fullmatch(word):
        return False
    if word in _GENERIC_KW or word in STOPWORDS:
        return False
    if word[0] in _CANNOT_START or word[-1] in _CANNOT_END:
        return False
    if any(c in STOPWORDS or c in _NEVER_INTERNAL for c in word):
        return False
    return not lex or word in lex


def _window_ok(text: str, i: int, w: int) -> bool:
    """候选窗口必须落在纯 CJK 段内，且首/尾/内部都不是功能字。"""
    win = text[i:i + w]
    if not CJK_RE.fullmatch(win):
        return False
    if win in _GENERIC_KW:
        return False
    if win[0] in _CANNOT_START or win[-1] in _CANNOT_END:
        return False
    if any(c in _NEVER_INTERNAL for c in win):
        return False
    if any(c in STOPWORDS for c in win):  # 内部含功能字（在/和/与/一…）
        return False
    return True


def _window_score(text: str, i: int, w: int) -> float:
    """边界强度（两侧硬边界=完整词）+ 长度 + 复现频率。"""
    n = len(text)
    left_hard = i == 0 or not CJK_RE.fullmatch(text[i - 1])
    right_hard = i + w >= n or not CJK_RE.fullmatch(text[i + w])
    left_soft = i > 0 and text[i - 1] in _FUNC_BOUNDARY
    right_soft = i + w < n and text[i + w] in _FUNC_BOUNDARY
    boundary = 1.0 * (left_hard + right_hard) + 0.4 * (left_soft + right_soft)
    freq = text.count(text[i:i + w])
    return boundary + 0.5 * (w - 2) + 1.2 * (freq - 1)


def keyword_spans(text: str, chosen: list[str], max_k: int = 2,
                  ban: list[tuple[int, int]] | None = None) -> list[tuple[str, int, int]]:
    """分词后按内容词选关键词：候选 = 单词 + 相邻双词复合（人工|智能 → 人工智能）。
    评分：词频（对数，封顶）+ 词长 + 本文复现次数；复合词额外加权（完整语义单元更耐读）。"""
    lex = load_lexicon()
    ban = ban or []
    toks = segment(text) if lex else [
        (text[i:i + w], i, i + w) for w in (2, 3, 4) for i in range(max(len(text) - w + 1, 0))]

    def wscore(word: str) -> float:
        return min(math.log(lex.get(word, 40) + 1), 6.5)

    counts: dict[str, int] = {}
    raw: list[tuple[str, int, int, float]] = []
    for idx, (w, s, e) in enumerate(toks):
        counts[w] = counts.get(w, 0) + 1
        if _is_content_word(w, lex):
            raw.append((w, s, e, wscore(w) + 0.7 * (len(w) - 2)))
        if idx + 1 < len(toks):
            w2, s2, e2 = toks[idx + 1]
            left_ok = _is_content_word(w2, lex) and (
                len(w) >= 2 and _is_content_word(w, lex)
                or (len(w) == 1 and w in _MODIFIER_CHARS and CJK_RE.fullmatch(w)))
            if left_ok and s2 == e and len(w) + len(w2) <= 5:
                comp = w + w2
                if (CJK_RE.fullmatch(comp) and comp not in _GENERIC_KW
                        and not any(c in STOPWORDS or c in _NEVER_INTERNAL for c in comp)
                        and not any(c in _TIME_CHARS for c in comp)):
                    raw.append((comp, s, e2,
                                wscore(w) + wscore(w2) + 0.7 * (len(comp) - 2) + 1.2))
    cands: list[tuple[float, int, str]] = []
    for w, s, e, base in raw:
        if any(s < b_e and e > b_s for b_s, b_e in ban):   # 数字 token 不作关键词
            continue
        if any(w in c or c in w for c in chosen):
            continue
        cands.append((-(base + 0.9 * (counts.get(w, 1) - 1)), s, w))
    for m in _LATIN_RE.finditer(text):
        tok = m.group(0)
        if len(tok) >= 2 and not any(tok.lower() in c.lower() for c in chosen):
            cands.append((-4.0, m.start(), tok))
    cands.sort()
    out: list[tuple[str, int, int]] = []
    for _, s, win in cands:
        if any(win in o for o, _, _ in out):
            continue
        if any(s < e and s + len(win) > st for _, st, e in out):
            continue
        # 共享二字片段（小模型/大模型、风格推荐/推荐风格）：语义重复，换个维度更丰富
        if any(len(win) >= 2 and _shares_bigram(win, o) for o, _, _ in out):
            continue
        out.append((win, s, s + len(win)))
        if len(out) >= max_k:
            break
    out.sort(key=lambda t: t[1])
    return out


def _unused_merge_left(kw: tuple[str, int, int], toks: list[tuple[str, int, int]],
                      lex: dict[str, int], max_len: int = 5) -> tuple[str, int, int]:
    """（已废弃：复合词改在候选阶段生成）向前合并相邻内容词。"""
    word, s, e = kw
    prev = [t for t in toks if t[2] == s and _is_content_word(t[0], lex)]
    if not prev:
        return kw
    pw, ps, _ = prev[-1]
    if len(pw) + len(word) <= max_len:
        return (pw + word, ps, e)
    return kw


def pick_keywords(text: str, chosen: list[str], max_k: int = 2,
                  ban: list[tuple[int, int]] | None = None) -> list[str]:
    kws = [w for w, _, _ in keyword_spans(text, chosen, max_k, ban)]
    if kws:
        return kws
    return _fallback_keywords(text, chosen, max_k, ban)


def _fallback_keywords(text: str, chosen: list[str], max_k: int,
                       ban: list[tuple[int, int]] | None = None) -> list[str]:
    """词表不可用时的字符窗口启发式（保留兼容）。"""
    n = len(text)
    ban = ban or []
    cands: list[tuple[float, int, str]] = []
    for w in (2, 3, 4):
        for i in range(0, max(n - w, 0) + 1):
            if not _window_ok(text, i, w):
                continue
            if any(i < be and i + w > bs for bs, be in ban):
                continue
            win = text[i:i + w]
            if any(win in c or c in win for c in chosen):
                continue
            cands.append((-_window_score(text, i, w), i, win))
    cands.sort()
    out, spans = [], []
    for _, i, win in cands:
        if any(win in o or o in win for o in out):
            continue
        if any(i < e and i + len(win) > s for s, e in spans):
            continue
        if any(win[-2:] == o[-2:] or win[:2] == o[:2] for o in out):
            continue
        out.append(win)
        spans.append((i, i + len(win)))
        if len(out) >= max_k:
            break
    return out


def label_before(text: str, pos: int, taken: list[tuple[int, int]]) -> str:
    """数值 token 前最近的内容词（如 3倍 → 增长；三成 → 复现），作图表类目锚点。"""
    lex = load_lexicon()
    best = ""
    if lex:
        for w, s, e in segment(text):
            if e > pos:
                break
            if not _is_content_word(w, lex):
                continue
            if w[-1] in "年月日周天分秒":   # 时间量词不做类目锚点
                continue
            if any(s < b_e and e > b_s for b_s, b_e in taken):
                continue
            best = w
    if best:
        return best
    for j in range(pos - 1, max(pos - 8, -1), -1):
        for w in (4, 3, 2):
            i = j - w + 1
            if i < 0:
                continue
            if any(i < e and j + 1 > s for s, e in taken):
                continue
            win = text[i:j + 1]
            if not CJK_RE.fullmatch(win) or win in _GENERIC_KW:
                continue
            if win[0] in _CANNOT_START or win[-1] in _CANNOT_END:
                continue
            if any(c in STOPWORDS for c in win):
                continue
            return win
    return ""


def group_clauses(clauses: list[dict]) -> list[list[dict]]:
    """6–8s 贪心归组：累计 <6s 继续并；尾句 <2s 并入上一场；硬上限 12s。"""
    groups: list[list[dict]] = []
    cur = [clauses[0]]
    for c in clauses[1:]:
        cur_dur = cur[-1]["endTime"] - cur[0]["stamps"][0]
        c_dur = c["endTime"] - c["stamps"][0]
        if cur_dur < 6.0 and cur_dur + c_dur <= 12.0:
            cur.append(c)
        else:
            groups.append(cur)
            cur = [c]
    groups.append(cur)
    if len(groups) > 1:
        last = groups[-1]
        last_dur = last[-1]["endTime"] - last[0]["stamps"][0]
        prev_dur = groups[-2][-1]["endTime"] - groups[-2][0]["stamps"][0]
        if last_dur < 2.0 and prev_dur + last_dur <= 12.0:
            groups[-2].extend(last)
            groups.pop()
    return groups


def clause_text(clause: dict) -> str:
    return "".join(t for t in clause["tokens"] if t not in PUNCT)


def join_clauses(texts: list[str]) -> str:
    """子句拼接用非汉字分隔符：防止分词把相邻子句的尾首词黏成一个复合词
    （交付|业主 跨逗号→「交付业主」），保证关键词落在单一子句内。"""
    return "\n".join(texts)


# ---------------------------------------------------------------------------
# 模板解析：fragment（<style>/<div>…</div>）+ 尾注里的 GSAP timeline JS + 全局 helper
# ---------------------------------------------------------------------------

def parse_template(style: str) -> dict:
    path = ROOT / "assets" / "templates" / "scenes" / f"{style}.html"
    if not path.exists():
        die(f"style template not found: {path}", 2)
    text = path.read_text(encoding="utf-8")

    marker_at = text.find("GSAP timeline fragment")
    if marker_at < 0:
        die(f"template {style}: no 'GSAP timeline fragment' marker — cannot assemble", 2)
    tstart = text.rfind("<!--", 0, marker_at)
    tend = text.find("-->", marker_at)
    if tstart < 0 or tend < 0:
        die(f"template {style}: trailing comment is malformed", 2)
    body = text[text.index("-->") + 3: tstart]

    # fragment = first <div>/<style> .. last </div> before the trailing comment
    fm = re.search(r"<(?:div|style)\b", body)
    if not fm:
        die(f"template {style}: no <div>/<style> fragment found", 2)
    fend = body.rfind("</div>")
    if fend < 0:
        die(f"template {style}: fragment has no closing </div>", 2)
    fragment = body[fm.start():fend + len("</div>")]

    # timeline JS lives after the marker line; helpers (function ...) hoisted once
    lines = text[tstart + 4:tend].splitlines()
    mi = next(i for i, ln in enumerate(lines) if "GSAP timeline fragment" in ln)
    js_start = next((i for i, ln in enumerate(lines[mi + 1:], mi + 1)
                     if re.match(r"\s*(tl\.|const |function )", ln)), None)
    if js_start is None:
        die(f"template {style}: no timeline JS found after the marker", 2)

    helpers: list[str] = []
    js_lines: list[str] = []
    i = js_start
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if re.match(r"function\s+\w+\s*\(", s):
            block = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() != "}":
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i])
            helpers.append("\n".join(block))
            i += 1
            continue
        # prose (CJK without // prefix) is dropped; JS and // comments kept
        if not s or s.startswith("//") or not any("\u4e00" <= c <= "\u9fff" for c in s):
            js_lines.append(ln)
        i += 1
    scene_js = "\n".join(js_lines).strip()
    if "tl." not in scene_js:
        die(f"template {style}: extracted timeline JS references no tl — "
            f"style not supported by make_video.py auto-assembly "
            f"(smoke-tested styles are listed in the skill report)", 2)
    return {"fragment": fragment, "helpers": "\n\n".join(helpers), "scene_js": scene_js}


def fill_slots(fragment: str, scene: dict, index: int, extra: dict | None = None) -> str:
    """{{SLOT}} 填充：HEADLINE 取首关键词/旁白前 10 字；POINT 取后续子句片段；
    图表槽位（TITLE/UNIT/BARS）由 extra 提供；其余置空。"""
    kws = [k["text"] for k in scene.get("keywords", [])]
    narr = scene.get("narration", "")
    parts = scene.get("_clauseTexts") or [narr]
    headline = kws[0] if kws else narr[:10]
    point1 = parts[1][:12] if len(parts) > 1 else (parts[0][:12] if parts and parts[0] != headline else "")
    point2 = parts[2][:12] if len(parts) > 2 else ""
    slots = {
        "HEADLINE": headline,
        "POINT_1": point1,
        "POINT_2": point2,
        "PHOTO_CAP": f"FIG. {index + 1:02d}",
    }
    if extra:
        slots.update(extra)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: slots.get(m.group(1), ""), fragment)


# ---------------- data-viz 图表数据（{{BARS}} 填充） ----------------
_CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_NUM_CLS = "零〇一二两三四五六七八九十"
_UNIT_MAG = {"千亿": 1e11, "万亿": 1e12, "百亿": 1e10, "十亿": 1e9, "亿": 1e8,
             "千万": 1e7, "百万": 1e6, "十万": 1e5, "万": 1e4, "千": 1e3}
_NUM_SCALE_RE = re.compile(  # 数字/中文数字 + 量级单位：五万、3亿、千亿级同理由 WORD 兽接
    r"(\d+(?:\.\d+)?|[" + _CN_NUM_CLS + r"]+)(千亿|万亿|百亿|十亿|千万|百万|十万|亿|万|千)")
_SCALE_WORD_RE = re.compile(r"(千亿|万亿|百亿|十亿|千万|百万|十万)")  # 单独出现的量级词（本身即数值）
_NUM_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?|[" + _CN_NUM_CLS + r"]+)\s*(成|倍|%|％)")
_YEAR_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?=年)")
_FALLBACK_HEIGHTS = [(36, 58, 86), (44, 62, 88), (30, 54, 82)]


def _cn_to_num(s: str) -> float | None:
    total, num = 0, 0
    for ch in s:
        if ch in _CN_DIGIT:
            num = _CN_DIGIT[ch]
        elif ch == "十":
            total += (num or 1) * 10
            num = 0
        else:
            return None
    return total + num


def _parse_num(s: str) -> float | None:
    if s[0].isdigit():
        return float(s)
    return _cn_to_num(s)


def extract_numbers(text: str) -> list[dict]:
    """从文案提取带量纲的数字 token（展示用原文，量值用可比较的 magnitude）。
    不提纯裸数字——无单位的数字填进图表是捏造。"""
    out: list[dict] = []
    taken: list[tuple[int, int]] = []

    def overlap(sp: tuple[int, int]) -> bool:
        return any(a < sp[1] and sp[0] < b for a, b in taken)

    def add(display: str, value: float, kind: str, sp: tuple[int, int]) -> None:
        out.append({"display": display, "value": value, "kind": kind,
                    "start": sp[0], "end": sp[1]})
        taken.append(sp)

    for m in _NUM_SCALE_RE.finditer(text):
        n = _parse_num(m.group(1))
        if n is not None:
            add(m.group(0), n * _UNIT_MAG[m.group(2)], "scale", m.span())
    for m in _SCALE_WORD_RE.finditer(text):
        if not overlap(m.span()):
            add(m.group(0), _UNIT_MAG[m.group(1)], "scale", m.span())
    for m in _NUM_UNIT_RE.finditer(text):
        if overlap(m.span()):
            continue
        n = _parse_num(m.group(1))
        if n is None:
            continue
        u = m.group(2)
        disp = m.group(1) + "%" if u in ("%", "％") else m.group(0)
        add(disp, n * 10 if u == "成" else n, "pct" if u != "倍" else "mult", m.span())
    return out


def _scene_title(scene: dict, kws: list[str]) -> str:
    """图表标题：关键词优先；无关键词时取最长≤14字的子句（剥年份前缀），不硬切半句。"""
    if kws:
        return kws[0]
    texts = scene.get("_clauseTexts") or [scene.get("narration", "")]
    cands = [re.sub(r"^(?:19|20)\d{2}年[，,]?", "", t).strip("，。,.、；;：: ") for t in texts]
    cands = [c for c in cands if c]
    good = [c for c in cands if len(c) <= 14]
    if good:
        return max(good, key=len)
    return (cands[0] if cands else "")[:14]


def chart_for_scene(scene: dict, index: int, data_spec: list | None) -> dict:
    """图表数据三级来源：--data 结构化覆盖 > 文案数字提取 > 关键词占位。"""
    texts = scene.get("_clauseTexts") or [scene.get("narration", "")]
    full = join_clauses(texts)
    kws = [k["text"] for k in scene.get("keywords", [])]
    chart = {
        "source": "extracted",
        "title": _scene_title(scene, kws),
        "unit": "",
        "labels": [],
        "values": [],       # [{display, value, kind}]
        "key": None,        # 强调柱下标
        "fallback": False,
    }
    if data_spec and index < len(data_spec) and data_spec[index]:
        d = data_spec[index]
        chart["source"] = "user-data"
        chart["fallback"] = False
        for k in ("title", "unit", "labels", "key"):
            if k in d and d[k] is not None:
                chart[k] = d[k]
        if d.get("values"):
            vals = d["values"]
            chart["values"] = [
                {"display": str(v), "value": float(v), "kind": "data"}
                if not isinstance(v, dict) else v for v in vals]
        if d.get("fallback"):
            chart["fallback"] = True
    if not chart["values"] and not chart["fallback"]:
        nums = extract_numbers(full)
        years = _YEAR_RE.findall(full)
        if len(nums) >= 2:
            chart["values"] = nums[:3]
            chart["key"] = len(chart["values"]) - 1  # 语义重心通常落在末值
        else:
            chart["fallback"] = True
            if len(nums) == 1:
                chart["single"] = nums[0]["display"]
        if len(years) >= 2:
            chart["years"] = years
    if not chart["labels"]:
        if chart.get("years") and len(chart["years"]) >= 2:
            chart["labels"] = list(chart["years"])          # 年份天然就是类目轴
        elif chart["values"]:
            taken_spans: list[tuple[int, int]] = []
            for ent in chart["values"]:
                sp = (ent.get("start", 0), ent.get("end", 0))
                lab = label_before(full, ent.get("start", 0), taken_spans)
                if lab and lab not in chart["labels"]:
                    chart["labels"].append(lab)
                    taken_spans.append(sp)
                else:
                    chart["labels"].append("")
        if not chart["labels"]:
            chart["labels"] = kws or ["起点", "变化", "关键"]
    kinds = {v.get("kind") for v in chart["values"]}
    if chart["fallback"]:
        chart["mode"] = "fallback"
    elif len(chart["values"]) >= 2 and len(kinds) > 1:
        chart["mode"] = "cards"        # 量纲不同：不做同一坐标轴比较，改指标卡
    else:
        chart["mode"] = "bars"
    return chart


def _slot_geometry(n: int) -> list[tuple[float, float]]:
    """柱位几何：柱宽 60/n%，柱心在 [4+w/2, 96−w/2] 内等距分布 → 任意 n 都铺满绘图区。"""
    width = 60.0 / n
    lo, hi = 4 + width / 2, 96 - width / 2
    centers = [50.0] if n == 1 else [lo + (hi - lo) * j / (n - 1) for j in range(n)]
    return [(c - width / 2, width) for c in centers]


def _is_negative(label: str) -> bool:
    return bool(label) and label[0] in "不没无否未别难"


def _card_html(display: str, label: str, is_key: bool) -> str:
    val_c = "var(--fg,#11110F)" if (is_key and _is_negative(label)) else (
        "var(--accent,#D8341F)" if is_key else "var(--fg,#11110F)")
    key_cls = " km-viz__bar--key" if is_key else ""
    return (
        '    <div class="km-viz__card" style="flex:1;background:rgba(127,127,127,.10);'
        'border-radius:20px;padding:40px 24px 32px;text-align:center;">\n'
        f'      <div class="km-viz__bar{key_cls}" style="height:8px;width:56%;margin:0 auto 28px;'
        f'background:{val_c};transform-origin:bottom center;"></div>\n'
        f'      <div class="km-viz__value" style="font:800 88px system-ui;line-height:1.05;color:{val_c};">'
        f'{display}</div>\n'
        f'      <div class="km-viz__label" style="margin-top:24px;font:700 32px system-ui;'
        f'color:var(--fg,#11110F);opacity:.78;">{label}</div>\n'
        '    </div>')


def render_bars(chart: dict, index: int) -> str:
    """生成柱体/数值/类目标堆 HTML（类名与模板 timeline fragment 的选择器对齐）。
    量纲不同的值（倍数 vs 百分比）不做同一坐标轴比较，改用指标卡。"""
    values = chart["values"]
    kinds = {v.get("kind") for v in values}
    if len(values) >= 2 and len(kinds) > 1:
        labels = list(chart["labels"]) + [""] * len(values)
        key = chart.get("key")
        cards = [_card_html(v["display"], labels[j], (key if key is not None else len(values) - 1) == j)
                 for j, v in enumerate(values)]
        return ('  <div class="km-viz__cards" style="position:absolute;left:8%;top:26%;width:84%;'
                'display:flex;gap:4%;align-items:stretch;">\n' + "\n".join(cards) + "\n  </div>")
    parts: list[str] = []
    vals = values
    if vals:
        n = len(vals)
        vmax = max(v["value"] for v in vals) or 1.0
        key = chart.get("key")
        labels_all = list(chart["labels"])[:n] + [""] * max(0, n - len(chart["labels"]))
        for j, (ent, (left, width)) in enumerate(zip(vals, _slot_geometry(n))):
            # 零基线线性比例（柱高必须与数值成正比，否则图表就在说谄）
            h = min(82.0, max(2.5, 82.0 * ent["value"] / vmax))
            is_key = (key if key is not None else n - 1) == j
            bar_cls = "km-viz__bar km-viz__bar--key" if is_key else "km-viz__bar"
            bar_bg = ("var(--fg,#11110F)" if _is_negative(labels_all[j])
                      else "var(--accent,#F36B3D)") if is_key else "var(--fg,#11110F)"
            val_c = "var(--fg,#11110F)" if is_key and _is_negative(labels_all[j]) else (
                "var(--accent,#D8341F)" if is_key else "var(--fg,#11110F)")
            parts.append(
                f'    <div class="km-viz__group" style="position:absolute;left:{left:.1f}%;bottom:3px;'
                f'width:{width:.1f}%;height:100%;display:flex;align-items:flex-end;justify-content:center;">\n'
                f'      <div class="{bar_cls}" data-value="{ent["display"]}" '
                f'style="width:70%;height:{h:.1f}%;background:{bar_bg};transform-origin:bottom;"></div>\n'
                f'    </div>\n'
                f'    <div class="km-viz__value" style="position:absolute;left:{left + width / 2:.1f}%;'
                f'bottom:{h + 4:.1f}%;transform:translateX(-50%);font:800 30px system-ui;color:{val_c};">'
                f'{ent["display"]}</div>')
        labels = list(chart["labels"])[:n] + [""] * max(0, n - len(chart["labels"]))
        for j, ((left, width), lab) in enumerate(zip(_slot_geometry(n), labels)):
            parts.append(
                f'    <div class="km-viz__label" style="position:absolute;left:{left:.1f}%;top:calc(100% + 16px);'
                f'width:{width:.1f}%;text-align:center;font:700 26px system-ui;color:var(--fg,#11110F);'
                f'opacity:.78;">{lab}</div>')
    else:  # 占位：柱高随场景序变化，不三场同图；类目用关键词
        hs = _FALLBACK_HEIGHTS[index % len(_FALLBACK_HEIGHTS)]
        kws = list(chart["labels"])[:3] + [""] * 3
        for j, (left, width) in enumerate(_slot_geometry(3)):
            h = hs[j]
            is_key = j == 2
            bar_cls = "km-viz__bar km-viz__bar--key" if is_key else "km-viz__bar"
            bar_bg = "var(--accent,#F36B3D)" if is_key else "var(--fg,#11110F)"
            parts.append(
                f'    <div class="km-viz__group" style="position:absolute;left:{left:.1f}%;bottom:3px;'
                f'width:{width:.1f}%;height:100%;display:flex;align-items:flex-end;justify-content:center;">\n'
                f'      <div class="{bar_cls}" style="width:70%;height:{h}%;background:{bar_bg};'
                f'transform-origin:bottom;"></div>\n'
                f'    </div>')
            if kws[j]:
                parts.append(
                    f'    <div class="km-viz__label" style="position:absolute;left:{left:.1f}%;top:calc(100% + 16px);'
                    f'width:{width:.1f}%;text-align:center;font:700 26px system-ui;color:var(--fg,#11110F);'
                    f'opacity:.78;">{kws[j]}</div>')
    return "\n".join(parts)


def namespace_ids(fragment: str, js: str, prefix: str) -> tuple[str, str]:
    """id="X" → id="p-X"；fragment 内 url(#X) 与 JS 里 "#x-y" 选择器同步改名。
    选择器匹配要求 id 含连字符（模板约定），避免误伤 #RRGGBB 颜色字面量。"""
    frag = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', fragment)
    frag = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}-{m.group(1)})", frag)
    js2 = re.sub(r'(["\'])#([A-Za-z][A-Za-z0-9]*-[A-Za-z0-9-]*)',
                 lambda m: f"{m.group(1)}#{prefix}-{m.group(2)}", js)
    return frag, js2


POS_PARAM_RE = re.compile(r",\s*(\d+(?:\.\d+)?)\s*\)")


def remap_times(js: str, start: float, end: float) -> str:
    """把模板的 scene-relative 位置参数线性映射到 [start+0.1, end-hold]（时长参数不动）。"""
    hold = min(1.5, 0.25 * (end - start))
    a, b = start + 0.1, end - hold
    if b - a < 1.0:  # 极短场景兜底：留出进场与收尾
        a, b = start + 0.05, end - 0.05
    matches = list(POS_PARAM_RE.finditer(js))
    times = sorted({float(m.group(1)) for m in matches})
    if not times:
        return js
    t0, t1 = times[0], times[-1]

    def mapt(t: float) -> float:
        if t1 <= t0:
            return a
        return a + (t - t0) * (b - a) / (t1 - t0)

    out = js
    for m in reversed(matches):
        out = out[:m.start(1)] + f"{mapt(float(m.group(1))):.2f}" + out[m.end(1):]
    return out


def resolve_asset_srcs(fragment: str, comp_dir: Path, project: Path) -> str:
    """素材槽位解析：composition 内已有 → 原样；project/assets/media 有（fetch_assets 下载）
    → 改指 ../assets/media/；都缺 → 内联 SVG 占位（模板 onerror/CSS 兑底依然成立）。"""

    def repl(m: re.Match) -> str:
        src = m.group(1)
        name = src.split("/")[-1]
        if (comp_dir / src).exists():
            return m.group(0)
        if (project / "assets" / "media" / name).exists():
            return f'src="../assets/media/{name}"'
        return f'src="{PLACEHOLDER_SRC}"'

    return re.sub(r'src="(assets/media/[^"]+)"', repl, fragment)


def indent_block(text: str, pad: str = "    ") -> str:
    return "\n".join(pad + ln if ln.strip() else ln for ln in text.splitlines())


def build_composition(project: Path, manifest: dict, style: str, title: str) -> Path:
    """组装 composition/index.html（wrapper 约定对齐 showcase gold standard）。"""
    tpl = parse_template(style)
    proj = manifest["project"]
    scenes = manifest["scenes"]
    w, h, dur = proj["width"], proj["height"], round(proj["durationSec"], 2)
    pal = STYLE_PALETTES[style]
    comp_id = f"mv-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{style}"

    comp_dir = project / "composition"
    comp_dir.mkdir(parents=True, exist_ok=True)
    vendor_src = ROOT / "examples" / "showcase-project" / "composition" / "vendor"
    vendor_dst = comp_dir / "vendor"
    if vendor_src.exists() and not vendor_dst.exists():
        shutil.copytree(vendor_src, vendor_dst)

    sections = [
        f'  <!-- ============ furniture · 0–{dur}s · track 0 ============ -->',
        f'  <section class="clip" id="furniture-base" data-start="0" data-duration="{dur}" data-track-index="0">',
        '    <div class="fu-meta"><span>KNOWLEDGE / MOTION</span>'
        f'<span>{style.upper()} · {dur}s</span></div>',
        '    <div class="fu-rule" id="fu-rule"></div>',
        '  </section>',
    ]
    js_blocks: list[str] = []
    charts: list[dict] = []
    data_spec = manifest.pop("_dataSpec", None)
    for i, sc in enumerate(scenes, 1):
        sid = sc["id"]
        start, sdur = round(sc["startSec"], 2), round(sc["durationSec"], 2)
        extra: dict = {}
        if "{{BARS}}" in tpl["fragment"]:
            chart = chart_for_scene(sc, i - 1, data_spec)
            charts.append({"scene": sid, "mode": chart.get("mode", "bars"),
                           **{k: chart[k] for k in
                              ("source", "title", "unit", "labels", "key", "fallback")},
                           "values": [v.get("display", "") for v in chart["values"]]})
            extra = {"TITLE": chart["title"], "UNIT": chart["unit"],
                     "BARS": render_bars(chart, i - 1)}
        frag = fill_slots(tpl["fragment"], sc, i - 1, extra)
        frag = resolve_asset_srcs(frag, comp_dir, project)
        frag, sc_js = namespace_ids(frag, tpl["scene_js"], sid)
        sc_js = remap_times(sc_js, start, start + sdur)
        sections += [
            f'  <!-- ============ {sid} · {start}–{round(start + sdur, 2)}s ============ -->',
            f'  <section class="clip" id="clip-{sid}" data-start="{start}" '
            f'data-duration="{sdur}" data-track-index="1">',
            indent_block(frag),
            '  </section>',
        ]
        js_blocks.append(f"  {{ /* {sid} · {start}-{round(start + sdur, 2)}s */\n"
                         f"{indent_block(sc_js, '    ')}\n  }}")

    helpers = tpl["helpers"]
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width={w}, height={h}" />
  <title>{title} · {style} visual master · {dur}s</title>
  <script src="vendor/gsap.min.js"></script>
  <style>
    @font-face {{ font-family: 'PingFang SC'; src: local('PingFang SC'); }}
    @font-face {{ font-family: 'Noto Sans SC'; src: local('Noto Sans SC'); }}
    :root {{ --bg:{pal['background']}; --fg:{pal['foreground']}; --accent:{pal['accent']}; --muted:{pal['muted']}; }}
    * {{ box-sizing:border-box; }}
    html, body {{ margin:0; width:{w}px; height:{h}px; overflow:hidden; background:var(--bg); color:var(--fg); font-family:"PingFang SC","Noto Sans SC",sans-serif; }}
    #root {{ position:relative; width:{w}px; height:{h}px; overflow:hidden; }}
    .clip {{ position:absolute; inset:0; overflow:hidden; background:var(--bg); }}
    .fu-meta {{ position:absolute; top:86px; left:72px; right:72px; display:flex; justify-content:space-between; font:700 24px ui-monospace,SFMono-Regular,monospace; color:var(--muted); letter-spacing:.12em; }}
    .fu-rule {{ position:absolute; left:72px; right:72px; top:145px; height:4px; background:var(--accent); transform-origin:left center; }}
  </style>
</head>
<body>
<div id="root" data-composition-id="{comp_id}" data-start="0" data-width="{w}" data-height="{h}" data-duration="{dur}">
{chr(10).join(sections)}
</div>

<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused:true }});
{('  ' + helpers.replace(chr(10), chr(10) + '  ')) if helpers else ''}
  /* ============ furniture ============ */
  tl.fromTo('#fu-rule', {{ scaleX:0 }}, {{ scaleX:1, duration:.5, ease:'power3.out' }}, .15);

{chr(10).join(js_blocks)}

  window.__timelines['{comp_id}'] = tl;
</script>
</body>
</html>
"""
    out = comp_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    manifest["_charts"] = charts
    return out


# ---------------------------------------------------------------------------
# 各步骤
# ---------------------------------------------------------------------------

def step_recommend(text: str, project: Path, chosen: str | None) -> tuple[dict, str]:
    rec = recommend(text)
    print(render_report(rec))
    sb = project / "storyboard"
    sb.mkdir(parents=True, exist_ok=True)
    primary = rec["recommendation"]["primary"]
    decision = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "chosen_style": chosen or primary,
        "chosen_by": "user(--style)" if chosen else "auto(recommendation primary)",
        "recommendation": rec,
    }
    (sb / "style-decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n决策链已写入 {sb / 'style-decision.json'}")
    return rec, decision["chosen_style"]


def gate(chosen: str) -> None:
    print("\n== 确认门（STOP）==")
    print(f"  推荐风格：{chosen}")
    print("  下一步：确认风格后追加 --go 重跑，或 --style <名> 覆盖推荐。")
    print("  例：python3 scripts/make_video.py --copy copy.txt --project outdir "
          f"--go --style {chosen}")


def step_narration(args, project: Path, copy_path: Path) -> Path | None:
    audio_dir = project / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    narr = audio_dir / "narration.mp3"
    if args.transcript and args.no_render:
        # 转写直供 + 不渲染：旁白音频只服务 finalize，可整体跳过（冒烟/组装检查路径）
        print("旁白：--transcript + --no-render，跳过旁白音频生成")
        return None
    if args.narration:
        suffix = args.narration.suffix or ".mp3"
        narr = audio_dir / f"narration{suffix}"
        if args.narration.resolve() != narr.resolve():
            shutil.copy(args.narration, narr)
        print(f"旁白：使用 --narration → {narr}")
        return narr
    try:
        import importlib.util
        if importlib.util.find_spec("edge_tts") is None:
            raise ImportError
    except ImportError:
        die(
            "未提供 --narration 且 edge_tts 不可用。\n"
            "  调用方（AI agent）请用自己的 TTS 工具生成旁白音频后重跑并传 --narration <mp3>；\n"
            "  或先 pip install edge-tts 再重跑（将默认使用 tts_edge.py，"
            f"voice={DEFAULT_VOICE}）。", 3)
    (project / "script").mkdir(parents=True, exist_ok=True)
    (project / "script" / "narration.md").write_text(copy_path.read_text(encoding="utf-8"),
                                                     encoding="utf-8")
    proc = run([sys.executable, SCRIPTS / "tts_edge.py",
                "--text-file", project / "script" / "narration.md",
                "--voice", DEFAULT_VOICE, "--out-dir", audio_dir])
    if proc.returncode != 0 or not narr.exists():
        die(f"tts_edge.py failed:\n{proc.stderr.strip()}", 1)
    print(f"旁白：edge-tts 生成 → {narr}")
    return narr


def step_transcript(args, project: Path, narration: Path | None) -> Path:
    (project / "script").mkdir(parents=True, exist_ok=True)
    out = project / "script" / "transcript.json"
    if args.transcript:
        if args.transcript.resolve() != out.resolve():
            shutil.copy(args.transcript, out)
        print(f"转写：使用 --transcript → {out}")
    else:
        if narration is None:
            die("需要旁白音频才能跑 coli asr；或改用 --transcript 提供现成转写", 2)
        if shutil.which("coli") is None:
            die("coli 命令不存在且未提供 --transcript；"
                "请用 --transcript 提供词级转写 JSON（tokens+timestamps）", 2)
        proc = run(["coli", "asr", "-j", narration])
        if proc.returncode != 0:
            die(f"coli asr failed:\n{proc.stderr.strip()}", 1)
        out.write_text(proc.stdout, encoding="utf-8")
        print(f"转写：coli asr → {out}")

    # --corrections 词级纠错：bad=good，精确匹配 token 后替换
    if args.corrections:
        data = json.loads(out.read_text(encoding="utf-8"))
        pairs = [p.split("=", 1) for p in args.corrections.split(",") if "=" in p]
        tokens = data.get("tokens", [])
        fixed = 0
        for bad, good in pairs:
            fixed += sum(1 for i, t in enumerate(tokens) if t == bad)
            tokens = [good if t == bad else t for t in tokens]
        data["tokens"] = tokens
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"纠错：--corrections 共替换 {fixed} 个 token")
    return out


def step_storyboard(args, project: Path, transcript: Path, text: str, style: str) -> dict:
    tr = json.loads(transcript.read_text(encoding="utf-8"))
    tokens, stamps = tr["tokens"], tr["timestamps"]
    clauses = split_clauses(tokens, stamps)
    if not clauses:
        die("transcript 切不出任何子句（tokens 为空？）", 2)
    groups = group_clauses(clauses)

    # 关键词：逐场滑窗提取，跨场景去重；并映射回所属子句供 derive_timing 定位
    chosen: list[str] = []
    spec_clauses: list[dict] = []
    scene_meta: list[dict] = []
    for gi, grp in enumerate(groups):
        sid = f"s{gi + 1:02d}"
        texts = [clause_text(c) for c in grp]
        joined = join_clauses(texts)
        ban = [(e["start"], e["end"]) for e in extract_numbers(joined)]  # 数字 token 不作关键词
        kws = pick_keywords(joined, chosen, ban=ban)
        chosen.extend(kws)
        for c, t in zip(grp, texts):
            entry: dict = {"scene": sid, "text": t}
            hit = [k for k in kws if k in t]
            if hit:
                entry["keywords"] = hit
            spec_clauses.append(entry)
        scene_meta.append({"id": sid, "texts": texts, "keywords": kws})

    tmp = tempfile.mkdtemp(prefix="make-video-")
    try:
        spec_path = Path(tmp) / "clauses-spec.json"
        spec_path.write_text(json.dumps({"clauses": spec_clauses}, ensure_ascii=False),
                             encoding="utf-8")
        timing_out = Path(tmp) / "timing.json"
        proc = run([sys.executable, SCRIPTS / "derive_timing.py",
                    "--transcript", transcript, "--spec", spec_path, "--out", timing_out])
        if proc.returncode != 0:
            die(f"derive_timing failed:\n{proc.stderr.strip()}", 2)
        timing = json.loads(timing_out.read_text(encoding="utf-8"))
    finally:
        if not args.keep_work:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print(f"temp kept: {tmp}", file=sys.stderr)

    width, height = ASPECTS[args.aspect]
    safe = {
        "x": round(width * 0.067),
        "y": round(height * 0.8176),
        "width": round(width * 0.8667),
        "height": round(height * 0.12),
    }
    pal = STYLE_PALETTES[style]
    total = round(timing["scenes"][-1]["startSec"] + timing["scenes"][-1]["durationSec"], 2)

    scenes_out: list[dict] = []
    for meta, tsc in zip(scene_meta, timing["scenes"]):
        sdur = float(tsc["durationSec"])
        kws = tsc.get("keywords", [])
        beats = [{"atSec": 0.1, "action": "template opening beat"}]
        for k in kws:
            beats.append({"atSec": min(float(k["atSec"]), round(sdur - 0.05, 2)),
                          "action": f"keyword 「{k['text']}」 lands on the spoken token"})
        scenes_out.append({
            "id": tsc["id"],
            "startSec": tsc["startSec"],
            "durationSec": tsc["durationSec"],
            "narration": tsc.get("clauseText", "".join(meta["texts"])),
            "keywords": kws,
            "purpose": "auto",
            "semanticClass": "auto",
            "style": style,
            "visualSubject": STYLE_SUBJECTS[style],
            "visualVerb": "auto",
            "layout": "template",
            "camera": "locked-frame",
            "transitionIn": "hard-cut",
            "transitionOut": "hard-cut",
            "assets": [],
            "beats": beats,
            "finalState": f"Resolved template state holds {min(1.5, 0.25 * sdur):.1f}s",
            "renderer": "hyperframes",
            "_clauseTexts": meta["texts"],
        })

    manifest = {
        "version": 1,
        "project": {
            "title": re.split(r"[。！？!?\n]", text.strip())[0][:24] or "make-video",
            "language": "zh-CN",
            "width": width,
            "height": height,
            "fps": args.fps,
            "durationSec": total,
            "style": style,
            "captionSafeArea": safe,
        },
        "design": {
            **pal,
            "displayFont": "Noto Sans SC",
            "bodyFont": "Noto Sans SC",
        },
        "timing": {"method": "make_video.py auto"},
        "scenes": scenes_out,
    }
    for sc in manifest["scenes"]:
        sc.pop("_clauseTexts", None)
        # 保留 clauseTexts 供槽位填充：单独放回（不写入 scenes.json）
    # 槽位填充需要的子句片段临时存一份（写盘前剔除）
    clause_map = {m["id"]: m["texts"] for m in scene_meta}
    (project / "storyboard").mkdir(parents=True, exist_ok=True)
    out = project / "storyboard" / "scenes.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errors = validate_scenes.validate(out)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        die("scenes.json 校验失败", 2)
    print(f"分镜：{len(scenes_out)} 场 / {total}s → {out}（validate_scenes OK）")
    manifest["_clauseMap"] = clause_map
    return manifest


def lint_composition(comp_dir: Path) -> tuple[int, str]:
    proc = run(["node", ROOT / "node_modules" / ".bin" / "hyperframes",
                "lint", comp_dir], cwd=ROOT)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--copy", type=Path, required=True, help="文案文件（.txt）")
    ap.add_argument("--project", type=Path, required=True, help="输出项目目录")
    ap.add_argument("--style", choices=sorted(STYLE_PALETTES), help="显式指定风格（跳过推荐采用，但仍打印决策链）")
    ap.add_argument("--go", action="store_true", help="通过确认门继续执行")
    ap.add_argument("--narration", type=Path, help="现成旁白音频（优先）")
    ap.add_argument("--transcript", type=Path, help="现成词级转写 JSON（tokens+timestamps），跳过 coli asr")
    ap.add_argument("--corrections", default="", help='ASR 词级纠错，如 "一只=一支,语意=语义"')
    ap.add_argument("--aspect", choices=ASPECTS, default="9:16")
    ap.add_argument("--fps", type=int, choices=FPS_CHOICES, default=30)
    ap.add_argument("--bgm", type=Path, help="背景音乐（finalize 时 0.18 音量混入）")
    ap.add_argument("--speaker-hint", default="", help="配音音色提示（记录进 BRIEF，供 TTS 环节参考）")
    ap.add_argument("--data", type=Path, help="图表数据 JSON（数组，按场景序："
                   "[{title,unit,labels:[…],values:[…],key}]），覆盖文案自动提取")
    ap.add_argument("--no-render", action="store_true", help="只组装 + lint（跳过渲染与 final 合成）")
    ap.add_argument("--keep-work", action="store_true", help="不清理临时文件")
    args = ap.parse_args()

    text = args.copy.read_text(encoding="utf-8").strip()
    if len(text) < 10:
        die("文案太短（<10 字），无法分析", 1)
    project = args.project.expanduser().resolve()
    project.mkdir(parents=True, exist_ok=True)

    # 1. 推荐 + 决策链
    rec, chosen = step_recommend(text, project, args.style)

    # 2. 确认门：无 --go 且未显式 --style → 非交互默认停下
    if not args.go and not args.style:
        gate(chosen)
        return 0

    # 3. 风格确认 + 模板存在性
    style = args.style or chosen
    if not (ROOT / "assets" / "templates" / "scenes" / f"{style}.html").exists():
        die(f"assets/templates/scenes/{style}.html 不存在", 2)
    print(f"\n== 风格锁定：{style} ==")

    # 4. 脚手架 + 调色板覆盖 + BRIEF 补充
    title = re.split(r"[。！？!?\n]", text)[0][:24] or "make-video"
    proc = run([sys.executable, SCRIPTS / "scaffold_project.py", project,
                "--title", title, "--aspect", args.aspect, "--fps", args.fps])
    if proc.returncode != 0:
        die(f"scaffold failed:\n{proc.stderr.strip()}", 1)
    with (project / "BRIEF.md").open("a", encoding="utf-8") as f:
        f.write(f"- Style: {style} (chosen_by: {'user' if args.style else 'auto'})\n")
        if args.speaker_hint:
            f.write(f"- Speaker hint: {args.speaker_hint}\n")
        f.write(f"- Generated by: make_video.py\n")

    # 5. 旁白（--transcript + --no-render 时可跳过）
    narration = step_narration(args, project, args.copy)

    # 6. ASR / 转写 + 纠错
    transcript = step_transcript(args, project, narration)

    # 7. 自动分镜
    manifest = step_storyboard(args, project, transcript, text, style)
    clause_map = manifest.pop("_clauseMap", {})
    for sc in manifest["scenes"]:
        sc["_clauseTexts"] = clause_map.get(sc["id"], [sc.get("narration", "")])
    data_spec = None
    if args.data:
        data_spec = json.loads(args.data.read_text(encoding="utf-8"))
        manifest["_dataSpec"] = data_spec

    # 8. 组装 composition + lint
    comp = build_composition(project, manifest, style, title)
    charts = manifest.pop("_charts", [])
    if charts:
        charts_path = project / "storyboard" / "charts.json"
        charts_path.write_text(json.dumps(charts, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(f"\n== 组装 composition → {comp} ==")
    code, output = lint_composition(comp.parent)
    print(output)
    if code != 0 or re.search(r"[1-9]\d* error", output):
        die("hyperframes lint 报错（见上），composition 未达标", 2)
    for sc in manifest["scenes"]:
        sc.pop("_clauseTexts", None)

    # 9. 渲染 + 字幕 + final + verify
    if not args.no_render:
        renders = project / "renders"
        renders.mkdir(exist_ok=True)
        master = renders / "visual-master.mp4"
        proc = run(["node", ROOT / "node_modules" / ".bin" / "hyperframes", "render",
                    comp.parent, "--output", master, "--fps", str(args.fps), "--quiet"],
                   cwd=ROOT)
        if proc.returncode != 0 or not master.exists():
            die(f"hyperframes render failed:\n{proc.stderr.strip()}", 1)
        captions = project / "captions"
        proc = run([sys.executable, SCRIPTS / "build_captions.py",
                    "--transcript", transcript, "--scenes", project / "storyboard" / "scenes.json",
                    "--out-dir", captions])
        if proc.returncode != 0:
            die(f"build_captions failed:\n{proc.stderr.strip()}", 1)
        cmd = [sys.executable, SCRIPTS / "finalize.py", "--visual", master,
               "--captions", captions / "captions.ass",
               "--out", renders / "final.mp4"]
        if narration is not None:
            cmd += ["--narration", narration]
        if args.bgm:
            cmd += ["--bgm", args.bgm]
        proc = run(cmd)
        if proc.returncode != 0:
            die(f"finalize failed:\n{proc.stderr.strip()}", 1)
        proc = run([sys.executable, SCRIPTS / "verify.py", project])
        print(proc.stdout)
        if proc.returncode != 0:
            die("verify 未通过（见上）", 1)

    # 10. 汇总报告
    print("\n== 成片报告 ==")
    print(f"  风格：{style} —— {rec['recommendation']['why']}")
    print(f"  {'id':<6}{'start':>8}{'dur':>8}  keywords")
    for sc in manifest["scenes"]:
        kws = "、".join(k["text"] for k in sc["keywords"]) or "-"
        print(f"  {sc['id']:<6}{sc['startSec']:>8.2f}{sc['durationSec']:>8.2f}  {kws}")
    print("  产物：")
    for rel in ("storyboard/style-decision.json", "storyboard/scenes.json",
                "storyboard/charts.json", "script/transcript.json", "composition/index.html",
                "renders/visual-master.mp4", "renders/final.mp4"):
        p = project / rel
        if p.exists():
            print(f"    {p}")
    for p in sorted((project / "audio").glob("narration.*")):
        print(f"    {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
