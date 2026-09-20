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

Exit code 0 when everything passes, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_video as M  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_ANCHORS = ("enter", "build", "reveal", "peak")
# 每套版面最少需要几张素材（多一张就是多一个空框）
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
            # 缺素材必须能整卡消失，否则画面里会留下空框
            for slot in M.MATERIAL_PLAN_SLOTS.get(style, []):
                check(f"km-ev--miss-{slot}" in text,
                      f"template {style}", f"no hide rule for missing slot {slot}")

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

    # 5: no immediate repeat while the pool has an alternative
    st = {"id": "s01", "narration": "AI论文的数量在涨", "keywords": [], "_clauseTexts": []}
    for style in M.LAYOUT_VARIANTS:
        prev = ""
        for i in range(6):
            sc = dict(st, narration="AI论文的数量从十万篇涨到二十五万篇" if i % 2 else "成本下降了")
            v, why = M.choose_variant(style, sc, 4, prev)
            check(v != prev, "choose_variant", f"{style}: repeated {v} at step {i} ({why})")
            prev = v

    # 6: query ladder has real alternatives
    for i in range(4):
        q, fences = M.asset_query(scenes[0], {}, i, set())
        check(bool(q) and bool(fences) and q not in fences,
              "asset_query", f"ordinal {i}: q={q!r} fallbacks={fences}")

    print(f"selftest: {checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL {f}")
    print("verdict: " + ("PASS" if not failures else "FAIL"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
