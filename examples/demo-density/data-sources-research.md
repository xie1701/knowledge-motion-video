# AI 论文「数量膨胀 vs 可复现性 / 效率密度」可核验数据报告

主题：为 60 秒中文知识科普短片收集**可核验的真实数字**。
采集日期：2026-09-20。所有 URL 均为实际访问或检索命中的公开链接。

**可信度标签约定**

- **实测**：原始实验/基准测量值（有人跑了、有方法论）
- **机构报告**：机构统计口径（Stanford HAI AI Index、arXiv 官方年报等）
- **机构估计**：由第三方用公开信息反推的估算（Epoch AI、AI Index 的碳排放/成本估算）
- **报道**：媒体或公司口径的自述、官方新闻稿

⚠️ 全片最需要小心的一点：**「AI 论文三倍增长」这个说法在不同口径下不成立或只算勉强成立**。Stanford AI Index 自己的措辞是 2013→2023「nearly tripled（接近三倍）」，但给出的数字 102,000 → 242,000 实际是 **2.37 倍**；2026 版改用「more than doubled（翻了一倍多）」描述 2013→2024 的 102,000 → 258,000（**2.53 倍**）。若要保留「三倍」，建议改用**会议投稿量**（NeurIPS 2021→2025 约 2.4 倍，2018→2025 约 4.4 倍）或**专利数**（2010→2023，3,833 → 122,511，32 倍）来承载，或直接说「十余年间翻了一倍多」。

---

## 一、AI 论文数量的增长（起点年 vs 终点年）

### 1.1 Stanford AI Index：AI 论文总量（2013 vs 2023/2024）

| 项 | 内容 |
|---|---|
| **数值** | 约 102,000（2013）→ 超过 242,000（2023）→ 约 258,000（2024） |
| **单位** | 篇/年（CS 及相关学科 AI 相关论文，Scopus 口径） |
| **年份** | 2013 / 2023 / 2024 |
| **来源机构** | Stanford HAI, AI Index Report（2025 版、2026 版） |
| **URL** | https://hai.stanford.edu/ai-index/2025-ai-index-report/research-and-development ; https://hai.stanford.edu/ai-index/2026-ai-index-report/research-and-development ; 2026 PDF: https://hai.stanford.edu/assets/files/ai_index_report_2026.pdf |
| **原文摘录** | 2025 版：「Between 2013 and 2023, the total number of AI publications in venues related to computer science and other scientific disciplines **nearly tripled**, increasing from approximately 102,000 to over 242,000.」<br>2026 版（经 IEEE Spectrum 转引）：「The number of AI-related computer science publications has **more than doubled** over the past decade, from **102,000 to 258,000**.」 |
| **可信度** | 机构报告（Scopus 数据） |

补充（同一来源，2026 版）：**AI 占 CS 论文份额** 21.6%（2013）→ 41.8%（2023）；2024 年 AI 论文中 **68%+ 来自学术界**，政府 11.5%、产业 12.5%。
URL: https://hai.stanford.edu/ai-index/2025-ai-index-report/research-and-development

### 1.2 arXiv：年度新投稿量（2023 / 2024 / 2025）

| 项 | 内容 |
|---|---|
| **数值** | 208,493（2023）→ 244,031（2024）→ **284,486（2025）**；2025 同比 +16% |
| **单位** | 篇/年（全站新投稿） |
| **年份** | 2023–2025 |
| **来源机构** | arXiv（Cornell Tech）官方年报 |
| **URL** | https://info.arxiv.org/about/reports/2023_arXiv_annual_report.pdf ; https://info.arxiv.org/about/reports/2025_arXiv_annual_report.pdf |
| **原文摘录** | 「arXiv received **284,486** new submissions in 2025, up from **244,031** the previous year – an increase of over 16%.」「Computer science (CS) is arXiv's fastest growing category, and in 2025 CS papers comprised **46%** of arXiv's submissions.」 |
| **可信度** | 机构报告（官方年报，可视为实测计数） |

- 单月纪录：2023-10 为 **20,710**；2024-10 为 **24,226**；2025-10 为 **27,692**。
  URL: https://info.arxiv.org/about/reports/2023_arXiv_annual_report.pdf ; https://blog.arxiv.org/2024/11/04/arxiv-sets-new-record-for-monthly-submissions-again/ ; https://info.arxiv.org/about/reports/2025_arXiv_annual_report.pdf
- 累计总量：**3,173,333** 篇（截至 2026-09-20；2022 年突破 2,000,000）。
  URL: https://arxiv.org/show_monthly_submissions
- 官方口径提醒：arXiv 2025 年报明确说 2025 年「AI 生成论文」激增、拒稿率上升，这是**质量侧**的一手证据。
  原文：「arXiv has seen a significant increase in rejection rates ... This increase is to due to: Overall increases in submissions (LLM and AI as research topics that also speed up research writing) / Increases in marginal and below the bar AI-generated content ...」
  URL: https://info.arxiv.org/about/reports/2025_arXiv_annual_report.pdf

### 1.3 顶会投稿量（更适合做「三倍」对比图）

| 项 | 内容 |
|---|---|
| **数值** | NeurIPS 主赛道：9,122（2021）→ 15,671（2024）→ **21,575（2025）**，2025 同比 +38%，录用 5,290（24.5%） |
| **单位** | 篇/届 |
| **年份** | 2021 / 2024 / 2025 |
| **来源机构** | NeurIPS 程序委员会官方博客 |
| **URL** | https://blog.neurips.cc/2025/09/30/reflections-on-the-2025-review-process-from-the-program-committee-chairs/ |
| **原文摘录** | 「The main track this year received **21,575** valid paper submissions, of which 5,290 were accepted.」 |
| **可信度** | 实测/官方（会议投稿统计）；2021 年 9,122 的数字来自二手统计站 https://csconfstats.xoveexu.com/conferences/neurips/ ，建议二次核对官方记录 |

| 项 | 内容 |
|---|---|
| **数值** | ICLR：11,565（2025）→ 19,525（2026，+69%） |
| **单位** | 篇/届 |
| **年份** | 2025 / 2026 |
| **来源机构** | ICLR 官方博客 / 官方社媒 |
| **URL** | https://blog.iclr.cc/2026/03/31/a-retrospective-on-the-iclr-2026-review-process/ |
| **原文摘录** | 「ICLR 2026 received **19,525** valid, format-compliant submissions. 5,355 papers were accepted ...」 |
| **可信度** | 官方（会议统计） |

### 1.4 对照：AI 专利（增长最夸张的一条）

| 项 | 内容 |
|---|---|
| **数值** | 3,833（2010）→ 122,511（2023）；2023 同比 +29.6%；中国占 2023 年授权量 69.7% |
| **单位** | 件/年 |
| **年份** | 2010 / 2023 |
| **来源机构** | Stanford HAI, AI Index 2025 |
| **URL** | https://hai.stanford.edu/ai-index/2025-ai-index-report/research-and-development |
| **原文摘录** | 「Between 2010 and 2023, the number of AI patents has grown steadily and significantly, ballooning from **3,833 to 122,511**.」 |
| **可信度** | 机构报告 |

---

## 二、AI/ML 论文的可复现性（注明样本与方法）

### 2.1 复现实验：255 篇 ML 论文，成功率 63.5%（Raff, NeurIPS 2019）

| 项 | 内容 |
|---|---|
| **数值** | **63.5%** 复现成功率（255 篇论文，1984–2017） |
| **单位** | %（人工复现实验） |
| **年份** | 2019（论文） |
| **来源机构** | Edward Raff / NeurIPS 2019 |
| **URL** | https://papers.nips.cc/paper/8787-a-step-toward-quantifying-independently-reproducible-machine-learning-research ; https://arxiv.org/abs/1909.06674 |
| **原文摘录** | 「We take the first step toward a quantifiable answer by manually attempting to implement **255 papers** published from 1984 until 2017, recording features of each paper, and performing statistical analysis...」（原文摘要）<br>成功率数字见 Patterns 2026 转引：「Raff estimated the reproducibility rate for machine learning (ML) studies to be **63.5%**.」 |
| **可信度** | **实测**（独立复现实验，非问卷） |

作者补充细节（作者自述，转载于 The Gradient）：「In the 24 cases where I never got a reply, I was able to reproduce their results only once (a **4%** success rate).」
URL: https://thegradient.pub/independently-reproducible-machine-learning/ — 可信度：报道（作者自述）

### 2.2 复现实验：被引最高的 AI 论文，成功率 50%（Gundersen et al., AAAI 2025）

| 项 | 内容 |
|---|---|
| **数值** | **(部分) 成功率 50.0%**；22 篇可复现目标论文（从 30 篇高被引论文中筛出），限时 40 工作小时；成功者平均耗时 34 小时 |
| **单位** | %（限时复现实验） |
| **年份** | 2025 |
| **来源机构** | Gundersen, Cappelen, Mølnå et al. / AAAI 2025 |
| **URL** | https://ojs.aaai.org/index.php/AAAI/article/view/34818 （数字与描述转引自已发表的同行评议论文 https://www.cell.com/patterns/fulltext/S2666-3899(26)00149-2 ） |
| **原文摘录** | 「Gundersen et al. attempted to reproduce the **30 most cited AI studies** and found an average reproducibility rate of **50.0%**.」「They found a shockingly low (partial) success rate of **50%** within a time limit of 40 working hours. The average successful reproduction, including partial success, took the authors **34 h** out of a 40-h time limit.」 |
| **可信度** | **实测**（独立复现实验）；样本量小（22 篇），需注明 |

### 2.3 文献计量：400 篇 AI 论文，无一篇「完全可复现」（Gundersen & Kjensmo, AAAI 2018）

| 项 | 内容 |
|---|---|
| **数值** | **0 篇**记录全部可复现变量；每个因素仅有 **20%–30%** 的变量被记录 |
| **单位** | %（文献计量打分） |
| **年份** | 2018（样本为 IJCAI/AAAI 论文） |
| **来源机构** | Gundersen & Kjensmo / AAAI 2018 |
| **URL** | https://ojs.aaai.org/index.php/AAAI/article/view/11503 （DOI: 10.1609/aaai.v32i1.11503） |
| **原文摘录** | 「A total of **400 research papers** from the conference series IJCAI and AAAI have been surveyed using the metrics. Findings: **None of the papers document all of the variables. The metrics show that between 20% and 30% of the variables for each factor are documented.**」 |
| **可信度** | **实测**（人工文献打分，非问卷） |

### 2.4 2026 年最新：918 篇 AI 论文的「复现成本」研究

| 项 | 内容 |
|---|---|
| **数值** | 分析 918 篇（从 1,061 篇中筛出）2022–2024 年 7 大顶会/期刊论文；**6.72% 的代码仓库链接已失效或为空**；NeurIPS 公开实现率 80.17%；公开数据率 94.01%；联系作者索取补充材料**不成功率为 36.84%** |
| **单位** | %（人工打分 + 文献调研） |
| **年份** | 2022–2024 样本，2026 年发表 |
| **来源机构** | Snelleman, Hermann, Gundersen / Patterns (Cell Press) |
| **URL** | https://www.cell.com/patterns/fulltext/S2666-3899(26)00149-2 |
| **原文摘录** | 「We review **918 publications between 2022 and 2024** at top AI venues ... **6.72%** of implementation repository links were broken.」「even NeurIPS, with a public rate of **80.17%**, has 23.97% of studies with a cost of six or higher」 |
| **可信度** | **实测**（人工标注，含二次评审与 ICC 一致性检验） |

### 2.5 全科学口径的问卷（背景用，非 AI 专属）

| 项 | 内容 |
|---|---|
| **数值** | 调查 **1,576** 名研究者：**>70%** 曾尝试复现他人实验失败；**>50%** 复现自己实验失败；约 **52%** 认为存在「显著的」可复现性危机 |
| **单位** | %（在线问卷，自报） |
| **年份** | 2016 |
| **来源机构** | Monya Baker / Nature（Springer Nature 读者调查） |
| **URL** | https://www.nature.com/articles/533452a |
| **原文摘录** | 「More than **70% of researchers** have tried and failed to reproduce another scientist's experiments, and more than half have failed to reproduce their own experiments.」（Nature 原文摘要行） |
| **可信度** | **问卷自报**（不是复现实验，不能等同于真实失败率） |

### 2.6 数据泄漏：17 个领域、294 篇论文（Kapoor & Narayanan, Patterns 2023）

| 项 | 内容 |
|---|---|
| **数值** | **17 个研究领域**发现数据泄漏错误，波及 **294 篇论文**（正式发表版口径；预印本 arXiv 2207.07048 为 329 篇 / 20 篇综述） |
| **单位** | 篇 / 领域 |
| **年份** | 2022（预印本）/ 2023（正式发表） |
| **来源机构** | Princeton 大学（Sayash Kapoor, Arvind Narayanan）/ Patterns |
| **URL** | https://pubmed.ncbi.nlm.nih.gov/37720327/ ; https://www.sciencedirect.com/science/article/am/pii/S2666389923001599 |
| **原文摘录** | 「Through a survey of literature in fields that have adopted ML methods, we find **17 fields** where leakage has been found, collectively affecting **294 papers** and, in some cases, leading to wildly overoptimistic conclusions.」 |
| **可信度** | **实测**（系统性文献综述 + 错误复算） |

### 2.7 ⚠️ 未找到可核验来源的一条常见说法

网上流传「同时共享代码与数据的论文可复现率约 86%，仅共享数据约 33%」（见 sandgarden.com 等二手页面）。**未找到可核验的原始论文或数据集**，推测为二手转述或对多份研究的拼接。**不建议上屏**。

---

## 三、大模型参数规模里程碑

### 3.1 GPT-3：1750 亿参数（2020）

| 项 | 内容 |
|---|---|
| **数值** | **175,000,000,000（175B）** 参数；同一系列最大训练到 175B，最小 125M，跨三个数量级 |
| **单位** | 参数个数 |
| **年份** | 2020 |
| **来源机构** | OpenAI / NeurIPS 2020（Brown et al.） |
| **URL** | https://arxiv.org/abs/2005.14165 ; https://openai.com/index/language-models-are-few-shot-learners/ |
| **原文摘录** | 「Specifically, we train GPT-3, an autoregressive language model with **175 billion parameters**, 10x more than any previous non-sparse language model.」 |
| **可信度** | **实测**（官方技术报告，明确披露） |

### 3.2 GPT-4：参数从未公开（2023）

| 项 | 内容 |
|---|---|
| **数值** | **未披露**。GPT-4 技术报告明确不公开架构、模型规模、硬件、训练算力、数据等 |
| **单位** | — |
| **年份** | 2023 |
| **来源机构** | OpenAI, GPT-4 Technical Report |
| **URL** | https://arxiv.org/abs/2303.08774 ; https://cdn.openai.com/papers/gpt-4.pdf |
| **原文摘录** | 「Given both the competitive landscape and the safety implications of large-scale models like GPT-4, this report contains **no further details about the architecture (including model size), hardware, training compute, dataset construction, training method, or similar**.」（该句被多方公开引用；本条摘录来自公开转引，建议正式引用前核对报告原文段落） |
| **可信度** | 官方声明（未披露即事实）；网上流传的「GPT-4 为 1.8 万亿参数」出自 Semafor 引述匿名信源，**不可作为事实** |

### 3.3 开源模型参数量（2024）

| 模型 | 参数量 | 时间 | 来源 URL | 原文摘录 | 可信度 |
|---|---|---|---|---|---|
| Llama 3 | **8B / 70B**（预训练 **>15 万亿 tokens**） | 2024-04-18 | https://ai.meta.com/blog/meta-llama-3/ ; https://huggingface.co/meta-llama/Meta-Llama-3-70B | 「Our new **8B and 70B parameter** Llama 3 models...」/「Llama 3 was pretrained on over **15 trillion tokens**」 | 官方模型卡（实测） |
| Llama 3.1 | **405B**（同时有 8B/70B） | 2024-07-23 | https://ai.meta.com/blog/meta-llama-3-1/ | 405B 为最大开源密集模型 | 官方模型卡 |
| Qwen2 | **0.5B / 1.5B / 7B / 72B** + MoE（Qwen2-57B-A14B） | 2024-06 | https://arxiv.org/html/2407.10671v1 | 「Our release comprises four dense models with parameter counts of **0.5 billion, 1.5 billion, 7 billion, and 72 billion**, plus a Mixture-of-Experts model」 | 技术报告（实测） |
| Qwen2.5 | **0.5B–72B 共 7 个规模** | 2024-09-19 | https://qwenlm.github.io/blog/qwen2.5/ ; https://huggingface.co/collections/Qwen/qwen25 | 「available in various sizes, including: Qwen2.5: 0.5B, ... Qwen2.5-72B」 | 官方发布（实测） |

补充（AI Index 2026）：「Parameter counts have stayed near **1 trillion** for three years, though reporting from frontier labs has stopped.」
URL: https://hai.stanford.edu/ai-index/2026-ai-index-report/research-and-development — 可信度：机构报告

---

## 四、端侧小模型跑在手机上（实测数字）

### 4.1 Apple：~3B 端侧模型，iPhone 15 Pro 上 30 tokens/s

| 项 | 内容 |
|---|---|
| **数值** | 参数量 **~3B**；量化 **平均 3.7 bits/weight**（2-bit+4-bit 混合；可压到 3.5 bits/weight）；iPhone 15 Pro 上 **生成速度 30 tokens/s**，首 token 延迟约 **0.6 ms/prompt token** |
| **单位** | tokens/s、ms、bits/weight |
| **年份** | 2024（WWDC24 / 技术报告） |
| **来源机构** | Apple（Apple Intelligence Foundation Language Models） |
| **URL** | https://machinelearning.apple.com/research/introducing-apple-foundation-models |
| **原文摘录** | 「With this set of optimizations, on **iPhone 15 Pro** we are able to reach time-to-first-token latency of about **0.6 millisecond per prompt token**, and a generation rate of **30 tokens per second**.」「the model can be compressed to **3.5 bits-per-weight** without significant quality loss」 |
| **可信度** | **实测**（厂商自测，方法论公开） |

### 4.2 第三方实测：Qwen2.5-1.5B（4-bit）在四类设备上的持续推理

| 设备 | 实测速度 | 备注 |
|---|---|---|
| iPhone 16 Pro（A18 Pro / MLX） | 峰值 **40.49 tokens/s** → 稳定热点态 **23.67 tokens/s**（20 次连续推理内下降 **41.5%**） | 3 次迭代即进入 Warm 态 |
| Samsung Galaxy S24 Ultra（骁龙 8 Gen 3 / MLC-LLM） | 平均 **10.83 tokens/s**，处理器稳压后 **10.38±0.44 tokens/s**（较峰值 −22%） | GPU 从 1000MHz 降到 720–770MHz |
| Raspberry Pi 5 + Hailo-10H NPU | **6.914 tokens/s**，整机功耗 **1.87 W**，**270.5 mJ/token**，吞吐变异系数 0.04% | 论文中最省电、最稳定 |
| 笔记本 RTX 4050（vLLM） | **131.7 tokens/s**，功耗 ~34 W，**297.3 mJ/token** | 电池供电被限频 |

| 项 | 内容 |
|---|---|
| **数值** | 同上表 |
| **单位** | tokens/s、W、mJ/token |
| **年份** | 2026（论文） |
| **来源机构** | Conscious Engines（arXiv 预印本） |
| **URL** | https://arxiv.org/html/2603.23640v2 |
| **原文摘录** | 「the iPhone 16 Pro loses roughly **40%** of its peak throughput within three iterations and settles into a Hot-state plateau near **23.7 tok/s**」「the Hailo-10H sustains **6.9 tok/s** at under 2 W」「Qwen 2.5 1.5B (4-bit quantised) ... a **sub-1 GB memory footprint**」 |
| **可信度** | **实测**（第三方独立基准，含方法论与局限声明；属预印本，非同行评议定稿） |

### 4.3 手机 SoC 厂商口径（报道，需标注为厂商宣称）

| 项 | 内容 |
|---|---|
| **数值** | MediaTek Dimensity 9300+：**7B 模型 22 tokens/s**（启用 NeuroPilot 推测解码）；支持 1B/7B/13B，可扩展到 33B |
| **单位** | tokens/s |
| **年份** | 2024 |
| **来源机构** | MediaTek 官方新闻稿 |
| **URL** | https://www.mediatek.com/press-room/mediatek-boosts-flagship-smartphone-performance-with-dimensity-9300-soc |
| **原文摘录** | 「With NeuroPilot Speculative Decode Acceleration, Dimensity 9300+ can run LLMs with **seven billion parameters at 22 tokens per second**.」 |
| **可信度** | **报道**（厂商宣称，非第三方实测） |

| 项 | 内容 |
|---|---|
| **数值** | Qualcomm：Llama 2-7B 在 Adreno GPU 上 **>13 tokens/s**；Snapdragon X Elite 上 Llama 2-7B 最高 **30 tokens/s**（CPU） |
| **单位** | tokens/s |
| **年份** | 2023 |
| **来源机构** | Qualcomm Technologies 白皮书 |
| **URL** | https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/Unlocking-on-device-generative-AI-with-an-NPU-and-heterogeneous-computing.pdf |
| **原文摘录** | 「Llama 2-7B can generate **more than 13 tokens per second** on the Adreno...」「On Snapdragon X Elite, Llama 2-7B ran at up to **30 tokens per second** on the Qualcomm Oryon CPU.」 |
| **可信度** | **报道**（厂商白皮书）；另有开发者实测反馈 8B 模型约 **5.1 tokens/s**（论坛帖 https://mysupport.qualcomm.com/supportforums/s/question/0D5dK00000GkGOtSAN/ ，可信度：报道/个人实测） |

### 4.4 论文级优化：1B 级模型手机端预填充突破 1000 tokens/s

| 项 | 内容 |
|---|---|
| **数值** | **>1,000 tokens/s 预填充**（Qwen1.5-1.8B，NPU 方案）；另有 Gemma-2B 达 **102 tokens/s** 生成速度 |
| **单位** | tokens/s |
| **年份** | 2025（ASPLOS '25，作者版含 2024 预印本 arXiv 2407.05858） |
| **来源机构** | 上海交大等（ASPLOS 2025 论文 mllm-NPU） |
| **URL** | https://xumengwei.github.io/files/ASPLOS25-NPU.pdf ; 预印本 https://arxiv.org/html/2407.05858v1 |
| **原文摘录** | 「For the first time, mllm-NPU achieves more than **1,000 tokens/sec prefilling** for a billion-sized model (Qwen1.5-1.8B)」（数字来自检索摘要；抓取 arXiv HTML 页面时返回异常，**建议引用前核对 PDF 正文**） |
| **可信度** | **实测**（同行评议论文，但本条摘录未完成直接核验） |

### 4.5 端侧评测框架（可作方法论背书）

- **MobileAIBench**（arXiv 2406.10290）：在同一批真机上测 LLM/LMM 的时延、内存、CPU 占用与电量消耗。https://arxiv.org/abs/2406.10290
- **COSTS 手机实测研究**（arXiv 2410.03613）：在多款商用手机上测 7B 模型（llama.cpp / MLC-LLM），发现骁龙 8 Gen 3（小米 14 Pro）吞吐约为 Dimensity 9300 的 80%。https://arxiv.org/html/2410.03613v1
- **MLPerf Mobile**（MLCommons 官方基准，v6.0 起加入 Llama 3.1/3.2 生成式 AI 项）：https://mlcommons.org/2026/06/mlperf-mobile-v6/

关于「第一次在手机上跑通 7B」的确切时间点：**未找到可核验的单一时点声明**。可核验的里程碑是厂商动作——Qualcomm 与 Meta 于 **2023-07** 宣布 Llama 2 将在 **2024 年起**的旗舰手机上端侧运行（https://www.qualcomm.com/news/releases/2023/07/qualcomm-works-with-meta-to-enable-on-device-ai-applications-usi ），MediaTek 于 2024 年 MWC 演示 Dimensity 9300/8300 支持 Llama 2 7B。

---

## 五、效率密度侧的其他硬数字（成本 / 能耗 / 单位算力产出）

### 5.1 推理价格：18 个月内降 280 倍

| 项 | 内容 |
|---|---|
| **数值** | GPT-3.5 水平（MMLU 64.8）的查询成本：**$20.00 / 百万 tokens（2022-11）→ $0.07 / 百万 tokens（2024-10，Gemini-1.5-Flash-8B）**，降幅 **>280 倍**；依任务不同每年降 **9–900 倍** |
| **单位** | 美元/百万 tokens |
| **年份** | 2022-11 → 2024-10 |
| **来源机构** | Stanford HAI, AI Index 2025（价格数据源：Epoch AI / Artificial Analysis） |
| **URL** | https://hai.stanford.edu/ai-index/2025-ai-index-report/research-and-development |
| **原文摘录** | 「The cost of querying an AI model that scores the equivalent of GPT-3.5 (64.8) on MMLU ... dropped from **$20.00** per million tokens in November 2022 to just **$0.07** per million tokens by October 2024 (Gemini-1.5-Flash-8B)—a more than **280-fold reduction** in approximately 18 months.」 |
| **可信度** | 机构报告（基于第三方价格追踪） |

Epoch AI 独立口径（2025）：「We find a range from **9x to 900x per year** across different benchmarks and performance levels.」
URL: https://epoch.ai/data-insights/llm-inference-price-trends — 可信度：机构估计

### 5.2 头部推理价差：DeepSeek-R1 vs OpenAI o1（2025-01）

| 项 | 内容 |
|---|---|
| **数值** | DeepSeek-R1：**$0.55 / 百万 input tokens**（缓存命中 $0.14）、**$2.19 / 百万 output tokens**；同期 OpenAI o1：**$15 / $60**（报道口径）→ 输入约 **27 倍**、输出约 **27 倍**价差 |
| **单位** | 美元/百万 tokens |
| **年份** | 2025-01-20 |
| **来源机构** | DeepSeek 官方 API 文档；o1 价格见多家媒体与价格对比站 |
| **URL** | https://api-docs.deepseek.com/news/news250120 ; https://llm-stats.com/models/compare/deepseek-r1-vs-o1-preview |
| **原文摘录** | 「Performance on par with OpenAI-o1. … $0.14 / million input tokens (cache hit), **$0.55 / million input tokens**, **$2.19 / million output tokens**」 |
| **可信度** | DeepSeek 价格＝官方（实测标价）；o1 价格＝报道，建议核对 OpenAI 当期定价页面 |

### 5.3 训练成本：从 GPT-4 的「1 亿美元级」到 DeepSeek-V3 的 557.6 万美元

| 项 | 内容 |
|---|---|
| **数值** | GPT-4 训练成本：Sam Altman 称「**超过 1 亿美元**」；Stanford AI Index 2024 估 **$78.4M**；Epoch AI 另一口径估 **$40M**（硬件成本摊销） |
| **单位** | 美元 |
| **年份** | 2023（GPT-4）/ 2024（各估算） |
| **来源机构** | WIRED（Altman 原话）；Stanford HAI AI Index 2024；Epoch AI |
| **URL** | https://www.wired.com/story/openai-ceo-sam-altman-the-age-of-giant-ai-models-is-already-over/ ; https://hai.stanford.edu/ai-index/2024-ai-index-report ; https://arxiv.org/html/2405.21015v2 |
| **原文摘录** | Altman：「At the MIT event, Altman was asked if training GPT-4 cost $100 million; he replied, **'It's more than that.'**」／AI Index 2024：「OpenAI's GPT-4 used an estimated **$78 million** worth of compute to train, while Google's Gemini Ultra cost **$191 million** for compute.」 |
| **可信度** | 混合：官方自述（>1 亿）+ 机构估计（$78M / $40M）。**三份数字不一致，上屏需标注为「估计」** |

| 项 | 内容 |
|---|---|
| **数值** | DeepSeek-V3（671B 总参数 / 每 token 激活 37B）：**2.788M H800 GPU 小时**，按 $2/GPU 小时计，**总训练成本 $5.576M** |
| **单位** | GPU 小时 / 美元 |
| **年份** | 2024-12 |
| **来源机构** | DeepSeek（技术报告 arXiv 2412.19437） |
| **URL** | https://arxiv.org/abs/2412.19437 |
| **原文摘录** | 「DeepSeek-V3 requires only **2.788M H800 GPU hours** for its full training.」「Assuming the rental price of the H800 GPU is $2 per GPU hour, our total training costs amount to only **$5.576M**.」 |
| **可信度** | **实测**（官方技术报告，明确注明算法口径）；注意该数字不含研发、消融与前期实验成本 |

### 5.4 能耗与碳排

| 项 | 数值 | 年份 | 来源 | 原文摘录 | 可信度 |
|---|---|---|---|---|---|
| 训练碳排（估算） | AlexNet 0.01 t → GPT-3 **588 t** → GPT-4 **5,184 t** → Llama 3.1 405B **8,930 t**；Grok 4（2025）**72,816 t** CO₂e（Epoch AI 独立估计约 14 万吨） | 2012–2025 | Stanford AI Index 2025/2026 | 「GPT-3 (2020) at **588 tons**, GPT-4 (2023) at **5,184 tons**, and Llama 3.1 405B (2024) at **8,930 tons**」 | 机构估计 |
| 单次文本 prompt 能耗 | 中位数 **0.24 Wh**、**0.03 gCO₂e**、**0.26 mL 水**（Gemini Apps，2025-05）；2024-05→2025-05 单次能耗降 **33 倍** | 2025 | Google Cloud / arXiv 2508.15734 | 「the median Gemini Apps text prompt uses **0.24 watt-hours (Wh)** of energy, emits **0.03 grams of carbon dioxide** ...」 | **实测**（Google 自测，方法论公开但被批评细节不足） |
| 推理功率差异 | 中长 prompt 下 DeepSeek V3 约 **23 W**，Claude 4 Opus 约 **5 W**；最低效模型推理碳排是最优的 **10 倍以上** | 2025/2026 | Stanford AI Index 2026（经 IEEE Spectrum 转引） | 「DeepSeek's V3 models were estimated to consume around **23 watts** when responding to a 'medium-length' prompt, while Claude 4 Opus was estimated to consume about **5 watts**.」 | 机构估计 |
| 硬件效率 | ML 硬件 16-bit 算力 **年增 43%**（1.9 年翻倍）；性价比**年降 30%**；能效**年增 40%** | 2025 | Stanford AI Index 2025 | 「machine learning hardware performance ... has grown **43% annually**, doubling every 1.9 years. Price performance ... **30% per year**, while energy efficiency has increased by **40% annually**.」 | 机构报告 |
| 全球 AI 算力 | **3.3 倍/年**（2022 起），2025 年达 **1710 万 H100 当量**；Nvidia 占 >60% | 2026 | Stanford AI Index 2026 | 「Global AI compute capacity grew **3.3x per year since 2022**, reaching **17.1 million H100-equivalents**.」 | 机构估计 |

### 5.5 「密度在收缩」的正向证据（小模型追上大模型）

| 项 | 内容 |
|---|---|
| **数值** | OLMo 3.1 Think 32B 以比 Grok 4 **少近 90 倍**的参数，在多个基准上达到相当水平（仅靠剪枝、去重、数据筛选） |
| **单位** | 参数倍数 |
| **年份** | 2026 报告（覆盖 2025 模型） |
| **来源机构** | Stanford HAI, AI Index 2026 |
| **URL** | https://hai.stanford.edu/ai-index/2026-ai-index-report/research-and-development |
| **原文摘录** | 「OLMo 3.1 Think 32B, with nearly **90 times fewer parameters** than Grok 4, achieves comparable results on several benchmarks through pruning, deduplication, and curation alone.」 |
| **可信度** | 机构报告 |

另一条同源：Apple 的 **~3B 端侧模型**在人工偏好评测中优于 Llama-3-8B、Mistral-7B、Gemma-7B、Phi-3-mini（ifeval 指令遵循 85.7% vs Llama-3-8B 82.5%）。
URL: https://machinelearning.apple.com/research/introducing-apple-foundation-models — 可信度：实测（厂商自测）

---

## 六、可上屏的候选数据表（JSON，3 组）

### 组 1：AI 论文数量（十年膨胀）

```json
{
  "title": "AI 论文数量的十年膨胀（2013 → 2024）",
  "unit": "篇/年",
  "labels": ["2013", "2023", "2024"],
  "values": [102000, 242000, 258000],
  "source": "Stanford HAI, AI Index Report 2025 & 2026（Scopus 口径）。AI Index 原文：2013→2023「nearly tripled, from approximately 102,000 to over 242,000」；2026 版：2013→2024「more than doubled, from 102,000 to 258,000」",
  "source_url": "https://hai.stanford.edu/ai-index/2025-ai-index-report/research-and-development",
  "confidence": "机构报告",
  "note": "实际倍数 2.37x / 2.53x，不是精确 3x；若必须用「3 倍」，改用顶会投稿量或 AI 专利数据"
}
```

**若脚本坚持「三倍」叙事，可替换为下面这组（增长更陡、更好看）：**

```json
{
  "title": "AI 专利申请量的十五年增长（2010 → 2023）",
  "unit": "件/年",
  "labels": ["2010", "2023"],
  "values": [3833, 122511],
  "source": "Stanford HAI, AI Index Report 2025：「ballooning from 3,833 to 122,511」",
  "source_url": "https://hai.stanford.edu/ai-index/2025-ai-index-report/research-and-development",
  "confidence": "机构报告"
}
```

### 组 2：AI 论文的可复现率（三条独立研究）

```json
{
  "title": "AI/ML 论文到底有多少能被复现？——三项独立研究的结论",
  "unit": "%",
  "labels": ["完全可复现（Gundersen & Kjensmo 2018, 400篇）", "限时复现成功（Gundersen et al. 2025, 22篇高被引）", "独立复现成功（Raff 2019, 255篇）"],
  "values": [0, 50.0, 63.5],
  "source": "① AAAI 2018 文献计量：400 篇 IJCAI/AAAI 论文中「None of the papers document all of the variables」；② AAAI 2025 复现实验：30 篇最高被引 AI 论文中 22 篇可复现，40 工作小时限时下(部分)成功率 50.0%；③ NeurIPS 2019：人工复现 255 篇 ML 论文，成功率 63.5%",
  "source_urls": [
    "https://ojs.aaai.org/index.php/AAAI/article/view/11503",
    "https://ojs.aaai.org/index.php/AAAI/article/view/34818",
    "https://papers.nips.cc/paper/8787-a-step-toward-quantifying-independently-reproducible-machine-learning-research"
  ],
  "confidence": "实测（文献计量 + 对比实验，非问卷）",
  "note": "三项研究口径不同（0% 是「全变量记录」的极端口径），建议图上用「复现成功率」两条柱更稳妥：50% / 63.5%"
}
```

### 组 3：端侧小模型在真机上的实测速度（同款模型 Qwen2.5-1.5B 4-bit 对照）

```json
{
  "title": "同一个 1.5B 小模型（Qwen2.5-1.5B, 4-bit）在四类设备上的持续推理速度",
  "unit": "tokens/s",
  "labels": ["笔记本 RTX 4050", "iPhone 16 Pro（热稳定态）", "三星 S24 Ultra（降频后）", "树莓派5 + Hailo-10H NPU"],
  "values": [131.7, 23.67, 10.38, 6.914],
  "source": "Conscious Engines, arXiv 2603.23640v2（2026）：20 次连续推理、greedy 解码、2048 token KV 上限；iPhone 峰值 40.49 tok/s 但 3 次迭代内掉 ~40%；S24 Ultra 均值 10.83 tok/s",
  "source_url": "https://arxiv.org/html/2603.23640v2",
  "confidence": "实测（第三方独立基准，预印本）",
  "note": "能量侧同步可标：Hailo-10H 270.5 mJ/token @1.87W；RTX 4050 297.3 mJ/token @34W"
}
```

**补充组（如需第四根柱或另一个视角）：iPhone 上更大模型反而更快 + 厂商口径**

```json
{
  "title": "手机上跑大模型的实测/宣称速度对比",
  "unit": "tokens/s",
  "labels": ["Apple ~3B（iPhone 15 Pro，Apple 实测）", "iPhone 16 Pro + Qwen2.5-1.5B（第三方实测·热稳定）", "Dimensity 9300+ 7B（MediaTek 宣称）", "三星 S24 Ultra + Qwen2.5-1.5B（第三方实测）"],
  "values": [30, 23.67, 22, 10.83],
  "source": "Apple 官方技术说明；MediaTek 官方新闻稿；Conscious Engines arXiv 2603.23640v2",
  "source_urls": [
    "https://machinelearning.apple.com/research/introducing-apple-foundation-models",
    "https://www.mediatek.com/press-room/mediatek-boosts-flagship-smartphone-performance-with-dimensity-9300-soc",
    "https://arxiv.org/html/2603.23640v2"
  ],
  "confidence": "混合：前两项为厂商实测，第三项为厂商宣称，第四项为第三方实测",
  "note": "不同模型/不同量化/不同框架，不能等同比较，仅作趋势示意"
}
```

---

## 七、未找到可核验来源 / 需谨慎的点

1. **「共享代码+数据 → 86% 可复现，仅共享数据 → 33%」**：仅见于二手科普网站，未找到原始论文。**不建议上屏**。
2. **GPT-4 参数量**：从未公开。任何「1.8 万亿 / 1 万亿参数」都是媒体引述匿名信源。
3. **GPT-4 训练成本**：三个数字并存（Altman「>1 亿」、AI Index $78.4M、Epoch AI $40M），须标注为估计且不要混用。
4. **「AI 论文增长三倍」**：按 AI Index 自己的数字是 2.37x / 2.53x。若需 3x，改用顶会投稿量（NeurIPS 2018→2025 约 4.4x，2021→2025 约 2.4x）或 AI 专利（32x），并注明来源口径。
5. **1,000 tokens/s 预填充**（mllm-NPU）：数字来自检索摘要，抓取论文正文失败，上屏前需核对 ASPLOS'25 PDF。
6. **「第一次在手机上跑通 7B」的确切时间**：未找到可核验的单一时点；只有厂商在 2023–2024 年的量产化公告。
