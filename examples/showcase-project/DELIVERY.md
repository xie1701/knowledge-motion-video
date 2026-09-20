# Delivery — Showcase「文案进，成片出」(v2.3, end-to-end verified)

- Format: 1080×1920, 30fps, H.264 + AAC, **32.3s**
- **整片单一风格**：hand-sketch（全片米白网格底、黑色描边自绘、#E34234 单强调色、笔尖引导）——
  文案是"方法论证"型，按整片级风格路由选定；v2.2 的多风格混搭方案已废弃
- Narration: AI TTS (31.28s)，词级时间戳由本地 ASR (`coli asr`) 获得
- **时间轴全部程序化推导**（`derive_timing.py`）：场景边界 = 子句间停顿中点；关键词 beat =
  token 精确落点。v2.2 实测手工 beat 最大偏移 2.06s，本版归零
- BGM: Openverse 无密钥获取的 CC0 钢琴循环（Soft Piano Loop 160BPM, freesound CC0），
  循环拼接至片长 + 2.5s 淡入 / 3.9s 淡出，finalize.py 以 0.18 音量垫底
- SFX: 无（v2.2 反馈音效突兀；v2.3 默认无音效，策略见 SKILL.md）
- Real asset: 1 张语义匹配照片（复古胶片相机，Wikimedia CC BY-SA 2.0），经素材目检关卡

## 同步性验证（v2.3 专项）

| 关键词 | 语音落点(ASR) | 视觉动作 | 实测 |
|---|---|---|---|
| 论证结构 | 5.76s | 骨架笔画起笔 | 落点起笔、6.45s 画完 ✓ |
| 照片和视频 | 19.62s | 真实照片钉入 | 19.9s 帧照片+箭头+胶带齐全 ✓ |
| 特效 | 30.48s | 红叉划掉"特效" | 30.5s 帧已呈现 ✓ |
| 字幕（抽样 t=2s/24s） | — | 逐字转录 | 与语音逐句一致 ✓ |

## Verified outputs

| Artifact | Path | Check |
|---|---|---|
| Visual master | `renders/visual-master.mp4` | ffprobe 32.3s 1080×1920, 969 frames; lint 0 errors |
| Final delivery | `renders/final-showcase.mp4` | narration + BGM(0.18) + loudnorm + captions burned |
| Captions | `captions/captions.{srt,ass}` | 11 cues, word-timed, ASR 误字已修正（一支/语义），断句修正（成片出） |
| Contact sheet | `assets/media/contact-sheet.jpg` | 素材目检关卡输出 |
| License manifest | `assets/media/manifest.json` | license/attribution/source_page 齐全 |
| Verify report | `verify/report.json` | verdict PASS |
| QC frames | `renders/qc-frames/`, `renders/qc-final/` | 关键词落点抽帧 vision 复核 |

## Known notes

- 旁白 ASR 误字（一支/语义）已人工修正进字幕；其他项目复现时应同样过一遍字幕校对
- BGM 音源为 Freesound CC0 预览音质（hq mp3）；对音质有更高要求可替换 `assets/bgm/` 本地音乐
- v2.2 的 5 场景混风格案例已由本案例替代（其风格混搭正是本版路由机制修正的问题）
