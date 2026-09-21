# A/B: two grammars, one script (v2.9)

同一份文案、同一条旁白、同一个 56 场计划，跑两条 sketch 风格，然后并排看。
source: **TOC 瓶颈理论从入门到精通**（4.4 万字的报告 → 1,066 字解说稿 → 319.07s / 56 场 / 1080×1920）。

| | A · hand-sketch | B · swiss-sketch |
|---|---|---|
| 语法 | 纸纹 + feTurbulence 微抖线条 + 胶带/旋转相框 | 严格模数网格 + 尺规直线 + 只当结构用的红块 |
| 场次 / 时长 | 56 / 319.07s | 56 / 319.07s |
| 版面种类 | 5（statement 22 · thesis 16 · contrast 11 · step 5 · number 2） | 5（同上） |
| 换版率 / 同版面最长连续 | 0.964 / 2 场 | 0.964 / 2 场 |
| 全片最长冻帧 | **0.00s** | **0.00s** |
| meanDiff（8fps，跟一秒前比） | 10.07 | **10.77** |
| 最低单场 meanDiff | 3.99 | 3.77 |
| 素材就绪 | 56/56 | 56/56 |

## 怎么看这张表

- **版面分布两版完全一样，这是设计使然**：两条风格都是「按句子形状选版面」，同一句话在两边
  会得到同一套版面。所以这一轮比的是**语法**，不是节奏——节奏由文案形状决定，与风格无关。
- **「呆板」在这一轮是可量测的**：`verify.py` 的 motion 门禁（8fps 采样、每帧跟**一秒前的同一
  位置**比）在两版上都是 **0.00s 最长冻帧**，没有任何一场低于门槛。两版的差别不在「动不动」，
  而在线条、字型、红色的用法。
- swiss 的 meanDiff 略高，主要来自它的**尺规线是在场景时间里被画出来的**（见下）以及通栏出血的
  照片带；这不是「更不呆板」的证据，只是画面变化量的差异，别过度解读。

## 这一轮顺带修掉的三条真 bug（都是靠抽帧看出来的）

见 [`../../CHANGELOG.md`](../../CHANGELOG.md) 的 v2.9.0 条目，这里只留结论：

1. 重定时器把助手调用的**时长参数**当成 tween 位置参数（0.60 → 9.26）；本次再查下去发现更严重的
   第二层：场景 JS 用**全文档查询**挑墨迹组，56 个场景块一起去驱动 s01 的两条线，而本场的线从来
   没被设过 `dasharray`——**「线条被画出来」这个动作一次都没发生过**，线从第一帧就是画完的。
2. 笔尖可见性挂在 `onStart`/`onComplete` 上，seek 型渲染器不保证回调跑到 → 一枚笔尖留在画面里。
3. 助手函数按「遇到一行只有 `}` 就停」收集 → 助手体内有嵌套块就被截断，整段 `<script>` 语法报错。

三条现在都有 `selftest.py` 断言（自带 204 项，不需要渲染、一秒跑完）。

## 复现

```bash
python3 scripts/make_video.py --copy copy.txt --project p-hand --style hand-sketch --go \
    --narration narration.m4a --transcript narration-asr.json \
    --assets assets-override.json --bgm bgm.wav
python3 scripts/make_video.py --copy copy.txt --project p-swiss --style swiss-sketch --go \
    --narration narration.m4a --transcript narration-asr.json \
    --assets assets-override.json --bgm bgm.wav

python3 scripts/compare_films.py --a p-hand --b p-swiss --cols 6 --out-dir q/
```

`compare-stats.json` 是上面那张表的原始数据；`compare-sheet.jpg` 是同一场（同一句话）在两版里的
并排抽帧，上 A 下 B，两版选了**不同**版面的格子带 `*`。

## 诚实边界

- **风格不是「更不呆板」的开关**：呆板要看编排（入场 + 中段发屏 + 环境微动）与版面是否逐场变化，
  这两件事两条风格都做了；换风格换掉的是气质，不是节奏。
- 两版都还有 22 场落在 `statement`（短句多），这是这条文案的形状决定的，不是风格选错。
- 素材相关度仍然约「三张里两三张对题」（无密钥源）；两版共用同一套 `--assets` 覆写。
