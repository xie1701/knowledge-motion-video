#!/usr/bin/env python3
"""derive_timing.py — 从词级 ASR 时间戳推导场景边界与关键词 beat。

规则（v2.3 旁白时钟硬约束，见 research/v23-design.md §2）：
  - 场景边界 = 相邻子句之间停顿区间的中点（子句尾标点 → 下一子句首词）；
  - 关键词 beat = 该词 token 起始时间（scene-relative）；
  - 严禁把切场放进语音中间：边界必须落在停顿区间内。

输入：coli asr -j 的 JSON + 一个场景定义文件（YAML-ish JSON，手工声明子句分组与关键词）。
场景定义格式（与 ASR 切出的子句一一对应，连续同 scene 自动归组为一个场景）：
  {
    "clauses": [
      {"scene": "s01", "keywords": ["文案"], "text": "可选校验文本"},
      {"scene": "s01", "keywords": ["知识视频"]},
      ...
    ]
  }

输出：JSON 片段 {"scenes": [{"id","startSec","durationSec","keywords":[{text,atSec}], "clauseText"}]}
直接可贴进 scenes.json。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PUNCT = set("，。？！、：；,.")
FILLER = {"的", "之"}   # 复合关键词可以跨过修饰助词（论文|的|数量 → 论文数量）


def find_keyword(tokens: list[str], word: str) -> int | None:
    """在 token 序列里定位关键词起点：先找连续匹配，再允许跨过「的/之」。"""
    for j in range(len(tokens)):
        if "".join(tokens[j:j + len(word)]) == word:
            return j
    for j in range(len(tokens)):
        k, pos, skipped = j, 0, False
        while k < len(tokens) and pos < len(word):
            tok = tokens[k]
            if tok in FILLER:
                k += 1
                skipped = True
                continue
            if word.startswith(tok, pos):
                pos += len(tok)
                k += 1
                continue
            break
        if pos == len(word) and skipped:
            return j
    return None


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def split_clauses(tokens: list[str], stamps: list) -> list[dict]:
    """按标点切子句；返回 [{tokens, stamps, endTime, nextStart}]。"""
    clauses, cur_t, cur_s = [], [], []
    for tok, st in zip(tokens, stamps):
        t = float(st if not isinstance(st, (list, tuple)) else st[0])
        cur_t.append(tok)
        cur_s.append(t)
        if tok in PUNCT:
            clauses.append({"tokens": cur_t, "stamps": cur_s, "endTime": t})
            cur_t, cur_s = [], []
    if cur_t:
        clauses.append({"tokens": cur_t, "stamps": cur_s, "endTime": float(stamps[-1])})
    return clauses


def split_one(clause: dict, word: str) -> list[dict]:
    """在子句内 word 首次出现处切成两段（用于 ASR 未打标点的真实停顿处）。"""
    toks, sts = clause["tokens"], clause["stamps"]
    for j in range(len(toks) - len(word) + 1):
        if "".join(toks[j:j + len(word)]) == word and j > 0:
            return [
                {"tokens": toks[:j], "stamps": sts[:j], "endTime": sts[j - 1]},
                {"tokens": toks[j:], "stamps": sts[j:], "endTime": clause["endTime"]},
            ]
    return [clause]


def main() -> int:
    ap = argparse.ArgumentParser(description="从 ASR 词级时间戳推导场景边界与 beat")
    ap.add_argument("--transcript", required=True, help="coli asr -j JSON")
    ap.add_argument("--spec", required=True, help="clauses 场景定义 JSON")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    tr = load(Path(args.transcript))
    spec = load(Path(args.spec))
    tokens, stamps = tr["tokens"], tr["timestamps"]
    clauses = split_clauses(tokens, stamps)
    declared = spec["clauses"]
    if len(clauses) != len(declared):
        print(f"ERROR: ASR 切出 {len(clauses)} 个子句，但 spec 声明了 {len(declared)} 个",
              file=sys.stderr)
        for i, c in enumerate(clauses):
            print(f"  [{i}] {''.join(c['tokens'])}", file=sys.stderr)
        return 1
    # 子句内切分（splitBefore）：处理 ASR 漏标点的真实停顿；
    # 切分后段继承下一条声明（前段属于本条 scene，后段属于下一 scene）
    pairs = []
    for i, (c, d) in enumerate(zip(clauses, declared)):
        if d.get("splitBefore"):
            parts = split_one(c, d["splitBefore"])
            pairs.append((parts[0], d))
            nxt = declared[i + 1] if i + 1 < len(declared) else d
            pairs.append((parts[1], nxt))
        else:
            pairs.append((c, d))

    # 归组：连续同 scene 的子句合成一个场景
    groups: list[dict] = []
    for c, d in pairs:
        sid = d["scene"]
        if not groups or groups[-1]["id"] != sid:
            groups.append({"id": sid, "clauses": [(c, d)]})
        else:
            groups[-1]["clauses"].append((c, d))

    scenes, cursor = [], 0.0
    for gi, g in enumerate(groups):
        first_c = g["clauses"][0][0]
        last_c = g["clauses"][-1][0]
        start = (cursor + first_c["stamps"][0]) / 2 if gi > 0 else 0.0
        end = (last_c["endTime"] + groups[gi + 1]["clauses"][0][0]["stamps"][0]) / 2 \
            if gi + 1 < len(groups) else float(tr.get("duration") or last_c["endTime"]) + 1.0
        text = "".join(t for cc in g["clauses"] for t in cc[0]["tokens"] if t not in PUNCT)
        expect = "".join(d.get("text", "") for _, d in g["clauses"]).replace("，", "").replace("。", "")
        if expect and not text.startswith(expect[:6]):
            print(f"WARN: 场景 {g['id']} 文本校验不符: ASR={text!r} spec={expect!r}", file=sys.stderr)
        kws = []
        for c, d in g["clauses"]:
            for w in d.get("keywords", []):
                idx = find_keyword(c["tokens"], w)
                if idx is None:
                    print(f"WARN: 关键词 {w!r} 未在场景 {g['id']} 找到，跳过", file=sys.stderr)
                    continue
                kws.append({"text": w, "atSec": round(c["stamps"][idx] - start, 2)})
        scenes.append({"id": g["id"], "startSec": round(start, 2),
                       "durationSec": round(round(end, 2) - round(start, 2), 2),
                       "keywords": kws,
                       "clauseText": text})
        cursor = last_c["endTime"]

    out = json.dumps({"scenes": scenes}, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(out)
    else:
        Path(args.out).write_text(out + "\n", encoding="utf-8")
        print(f"written: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
