# Style router

按解释功能路由，不按视觉新鲜感路由。每条路由描述：适用内容、视觉语法、默认素材策略、运动语言、避免事项、HyperFrames 实现要点。

## 路由总表

| Route | Best for | Visual grammar | Default assets | Avoid |
|---|---|---|---|---|
| editorial-collage | events, evidence, culture, history, people | torn masks, crop windows, labels, arrows, parallax layers, editorial type | licensed photos, documents, maps, code-drawn marks | random scrapbooking without semantic relations |
| character-concept-comic | psychology, workplace, ethics, recurring dilemmas | one recurring character, panels, reaction poses, symbolic props, hard cuts | original/generated character sheets, SVG speech/impact marks | changing character identity between shots |
| paper-diorama | systems, ecology, engineering, invention, chronology | layered paper planes, tabs, folded mechanisms, top/three-quarter camera, assembly | generated paper-texture illustrations, SVG layers | fake depth made only by scaling a flat image |
| swiss-sketch | arguments, comparisons, methods, commentary | grid, large type, black/red/cream, line drawing, hand/pen reveal, generous whitespace | SVG line art, diagrams, typography | turning every scene into a static poster |
| ui-demo | exact operation and software evidence | screen crop, cursor, focus zoom, callouts, state transitions | screenshots/video captures | using UI when the point is conceptual |
| generated-cinematic | emotional or impossible illustrative beats | strong composition, restrained camera, short generated clips | image/video models | facts, precise labels, stable recurring characters without references |
| data-viz | 数量对比、趋势、排名、占比 | 图表即主角：坐标轴、条/线/环、直接标注数值、最小网格 | 自绘 SVG 图表，数据硬编码进 DOM | 3D 饼图、双轴炫技、无标签的纯装饰动画 |
| kinetic-typography | 金句、定义、转折、强观点 | 超大字重排、逐词/逐行入场、缩放强调、节奏剪切 | 纯文字 + 简单几何衬底，全部自绘 | 长段落上屏、每句都炸、遮挡字幕安全区 |
| whiteboard-tutorial | 概念推导、分步教学、算式/画法演示 | 手写笔迹逐步出现、圈注、箭头、擦除重来 | SVG 线稿 + stroke-dashoffset 手写感 | 一次性甩出整版内容、笔迹与叙述不同步 |
| timeline-history | 年表、大事记、演进过程 | 水平/垂直主轴线、节点、年代标签、前后叠压 | 自绘轴线 + 节点 + 短文本卡片 | 节点过密、无先后运动语义、随机漂浮 |
| process-flow | 流程、系统架构、决策分支 | 节点 + 连线、逐段点亮、分支高亮、容器分组 | 自绘 SVG 流程图，节点/边分离 | 一次全亮、连线交叉成网、节点文字溢出 |
| map-geo | 地理分布、空间关系、区域对比 | 简化轮廓地图、定位点、扩散圈、路径连线、区域填色 | 自绘简化 SVG 轮廓或授权地图底图 | 高精度国界争议细节、无比例感的炫技飞行 |
| collage-evidence | 需要真实照片/视频证据的叙事（历史、事件、产品、可信度论证） | 真实照片/视频卡、撕纸边缘、投影、色块 caption、档案标签 | Pexels/Pixabay/Openverse/Wikimedia 照片与视频（fetch_assets.py） | 无语义关系的随机堆图、素材全屏铺满 |
| hand-sketch | 观点、方法、步骤论证（带手作温度） | SVG 描边自绘线条、笔尖沿路径移动、feTurbulence 手感、网格留白 | 自绘 SVG 线稿 + 可嵌一张证据照片 | 堆卡片装饰、线条一次全部出现 |
| paper-fold | 科普、系统、结构演示（折纸特效） | perspective 3D 折叠立起、折痕阴影线、纸边厚度、纸纹 overlay、由后到前装配 | 纯 CSS/SVG 纸雕 + 翻纸音效 | 只有 scale 缩放的伪立体 |

## 路由详述

### editorial-collage — 编辑拼贴

- 适用内容：事件复盘、证据呈现、历史人物、文化语境、新闻背景。
- 视觉语法：撕边遮罩、裁切窗口、标签贴纸、箭头批注、多层视差、编辑感排版。
- 默认素材策略：授权图片/文档扫描件 + 代码绘制的标记物（胶带、角标、下划线）。无图时退化为纯排版拼贴，不放假图。
- 运动语言：mask reveal、纸片滑入、层间视差、盖章、crop zoom（从全图推到证据局部）。
- 避免事项：无语义关系的随手堆贴；素材之间没有指向同一论点。
- HyperFrames 实现要点：多层 `clip-path` + `fromTo` 位移错峰；视差用不同 duration 的 y 位移在同一 timeline 上叠加；盖章用 `scale: 1.6 → 1` + `ease: "power4.in"` 落下。

### character-concept-comic — 角色概念漫画

- 适用内容：心理、职场张力、伦理困境、反复出现的两难情境。
- 视觉语法：一个贯穿全片的角色、分格 panel、反应姿势、象征道具、硬切。
- 默认素材策略：原创角色设定图（生成或自绘 SVG 姿势），SVG 对话/冲击符号。
- 运动语言：panel snap（整格吸附入场）、姿势替换（同格内 pose A→B）、速度线、反应定格。
- 避免事项：角色形象跨镜头漂移；表情与叙述情绪不匹配。
- HyperFrames 实现要点：姿势替换用两组 SVG 的 `autoAlpha` 零时长切换，绝不用变形补间；panel 入场用 `fromTo(el, {scale:1.08, autoAlpha:0}, {scale:1, autoAlpha:1})`；速度线是有限次数的 stroke-dashoffset 动画。

### paper-diorama — 纸艺立体场景

- 适用内容：机制原理、工程结构、生态、发明、按时间装配的叙事。
- 视觉语法：层叠纸面、拉页 tab、折叠机构、俯视/四分之三视角、逐件装配。
- 默认素材策略：纸质感插画的分层 SVG（每层独立 group），代码绘制投影。
- 运动语言：lift（层抬升露出下层）、fold、slot（插入槽位）、铰链旋转、自上而下装配。
- 避免事项：只靠缩放一张平面图伪造景深；层间没有真实遮挡关系。
- HyperFrames 实现要点：真实遮挡靠 DOM 层叠顺序 + `transform-origin` 铰链旋转（`rotateX` 需 `transformPerspective`）；投影用伪元素阴影随位移同步 `fromTo`；每层一个 fromTo，显式起始状态。

### swiss-sketch — 瑞士平面手绘

- 适用内容：论点、对比、方法、商业/社会评论、抽象关系。
- 视觉语法：网格、超大字、黑/红/米白三色、线描、手绘显现、大量留白。
- 默认素材策略：全部 SVG 线稿 + 排版，无位图。
- 运动语言：stroke draw、红色对位标记、字体锁定（type lockup）、沿网格平移。
- 避免事项：把每个 scene 做成静态海报；红点乱飞不带语义。
- HyperFrames 实现要点：线稿用 `stroke-dasharray` + `fromTo(strokeDashoffset)` 画线；文字锁定用逐元素 `fromTo(y:24→0, autoAlpha:0→1)` 错峰；对位标记用 scale 微弹（`back.out(2)`）。

### ui-demo — 界面演示

- 适用内容：确切的软件操作、界面状态证据；屏幕行为本身就是论据时才用。
- 视觉语法：屏幕裁切、光标、焦点缩放、callout 标注、状态前后对比。
- 默认素材策略：真实截图或录屏切片（本地资产）；空态可用自绘假界面 SVG 占位。
- 运动语言：cursor travel（缓入缓出的路径移动）、press/release、focus zoom、state before/after。
- 避免事项：论点是概念性的时候硬套 UI；光标移动节奏与叙述脱节。
- HyperFrames 实现要点：光标用 `motionPath` 或分段 fromTo 走显式路径；focus zoom 用容器 `scale` + `transformOrigin` 指向目标控件；高亮框用描边 fromTo 画出，不要用 box-shadow 闪烁。

### generated-cinematic — 生成式电影感

- 适用内容：情绪镜头、不可能画面、氛围过渡；使用频率压到最低。
- 视觉语法：强构图、克制运镜、短生成片段。
- 默认素材策略：图像/视频模型生成的本地片段；失败时退化为代码绘制的抽象光效/剪影。
- 运动语言：单一方向慢推或慢拉、淡入淡出、硬切进出。
- 避免事项：承载事实、精确标签、需要跨镜头一致的角色。
- HyperFrames 实现要点：`<video>` 由框架接管播放，只 trim 不用 GSAP 驱动；容器上叠加的标注文字用独立 fromTo；转场用两个 clip 的时间轴衔接而非 mask 炫技。

### data-viz — 数据图表

- 适用内容：数量对比、随时间趋势、排名变化、占比构成、指数级差异。
- 视觉语法：图表即主角——柱/条/折线/环/点阵；坐标轴与单位一开始就在；数值直接标注在图形上，弱化图例；网格线极淡。
- 默认素材策略：自绘 SVG 图表，数据点硬编码进 DOM（`data-value` 属性），无外部图表库。
- 运动语言：条形生长（scaleY 从基线起）、折线描画（strokeDashoffset）、数值 counter（显式 fromTo 到最终值）、排名条互换位置（y 位移交换）、关键项 accent 高亮 + 其余项压灰。
- 避免事项：3D 饼图、双 Y 轴炫技、先出图表后出坐标轴（先轴后数据）、为装饰而动的无意义浮动。
- HyperFrames 实现要点：条形生长必须 `transformOrigin` 固定在基线端 + `fromTo(scaleY:0→1)`，禁止改 height（触发布局）；折线用 `stroke-dasharray: L; fromTo(strokeDashoffset: L→0)`；数值滚动用 `textContent` 快照不安全，改为数字层上下交换或 `snap` 步进补间并锁终值；高亮对比用 `gsap.to(其余项, {opacity:0.35})` 的显式两态。

### kinetic-typography — 纯文字冲击

- 适用内容：金句、定义、强观点、转折点、章节宣言；叙述只有一句核心话时。
- 视觉语法：超大字重、逐词或逐行入场、关键词缩放/变色强调、节奏式硬切、极简几何衬底（色块、下划线、框）。
- 默认素材策略：纯文字 + 自绘几何衬底，零位图；换行手动控制，禁止依赖自动折行。
- 运动语言：word slam（词从大到小砸入）、行替换（旧行上移出、新行上移入）、关键词 scale 脉冲一次（有限次数）、下划线/色块从左扫入。
- 避免事项：长段落实质内容上屏（那是字幕的事）；每句话都炸（一次 scene 只强调一个词）；字号大到侵入字幕安全区或顶到画面边缘。
- HyperFrames 实现要点：词入场 `fromTo(el, {scale:1.4, autoAlpha:0}, {scale:1, autoAlpha:1, ease:"power3.out"})`；行替换用两行绝对定位同槽位 + autoAlpha/y 交换；下划线 scaleX `transformOrigin:left`；一切位移只用 transform。

### whiteboard-tutorial — 教学白板

- 适用内容：概念推导、分步教学、算式演算、画法演示、"为什么"类解释。
- 视觉语法：手写笔迹逐步出现、圈注重点、箭头连接、擦除重来、便签/下划线辅助；笔迹与叙述逐句对齐。
- 默认素材策略：全部 SVG stroke 线稿（文字轮廓或手写感路径），代码绘制；不用真实手写视频。
- 运动语言：stroke draw 逐笔出现、圈注（椭圆描边一遍）、箭头生长、整块内容擦除（autoAlpha 归零 + 轻微位移退出）后写新内容。
- 避免事项：一次性甩出整版推导；笔迹速度与叙述语速无关；内容太多导致字号不可读。
- HyperFrames 实现要点：所有笔迹 `stroke-dasharray` + `fromTo(strokeDashoffset)`，每笔时长按笔画长度估；圈注在关键词出现后 +0.2s 开始；擦除用零时长 autoAlpha set 或 0.3s fromTo，禁止 repeat:-1 的"擦拭循环"；一屏最多 3-4 步，超出就拆 scene。

### timeline-history — 时间轴/大事记

- 适用内容：年表、大事记、技术演进、人物履历、因果链条的先后呈现。
- 视觉语法：一条主轴线（水平或垂直）、节点/刻度、年代标签、事件短卡片、按先后依次点亮；关键节点放大高亮。
- 默认素材策略：自绘 SVG 轴线 + DOM 节点卡片，全部代码绘制。
- 运动语言：轴线先画出（stroke draw），节点按时间顺序 pop（scale + autoAlpha），事件卡滑入，关键节点 accent 高亮 + 轻推镜头（容器 x/y 位移）。
- 避免事项：节点过密（一屏超过 5 个就滚动/分段）；节点出现顺序不等于时间顺序；无语义的均匀节奏（关键事件应有更长的停留）。
- HyperFrames 实现要点：轴线 stroke draw 与第一个节点入场有 0.1s overlap；节点 stagger 用 `stagger: {each: 0.15}` 但关键节点单独 fromTo 加长；镜头平移用外层容器 `fromTo(x)`，内部元素相对容器定位；每个节点入场必须在时间轴上有显式位置（不用 delay 链）。

### process-flow — 流程图/系统架构

- 适用内容：流程步骤、系统架构、数据流向、决策分支、多方关系。
- 视觉语法：节点框 + 连线、逐段点亮路径、分支条件标签、容器分组（虚线框圈出子系统）、输入/输出端点。
- 默认素材策略：自绘 SVG，节点与边分离为独立元素（边用 line/path，节点用 rect + text），便于按路径分步点亮。
- 运动语言：连线生长（strokeDashoffset 从源到汇）、节点点亮（边框/填充两态切换）、数据点沿路径移动（motionPath 或分段 fromTo）、分支高亮（走到的分支 accent，未走分支压灰）。
- 避免事项：所有元素一次全亮；连线交叉成网状难以追踪；节点文字溢出边框；动画方向与数据流向不一致。
- HyperFrames 实现要点：边用 `fromTo(strokeDashoffset)` 且 `stroke-dasharray` 等于路径实际长度；节点两态用 `fromTo({opacity:0.4},{opacity:1})` + 描边色 fromTo（不 tween 颜色字符串以外的复合值）；流动物用 `motionPath` 需在 GSAP 注册插件一次，否则用分段 translate；分支对比先亮目标分支再压灰其余分支，顺序不可反。

### map-geo — 地理/空间

- 适用内容：地理分布、区域对比、迁移/扩散路径、空间关系、选址逻辑。
- 视觉语法：简化轮廓地图（低细节、无争议边界）、定位 pin、扩散圈（有限次数）、路径连线、区域填色对比。
- 默认素材策略：自绘简化 SVG 轮廓（或授权底图本地化），点位与标注代码绘制；不用在线瓦片。
- 运动语言：底图先淡入、pin 逐个落下（y 位移 + 微弹）、扩散圈 scale 1→2 且只重复 2 次后定格、路径 stroke draw、区域填色 fromTo 两态。
- 避免事项：高精度国界/争议边界；无比例感的长距离炫技飞行线；点位过密无聚合；地图只是背景板而信息全在文字里。
- HyperFrames 实现要点：扩散圈 `fromTo(scale:0.6→1.8, autoAlpha:0.8→0)` 且 `repeat: 2`（有限）后用零时长 set 定格最终状态；pin 落下 `fromTo(y:-24→0, ease:"bounce.out")`；路径连线同 strokeDashoffset 技巧；镜头区域聚焦用外层容器 scale + transformOrigin 指向目标区域。

## 路由打分机制

对每个 scene 按 0–2 分为下列轴打分，取最高分路由：

- 证据/文档依赖 → editorial-collage；
- 复现的人类冲突/情绪 → character-concept-comic；
- 物理机制/空间装配 → paper-diorama；
- 抽象命题/对比/评论 → swiss-sketch；
- 确切点击/状态序列 → ui-demo；
- 氛围/不可能画面 → generated-cinematic；
- 数量、趋势、排名、占比是叙事核心 → data-viz；
- 单句核心观点、需要冲击力 → kinetic-typography；
- 分步推导/教学过程本身是内容 → whiteboard-tutorial；
- 明确的时间先后/演进 → timeline-history；
- 系统/流程/分支关系 → process-flow；
- 地理/空间分布是叙事核心 → map-geo。

打分细则：

1. 每轴打 0–2：0 = 无关；1 = 相关但非核心；2 = 去掉这一轴场景就不成立。
2. 最高分胜出；平分时用本章主导风格，除非风格对比本身承载叙事含义（如"过去用 timeline，现在用 process-flow"表转折）。
3. 如果两个 2 分轴并存（如"某技术历年份额变化"同时命中 data-viz 和 timeline-history），拆成两个 scene，各用一个路由，不要在同一 scene 里混两套图表语法。
4. 没有任何轴达到 1 分时，回退到章节主导风格，并在 storyboard 中标注原因。

## Cross-style continuity

风格切换时保持全局一致：

- typography family and subtitle treatment;
- one accent color or a controlled accent mapping;
- safe areas and persistent series furniture（见 `series-furniture.md`）;
- motion cadence: build, breathe, resolve;
- recurring icon or character identity;
- audio palette and loudness.

Use style changes as chapter punctuation, not every-shot novelty.
