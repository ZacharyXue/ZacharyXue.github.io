---
title: "多 Agent 协作协议：角色矩阵、文件所有权与独立评审门禁"
domain: "llm-eng"
domainLabel: "LLM 工程"
created: "2026-09-07"
updated: "2026-09-07"
type: "concept"
tags:
  - "多agent"
  - "agent"
sources:
  - "https://zacharyxue.github.io/blog/codex-agent-team/"
confidence: "high"
summary: "多 Agent 系统的本质不是再造一个「AI 版 Jira」（调度服务器+任务队列+状态数据库），而是把真实软件团队的合作习惯——分工、交接、评审、止损——显式化成 Agent 可反复读取的系统。Agent 能否成为可信的工程同事，取决于文件所有权互斥、仓库文件共享记忆、独立评审门禁和可恢复状态这五样东西，而非角色名字像不像人。"
---
## 一句话本质
**多 Agent 系统的本质不是再造一个「AI 版 Jira」（调度服务器+任务队列+状态数据库），而是把真实软件团队的合作习惯——分工、交接、评审、止损——显式化成 Agent 可反复读取的系统**。Agent 能否成为可信的工程同事，取决于文件所有权互斥、仓库文件共享记忆、独立评审门禁和可恢复状态这五样东西，而非角色名字像不像人。

## 核心认知

- **打破幻觉**：协作无需强制调度控制平面，全部资产品可以是「提示词+一组 Markdown 文件」——把团队协作协议显式化（requirements/spec/design/tasks/decisions/review 文件），而非做一个任务系统。
- **角色按工程责任而非语言划分**：fullstack-agent 定需求/委派/整合（禁止写生产代码）、coding-agent 限定文件范围写代码+测试（禁止越界写文件、自审自评）、devops-agent 管 CI/CD/IaC（禁止改业务逻辑）、review-agent 独立审查（禁止改代码）、sa-agent 管架构/安全/成本；每个角色必须同时写明「该干什么」和「禁止干什么」。
- **并行规则是文件所有权互斥而非「同时开始」**：并发上限由「互不重叠的文件写入范围」决定；任务必须写明 Scope（限定文件）、Contract（对接哪个接口）、Verify（真实验证命令）、禁止项。按「前端/后端/测试」拆角色会翻车（都改同一份测试夹具）；正确做法是锁定共享接口→按文件边界扇出→冲突则串行或指定唯一 Merge Owner。
- **主线程四步循环** Spawn→Wait→Steer→Close：沉默不是失败，不能仅凭「没消息」就复制任务；对不完整结果只做最小范围纠正；每波次结束收割结果并关闭已完成 Agent。
- **独立评审三条铁律**：Lead 不得在 review.md 写 PASS、实现 Agent 自检不算评审、分析 Reviewer 不能写最终结论；每轮只有一个综合 Reviewer，等齐所有分析结果或显式记录缺失。评审预算在 Reviewer 启动时就消耗（模型路由故障/基础设施抖动同样消耗），要区分「工程失败」和「平台失败」。
- **共享记忆**：对话负责沟通，仓库文件负责记忆——会话中断后重新读文件而不是重放对话；事实优先级「文件+Diff > specs > 命令输出 > Agent 消息 > 旧摘要 > 沉默」。

## 护栏三层定位

| 层 | 角色 | 性质 |
|---|---|---|
| 提示词 | 组织制度 | 软约束 |
| Hook | 审计日志（记录 Agent 生命周期） | fail-open |
| Rules | 局部门禁（高风险命令确认/拦截） | 硬闸 |

三者合起来也不等于强制调度控制平面——协作约束若只是提示词级别会**静默失效**（无法机器验证文件重叠、无法阻止第四轮评审）。

## 落地顺序

先最小可信闭环（specs 生成、Worker 文件不重叠、结果含真实验证命令、review.md 由独立 Reviewer 写出、无遗留 Agent）→ 再补机器护栏（.gitignore、固定版本、可解析任务结构、Spawn 前文件重叠检查）→ 最后才扩大角色池。**核心顺序：先证明闭环再扩展吞吐，先增加可验证性再增加自治。**

## 记住点
提示词是组织制度，Hook 是审计日志，Rules 是局部门禁——agent 可信靠文件所有权、独立评审、可恢复状态，不靠角色名字；先闭环再吞吐。

## 相关
- [Loop Engineering](/wiki/llm-eng/loop-engineering)（review-agent 门禁=Maker-Checker 双校验、文件互斥=Worktrees 沙箱、评审修复波次=控制论离散纠偏）
- [确定性工程 × Agent 混合](/wiki/llm-eng/deterministic-agent-hybrid)（独立评审+验证证据=review.md 门禁实践）