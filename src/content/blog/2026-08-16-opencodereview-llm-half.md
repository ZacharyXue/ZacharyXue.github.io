---
title: OpenCodeReview 源码拆解：LLM 只负责一半 —— 确定性工程 × Agent 混合架构
date: 2026-08-16
tags: [代码评审, Agent, 架构, 确定性工程, 源码阅读]
description: 阿里 OpenCodeReview (ocr) 源码深读：把 LLM 容易失控的部分全部搬回确定性工程，LLM 只保留「判断问题是否真实」一个职责。
draft: true
hide_from_home: true
---

# OpenCodeReview 源码拆解：LLM 只负责一半

> 源码：github.com/alibaba/open-code-review (Go) · 基于本地 v1.9.x 主线 + 官方 README + 公众号拆解交叉验证

## 一句话

**把 LLM 容易失控的部分，全部搬回确定性工程；LLM 只保留「判断题」这一件事。**

```mermaid
graph LR
    subgraph 确定性工程["确定性工程 (程序决定)"]
        F1["审哪些文件"]
        F2["每文件用什么规则"]
        F3["评论落哪一行"]
        F4["预算/并发/超时"]
    end
    subgraph LLM["Agent (模型判断)"]
        L1["问题是否真实"]
        L2["何时取上下文"]
        L3["怎么改"]
    end
    F1 --> L1
    F2 --> L1
    F3 --> L1
```

**结果**：同模型下 Precision/F1 更高、token 约 1/9、更快；代价 Recall 更低（刻意取舍：低误报 > 高召回）。

## 为什么不能把整个 PR 扔给 Agent

```mermaid
graph LR
    A["通用Agent<br/>审大变更"] --> B["覆盖不全<br/>有的文件没看"]
    A --> C["位置漂移<br/>评论落错行"]
    A --> D["质量不稳<br/>规则执行不一致"]
    B --> E["根因: 纯语言驱动<br/>缺乏硬约束"]
    C --> E
    D --> E
```

「必须审完哪些文件」「评论落哪一行」「用哪套检查清单」——都是**可以写成程序的约束问题**，不需要开放式推理。

## 架构：扁平并行，不是主从树形

```mermaid
graph TB
    subgraph 调度器["dispatchSubtasks (普通Go函数, 不是LLM)"]
        S["并发8 goroutine · token预算前瞻 · 超时 · panic隔离"]
    end
    S --> A1["Agent D1<br/>Plan→Main→Filter"]
    S --> A2["Agent D2<br/>Plan→Main→Filter"]
    S --> A3["Agent D3<br/>Plan→Main→Filter"]
    S --> A4["...×N<br/>上下文完全隔离"]
    A1 --> C["CommentCollector<br/>线程安全共享存储"]
    A2 --> C
    A3 --> C
    A4 --> C
    C --> OUT["wg.Wait() 全部跑完 → 一次性取出 → 输出"]
```

**没有「主 Agent 汇总子结果再综合判断」的环节**——评论直接落共享 Collector。这是省 9 倍 token 的关键：没有「子结果回传主 Agent」这个最烧钱的环节。

## 一条 comment 的完整生命周期

```mermaid
flowchart LR
    G["git diff"] --> P["diff解析<br/>+全量DiffMap"]
    P --> FL["过滤<br/>大diff剔除<br/>路径/扩展名规则"]
    FL --> D["调度<br/>每文件goroutine"]
    D --> PL["Plan预规划<br/>(可选, <50行跳过)"]
    PL --> M["Main loop<br/>≤30轮工具循环"]
    M --> LOC["行号定位<br/>确定性优先"]
    LOC --> RF["反思过滤<br/>证明制fail-open"]
    RF --> OUT["汇总输出"]
    style PL fill:#ffd8a8
    style M fill:#a5d8ff
    style LOC fill:#c3fae8
    style RF fill:#ffc9c9
```

## 规则系统：两级结构

```mermaid
graph TB
    subgraph 第一层["第一层: 工程规则 (确定性执行)"]
        R1["glob路径匹配<br/>system_rules.json<br/>**/*.go → go.md"]
        R2["include/exclude<br/>token阈值<br/>定位算法"]
    end
    subgraph 第二层["第二层: 自然语言checklist (LLM执行)"]
        R3["rule_docs/*.md<br/>语言特定审查清单"]
    end
    R1 --> R3["命中 → 替换进<br/>{{system_rule}}"]
    R3 --> M["主Agent prompt"]
```

规则优先级：`--rule` > 仓库 `.opencodereview/rule.json` > 用户全局 > 内置系统；用户规则默认**替换**系统规则。

**Go 规则示例**：
- 声称竞态/输入可控/资源归属前，**先用工具查调用点**（Favor precision over recall）
- 不重复 go vet / Staticcheck / race detector 能发现的问题
- 版本差异都考虑：`time.After` 在 Go 1.23+ 不单独算泄漏

## Plan：固定框架 + 现场内容

```mermaid
graph LR
    subgraph 固定["固定 (经验沉淀)"]
        S1["JSON schema"]
        S2["severity 三档<br/>high/medium/low"]
        S3["按 severity 降序"]
        S4["工具仅参考<br/>不可调用"]
    end
    subgraph 动态["动态 (LLM现场)"]
        D1["change_summary"]
        D2["具体 issues"]
        D3["severity 判定"]
        D4["tool_guidance"]
    end
    LLM["plan LLM 调用<br/>(无Tools参数)"] --> 动态
    固定 --> LLM
    LLM --> INJ["注入 main prompt<br/>{{plan_guidance}}"]
    INJ --> M["主Agent"]
```

关键点：
- **骨架是经验，内容是现场**——流程模板固化，具体分析模型生成
- plan 失败**不阻塞**：`planResult=""` 继续跑 main
- 空 plan 时 `stripEmptyPlanBlock` 先剥掉整段（防字面量泄漏——历史 bug 修复）

## Main loop：30 轮封顶的工具循环

```mermaid
flowchart TD
    L["for toolReqCount > 0<br/>(默认30轮)"] --> Q{"有 tool_calls?"}
    Q -->|否| R["插入重试提示<br/>连续3轮空→停"]
    Q -->|是| T["逐个 executeToolCall"]
    T --> T1["task_done<br/>DONE/FAILED 退出"]
    T --> T2["code_comment<br/>强类型校验+异步定位"]
    T --> T3["file_read等<br/>同步执行"]
    T2 --> N["addNextMessage<br/>拼回对话<br/>60%/80%三区压缩"]
    T3 --> N
    R --> N
    N --> L
```

**主 Agent prompt = 确定性代码填充 7 个占位符**：

| 占位符 | 来源 |
|--------|------|
| `{{current_system_date_time}}` | 当前时间 |
| `{{current_file_path}}` | 当前文件 |
| `{{system_rule}}` | glob 匹配出的语言规则 |
| `{{change_files}}` | 其他变更文件列表（带状态前缀） |
| `{{diff}}` | 该文件 unified diff |
| `{{requirement_background}}` | 需求背景（--background 等） |
| `{{plan_guidance}}` | plan 的 JSON 计划 |

**防坑设计**：
- prompt 组装后 token > 80% max_tokens → **直接拒绝不发**
- 工具注册表 `Freeze()`：并发前冻结，防运行中改工具
- 主 Agent「不越界」：其他文件的问题只能帮助理解，不能评论
- 每轮重发完整对话 → 命中 provider prompt cache
- `code_comment` 的 path **强制覆盖**为真实路径（模型幻觉免疫）

## 行号定位：三级策略，LLM 只兜底

```mermaid
flowchart TB
    CM["LLM 提供 existing_code<br/>(不报行号)"] --> R1["① diff新侧匹配"]
    R1 -->|失败| R2["② 旧侧匹配"]
    R2 -->|失败| R3["③ 完整新文件扫描<br/>空白归一化+滑动窗口"]
    R3 -->|失败| R4["④ 跨文件重定向<br/>纯字符串匹配<br/>不用模型"]
    R4 -->|失败| R5["⑤ ReLocateComment<br/>LLM窄任务<br/>抽最小代码片段"]
    R5 --> V["ResolveComment 复验"]
    V -->|通过| OK["定位成功"]
    V -->|失败| DROP["保留原文<br/>放弃定位"]
```

## REVIEW_FILTER：证明制过滤

```mermaid
graph TB
    M["main loop 结束"] --> W["等异步评论排空<br/>AwaitKey"]
    W --> F["executeReviewFilter"]
    F --> LLM["LLM 二选一<br/>(ToolChoice: required)"]
    LLM -->|approve_all| KEEP["全部保留<br/>(默认答案)"]
    LLM -->|report_incorrect| JUDGE{"满足证明制?"}
    JUDGE -->|Ground A: 代码不在diff| DEL["删除"]
    JUDGE -->|Ground B: diff明文矛盾| DEL
    JUDGE -->|保护主题 veto| KEEP
    JUDGE -->|无法证明| KEEP
    F -->|LLM失败/解析失败| KEEP["fail-open: 一条不删"]
```

- **删除仅两条理由**：Ground A（代码不在 diff）/ Ground B（diff 明文矛盾，须直接读出，不允许推理链）
- **保护主题 veto**：内存安全、并发、链接一致性、行为变更、未使用参数 → 禁止删除
- **玄机**：工具参数 `analysis` 排在 `comment_ids` 前——Go 按字母序序列化，逼模型先推理再提交 id（顺序反了模型会先选 id 再编理由）
- 一切失败 → **fail-open**（宁可多留噪声，绝不误删真问题）

## 工具集：6 个只读工具

```mermaid
graph LR
    subgraph 工具["6个只读工具 (无shell, 无写文件)"]
        T1["file_read"]
        T2["file_read_diff"]
        T3["file_find"]
        T4["code_search"]
        T5["code_comment"]
        T6["task_done"]
    end
```

从大规模生产数据（调用频率分布、重复率、新工具影响）蒸馏出的场景专属工具集。

## 数据边界 & 适用场景

**部署前四问**：endpoint 在哪？provider 是否保留请求？谁能看会话记录？MCP 是否转发第三方？

| 适合 | 不适合 |
|------|--------|
| 已有稳定 Git 流程 | 作为合并前的最终裁判 |
| 愿意维护项目规则 | 替代测试/静态分析/安全扫描 |
| CI 里过滤高置信问题 | 替代人工架构审查 |
| 大改动逐文件并发 | — |

> **定位**：高精度的「第二双眼睛」，不是「最终裁判」。

**上线前**：`ocr review --preview` 看覆盖 → 写项目规则 `ocr rules check` → 历史 PR 盲测算 Precision/Recall。

## 一句话总结

```mermaid
graph LR
    A["确定性工程<br/>负责'不能出错'"] --- B["Agent<br/>负责'需要智能'"]
    A -.->|硬约束| B
    B -.->|动态决策| A
```

**让模型做它擅长的判断题，让代码做它该做的约束——这就是 OCR 的全部秘密。**
