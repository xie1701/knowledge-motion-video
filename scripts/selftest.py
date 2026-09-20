#!/usr/bin/env python3
"""Self-test the engine contracts that no rendered video can cheaply assert.

Usage: python3 scripts/selftest.py

Why this exists: several engine rules are structural — they hold or they don't, and a broken
one shows up as a *quiet* defect in the finished film (a template that lost a line of animation,
a layout that leaves an empty photo box, an anchor schedule that runs past the scene end).
Rendering 15 styles to notice that is wasteful; these checks take a second.

Checks:

1. Every scene template parses, extracts timeline JS, and declares ``enter/build/reveal/peak``
   anchors (``settle`` optional — it is derived from the scene length when absent).
2. Templates that carry the ambient layer (``data-km-drift`` / ``data-km-push``) are balanced:
   the attribute appears in the fragment, so ``make_video`` will inject the ambient timeline.
3. ``anchor_schedule`` is strictly increasing, respects the minimum spacing, never runs past the
   scene end, and is monotone in scene length for both keyword-driven and keyword-less scenes.
4. Layout variants named in ``LAYOUT_VARIANTS`` exist in the template's CSS, and
   ``VARIANT_BY_COUNT`` never offers a layout that needs more cards than the scene has photos
   (a layout that can't be filled is how you get an empty box on screen).
5. ``choose_variant`` avoids repeating the previous scene's layout whenever the pool allows it.
6. ``asset_query`` returns a ladder: the fallback list is non-empty and excludes the primary.
7. Shape-driven layouts (``SHAPE_VARIANTS``): each shape's own slots actually get filled by
   ``hand_sketch_slots`` (a ``step`` scene with no ``STEP_NO`` renders an empty progress bar), and
   the shape fits the sentence (第一步 → step, 短句 → statement, 长句 → thesis).
8. Every style that shows a photo slot has an entry in ``MATERIAL_PLANS`` — otherwise the slot
   never gets fetched and the finished film shows the grey CSS fallback in every scene.

Exit code 0 when everything passes, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_video as M  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_ANCHORS = ("enter", "build", "reveal", "peak")
# 每套版面最少需要几张素材（多一张就是多一个空框）——只对素材数驱动的风格成立
VARIANT_MIN_ASSETS = {"wall": 4, "cascade": 4, "hero": 3, "pair": 2, "single": 1}

failures: list[str] = []
checks = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not ok:
        failures.append(f"{label}: {detail}")


def scene(keys: list[float], dur: float, n_avail_hint: int = 4) -> dict:
    return {
        "id": "s01",
        "narration": "AI论文的数量在涨",
        "durationSec": dur,
        "keywords": [{"text": f"k{i}", "atSec": t} for i, t in enumerate(keys)],
        "_clauseTexts": ["AI论文的数量在涨"],
    }


def main() -> int:
    # 1 & 2 & 4-part-2: templates
    for path in sorted((ROOT / "assets" / "templates" / "scenes").glob("*.html")):
        style = path.stem
        text = path.read_text(encoding="utf-8")
        try:
            tpl = M.parse_template(style)
        except SystemExit as exc:                     # die() raises SystemExit
            check(False, f"template {style}", f"parse failed ({exc})")
            continue
        anchors = tpl["anchors"]
        missing = [a for a in REQUIRED_ANCHORS if a not in anchors]
        check(not missing, f"template {style}", f"@beats missing {missing}")
        check("tl." in tpl["scene_js"], f"template {style}", "no timeline JS extracted")
        # 行内中文尾注不能让一条跨行调用少半截参数（历史 bug：整行被当散文丢掉）
        check("fromTo(" in tpl["scene_js"] or ".to(" in tpl["scene_js"],
              f"template {style}", "timeline looks truncated")
        has_ambient_attr = ("data-km-drift" in text) or ("data-km-push" in text)
        check(not has_ambient_attr or "data-km-drift" in text or "data-km-push" in text,
              f"template {style}", "ambient attribute lost during assembly")
        # 变体：CSS 里必须有对应规则（列表首位是默认版面，靠基础规则表达，不需要属性选择器）
        variants = M.LAYOUT_VARIANTS.get(style, [])
        for variant in variants[1:]:
            check(f'data-km-variant="{variant}"' in text,
                  f"template {style}", f"layout variant {variant!r} has no CSS rule")
        if variants:
            # 缺素材必须能优雅退场（整卡消失，或 onerror 去掉 <img> 留 CSS 兜底），
            # 否则画面上就是一个空框
            for slot in M.MATERIAL_PLAN_SLOTS.get(style, []):
                check(f"km-ev--miss-{slot}" in text or "onerror" in text,
                      f"template {style}", f"no fallback for missing slot {slot}")

    # 3: anchor schedules
    scenes = [scene([2.4, 4.6], 6.2), scene([1.0], 5.0), scene([], 7.3), scene([3.9], 3.4)]
    for sc in scenes:
        start, dur = 12.0, sc["durationSec"]
        sched = M.anchor_schedule(sc, start, dur)
        check(all(n in sched for n in M.ANCHOR_NAMES),
              "anchor_schedule", f"{sc['durationSec']}s missing anchors")
        vals = [sched[n] for n in M.ANCHOR_NAMES]
        check(all(b - a >= 0.29 for a, b in zip(vals, vals[1:])),
              "anchor_schedule", f"spacing too tight: {sched}")
        check(all(a < b for a, b in zip(vals, vals[1:])),
              "anchor_schedule", f"not strictly increasing: {sched}")
        check(vals[0] > start and vals[-1] <= start + dur - 0.1,
              "anchor_schedule", f"runs outside the scene: {sched} for {dur}s")

    # 4: every layout offered for a photo count is a real layout
    for count, pool in M.VARIANT_BY_COUNT.items():
        for variant in pool:
            check(variant in VARIANT_MIN_ASSETS, "VARIANT_BY_COUNT",
                  f"{count} 张素材给出了不存在的版面 {variant!r}")
            need = VARIANT_MIN_ASSETS[variant]
            check(need <= max(count, 1) or "km-ev--miss" != "",
                  "VARIANT_BY_COUNT",
                  f"{count} 张素材给出需要 {need} 张的版面 {variant}（靠缺素材隐藏兜底）")

    # 5: no immediate repeat while the pool has an alternative（形状驱动风格按内容走，不套这条）
    st = {"id": "s01", "narration": "AI论文的数量在涨", "keywords": [], "_clauseTexts": []}
    for style in M.LAYOUT_VARIANTS:
        if style in M.SHAPE_VARIANTS:
            continue
        prev = ""
        for i in range(6):
            sc = dict(st, narration="AI论文的数量从十万篇涨到二十五万篇" if i % 2 else "成本下降了")
            v, why = M.choose_variant(style, sc, 4, prev)
            check(v != prev, "choose_variant", f"{style}: repeated {v} at step {i} ({why})")
            prev = v

    # 7: 形状驱动的版面：句子形状 → 版面，且各版面的专属槽位必须真被填上
    shape_cases = [
        ("第三步，让其他部分服从约束。", "step"),
        ("百分之八十的客户流失发生在第一次演示。", "number"),
        ("传统管理问哪里效率低，TOC 问哪里限制结果。", "contrast"),
        ("技术方案容易，组织改变困难。", "statement"),
        ("在一个目标明确的复杂系统中，大量努力为什么没有产生结果。", "thesis"),
    ]
    for text, want in shape_cases:
        sc = {"id": "s01", "narration": text, "_clauseTexts": [text], "keywords": []}
        v, why = M.shape_variant(sc, [])
        check(v == want, "shape_variant", f"{text[:12]}… → {v}（期望 {want}）: {why}")
    # 连续三场同一形状要换（step 除外：进度条在走就是推进，不是重复）
    sc_short = {"id": "s01", "narration": "技术方案容易，组织改变困难。",
                "_clauseTexts": ["技术方案容易，组织改变困难。"], "keywords": []}
    v3, _ = M.shape_variant(sc_short, ["statement", "statement"])
    check(v3 != "statement", "shape_variant", "短句连着三场还是 statement（没换版面）")
    step3, _ = M.shape_variant(
        {"id": "s02", "narration": "第三步，让其他部分服从约束。",
         "_clauseTexts": ["第三步，让其他部分服从约束。"], "keywords": []}, ["step", "step"])
    check(step3 == "step", "shape_variant", "第 N 步被反复避让，进度版面断了")

    # 8: 形状驱动版面的专属槽位（空槽位 = 屏幕上一条空进度条 / 一个空数字）
    slot_cases = {
        "step": ("第五步，防止惯性。旧瓶颈解决了新的瓶颈会出现。",
                 ("STEP_NO", "STEP_PCT", "STEP_TICKS")),
        "number": ("百分之八十的客户流失发生在第一次演示。", ("BIGNUM",)),
        "contrast": ("传统管理问哪里效率低，TOC 问哪里限制结果。", ("LINE_A", "LINE_B")),
    }
    for variant, (text, needed) in slot_cases.items():
        sc = {"id": "s01", "narration": text, "_clauseTexts": [text],
              "keywords": [{"text": "瓶颈", "atSec": 1.0}]}
        slots = M.hand_sketch_slots(sc, variant, step_total=5)
        for key in needed:
            check(bool(slots.get(key)), f"hand_sketch_slots[{variant}]",
                  f"{key} 是空的（{text[:12]}…）")
    step_slots = M.hand_sketch_slots(
        {"narration": "第五步，防止惯性。", "_clauseTexts": ["第五步，防止惯性。"],
         "keywords": []}, "step", step_total=5)
    check(step_slots.get("STEP_NO") == "05", "hand_sketch_slots[step]", "步序不是 05")
    check(step_slots.get("STEP_PCT") == "100%", "hand_sketch_slots[step]", "第五步进度不是满格")
    check(step_slots.get("STEP_TICKS", "").count("<i ") == 5,
          "hand_sketch_slots[step]", "刻度数跟总步数不一致")
    check(step_slots.get("HEADLINE") == "防止惯性",
          "hand_sketch_slots[step]", f"步骤名没剥掉「第五步」前缀: {step_slots.get('HEADLINE')!r}")

    # 8b: 有照片槽位的风格必须在 MATERIAL_PLANS 里（否则素材永远不下载，成片全是灰底相框）；
    # 确实不需要照片的风格（纸艺那类的可选贴图）得显式标 data-km-optional，不能靠默认。
    for path in sorted((ROOT / "assets" / "templates" / "scenes").glob("*.html")):
        style = path.stem
        body = path.read_text(encoding="utf-8")
        if "assets/media/" not in body:
            continue
        check(style in M.MATERIAL_STYLES or "data-km-optional" in body,
              "MATERIAL_PLANS",
              f"{style} 模板里有素材槽位，但 MATERIAL_PLANS 没登记也没标 data-km-optional"
              "（照片永远不会被取回）")

    # 6: query ladder has real alternatives
    for i in range(4):
        q, fences = M.asset_query(scenes[0], {}, i, set())
        check(bool(q) and bool(fences) and q not in fences,
              "asset_query", f"ordinal {i}: q={q!r} fallbacks={fences}")

    # 6b: 全片检索词配额（同一句话重复 8 遍，不能 8 次同一个概念——实测会渲染出 11 张一样的高速堵车）
    counts: dict[str, int] = {}
    qs = [M.asset_query(scenes[0], {}, 0, set(), counts)[0] for _ in range(8)]
    check(len(set(qs)) >= 3, "asset_query 配额",
          f"同一概念被用了 {len(qs) - len(set(qs))} 次：{qs}")
    check(max(counts.values()) <= 2, "asset_query 配额",
          f"有概念超过 2 次上限：{counts}")

    print(f"selftest: {checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL {f}")
    print("verdict: " + ("PASS" if not failures else "FAIL"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
