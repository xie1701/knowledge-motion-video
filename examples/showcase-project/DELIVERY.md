# Delivery — Showcase「文案进，成片出」(v2.2, end-to-end verified)

- Format: 1080×1920, 30fps, H.264 + AAC, **37.5s**
- Routes: collage-evidence ×3, hand-sketch ×1, paper-fold ×1（5 scenes, narration-driven timing）
- Narration: AI TTS (36.5s), word timestamps via offline ASR (`coli asr`)
- Real assets: 5 photos + 1 real timelapse video (9s, cut from 35MB original to 720p card)
  fetched by `fetch_assets.py` from Wikimedia Commons / Openverse（无密钥源），6 条合成音效混入
- Captions: SRT + ASS by `build_captions.py`（ASR 误字已人工修正：一支/语义/逐镜/文案进成片出）
- SFX mix: `mix_audio.py`（旁白 + 6 条音效按 `startSec + atSec`，-6dB）

## Verified outputs

| Artifact | Path | Check |
|---|---|---|
| Visual master (HyperFrames render) | `renders/visual-master.mp4` | lint 0 errors; ffprobe 37.5s 1080×1920 h264, 1125 frames |
| Final delivery | `renders/final-showcase.mp4` | mix 混音 + loudnorm + 字幕烧录；ffprobe + 7 帧 vision 抽查 PASS |
| Contact sheet | `verify/contact-sheet.jpg` | scene midpoints s01–s05 |
| Verification report | `verify/report.json` | verdict PASS |
| Captions | `captions/captions.srt`, `captions.ass` | 15 cues, scene-bounded, word-timed |
| Asset license manifest | `assets/media/manifest.json` | 每条素材含 license/attribution/source_page |
| QC frames | `renders/qc-frames/`, `renders/qc-final/` | 抽帧 vision 复核：无空屏/无占位符/字幕无重叠 |

## Asset manifest（节选）

| id | type | source | license |
|---|---|---|---|
| photo-typewriter | photo | Wikimedia Commons | wikimedia-CC BY-SA 3.0 (Jorge Royan) |
| photo-notebook | photo | Openverse | CC（详见 manifest） |
| photo-pen | photo | Openverse | CC |
| photo-archive | photo | Wikimedia Commons | 见 manifest |
| photo-film | photo | Wikimedia Commons | 见 manifest |
| video-real-card.mp4 | video | Wikimedia Commons (Google Earth Timelapse) | 见 manifest；原片已裁 9s/720p |
| sfx-* | audio-sfx | 打包合成音效（make_sfx.py 自产） | bundled |

## Regression status

- `validate_scenes.py` passes（15-route enum，含 3 个新素材型路由）。
- 全部 Python 脚本 py_compile 通过；`doctor.py` core ready。
- HyperFrames lint 0 errors；渲染 24.2s 完成（本地 hyperframes 0.8.52）。
- `fetch_assets.py --dry-run` 幂等复跑：12/12 素材就绪。

## Known notes

- 真实视频素材为 Google Earth 卫星延时（城市地貌），与旁白「照片、档案、实拍视频」的
  「实拍视频」语义对应合理；如需人物/特写类实拍可配 Pexels key 后自动启用主源。
- SFX 为合成音效（非实录音效），打包于 `assets/sfx/`，用户可替换同名文件。
- 旧 10.4s 风格样片（style-samples）为无声风格循环，完整有声案例以本工程为准。
