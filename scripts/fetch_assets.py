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
  - 逐 scene 逐 asset 下载到 <project>/assets/media/<id>.<ext>
  - 回填 scenes.json 中该 asset 的 local / attribution / license 字段
  - 产出 assets/media/manifest.json（发布所需的素材与许可证清单）
  - 断点续跑：目标文件已存在且 >0 字节则跳过下载
  - 素材清单中每个 asset 必须 type ∈ {photo, video, audio-sfx}

用法：
  python3 fetch_assets.py --project <project_dir> [--local-dir DIR] [--dry-run] [--timeout 30]

退出码：0 成功 / 1 参数错误 / 2 全部素材缺失且 --strict
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
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
                        "license": "pexels-license", "page": item.get("url", "")})
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
                        "license": "pixabay-content", "page": item.get("pageURL", "")})
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
             "page": r.get("foreign_landing_url", "")} for r in (data or {}).get("results", [])]


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
                    "license": f"wikimedia-{lic}", "page": info.get("descriptionurl", "")})
    return out


SOURCES: list[tuple[str, object]] = [
    ("pexels", lambda q, k, t: search_pexels(q, k[0], k[1], t) if k[1] else []),
    ("pixabay", lambda q, k, t: search_pixabay(q, k[0], k[1], t) if k[1] else []),
    ("openverse", lambda q, k, t: search_openverse(q, k[0], t)),
    ("wikimedia", lambda q, k, t: search_wikimedia(q, k[0], t)),
]

SFX_LIBRARY = Path(__file__).resolve().parent.parent / "assets" / "sfx"


def fetch_asset(asset: dict, media_dir: Path, local_dir: Path | None,
                timeout: int, dry: bool) -> dict:
    """返回 {status: ok|local|sfx|missing, ...} 并就地回填 asset 字段。"""
    aid, kind, query = asset.get("id", "?"), asset.get("type", "photo"), asset.get("query", "")
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

    keys = (kind, os.environ.get("PEXELS_API_KEY", ""))
    pix_keys = (kind, os.environ.get("PIXABAY_API_KEY", ""))
    for name, fn in SOURCES:
        try:
            hits = fn(query, keys if name in ("pexels",) else
                      (pix_keys if name in ("pixabay",) else (kind,)), timeout)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name} 异常: {e}", file=sys.stderr)
            hits = []
        for h in hits:
            if not h.get("url"):
                continue
            ext_default = {"photo": "jpg", "video": "webm"}.get(kind, "mp3")
            dest = media_dir / f"{aid}.{_ext_of(h['url'], ext_default)}"
            if dest.exists() and dest.stat().st_size > 0:
                hit = h
            elif dry:
                hit = h
            else:
                if not _http_download(h["url"], dest, timeout):
                    continue
                hit = h
            asset["local"] = f"assets/media/{dest.name}"
            asset["attribution"] = re.sub(r"<[^>]+>", "", str(hit["attr"]))[:120]
            asset["license"] = hit["license"]
            asset["source_page"] = hit.get("page", "")
            return {"status": "ok", "source": name, "file": str(dest)}
    return {"status": "missing"}


def _contact_sheet(media_dir: Path, manifest: list[dict]) -> None:
    """素材接触表：网格缩略图，供 agent/人渲染前目检匹配度（先看后用）。"""
    import subprocess
    photos = [m for m in manifest if m.get("type") == "photo" and (media_dir / Path(m["local"]).name).is_file()]
    if not photos:
        return
    n = len(photos)
    cols = min(n, 3)
    rows = (n + cols - 1) // cols
    out = media_dir / "contact-sheet.jpg"
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    for m in photos:
        cmd += ["-i", str(media_dir / Path(m["local"]).name)]
    fc_parts = []
    for i, m in enumerate(photos):
        fc_parts.append(
            f"[{i}]scale=360:270:force_original_aspect_ratio=increase,crop=360:270,"
            f"drawtext=text='{m['id']}':fontsize=28:fontcolor=white:box=1:"
            f"boxcolor=black@0.6:x=8:y=8[t{i}]")
    if n == 1:
        fc = fc_parts[0]
    else:
        fc = ";".join(fc_parts) + ";" + "".join(f"[t{i}]" for i in range(n)) + f"tile={cols}x{rows}"
    subprocess.run(cmd + ["-filter_complex", fc, "-frames:v", "1", "-update", "1", str(out)], check=False)
    print(f"素材接触表: {out}（渲染前请目检匹配度）")


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
    scenes = doc.get("scenes", doc if isinstance(doc, list) else [])
    for sc in scenes:
        for asset in sc.get("assets", []) or []:
            aid = asset.get("id", "?")
            print(f"[scene {sc.get('id', '?')}] asset {aid} ({asset.get('type')}) q={asset.get('query')!r}")
            r = fetch_asset(asset, media_dir, local_dir, args.timeout, args.dry_run)
            print(f"  -> {r['status']}" + (f" via {r.get('source', '')}" if r.get("source") else ""))
            results.append({"scene": sc.get("id"), "asset": aid, **r})
            if r["status"] in ("ok", "local", "sfx"):
                manifest.append({"scene": sc.get("id"), "id": aid, "type": asset.get("type"),
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
