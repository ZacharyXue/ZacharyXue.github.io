---
title: "确定性工程 × Agent 混合架构：LLM 只做判断题"
domain: "llm-eng"
domainLabel: "LLM 工程"
created: "2026-09-07"
updated: "2026-10-02"
type: "concept"
tags:
  - "agent"
  - "代码评审"
sources:
  - "https://zacharyxue.github.io/blog/opencodereview-llm-half/"
confidence: "high"
summary: "把 LLM 容易失控的环节（审哪些文件、每文件用什么规则、评论落哪一行、预算/并发/超时）全部搬回确定性程序，LLM 只保留「判断问题是否真实」这一件事——「能写成程序的约束问题不需要开放式推理」，以刻意牺牲 Recall 为代价换取 Precision/F1 更高、token 约 1/9、更快。"
---
## 一句话本质
**把 LLM 容易失控的环节（审哪些文件、每文件用什么规则、评论落哪一行、预算/并发/超时）全部搬回确定性程序，LLM 只保留「判断问题是否真实」这一件事**——「能写成程序的约束问题不需要开放式推理」，以刻意牺牲 Recall 为代价换取 Precision/F1 更高、token 约 1/9、更快。

## 分工判据

问「这是约束问题还是判断题」——文件筛选、规则匹配、行号定位、预算并发都是可以写成程序的约束问题，不需要 LLM 开放式推理；LLM 只保留三个职责：**问题是否真实、何时取上下文、怎么改**。

## 关键设计

- **指标取舍是设计选择**：同模型下 Precision/F1 更高、token 约 1/9、更快，代价是 Recall 更低——刻意取舍「低误报 > 高召回」，定位是高精度的「第二双眼睛」，不是合并前的最终裁判，也不替代测试/静态分析/安全扫描/人工架构审查。
- **两级规则系统**：第一层工程规则由程序确定性执行（glob 路径匹配、include/exclude、token 阈值、定位算法）；第二层自然语言 checklist（按语言/文件类型的审查清单）注入 LLM 执行。规则优先级 CLI > 仓库配置 > 用户全局 > 内置，用户规则默认替换系统规则。
- **扁平并行架构是省 token 的关键**：调度器是普通 Go 函数而非 LLM，每文件一个 Agent session（Plan→Main→Filter），上下文完全隔离，评论直接落线程安全共享 Collector——**没有「主 Agent 汇总子结果再综合判断」的回传环节，去掉它才有 9 倍 token 节省**。
- **Plan 的「骨架是经验、内容是现场」**：JSON schema/severity 三档/按 severity 降序/工具仅参考不可调用是固定框架，change_summary/issues/tool_guidance 是 LLM 现场生成；plan 失败不阻塞主流程。
- **主循环防失控**：固定轮数上限，连续空 tool_calls 插入重试提示并逐步收紧；prompt 组装超限直接拒发；工具注册表并发前冻结；主 Agent 不越界（其他文件的问题只能帮助理解不能评论）；每轮重发完整对话以命中 provider prompt cache；评论路径强制覆盖为真实路径（模型幻觉免疫）。
- **行号定位三级策略、LLM 只兜底**：diff 新侧匹配→旧侧匹配→完整新文件扫描（空白归一化+滑动窗口）→跨文件字符串重定向→最后才派 LLM 窄任务定位并复验，失败保留原文放弃定位。
- **证明制过滤（fail-open）**：删除评论仅两条理由——代码不在 diff、diff 明文矛盾（须直接读出不允许推理链）；保护主题（内存安全/并发/行为变更）有一票否决权禁止删除；一切失败宁可多留噪声绝不误删真问题。

## 范式抽象：harness 决定可交付性

把本文的混合架构抽掉领域细节，得到一条通用范式：**LLM 只做"代码逻辑判断不了的部分"；内容尽量聚焦、上下文尽量可控、结果尽量可解释——这层脚手架就是 harness。**

| harness 做什么 | 换来什么 |
|---------------|---------|
| 压缩自由裁量区间（聚焦） | 输出空间收敛、结果可比 |
| 让失败可见（留痕/准则） | 可解释、可定位到改哪里 |
| 固定输入与判据（上下文可控） | 可复跑，接近"幂等" |

⚠️ 是「**接近**幂等」不是真幂等——LLM 是概率系统，同判据下仍有波动；工程目标不是幂等，而是「噪声可量化 + 误差可接受」。

**推论：能力上限由模型决定，可交付性由 harness 决定。** 而评估器本身也是 LLM 系统 → 评估器同样需要自己的 harness（即 Rubric），所以「**评估器本身也需要被评估**」：未经校准的 Judge 带来的虚假信心，比没有 Judge 更危险。详见 [Rubric 化评估器](/wiki/llm-eng/rubric-based-judge)。

## 记住点
让模型做它擅长的判断题，让代码做它该做的约束——确定性工程负责「不能出错」，Agent 负责「需要智能」，低误报压过召回。

## 相关
- [上下文压缩策略](/wiki/llm-eng/context-compression-strategies)（同源同项目，60%/80% 压缩是本篇点到为止之处的展开）
- [Loop Engineering](/wiki/llm-eng/loop-engineering)（证据链/fail-open 正是 Maker-Checker 硬证据思想的实现）
- [Rubric 化评估器](/wiki/llm-eng/rubric-based-judge)（harness 范式在评估器上的实例）
- [Agent 评测体系：五层 / 四步 / 三阶段](/wiki/llm-eng/agent-eval-framework)（规则层/模型层/实验层的体系视角）