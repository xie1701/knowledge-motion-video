#!/usr/bin/env python3
"""fetch_assets.py — 按 scenes.json 中的素材清单检索并下载真实素材。

管线（按可用性自动降级）：
  1. Pexels API    （PEXELS_API_KEY，照片+视频，免费可商用）
  2. Pixabay API   （PIXABAY_API_KEY，照片+视频）
  3. Openverse API （无需密钥，仅照片，CC/可商用过滤，匿名限流）
  4. Wikimedia Commons API（无需密钥，仅照片，公共领域/CC，历史档案题材强）
  5. 本地素材库    （--local-dir，直接复制）
  6. 跳过          （保留模板 CSS 兜底，不阻塞渲染）

行为：
  - 逐 scene 逐 asset 下载到 <project>/assets/media/<id>-<检索词指纹>.<ext>
  - 回填 scenes.json 中该 asset 的 local / attribution / license / used_query 字段
  - 产出 assets/media/manifest.json（发布所需的素材与许可证清单）
  - 断点续跑：目标文件已存在且 >0 字节则跳过下载；文件名带检索词指纹，
    换了检索词不会复用上一轮的旧图
  - 质量护栏：命中结果按检索词在标题里的命中数排序；下载后量宽度，太小的换下一张；
    本轮用过的源 URL 不再复用（同一场四张图不会长得一样）
  - 素材清单中每个 asset 必须 type ∈ {photo, video, audio-sfx}；accept 可声明类型优先序
    （如 ["video","photo"]），fallbacks 是检索词阶梯（长短语零命中时退裸概念）

用法：
  python3 fetch_assets.py --project <project_dir> [--local-dir DIR] [--dry-run] [--timeout 30]

退出码：0 成功 / 1 参数错误 / 2 全部素材缺失且 --strict
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = "knowledge-motion-skill/2.2 (open-source; contact: repo issues)"
SUPPORTED_TYPES = {"photo", "video", "audio-sfx"}


def _http_json(url: str, headers: dict | None = None, timeout: int = 30) -> dict | None:
    import time
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:  # noqa: BLE001 — 网络失败重试/降级
            last = e
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    print(f"  ! 检索失败 {url.split('?')[0]}: {last}", file=sys.stderr)
    return None


def _http_download(url: str, dest: Path, timeout: int = 60) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, dest.open("wb") as f:
            shutil.copyfileobj(r, f)
        return dest.stat().st_size > 0
    except Exception as e:  # noqa: BLE001
        print(f"  ! 下载失败 {url[:120]}: {e}", file=sys.stderr)
        if dest.exists():
            dest.unlink()
        return False


def _ext_of(url: str, default: str) -> str:
    m = re.search(r"\.(jpe?g|png|gif|webp|mp4|mov|webm|mp3|wav|ogg)(?:[?#]|$)", url, re.I)
    return (m.group(1).lower().replace("jpeg", "jpg") if m else default)


# ---------------------------------------------------------------- 检索源

def search_pexels(query: str, kind: str, key: str, timeout: int) -> list[dict]:
    base = "https://api.pexels.com/v1/search" if kind == "photo" else "https://api.pexels.com/videos/search"
    data = _http_json(f"{base}?query={urllib.parse.quote(query)}&per_page=3",
                      {"Authorization": key}, timeout)
    out = []
    for item in (data or {}).get("photos" if kind == "photo" else "videos", []):
        if kind == "photo":
            out.append({"url": item["src"]["large2x"], "attr": item.get("photographer", "?"),
                        "license": "pexels-license", "page": item.get("url", ""),
                        "title": item.get("alt") or ""})
        else:
            files = item.get("video_files", [])
            files = sorted(files, key=lambda f: f.get("width") or 0)
            cand = [f for f in files if (f.get("width") or 0) >= 1080] or files
            if cand:
                out.append({"url": cand[-1]["link"], "attr": item.get("user", {}).get("name", "?"),
                            "license": "pexels-license", "page": item.get("url", "")})
    return out


def search_pixabay(query: str, kind: str, key: str, timeout: int) -> list[dict]:
    if kind == "audio-sfx":
        return []
    base = "https://pixabay.com/api/" if kind == "photo" else "https://pixabay.com/api/videos/"
    data = _http_json(f"{base}?key={key}&q={urllib.parse.quote(query)}&per_page=3&safesearch=true", timeout=timeout)
    out = []
    for item in (data or {}).get("hits", []):
        if kind == "photo":
            out.append({"url": item.get("largeImageURL", ""), "attr": item.get("user", "?"),
                        "license": "pixabay-content", "page": item.get("pageURL", ""),
                        "title": item.get("tags", "")})
        else:
            vids = item.get("videos", {})
            pick = vids.get("large") or vids.get("medium") or vids.get("small")
            if pick:
                out.append({"url": pick["url"], "attr": item.get("user", "?"),
                            "license": "pixabay-content", "page": item.get("pageURL", "")})
    return out


def search_openverse(query: str, kind: str, timeout: int) -> list[dict]:
    if kind != "photo":
        return []
    data = _http_json("https://api.openverse.org/v1/images/?q=" + urllib.parse.quote(query)
                      + "&license_type=commercial&page_size=3", timeout=timeout)
    return [{"url": r["url"], "attr": r.get("creator", "?"),
             "license": "cc-" + ",".join(r.get("license", "?").split("-")),
             "page": r.get("foreign_landing_url", ""),
             "title": " ".join(str(r.get(k, "")) for k in ("title", "description", "tags"))}
            for r in (data or {}).get("results", [])]


def search_wikimedia(query: str, kind: str, timeout: int) -> list[dict]:
    if kind == "audio-sfx":
        return []
    ftype = "bitmap" if kind == "photo" else "video"
    api = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search"
           f"&gsrsearch=filetype:{ftype}%20{urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit=3"
           "&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1600&format=json")
    data = _http_json(api, timeout=timeout)
    out = []
    for page in (data or {}).get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        if kind == "video":
            path = str(info.get("url", "")).split("?")[0].lower()
            if not path.endswith((".webm", ".ogv")):
                continue  # FFmpeg 友好格式优先
            link = info.get("url", "")  # 原片；thumburl 是 jpg 海报，不能用
        else:
            link = info.get("thumburl") or info.get("url", "")
        meta = info.get("extmetadata", {})
        lic = (meta.get("LicenseShortName", {}) or {}).get("value", "see-commons")
        out.append({"url": link,
                    "attr": (meta.get("Artist", {}) or {}).get("value", "?"),
                    "license": f"wikimedia-{lic}", "page": info.get("descriptionurl", ""),
                    "title": f"{page.get('title', '')} "
                             f"{(meta.get('ImageDescription', {}) or {}).get('value', '')}"})
    return out


SOURCES: list[tuple[str, object]] = [
    ("pexels", lambda q, k, t: search_pexels(q, k[0], k[1], t) if k[1] else []),
    ("pixabay", lambda q, k, t: search_pixabay(q, k[0], k[1], t) if k[1] else []),
    ("openverse", lambda q, k, t: search_openverse(q, k[0], t)),
    ("wikimedia", lambda q, k, t: search_wikimedia(q, k[0], t)),
]

SFX_LIBRARY = Path(__file__).resolve().parent.parent / "assets" / "sfx"


_QUERY_STOP = {"the", "and", "with", "for", "from", "into", "over", "close", "still", "shot"}


def _apply_avoid(hits: list[dict], avoid: list[str]) -> list[dict]:
    """排除标题/描述里带这些词的命中（如 cinematic 风格不要「diagram / chart / schema」）。

    全都带这些词就放弃排除——宁可给一张凑合的图，不要给一个空槽。
    """
    if not avoid:
        return hits
    keep = [h for h in hits
            if not any(a.lower() in str(h.get("title", "")).lower() for a in avoid)]
    return keep or hits


def _rank_hits(hits: list[dict], query: str) -> list[dict]:
    """按「检索词在标题/描述/标签里出现过几个词」稳定排序。

    无密钥源的相关性很粗（实测「model scale」第一名是城堡模型照片），标题命中数
    是一个便宜且有效的护栏：一个词都不沾的结果排到最后，剩下按原顺序保持稳定。
    """
    toks = [t for t in re.split(r"[^a-z0-9]+", query.lower())
            if len(t) >= 4 and t not in _QUERY_STOP]
    if not toks:
        return hits

    def score(h: dict) -> int:
        title = str(h.get("title", "")).lower()
        return sum(1 for t in toks if t in title)

    return sorted(hits, key=lambda h: -score(h))


def _video_like(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".webm", ".ogv", ".mov"}


def _image_ok(path: Path, min_width: int = 900) -> bool:
    """下载后尺寸护栏：小于 min_width 的图铺到 1080 宽成片里会糊，宁可换下一张。
    ffprobe 量不出来（或不是图）就放行——宁可要一张小图，不要一个空槽。"""
    if _video_like(path):
        return True
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    try:
        w = int(proc.stdout.strip().split(",")[0])
    except (ValueError, IndexError):
        return True
    return w >= min_width


def fetch_asset(asset: dict, media_dir: Path, local_dir: Path | None,
                timeout: int, dry: bool, used: set[str] | None = None) -> dict:
    """返回 {status: ok|local|sfx|missing, ...} 并就地回填 asset 字段。

    accept：素材类型优先序（如 ["video","photo"]），拿不到视频就退照片；
    pick：在第几个命中 开始试（人工/agent 复核后换一张，不用改代码）；
    used：本轮已用过的源 URL——同一场四张图不应是同一张。
    """
    used = used if used is not None else set()
    aid, query = asset.get("id", "?"), asset.get("query", "")
    # 检索词阶梯：主检索词取不到就退到「不带修饰词的裸概念」（长短语在全文检索里命中率极低）
    queries = [query] + [q for q in (asset.get("fallbacks") or []) if q and q != query]
    accept = [k for k in (asset.get("accept") or [asset.get("type", "photo")]) if k]
    kinds = accept or ["photo"]
    kind = kinds[0]
    if not query:
        return {"status": "missing", "reason": "no query"}

    # 音效：从打包 sfx 库按文件名模糊匹配
    if kind == "audio-sfx":
        if SFX_LIBRARY.is_dir():
            stem = query.lower().replace(" ", "-")
            for f in sorted(SFX_LIBRARY.iterdir()):
                if stem and (stem in f.stem.lower() or any(w in f.stem.lower() for w in stem.split("-") if w)):
                    dest = media_dir / f"{aid}{f.suffix}"
                    if not dry:
                        shutil.copyfile(f, dest)
                    asset["local"], asset["license"], asset["attribution"] = (
                        f"assets/media/{dest.name}", f.name + " (bundled)", "knowledge-motion-skill sfx pack")
                    return {"status": "sfx", "file": str(dest)}
        return {"status": "missing", "reason": "no sfx match"}

    # 本地素材库优先（直接语义子串匹配文件名）
    if local_dir and local_dir.is_dir():
        for f in sorted(local_dir.iterdir()):
            if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"}:
                toks = [w for w in re.split(r"[\s,_-]+", query.lower()) if len(w) > 2]
                if any(w in f.stem.lower() for w in toks):
                    dest = media_dir / f"{aid}{f.suffix}"
                    if not dry:
                        shutil.copyfile(f, dest)
                    asset["local"], asset["license"], asset["attribution"] = (
                        f"assets/media/{dest.name}", "local", f"local library: {f.name}")
                    return {"status": "local", "file": str(dest)}

    for kind in kinds:   # 类型优先序：视频拿不到就退照片
      for query in queries:     # 检索词阶梯：主词取不到就退裸概念
        keys = (kind, os.environ.get("PEXELS_API_KEY", ""))
        pix_keys = (kind, os.environ.get("PIXABAY_API_KEY", ""))
        for name, fn in SOURCES:
            try:
                hits = fn(query, keys if name in ("pexels",) else
                          (pix_keys if name in ("pixabay",) else (kind,)), timeout)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {name} 异常: {e}", file=sys.stderr)
                hits = []
            hits = _rank_hits(_apply_avoid(hits, asset.get("avoid") or []), query)
            pick = int(asset.get("pick") or 0)
            if pick and hits:
                hits = hits[pick:] + hits[:pick]
            for h in hits:
                if not h.get("url") or h["url"] in used:
                    continue
                ext_default = {"photo": "jpg", "video": "webm"}.get(kind, "mp3")
                # 文件名带检索词指纹：换检索词不会复用上一轮的旧图（断点续跑仍成立）
                stem = f"{aid}-{hashlib.sha1(query.encode('utf-8')).hexdigest()[:6]}"
                dest = media_dir / f"{stem}.{_ext_of(h['url'], ext_default)}"
                if dest.exists() and dest.stat().st_size > 0:
                    hit = h
                elif dry:
                    hit = h
                else:
                    if not _http_download(h["url"], dest, timeout):
                        continue
                    if not _image_ok(dest):
                        print(f"  ! {aid} 尺寸不达标，换下一张: {h['url'][:80]}", file=sys.stderr)
                        dest.unlink(missing_ok=True)
                        continue
                    hit = h
                used.add(h["url"])
                asset["local"] = f"assets/media/{dest.name}"
                asset["attribution"] = re.sub(r"<[^>]+>", "", str(hit["attr"]))[:120]
                asset["license"] = hit["license"]
                asset["source_page"] = hit.get("page", "")
                asset["resolved_type"] = kind
                asset["used_query"] = query
                return {"status": "ok", "source": name, "type": kind, "file": str(dest),
                        "query": query}
    return {"status": "missing", "query": query, "accept": kinds}


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Label,Helvetica,26,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,3,2,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _label_ass(labels: list[tuple[str, int, int]], w: int, h: int, path: Path) -> Path:
    """标签用 libass 烧——本机 ffmpeg 未编 drawtext（无 freetype），与成片字幕同一条路径。"""
    events = "\n".join(
        f"Dialogue: 0,0:00:00.00,0:00:10.00,Label,,0,0,0,,{{\\pos({x},{y})}}{name}"
        for name, x, y in labels)
    path.write_text(ASS_HEAD.format(w=w, h=h) + events + "\n", encoding="utf-8")
    return path


def _contact_sheet(media_dir: Path, manifest: list[dict]) -> None:
    """素材接触表：网格缩略图 + 素材 id / 检索词标签，供渲染前目检匹配度（先看后用）。

    这是素材质量的唯一自动关卡之前的人工关卡：看一眼就知道取回来的图到底对不对题。
    （只放照片；视频素材请在成片抽帧里看。）"""
    photos = [m for m in manifest if m.get("type") == "photo"
              and (media_dir / Path(m["local"]).name).is_file()]
    if not photos:
        return
    n = len(photos)
    cw, ch = 360, 270
    cols = min(n, 4)
    rows = (n + cols - 1) // cols
    out = media_dir / "contact-sheet.jpg"
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    for m in photos:
        cmd += ["-i", str(media_dir / Path(m["local"]).name)]
    chain = [f"[{i}:v]scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch},"
             f"setsar=1[t{i}]" for i in range(n)]
    layout = "|".join(f"{(i % cols) * cw}_{(i // cols) * ch}" for i in range(n))
    chain.append("".join(f"[t{i}]" for i in range(n))
                 + f"xstack=inputs={n}:layout={layout}:fill=#111111[grid]")
    labels = [(f"{m['id']}  {str(m.get('query', ''))[:26]}",
               (i % cols) * cw + 12, (i // cols) * ch + 12)
              for i, m in enumerate(photos)]
    ass = _label_ass(labels, cols * cw, rows * ch, media_dir / "labels.ass")
    chain.append(f"[grid]ass={ass}[out]")
    proc = subprocess.run(cmd + ["-filter_complex", ";".join(chain), "-map", "[out]",
                                 "-frames:v", "1", "-update", "1", str(out)],
                          capture_output=True, text=True)
    if out.exists() and proc.returncode == 0:
        print(f"素材接触表: {out}（渲染前请目检匹配度）")
    else:
        print(f"素材接触表生成失败: {proc.stderr[-200:]}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="按 scenes.json 素材清单检索下载真实素材")
    ap.add_argument("--project", required=True, help="示例工程目录（含 storyboard/scenes.json）")
    ap.add_argument("--scenes", default=None, help="scenes.json 路径（默认 <project>/storyboard/scenes.json）")
    ap.add_argument("--local-dir", default=None, help="本地素材库目录（文件名含检索词即命中）")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--strict", action="store_true", help="有任何素材缺失则退出码 2")
    ap.add_argument("--sheet", action="store_true", help="生成素材接触表 contact-sheet.jpg（渲染前目检用）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    scenes_path = Path(args.scenes) if args.scenes else project / "storyboard" / "scenes.json"
    if not scenes_path.is_file():
        print(f"scenes.json 不存在: {scenes_path}", file=sys.stderr)
        return 1
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    media_dir = project / "assets" / "media"
    local_dir = Path(args.local_dir).resolve() if args.local_dir else None
    if not args.dry_run:
        media_dir.mkdir(parents=True, exist_ok=True)

    results, manifest = [], []
    used: set[str] = set()
    scenes = doc.get("scenes", doc if isinstance(doc, list) else [])
    for sc in scenes:
        for asset in sc.get("assets", []) or []:
            aid = asset.get("id", "?")
            acc = "/".join(asset.get("accept") or [asset.get("type", "photo")])
            print(f"[scene {sc.get('id', '?')}] asset {aid} [{acc}] q={asset.get('query')!r}")
            r = fetch_asset(asset, media_dir, local_dir, args.timeout, args.dry_run, used)
            print(f"  -> {r['status']}" + (f" via {r.get('source', '')} ({r.get('type', '')})"
                                           if r.get("source") else ""))
            results.append({"scene": sc.get("id"), "asset": aid, **r})
            if r["status"] in ("ok", "local", "sfx"):
                manifest.append({"scene": sc.get("id"), "id": aid,
                                 "type": r.get("type", asset.get("type")),
                                 "query": asset.get("query"),
                                 "description": asset.get("description", ""),
                                 "local": asset.get("local"),
                                 "license": asset.get("license"), "attribution": asset.get("attribution"),
                                 "source_page": asset.get("source_page", "")})

    if not args.dry_run:
        if getattr(args, "sheet", False):
            _contact_sheet(media_dir, manifest)
        mf = media_dir / "manifest.json"
        mf.write_text(json.dumps({"generated_by": "fetch_assets.py",
                                  "note": "发布前保留此清单：素材与许可证记录",
                                  "items": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")
        # 回填 scenes.json（保留缩进风格）
        scenes_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"素材清单: {mf}")

    ok = sum(1 for r in results if r["status"] in ("ok", "local", "sfx"))
    print(f"完成: {ok}/{len(results)} 素材就绪")
    if args.strict and results and ok < len(results):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
