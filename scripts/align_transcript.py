#!/usr/bin/env python3
"""align_transcript.py — 用文案原文校正 ASR 转写（时序留 ASR，文字用原文）。

ASR 的 ITN 与误字会污染下游两件事：字幕上屏的文字（「过去1年」「Arc save」）和
关键词提取（在错字上分词）。而旁白本来就是照着文案念的 —— 文案才是权威文本。

做法：对 (ASR 字符序列, 文案字符序列) 做 difflib 对齐，
  equal    → 沿用 ASR 时间戳
  replace  → 文案块按比例铺在 ASR 块的时间跨度上
  delete   → 丢掉 ASR 多出来的字符
  insert   → 文案多出来的字符插在边界时刻（零宽，随后由邻域时间插值补上）
相似度低于阈值则原样返回（拒绝把无关文本硬套上时间），保证不会为了「校正」而毁掉时序。

用法：
  align_transcript.py --transcript asr.json --text copy.txt --out fixed.json [--min-ratio 0.55]
输出 JSON 与 coli asr -j 同构：{text, tokens, timestamps, duration, ...}
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

SPACE_RE = re.compile(r"[\s\u3000]+")


def load_chars(path: Path) -> tuple[list[str], list[float]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tokens = list(data.get("tokens") or [])
    stamps = list(data.get("timestamps") or [])
    if len(stamps) != len(tokens):
        raise SystemExit(f"transcript tokens({len(tokens)}) 与 timestamps({len(stamps)}) 长度不一致")
    return tokens, [float(t) for t in stamps]


def align(tokens: list[str], stamps: list[float], text: str) -> tuple[list[str], list[float]]:
    target = list(SPACE_RE.sub("", text))
    matcher = difflib.SequenceMatcher(None, tokens, target, autojunk=False)
    ratio = matcher.ratio()
    if ratio < 0.55:
        return tokens, stamps
    out_t: list[str] = []
    out_s: list[float] = []

    def span(i1: int, i2: int) -> tuple[float, float]:
        """ASR 第 i1..i2-1 个 token 的时间跨度（用下一个 token 的起点收尾）。"""
        if i1 >= len(stamps):
            return (stamps[-1] if stamps else 0.0), (stamps[-1] if stamps else 0.0)
        start = stamps[i1]
        end = stamps[i2] if i2 < len(stamps) else (
            stamps[-1] + 0.3 if stamps else start + 0.3)
        return start, max(end, start)

    for op, a1, a2, b1, b2 in matcher.get_opcodes():
        if op == "equal":
            for k in range(b2 - b1):
                out_t.append(target[b1 + k])
                out_s.append(stamps[a1 + k])
        elif op == "replace":
            start, end = span(a1, a2)
            n = b2 - b1
            for k in range(n):
                out_t.append(target[b1 + k])
                out_s.append(start + (end - start) * k / max(n, 1))
        elif op == "insert":
            at = stamps[a1] if a1 < len(stamps) else (stamps[-1] if stamps else 0.0)
            for k in range(b2 - b1):
                out_t.append(target[b1 + k])
                out_s.append(at)
        # delete：ASR 多出来的字符直接丢
    # 时间戳单调化：插入的零宽字符继承左邻时刻，避免出现回声式倒流
    for i in range(1, len(out_s)):
        if out_s[i] < out_s[i - 1]:
            out_s[i] = out_s[i - 1]
    return out_t, [round(t, 3) for t in out_s]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--transcript", type=Path, required=True, help="ASR 转写 JSON（coli asr -j）")
    ap.add_argument("--text", type=Path, required=True, help="旁白文案原文（权威文本）")
    ap.add_argument("--out", type=Path, required=True, help="输出校正后的转写 JSON")
    ap.add_argument("--min-ratio", type=float, default=0.55, help="相似度阈值，低于则原样输出")
    args = ap.parse_args()

    raw = json.loads(args.transcript.read_text(encoding="utf-8"))
    tokens, stamps = load_chars(args.transcript)
    text = SPACE_RE.sub("", args.text.read_text(encoding="utf-8"))
    ratio = difflib.SequenceMatcher(None, tokens, list(text), autojunk=False).ratio()
    if ratio < args.min_ratio:
        print(f"对齐放弃：相似度 {ratio:.2f} < {args.min_ratio}（文案与转写不像同一段话）",
              file=sys.stderr)
        fixed_t, fixed_s = tokens, stamps
    else:
        fixed_t, fixed_s = align(tokens, stamps, text)
    out = {
        "text": "".join(fixed_t),
        "tokens": fixed_t,
        "timestamps": fixed_s,
        "duration": raw.get("duration") or (fixed_s[-1] if fixed_s else 0.0),
        "model": raw.get("model", ""),
        "lang": raw.get("lang", "zh"),
        "aligned_to_copy": True,
        "align_ratio": round(ratio, 4),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"对齐：相似度 {ratio:.3f} → {len(fixed_t)} tokens → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
