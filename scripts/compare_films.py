#!/usr/bin/env python3
"""A/B 两部成片的对比：同一份文案、同一条旁白、两条风格，差在哪。

用来回答「换个风格是不是就不呆了」这类问题——把主观感受换成三组可量测的东西：

1. **版面分布**：每套版面用了几次、同版面最长连续几场（一部片子里同一张版式播 11 遍，
   那就是「呆板」的字面定义）。
2. **运动门禁**：全片最长冻帧、逐场 meanDiff、有多少场低于门槛（verify.py 的口径：
   8fps 采样、跟一秒前的同一位置比）。
3. **并排抽帧**：同一场（同一句话）在两版里的画面并排，肉眼核对。

用法:
  python3 scripts/compare_films.py --a <projA> --b <projB> --cols 6 --out-dir ~/Desktop/ab
"""
from __future__ import annotations

import argparse
import collections
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

CELL_W = 340                      # 单格宽（高度按成片比例推）
STRIP = 26                        # 每格底部给场次标签留的条（否则标签会盖在成片字幕上）
ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cell,Helvetica,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,3,2,0,7,0,0,0,1
Style: Card,Helvetica,{card},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def must(cmd: list[str], what: str) -> None:
    """ffmpeg 失败必须炸出来：静默失败过（并排图没生成，脚本还打了「已生成」）。"""
    p = run(cmd)
    if p.returncode != 0:
        die(f"{what} 失败:\n{cmd[0]} ... {p.stderr.strip()[:600]}", 1)


def ass_file(path: Path, events: list[tuple[str, str, int, int]],
             w: int, h: int, size: int = 15, card: int = 26) -> Path:
    """events: (style, text, x, y) → libass 字幕文件。

    为什么走 libass：本机 ffmpeg 未编 drawtext（无 freetype），`ass=` 是唯一能烧文字的路径
    （与成片字幕同一条路径，行为一致）。"""
    body = "\n".join(
        f"Dialogue: 0,0:00:00.00,0:00:30.00,{style},,0,0,0,,{{\\pos({x},{y})}}{text}"
        for style, text, x, y in events)
    path.write_text(ASS_HEAD.format(w=w, h=h, size=size, card=card) + body + "\n",
                    encoding="utf-8")
    return path


def load_project(proj: Path) -> dict:
    sc_path = proj / "storyboard" / "scenes.json"
    if not sc_path.exists():
        die(f"{proj} 里没有 storyboard/scenes.json —— 指到项目目录（不是仓库根）")
    scenes = json.loads(sc_path.read_text(encoding="utf-8"))
    lay_path = proj / "storyboard" / "layouts.json"
    layouts = json.loads(lay_path.read_text(encoding="utf-8")) if lay_path.exists() else {}
    rep_path = proj / "verify" / "report.json"
    report = json.loads(rep_path.read_text(encoding="utf-8")) if rep_path.exists() else {}
    film = proj / "renders" / "final.mp4"
    if not film.exists():
        die(f"{proj} 里没有 renders/final.mp4")
    return {"dir": proj, "scenes": scenes, "layouts": layouts, "report": report, "film": film}


def stats(p: dict, label: str) -> dict:
    scenes = p["scenes"]["scenes"]
    project = p["scenes"]["project"]
    variants = [s.get("variant", "") for s in scenes]
    by_variant = collections.Counter(v for v in variants if v)
    longest_run, cur, prev = 0, 0, ""
    for v in variants:
        cur = cur + 1 if v == prev and v else 1
        prev = v
        longest_run = max(longest_run, cur if v else 0)
    switches = sum(1 for a, b in zip(variants, variants[1:]) if a != b)
    motion = {}
    for c in p["report"].get("checks", []):
        if c["name"] == "motion":
            motion = c.get("detail") or {}
    per_scene = motion.get("scenes") or []
    thr = motion.get("thresholds", {})
    floor = thr.get("minMeanDiff", 0.4)
    below = [d["scene"] for d in per_scene if d.get("meanDiff", 99) < floor]
    slots = [(s["id"], a) for s in scenes for a in (s.get("assets") or [])]
    ready = [a for _, a in slots if a.get("local")]
    return {
        "label": label,
        "style": p["layouts"].get("style") or project.get("style", ""),
        "dir": str(p["dir"]),
        "sceneCount": len(scenes),
        "durationSec": round(project.get("durationSec", 0), 2),
        "layouts": dict(by_variant),
        "layoutKinds": len(by_variant),
        "longestSameLayoutRun": longest_run,
        "layoutSwitches": switches,
        "switchRate": round(switches / max(len(scenes) - 1, 1), 3),
        "motion": {
            "meanDiff": motion.get("meanDiff"),
            "longestFrozenSec": motion.get("longestFrozenSec"),
            "worstScene": motion.get("worstScene", ""),
            "scenesBelowFloor": below,
            "minSceneMeanDiff": min((d.get("meanDiff", 99) for d in per_scene), default=None),
            "scenes": {d["scene"]: d.get("meanDiff") for d in per_scene},
            "frozen": {d["scene"]: d.get("longestFrozenSec") for d in per_scene},
        },
        "assets": {"total": len(slots), "ready": len(ready),
                   "readyPct": round(100.0 * len(ready) / max(len(slots), 1), 1)},
        "sceneTimes": {s["id"]: (s["startSec"], s["durationSec"]) for s in scenes},
    }


def pick_scenes(pa: dict, pb: dict, cols: int) -> list[str]:
    """挑要并排的场次：优先 A/B 版面不同、且在片子里均匀铺开的那几场。"""
    va = {s["id"]: s.get("variant", "") for s in pa["scenes"]["scenes"]}
    vb = {s["id"]: s.get("variant", "") for s in pb["scenes"]["scenes"]}
    ids = [s["id"] for s in pa["scenes"]["scenes"] if s["id"] in vb]
    if not ids:
        return []
    step = max(len(ids) // cols, 1)
    cand = ids[::step]
    # 版面不同（观众真能看出差别）的排前面，同时保持片头到片尾的铺开
    cand.sort(key=lambda i: (va.get(i) == vb.get(i), -ids.index(i)))
    chosen = sorted(set(cand[:cols]), key=ids.index)
    while len(chosen) < cols:
        nxt = next((i for i in ids if i not in chosen), None)
        if nxt is None:
            break
        chosen = sorted(chosen + [nxt], key=ids.index)
    return chosen


def frame(film: Path, t: float, out: Path, w: int, h: int,
          ass: Path | None = None) -> bool:
    # 必须 pad 到统一高度：scale=340:-2 会给出偶数高（604），跟卡片高差 6px，
    # hstack 直接报 "Input 1 height 604 does not match input 0 height 610"。
    vf = f"scale={w}:-2,pad={w}:{h}:0:0:color=0x11110F"
    if ass is not None:
        vf += f",ass={ass.as_posix()}"
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(film), "-frames:v", "1",
           "-vf", vf, "-y", str(out)]
    p = run(cmd)
    if p.returncode != 0:
        print(f"  ! 抽帧失败 t={t:.2f}: {p.stderr.strip()[:200]}")
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B 两部成片对比（版面 / 运动 / 并排抽帧）")
    ap.add_argument("--a", required=True, type=Path)
    ap.add_argument("--b", required=True, type=Path)
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--width", type=int, default=CELL_W)
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/kmv-compare"))
    args = ap.parse_args()

    pa, pb = load_project(args.a), load_project(args.b)
    sa = stats(pa, args.label_a)
    sb = stats(pb, args.label_b)
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- 表 ----
    rows = [("风格", "style"), ("场次", "sceneCount"), ("时长 s", "durationSec"),
            ("版面种类", "layoutKinds"), ("同版面最长连续", "longestSameLayoutRun"),
            ("换版率", "switchRate"), ("全片最长冻帧 s", "motion.longestFrozenSec"),
            ("meanDiff", "motion.meanDiff"), ("最低单场 meanDiff", "motion.minSceneMeanDiff"),
            ("低于门槛的场次", "motion.scenesBelowFloor"), ("素材就绪", "assets.readyPct")]
    print(f"\n{'':<22}{sa['label']:<24}{sb['label']:<24}")
    print("-" * 70)
    for title, key in rows:
        va, vb = sa, sb
        for k in key.split("."):
            va = va.get(k) if isinstance(va, dict) else None
            vb = vb.get(k) if isinstance(vb, dict) else None
        print(f"{title:<22}{str(va):<24}{str(vb):<24}")
    print(f"{'版面分布':<22}{json.dumps(sa['layouts'], ensure_ascii=False)}")
    print(f"{'':<22}{json.dumps(sb['layouts'], ensure_ascii=False)}")

    stats_out = {"a": sa, "b": sb}
    (out_dir / "compare-stats.json").write_text(
        json.dumps(stats_out, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- 并排抽帧 ----
    ids = pick_scenes(pa, pb, args.cols)
    if not ids:
        die("两版没有共同场次，无法并排")
    va = {s["id"]: s.get("variant", "") for s in pa["scenes"]["scenes"]}
    vb = {s["id"]: s.get("variant", "") for s in pb["scenes"]["scenes"]}
    w = args.width
    h_frame = round(w * pa["scenes"]["project"]["height"] / pa["scenes"]["project"]["width"] / 2) * 2
    h = h_frame + STRIP
    work = out_dir / "cells"
    work.mkdir(exist_ok=True)

    def scene_time(p: dict, sid: str) -> float:
        start, dur = p["sceneTimes"][sid]
        return start + max(min(dur * 0.72, dur - 0.35), 0.3)

    rows_files: list[Path] = []
    for p, s, tag, other in ((pa, sa, args.label_a, vb), (pb, sb, args.label_b, va)):
        cells: list[Path] = []
        # 行首卡片：说明这一行是谁 + 关键数字
        card = work / f"card-{tag}.jpg"
        card_ass = ass_file(work / f"card-{tag}.ass", [
            ("Card", f"{tag}", 22, 40),
            ("Card", s["style"], 22, 86),
            ("Card", f"{s['sceneCount']} scenes / {s['durationSec']}s", 22, 150),
            ("Card", f"layouts {s['layoutKinds']} kinds", 22, 196),
            ("Card", f"longest same-layout run {s['longestSameLayoutRun']}", 22, 242),
            ("Card", f"frozen {s['motion']['longestFrozenSec']}s", 22, 288),
            ("Card", f"meanDiff {s['motion']['meanDiff']}", 22, 334),
            ("Card", f"assets {s['assets']['ready']}/{s['assets']['total']}", 22, 380),
        ], w, h, card=22)
        must(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
              f"color=c=0x11110F:s={w}x{h}", "-frames:v", "1",
              "-vf", f"ass={card_ass.as_posix()}", "-y", str(card)], f"行首卡片 {tag}")
        cells.append(card)
        for sid in ids:
            t = scene_time(s, sid)
            cell = work / f"{tag}-{sid}.jpg"
            lab = ass_file(work / f"{tag}-{sid}.ass", [
                ("Cell", f"{sid} · {va.get(sid, '') if tag == args.label_a else vb.get(sid, '')}"
                         f"{'' if (va.get(sid) == vb.get(sid)) else '  *'}", 12, h_frame + 4),
            ], w, h)
            frame(p["film"], t, cell, w, h, lab)
            cells.append(cell)
        row = work / f"row-{tag}.jpg"
        must(["ffmpeg", "-v", "error"] + sum([["-i", str(c)] for c in cells], []) +
             ["-filter_complex", f"{''.join(f'[{i}]' for i in range(len(cells)))}hstack={len(cells)}",
              "-frames:v", "1", "-y", str(row)], f"拼行 {tag}")
        rows_files.append(row)

    sheet = out_dir / "compare-sheet.jpg"
    must(["ffmpeg", "-v", "error"] + sum([["-i", str(r)] for r in rows_files], []) +
         ["-filter_complex", "[0][1]vstack=2", "-frames:v", "1", "-q:v", "3", "-y", str(sheet)],
         "拼并排图")
    print(f"\n并排抽帧（上 {args.label_a} / 下 {args.label_b}，* = 两版版面不同）: {sheet}")
    print(f"统计: {out_dir / 'compare-stats.json'}")
    sheet_ok = sheet.exists() and sheet.stat().st_size > 0
    shutil.rmtree(work, ignore_errors=True)
    return 0 if sheet_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
