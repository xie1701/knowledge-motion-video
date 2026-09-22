# Changelog

## v2.9.1 — 2026-09-22

**开源发布件**：把仓库整理成一个能给别人看、也能自己跑通的公开项目。这一版不动引擎，只把门面、
CI 和包元数据补齐。

### README 重写为公开门面

- 结构改成「是什么 → 快速开始（一条命令）→ 真实案例（带数字）→ 15 种语法 → 怎么工作 →
  质量门禁 → 安装 → 环境 → 诚实边界 → 中文速览」。第一屏给的是 hero 图与一句定位，不是目录。
- 新增 `docs/hero.jpg`（三帧真实成片：两张带来源的数据图 + 一张拼贴证据墙）——**不是效果图**。
- 管线用 mermaid 画出来；15 种语法直接引 `docs/style-sweep/sweep-contact-sheet.jpg`；
  A/B 段引 `docs/style-ab/compare-sheet.jpg`。
- 明确写清「诚实边界」：无密钥素材相关度约三张里两三张对题、15 条模板里有 4 条开场仍过不了
  motion 门禁、TTS 会静默丢句、风格不是「更不呆板」的开关。

### CI 现在真的能跑通（之前推上去必红）

- **修**：`ci.yml` 引用了两个被 `.gitignore` 排除的文件（`examples/demo-density/sweep/copy.txt`、
  `transcript.json`）——第一次推送到 GitHub 时「Assemble every style template」这一步必然失败。
  现在这两个小文本进仓（同目录的音频/渲染产物仍然不进）。
- **补**：工作流缺少 Node 与渲染器依赖，而 `make_video.py` 的 lint 走 `node_modules/.bin/hyperframes`。
  新增 `setup-node@v4`（带 npm 缓存）+ `npm ci` + 「ffmpeg 不存在就装」的兜底步骤；
  `package-lock.json` 因此改为进仓（CI 用 `npm ci` 保证渲染器可复现）。
- 顺带把校验铺开：所有 `examples/**/storyboard/scenes.json`（含 4 条风格样片）逐份校验，
  并新增一步对已发布旁白跑 `check_narration.py`（静默丢句的守卫本身也要被 CI 看着）。
- 本地按 CI 逐步跑过：compile / doctor / selftest 204 / 7 份 storyboard / captions / align /
  narration guard / 15 条模板逐条 `--no-render` 组装 / fetch dry-run。

### 包元数据与许可证

- `package.json`：`knowledge-motion-skill` → `knowledge-motion-video`，补 `repository` / `homepage` /
  `keywords`；保持 `private: true`（这个包不发 npm，只做渲染器依赖）。lockfile 同步改名。
- `LICENSE`：署名补上 GitHub 账号；GSAP 那条从「via CDN」改成事实描述——它是
  **vendored**（`composition/vendor/gsap.min.js`），并说明超出 GreenSock 标准许可范围时该自己换授权。
  第三方声明移到 `THIRD-PARTY-NOTICES.md`：LICENSE 保持**纯 MIT 文本**，否则 GitHub 的许可证
  识别会把它判成「Other」，侧栏显示不出 MIT 徽章。
- `CONTRIBUTING.md`：加一条「提 PR 前先跑 `selftest.py` 与 CI 里的步骤」。

## v2.9.0 — 2026-09-21

**「换个风格是不是还呆板？」** —— 同一份 TOC 报告、同一条旁白，把 `swiss-sketch` 从一条 40 行的
老模板重做成与 `hand-sketch` 同级的形状驱动风格，两版成片并排比了一次。结论：**都不呆板**
（全片最长冻帧都是 **0.00s**，meanDiff 10.07 / 10.77，素材 56/56）——差别不在「动不动」，在语法：
手绘版是纸纹 + 微抖线条 + 胶带相框，瑞士版是严格网格 + 尺规直线 + 只当结构用的红块。

### swiss-sketch 重做：国际主义网格 + 五套内容形状版面

- 五套版面与 hand-sketch 共用同一套**形状语义**（`thesis` / `statement` / `contrast` / `step` /
  `number`），但几何全部重写：左右页边线 + 横规的模数网格、mono 场次编号（`07 / 56`）、
  红块只做结构标记（编号方块 / 进度当前段 / 收束粗规）。`statement` 的照片做成**通栏出血带**，
  `thesis` 的网格单元用尺规延长线标出，`number` 的巨号数字是红的、单位标签是黑的。
- `data-km-variant` 的五套轮廓互不相同，除 `step` 外不邻场重复（换版率 0.964，同版面最长连续 2 场）。
- 新增 `photo-1` 素材槽位 + `MATERIAL_PLANS` 登记（否则照片永远不下载，成片全是空框）；
  缺素材时留一个细线空框——「预留版位」仍然成立，不是一块灰底占位。
- 尺规线**只走直线、不加 feTurbulence**：两条风格都叫 sketch，但「手作抖动」是 hand-sketch 的
  语法，瑞士版要的是精确——这是两条风格能被看出来的根本区别。

### 顺手挖出四个真 bug（都是抽帧看出来的，不是猜的）

四个都是同一类病：**决定画面的东西被写成了回调或文本扫描，而不是时间的函数**；第 3 条还多一层：
**查询没有限定在本场**。其中第 3 条是这一轮最重要的发现——两条 sketch 风格的招牌动作（线条被
画出来）从 v2.2 立项起就**从来没有真正执行过**。

1. **重定时器把助手调用的时长参数当成 tween 位置参数。** `POS_PARAM_RE` 是「逗号 + 数字 + 右括号」，
   分不清 tween 的位置参数和普通函数调用的末尾数字参数：`kmSwPen(tl, strokes[0], pen, 1.78, 0.60)`
   里的 `0.60`（画多久）被映射成 **9.26**，跨过了一整个 2.46s 场景。后果有两层——笔尖的 tween
   永远「还在画」（回调不触发 → 一枚笔尖留在画面里），而真正的「线条被画出来」在时间上完全失控：
   起画时间还是模板原值（全局 1.78s），也就是说 **手绘线条其实从来没有在各自的场景里被画出来**，
   全片只有第一场有描边动画。这条从 v2.5 就存在，一直到这一轮抽帧才被抓到（因为描边最终是画完的，
   画面看着「没错」）。修法：只认挂在 `tl` 上的 tween 方法，取其右括号前的**最后一个数字**
   （结构化扫描 + 括号配平），并配 `selftest` 回归断言。
2. **笔尖的可见性挂在 `onStart`/`onComplete` 上。** seek 型渲染器不保证这两个回调跑到——笔尖就以
   不透明状态停在半路（实测：swiss 版一枚红点落在照片带边缘、hand-sketch 版一枚墨点落在照片上）。
   修法：显隐由 tween 自身的 `this.progress()` 推（progress 0/1 → 藏起来），并把描边本身改成
   **真正的 tween**（目标就是那条线），时长与起画时间都回到参数里——任何 seek 落点都自洽。
3. **场景 JS 用全文档查询挑本场元素。** `document.querySelectorAll(".km-sw__inkgroup")` 是全
   文档的：56 个场景块拿到的都是**第一个可见的墨迹组**（也就是 s01 的那两条线），于是全片 56 个
   场景块一起去驱动 s01 的线，而本场的线从来没被设过 `dasharray`。后果比前两条严重得多——
   **「线条被画出来」这个动作一次都没发生过**：每一场的线从第一帧就是画完的（旧成片里看不到
   描边，看到的只是线条本来就在那儿）。实测证据：探针在 12.45s 读到 s01 的两条 path 带着
   450/161 的偏移（正在被后场重画），而 s02…s56 的 path `style.strokeDasharray` 全是空串。
   修法：查询从**笔尖所在的本场根元素**出发（`pen.closest(".km-sw")`），segments 同理
   （不然 `stagger` 会被全片 280 个目标摊开）。
4. **助手函数按「遇到一行只有 `}` 就停」收集。** 助手体内只要有一个嵌套块（`if (on) { … }`），
   函数就被截断在半路，整段 `<script>` 语法报错、timeline 一条都不注册。修法：按大括号配平收块。
   同一个坑的另一面也补上了断言：模板尾注里一行**没有中文、也没写 `//`** 的英文散文会被当成代码
   留下（它的规则是「带中文才当散文丢掉」），抽出来的 JS 必须能被 `node --check` 解析。

### 新工具

- **`scripts/compare_films.py`** —— 两部成片的 A/B：「哪个风格好看」不该靠感觉回答。同一份文案 +
  同一条旁白的两版，输出并排数字表（版面分布 / 同版面最长连续 / 换版率 / 最长冻帧 / meanDiff /
  素材就绪）与一张上 A 下 B 的同场次抽帧图（两版选了不同版面的格子带 `*`）。
- **`render-browser.mjs --stills "t1,t2"`** —— 只抓指定时刻的静帧，不编码、不渲染全片。
  调版面几何时，5 张静帧比等 10 分钟渲染便宜得多（这一轮的三个 bug 都是这么看出来的）。

### 自检 143 → 198 项

新增：形状驱动风格的**模板私有类名前缀**必须与生成侧一致（`km-sw--h-m` 发错成 `km-sk--h-m`
只是静默失效）、抽出的 scene JS 必须能被 `node --check` 解析、笔尖可见性必须是时间的函数、
描边必须是真正的 tween、场景 JS 不得用全文档查询（必须 `closest()` 限定回本场）、
重定时不得吃普通函数调用的末尾数字参数、助手块必须按大括号配平。

### 数字

| | hand-sketch | swiss-sketch |
|---|---|---|
| 场次 / 时长 | 56 / 319.07s | 56 / 319.07s |
| 版面种类 / 同版面最长连续 | 5 / 2 | 5 / 2 |
| 全片最长冻帧 | 0.00s | 0.00s |
| meanDiff | 10.07 | 10.77 |
| 素材就绪 | 56/56 | 56/56 |

两版成片与并排抽帧见 [`docs/style-ab/`](docs/style-ab/)。

## v2.8.0 — 2026-09-20

**“把一篇 4.4 万字的报告做成一条 5 分 19 秒的片子”** —— 这是第一次拿**真实文档**（而不是
手写文案）跑全流程：`TOC瓶颈理论从入门到精通.md`（3,522 行 / 44,484 字）→ 1,066 字解说稿
（**42:1** 的重写）→ **56 场 / 319.07s / 1080×1920 / H.264+AAC**，verify 四项全 PASS
（motion：全片最长冻帧 **0.00s**、均值 10.35）。新流程写在
[`docs/document-to-film.md`](docs/document-to-film.md)。

### 手绘风格从 1 套版面变成 5 套（按句子形状逐场选）

- `hand-sketch` 现在声明 `{{VARIANT}}`，引擎按**这句话是什么形状**选版面：
  `number`（巨号数字 + 单位 + 一行说明）、`statement`（一句话大片 + 横贯照片）、
  `contrast`（上行为描边空心、下行为实心 + 强调下划线，中间一支箭）、
  `step`（进度条 + 巨号步序 + 步骤名）、`thesis`（标题 + 两条论点 + 右侧相框，默认）。
- **形状驱动的版面不再只看素材数**（那是 collage-evidence 的依据）：除 `step` 外，同一套版面
  连着两场就必须让位给「全片用得最少」的候选——55 场片子最长同版面连续 **2 场**
  （实测：只用形状、不让位时，会出现 11 场一模一样的版面）。
- `step` 的进度不写死 5 步：总步数从整片文案里「第 N 步」的最大值推，刻度、进度百分比、
  步序（`02`）都对得上；标题自动剥掉「第 N 步，」前缀（不然标题和步骤名重复）。
- **大标题不再拿关键词填**。这条风格的主视觉是一句能读的话：标题 = 首个子句，论点 = 后续子句，
  子句不够就不画（`km-sk--p0/p1/p2`）。实测拿关键词填时，屏幕上一整屏只有「加班」两个字。
- hand-sketch 进了 `MATERIAL_PLANS`：一条 55 场的片子自己取回 55 张配图（就绪 55/56），
  取不到图的那一场整块相框消失、只留手绘的空图框 + 图注，不留灰底占位。

### 旁白：TTS 会静默丢句，现在每次都体检

- 实测：同一篇 1,066 字的稿子生成两次，各出现一段 **41.3s / 58.5s 的纯静音**（对应文本只有
  约 6–7s），ASR 的时间戳直接跨过那段静音——表现出来就是 `scenes[N].durationSec must be > 0`
  或者一场 49s 的静止画面。两次丢句都落在「TOC」+短句+「：」附近。
- 新增 `scripts/check_narration.py`（时长 / 超长停顿 / 削波）和管线内的 `narration_silence_gaps()`：
  `--narration` 一进来就查 >3s 的静音并告警。**正解是分段生成**（每段 ≤450 字）+ 逐段体检 +
  段间 0.45s 拼接；丢了只重生成那一段。`align_transcript.py` 的相似度 <0.85 也会告警
  （8 成是又丢了一句）。

### 素材：同一概念不再刷屏

- **全片检索词配额**：一个概念最多用 2 次，超了就换同场景的下一候选（`asset_query` 的
  `counts/max_uses`）。实测：55 场里 11 场都取「traffic jam on highway」——现在 55 张素材用
  **39 个不同检索词**，最高频 3 次。
- `MATERIAL_PLANS["hand-sketch"]` 加了标题排除表（newspaper / manuscript / document /
  ledger / book page …）：无密钥源上「档案/历史」类概念很容易取回**报纸、手稿、书页扫描件**，
  而「白底图文」护栏只抓亮底白底，泛黄的中灰纸页会漏过。

### 这一轮逼出来的四个真 bug

1. **`derive_timing.py` 的取整漂移**：场景时长原来算 `round(end - start, 2)`，相邻两场各自
   取整后会差 0.01s，校验器直接判 `overlaps the previous scene`（这条 56 场的片子正好在第 38 场
   触发）。改成「取整后的边界相减」。
2. **转写快照没跟着旁白换**：`step_transcript` 里 `transcript.raw.json` 原来是「已存在就不写」，
   于是换了旁白音频、`--transcript` 指向新文件时，仍然拿**上一轮的旧快照**去对齐——时间轴整段
   错位，成片里出现一场 49s 的静止画面。现在每次都把「未校正的输入」快照一份再对齐。
3. **中文百分比拿不到数字**：`extract_numbers` 不认「百分之八十」，`number` 版面的大数字会是空的。
   新增 `percent_display()`。
4. **有照片槽位的风格没登记素材需求**：`paper-fold` 的 `photo-1` 是可选贴图（标了
   `data-km-optional`），而 `hand-sketch` 漏登记会让照片永远不下载、成片里全是空相框。
   self-test 现在会挡：模板里有 `assets/media/` 就必须在 `MATERIAL_PLANS` 里或显式标可选。

### 自检从 114 项扩到 143 项

新增：形状驱动版面的槽位真被填（`step` 没 `STEP_NO` 就是一条空进度条）、`第 N 步` → `step`、
短句 → `statement`、长句 → `thesis`、连着三场同形状要换、检索词配额（8 场里至少 3 个不同概念、
单概念 ≤2 次）、以及上面第 4 条的门禁。

## v2.7.0 — 2026-09-20

**“把「呆板」变成一条会挂的门禁”** —— 反馈只有两个字："还是很差劲！呆板。"这一版没有去讨论
什么叫呆板，而是先把它量出来：**入场动画结束后到下一场之间，画面真的逐像素不动**。旧成片实测
单场连续 1.75s 画面完全没变（collage 成片 s04）、1.50s（数据片 s04），全片 **24–27% 的采样点
低于「有变化」的门槛**；而且八场用的是**同一套卡片坐标**——同一张幻灯片播了八遍，
再多的入场动画也治不了。

### 运动变成可量测的硬指标（`verify.py` 新增 motion 检查）

- 8fps 采样，**把每一帧跟「一秒前的同一位置」比**（ffmpeg `blend=difference` + `signalstats`），
  而不是跟上一帧比：125ms 尺度上，3% 的慢推每帧挪不到一个像素会被判成「没动」，可它在一秒里
  是看得见的；真正的停住在哪个尺度上都是 0。阈值：**单段连续「画面没变」≤ 1.2s**、
  一秒尺度的全片均值 ≥ 0.4，报告里逐场给出数值。
- 这条门禁上线后，**两条已发布成片都挂了** —— 这正说明「呆板」不是口味问题。修完再过：
  collage 成片从「最长 1.75s 没变、27% 采样不达标」变成「**0.00s、0%**」（均值 19.1），
  数据片从 1.50s/24% 变成 **0.00s/1%**。
- 门禁默认只告警不挡流水线（`--strict-motion` 可改回硬失败）：还有几条模板的编排没抬到门槛，
  不该因此挡住成片产出。

### 环境微动层（引擎级，`data-km-drift` / `data-km-push`）

- 模板只在装饰层上标两个属性：`data-km-drift="20"`（纸纹/底色上下浮 20px）、
  `data-km-push="4"`（卡片内部的 `<img>` 全程慢推近 4%）。引擎按**整场时长**铺一条与落点
  无关的慢运动。
- 为什么不能靠再叠一个入场动画：入场是「东西出现」，只发生在前半场；后半场需要的是持续
  的低幅运动。属性不重叠（漂移打在装饰层、推近打在图片上）所以与入场编排互不干扰。
- 装饰层一律 `inset:-8%` 超出画布，微动几像素不会在边缘露出缝。

### 版面变体：八场一个样，是呆板的主因

- 模板声明 `{{VARIANT}}`，`make_video.py` 的 `choose_variant` 逐场挑版面，**不邻场重复**：
  `wall` 四张卡铺满 / `cascade` 斜向下叠放 / `hero` 一张满幅大图 + 两张小图 /
  `pair` 两张大图对看 / `single` 一张大图 + 一句大字。
- 第一依据是**本场真正取到的素材数**（`VARIANT_BY_COUNT`）：缺素材不是留个空框，而是换一套
  装得下的版面。内容再加一层偏好：有大数字 → `hero`（满幅），有对比语义 → `pair`。
  产物 `storyboard/layouts.json` 记录每场选了哪套、为什么。
- **缺素材 → 整卡消失**：引擎按槽位发 `km-ev--miss-photo-N` 类，模板把那张卡 `display:none`。
  灰底占位框会让整幅画面看着像坏了，一个素材都没取到的场景才保留关键词兜底层。

### collage-evidence 动效重做：三段式，而不是一段入场

- 入场（build）：四张卡按序切入 + **落纸回弹**（缩放 1.06→1）。
- 中段发屏（`mid`，本轮新增的锚点）：**焦点收拢** —— 主卡推近到 1.10，其余卡被挤开
  （x/y 位移）并压暗到 0.5。这是一次可见的重排，「画面变了」比「东西又出现一次」像在讲事。
- 收束（peak）：**图注定案** —— 图注条下的下划线从左画到右，角色芯片（主证据/对照/档案/细节）
  贴着图注条推出来。
- 去掉的东西比加上的更重要：上一版在照片上画一圈大红椭圆当批注，放大看就是一条跨图的乱线；
  手帐箭头也摆在照片中间指向真空。现在箭头是墨色细线、落在卡片之间的空当指向右下，
  圈注换成贴在图注条下沿的下划线。
- 图注条改成贴文字宽度（原来拉满整幅卡片，红底色块 + 圈注 + 芯片三条东西互相盖）；
  档案标签不再是「NO.01 / 1998-03」这种假日期（在讲 AI 的镜头上是误导），改为编号 + 该图在
  论证里的角色；标签加一圈描边，压在暗照片上也能读。

### 取图护栏：白底图文（论文插图/流程图/截图）判掉

- 新判定：首帧 `YAVG ≥ 205 且 SATAVG ≤ 30` → 判为纸面素材，换下一张（`--keep-all` 可关）。
  实测旧成片 29 张素材里 **7 张**是这一类（某张「World Population & Total Carbon Emissions」
  的 matplotlib 截图、流程图、论文插图），而真实照片 YAVG ≤ 160，两者分得很开。
- 概念表重写，加第三条写词规则：**第一顺位必须是「能拍出来的东西」**。抽象名词
  （`inference` / `algorithm` / `efficiency` / `market share`）在无密钥源上只命中论文插图，
  然后被护栏判掉 —— 等于这一场一张都取不到。实测素材就绪率 **28/32 → 32/32**。
- 检索词阶梯现在也挂同场景的其它概念候选：第一条被护栏拦下还有路可走。

### 修掉的两个引擎 bug

- `parse_template` 会把「含中文但没有 `//` 开头」的行整行当散文丢掉。于是 `… }, 0.50)  // 落纸回弹`
  这种**行内中文尾注**把跨行 `.fromTo(` 的后半截删了，生成出的 JS 直接语法错
  （lint: `invalid_inline_script_syntax`）。现在只切掉尾注、保留代码。
- `--data` 的 `values` 不是数字时抛 ValueError 堆栈；现在给一条能读的错误（也提醒别把
  `charts.json`（产物）当输入喂回来）。

### 新增 `scripts/selftest.py`（114 项结构断言，无网络无渲染，已接进 CI）

引擎里有一批规则是结构性的，坏了不会报错、只会在成片里安静地丑：模板丢了一行动画、
版面需要的卡比素材多、锚点排到场景外、变体名在 CSS 里不存在。这个自检一秒跑完。
它上线时抓到的真实问题：`wall` 作为默认版面没有属性规则、`cascade` 被排给只有 3 张素材的场。

### 实测

- collage 成片：8 场 49.9s，**五套版面全跑一遍**，一秒尺度上**全片没有任何一段画面停住**
  （最长 0.00s，原 1.75s），素材 32/32。
- 数据片：加纸纹微动层 + 通用镜头推近，同样从「s04 停住 1.50s」变成 0.00s。
- 15 条风格重扫：15/15 渲染成功，其中 motion 门禁 **11 条直接过**，4 条仍告警
  （map-geo / process-flow / kinetic-typography / timeline-history —— 都是大面积平色的版面，
  通用推近在这类画面上量不出变化；正解是给它们各做一次中段发屏，还没做）。

### 诚实边界

- 白底判定按亮度/饱和度：暗底的论文插图仍会漏过（s01 主证据仍是一张科研插图）。
- 无密钥素材源的语义相关度仍约「三张里两三张对题」，`contact-sheet.jpg` 目检 +
  `--assets`/`pick` 换图这条人工通道还是必要关卡。
- 缺素材靠版面重排吸收，代价是那块版面容空（宁可空着，不要灰框）。

## v2.6.0 — 2026-09-20

**“把素材型风格接上自动检索”** —— collage-evidence / editorial-collage / generated-cinematic
三条风格的画面主体是真实照片，而此前自动档只会在槽位里填一个内联占位图：一条风格好不好用，
取决于人有没有手动去找图。这一版让管线自己去取图，并把取图当成一个有质量护栏的步骤。

### 素材检索进管线（`make_video.py` 新增 `step_assets`）

- 三条素材风格声明自己需要的槽位（`MATERIAL_PLANS`：槽位名 / 角色 / 类型优先序 / 限定修饰词），
  `step_assets` 在**分镜之后、组装 composition 之前**跑：合成检索词 → 调 `fetch_assets.py`
  下载 → 把「本场实际下到的文件」映射回模板写死的槽位名。
- **检索词合成**：新增 `assets/lexicon/visual-concepts.txt`（自撰，MIT，52 条）：中文概念 →
  英文检索短语，每条给 2–4 个同域备选。为什么要它：Pexels/Pixabay/Openverse/Wikimedia 对英文
  召回远好于中文（实测「智能手机芯片」取回路由器与麦克风照片）；而且一条风格同一场往往要 4 张
  素材，四张都拿同一个检索词必是同一张脸——现在按候选表顺位取第 1/2/3/4 名，四张各不相同又
  都在同一语义域。命中不了概念表就退中文关键词。
- 检索词打分：命中触发词按字数计分，若触发词还是该场关键词的一部分，按覆盖率加权 3 分；
  同分则先出现在文案里的胜。
- `--assets plan.json` 逐场覆写检索词（`{"s01":[{"slot":"photo-1","query":"…","pick":0}]}`）；
  `--local-dir` 本地素材库优先；`--no-fetch` 保留模板兜底。产物：`storyboard/assets-plan.json`。

### 取图质量护栏（`fetch_assets.py`）

- **标题相关性排序**：命中结果按「检索词有几个词出现在标题/描述/标签里」稳定排序。无密钥源的
  相关性很粗——实测 `model scale` 第一名是一张城堡模型照片——标题命中是最便宜有效的护栏。
- **尺寸护栏**：下载后用 ffprobe 量宽度，小于 900px 的换下一张（铺到 1080 宽会糊）。
- **本轮 URL 去重**：同一个源图不会同时填两个槽位。
- **检索词阶梯**：主检索词零命中时退到不带修饰词的裸概念（长短语在全文检索里命中率极低，
  `neural network architecture cinematic still` 实测 0 命中）。
- **文件名带检索词指纹**：`s01-photo-1-b4f2f9.jpg`——换检索词不会静默复用上一轮那张图。
- 接触表改 libass 打标（本机 ffmpeg 未编 drawtext），标签现在真的显示，且带检索词。

### 模板与槽位解析

- 路径修正：HyperFrames 的项目根就是 composition 目录，素材必须拷进
  `composition/assets/media/` 并以根相对路径引用；旧的 `../assets/media/` 会被 lint 判为
  `invalid_parent_traversal_in_asset_path`，而文件不在 composition 下又会报
  `missing_local_asset`（渲染时静默丢图）。
- collage-evidence：四张卡的兜底层不再是「photo-1 / 素材占位」，改为当前场关键词 + 槽位角色
  （主证据/对照/档案/细节）——没取到图时画面仍然是一张设计过的卡片。
- editorial-collage：新增右下副素材窗口（photo-2）。没取到图时整块在构建期移除
  （`data-hide-when-empty`），不会留下一个空框。
- generated-cinematic：容器里新增真实静帧 `<img>`（media-1），保留原有渐变+环层兜底；
  视频优先、照片兜底（无密钥的免费视频源基本只有 Wikimedia 的 webm）。

### 扫描

- `style_sweep.py` 透传 `--assets` / `--local-dir` / `--no-fetch`；三条素材风格在扫描里
  会各自取图，扫描因此同时是素材通路的端到端回归网。
- 重新横扫 15 条风格并更新 `docs/style-sweep/`：素材型三风格从「空占位框」变成有真实照片的
  成片；逐条结论重写（见 `docs/style-sweep/README.md`）。
- CI 增加 --no-fetch 的 15 模板组装关卡（不联网）。

## v2.5.0 — 2026-09-20

**“把自动档做成真正能看的成片”** —— 上一版的自动档能跑通，但片子本身站不住：动画和旁白不同步，
场景被拦腰切断，图表只是真实数据的示意图。这一版把三件事拆开重做。

### 节奏：动画挂在念出的字上（`@beats` 锚点）

- 模板在尾注声明五个编排锚点
  `// @beats enter=… build=… reveal=… peak=… settle=…`，`make_video.py` 把它们解到场景时间：
  `enter` = 场次头 +0.12s，`build` = 首个内容词前 0.7s 起势（柱子是「边说边长」的），
  `reveal` / `peak` 落在旁白念到的关键词上，`settle` 收势。锚点时间表写到
  `storyboard/beats.json`。
- 修掉真正的病根：旧版把模板整套编排（典型 0.1–3.5s）**线性拉满整个场景**，
  一场 10s 的片子就是 10s 慢动作，说完话画面还在动。现在动画在词上完成，其余时间静止可读。
- 15 条模板全部声明锚点（各自由编排语义决定，例如 hand-sketch 的 `reveal` = 证据照片钉入、
  process-flow 的 `peak` = 数据包走完）。未声明的模板仍然安全：锚点从位置参数分布自动推断。

### 结构：一场一句，字幕逐字照文案

- `group_clauses` 改为**按文案句子分场**：一句一场；超过 8.2s 的句子在其内部标点处切成 5–7.5s
  的段；尾场 <2.2s 并回上一场。此前的纯时长贪心会把句子拦腰截断（「涨到二十五万八千篇
  投稿量还在涨」把两个话题黏在一场）。
- 新增 `scripts/align_transcript.py`：**转写以文案为准**。ASR 的 ITN 与误字
  （过去十年→过去1年、arXiv→Aive、三分之二→3分之2）会同时污染字幕与关键词分词，而旁白
  本来就是照文案念的——用 difflib 把文案文字套回 ASR 时间戳（相似度 <0.55 则放弃并原样保留），
  原始转写留在 `script/transcript.raw.json`。
- 关键词抽取继续抬地板：中文数词串禁入（十年/十六/三分/一倍）、复合词可跨「的/之」
  （论文的数量 → 论文数量）、可带单字后缀（投稿|量、复现|率）、紧邻数字的候选加权
  （那个词就是这张图的类目名）；`derive_timing.find_keyword` 同步支持跳修饰助词定位 beat。
- furniture 移到 `data-track-index="3"`（实测 **track 0 不渲染**，而场景 clip 不透明，
  原先 furniture 一直被盖住），现在片头/片尾标记真的会显示。

### 画面：data-viz v2 与五种诚实版式

- 场景现在是**大标题 + 口径行 + 绘图区 + 数据来源**四层结构（此前只有一个 42px 小标题钉在
  左上角，与 furniture 规则线相撞）。
- 按语义自动选版式：`trend`（年份序列折线，pathLength 生长）/ `bars`（同一量纲零基线柱）/
  `cards`（量纲不同并列参照）/ `bignum`（单个数：1750亿、280倍）/ `statement`（没有可上屏的
  数字就上大字陈述，**绝不画假柱**）。轴顶标出 vmax + 单位，类目标签在基线下方，负向指标
  不用强调色。
- 折线修了两个真 bug：path 缺 `viewBox` 导致坐标被当作像素、整条线缩在左上角；末端数值
  标签居中溢出画面（改为两端留边 + nowrap）。`--data` 支持指定 `mode`，未给则自动判定。

### 新增：风格扫描与数据片示例

- `scripts/style_sweep.py`：同一段文案在 **15 条风格**里各渲一遍，输出
  5×3 抽帧表（`sweep-contact-sheet.jpg`）、15 格并排对比片（`sweep-grid.mp4`）与
  `sweep-report.json`。既用于风格选型，也是每条模板组装路径的端到端回归。
- `examples/demo-density/`：8 场 / 49.9s 数据片《数量在膨胀，密度在收缩》——旁白 + CC0 BGM +
  烧录字幕，全部数字可溯源（Stanford HAI AI Index 2025/2026、arXiv 年度报告、NeurIPS 2019、
  AAAI 2025、arXiv 2603.23640），每张图都带来源行。

## v2.4.3 — 2026-09-20

- **Zero-based bar scale**: bar heights were `18% + 70%·v/vmax` — a non-zero baseline, so 12 and
  130 rendered as roughly 1:5 instead of 1:11. Bars now use a pure linear scale from the axis
  (`h = 82%·v/vmax`, 2.5% floor). Measured on the rendered frame: 79 / 302 / 878 px for 12 / 45 /
  130 → ratios 0.090 / 0.344 / 1.000 against the theoretical 0.092 / 0.346 / 1.000.
- **Chart slot geometry**: bars were laid out as `left = 4% + j·(84/n)%`, which only fills 72% of
  the plot at n=2 (the chart looked left-shifted and the second category label drifted away from
  its bar). Bar centres are now distributed evenly across `[4 + w/2, 96 − w/2]` with `w = 60/n`.
- **Labels below the axis**: category labels sat at `bottom: 16%` *inside* the plot, so any bar
  taller than 16% painted over its own label — a white label on a white bar is invisible (the
  middle scene lost 「不可复现」). Labels now sit under the baseline (`top: calc(100% + 16px)`),
  which is also the standard chart grammar.

## v2.4.2 — 2026-09-20

- **data-viz honesty fix — no cross-unit axes**: 3倍 (a multiplier) and 三成 (a share) used to
  share one bar axis, so 3 rendered shorter than 30 — visually false. Charts now carry a `mode`:
  `bars` when every value shares a unit family, `cards` (metric callouts: value + label, no axis)
  when units differ, `fallback` when the copy carries no unit-bearing numbers. Chart category
  labels switched from muted gray to foreground at 0.78 opacity (dark palettes were unreadable).
- **Keyword extraction rebuilt on real word segmentation**: the old 2–4 char sliding window
  was boundary-blind — it happily returned fragments like「正能复现」or「果不到」. `make_video.py`
  now segments Chinese by **maximum-probability path** (Σ log word-frequency + length bonus −
  single-char penalty) using a bundled lexicon, then picks keywords among *content words*,
  preferring compounds of adjacent words (人工|智能 → 人工智能, 论文|数量 → 论文数量,
  小|模型 → 小模型). No shared-bigram duplicates (风格推荐 vs 推荐风格), no generic filler
  (变成/结果/开始), and chart category labels anchor to the nearest real content word
  (3倍 → 增长, 三成 → 复现). Segments like 在/手机/上, 人工/智能, 复现 now come out right.
  Compounds never span clause boundaries (交付|业主 across a comma used to swallow the whole
  scene's keywords, since per-clause keyword mapping found no match).
- **Lexicon**: `assets/lexicon/zh-words.txt` — 83k words derived from jieba `dict.txt`
  (MIT License, Copyright (c) 2013 Sun Junyi), trimmed to multi-char freq ≥ 15 / single-char
  freq ≥ 400, plus a project-authored domain supplement (AI / content creation / home-renovation
  vocabulary: 大模型, 分镜, 边界感, 增项…). Attribution is in the file header.

## v2.4.1 — 2026-09-20

- **data-viz charts carry real numbers (auto pipeline)**: the one-shot orchestrator used to
  blank every chart slot — no title, no values, hard-coded placeholder bar heights identical
  across scenes. New `{{BARS}}` contract: unit-bearing tokens are extracted from the copy
  (3倍 / 三成 / 千亿 / 2021年; bare unitless digits are deliberately not fabricated into bars),
  bar heights scale from the real magnitudes, the key bar takes the accent color, and each
  scene's chart lands in `storyboard/charts.json` (fallback scenes are honestly marked).
  `--data <json>` accepts a per-scene `{title, unit, labels, values, key}` array for exact
  control. Template colors now come from the wrapper palette (`--bg/--fg/--accent`) instead
  of non-existent `--km-*` vars that silently fell back to light-theme inks on dark films.
  Chart titles clip at clause boundaries, never mid-word.
- **Caption breaks**: unbreakable bigram and dangling-tail sets extended (结果/复现/手机/千亿…;
  从/在 bind forward), verb-initial heads favored — no more 结|果 or 手|机 splits; showcase
  captions byte-identical after the change (regression-checked).

## v2.4 — 2026-09-20

- **One-shot pipeline** (`scripts/make_video.py`): copy in → style recommendation with a full
  auditable decision trace → non-interactive confirmation gate (`--go`/`--style` passes) →
  auto storyboard (punctuation clause grouping 6–8s, keyword extraction, word-level ASR
  timing via derive_timing) → per-scene template assembly (id namespacing, timeline position
  remapping, slot filling, SVG placeholder for missing photo slots) → lint → render →
  finalize → verify. 15/15 styles assemble with zero lint errors. Auto mode is documented as
  the floor; agent-authored scenes remain the ceiling.

## v2.3.1 — 2026-09-20

- **Narration voice & prosody**: showcase re-voiced with a narration-grade male TTS
  (解说小明); the copy itself gained punctuation so pauses land on semantic boundaries —
  prosody, not a speed parameter, is what fixes "unnatural pacing". Film is now 46.43s.
- **Caption layout engine**: `build_captions.py` rewritten — hard ≤9 glyphs/line limit
  (fontsize 97 in a 936px text area), cues longer than two lines re-chunked recursively,
  scene assignment by word start (a word straddling a boundary no longer splits mid-word,
  e.g. 跑|完), and a readability score for break points: unbreakable bigrams (怎么/变成/一支…),
  no trailing 的/每/这 at line end, no leading 的 at line start, verb-initial breaks favored.
  No more flash cues like「频，」; no more edge-clipped lines.
- **Style recommender**: new `scripts/recommend_style.py` — any copy in, auditable decision
  trace out: text stats → 12 semantic axes with quoted evidence → film decision-table hit
  (incl. two-axis blend rules) → per-style scores with anti-evidence → primary + runner-up.
  Docs: `docs/style-recommendation.md`.
- **Fix (SVG filter region)**: a lone horizontal stroke in its own filtered `<g>` has a
  zero-height objectBoundingBox, so the default filter region clips the output to nothing —
  the s05 progress underline vanished from renders while being provably correct in the DOM.
  Fixed with `filterUnits="userSpaceOnUse"` full-canvas regions.

## v2.3 — 2026-09-20

- **Film-level style routing**: style is a whole-film decision recorded as `project.style`
  (validator enforces one style per film); film-level decision table added to `style-router.md`;
  per-scene mixing demoted to intentional long-form chapters. Fixes the v2.2 mistake of mixing
  three grammars inside one 37.5s film.
- **Narration-clock hard constraint**: new `scripts/derive_timing.py` derives scene boundaries
  (pause midpoints) and keyword beats (exact ASR token times) from word-level transcripts —
  hand-authored beats were measured up to 2.06s off the voice in v2.2.
- **BGM**: keyless CC0/CC-BY music sourcing via the Openverse audio API; BGM mixed at 0.18
  under narration with fade-in/out (finalize.py `--bgm`).
- **Asset matching**: rich `description` field as the primary handle for the render-front asset
  gate; `fetch_assets.py --sheet` renders a contact sheet for agent/human visual review.
- **SFX restraint**: default no SFX; when used, effects sit at -12dB with 30ms/120ms fades
  (v2.2's full-volume noise bursts read as jarring).
- **Showcase rebuilt**: `examples/showcase-project/` — 32.3s single-grammar (hand-sketch)
  film with narration, burned captions, CC0 piano BGM, and one semantically matched real photo;
  every visual payoff lands on its spoken keyword within ±0.3s. Replaces the v2.2
  mixed-style showcase.
- `build_captions.py`: strip leading punctuation and drop punctuation-only cues.

## v2.2 — 2026-09-20

- **Real-asset pipeline**: `scripts/fetch_assets.py` — per-scene semantic asset search and
  download (Pexels / Pixabay via optional keys, keyless Openverse + Wikimedia Commons, local
  library, bundled SFX), auto-backfills `local`/`attribution`/`license` into `scenes.json` and
  writes a shippable license manifest; resume-safe.
- **Audio**: `scripts/mix_audio.py` (narration + per-scene SFX at `startSec + atSec`) and
  `scripts/make_sfx.py` (synthesized bundled SFX pack: paper, page, pen, click, whoosh).
- **Material-style routes**: three new routes (15 total) — `collage-evidence` (torn-paper
  evidence wall), `hand-sketch` (self-drawing SVG strokes + pen tip along path),
  `paper-fold` (CSS 3D origami pop-up with crease lines, thickness, texture). Upgraded
  `editorial-collage` and `paper-diorama` with torn edges, thickness, texture, and asset slots.
- **Showcase case**: `examples/showcase-project/` — 37.5s fully narrated, caption-burned,
  real-footage case (5 scenes, 5 photos + 1 real timelapse video + 6 SFX, all licensed and
  recorded), covering the three material-style routes.
- Schema/docs: optional per-scene `assets[]` contract (scene-schema.md), style-router table
  updated, showcase docs and CI coverage.

## v2.1 — 2026-09-19

- Style gallery: four 10-second sample renders (clean-education × whiteboard-tutorial,
  dark-technical × data-viz, warm-editorial × editorial-collage, bold-social × kinetic-typography)
  under `examples/style-samples/`, plus a side-by-side comparison GIF.
- Added GitHub Actions CI (compile, doctor, storyboard validation, sample caption build).
- Fixed `doctor.py` coli probe (uses `--help`; older builds rejected `--version`).
- Fixed caption word-joining for ASR tokens (`build_captions.py`) and short-cue merging.
- Fixed in-scene caption vs. burned subtitle collision in the sample project (caption-safe
  area rule now enforced in the furniture spec).

## v2 — 2026-09-19

- Generalized beyond the reference video's four styles: 12-route style router
  (data-viz, kinetic-typography, whiteboard-tutorial, timeline-history, process-flow,
  map-geo added).
- Added bundled fallback renderer `scripts/render-browser.mjs` (headless Chrome + FFmpeg,
  no HyperFrames CLI dependency).
- Added pipeline scripts: `doctor.py`, `build_captions.py`, `finalize.py`, `verify.py`,
  optional `tts_edge.py` adapter.
- Added series furniture layer (branding independent of scene style).
- Added design token presets and per-route scene templates.
- Open-source engineering: MIT license, README, CONTRIBUTING, install script, gitignore.
- Example project: Swiss-sketch portrait composition with motion assertions.

## v1 — 2026-09-19

- Initial MVP: SKILL.md, scene schema + validator, 6-route router, HyperFrames demo
  composition, open-source research report, video analysis report.
