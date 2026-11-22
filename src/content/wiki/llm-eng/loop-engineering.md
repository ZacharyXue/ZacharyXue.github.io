---
title: "Loop Engineering：用负反馈闭环收敛概率错误"
domain: "llm-eng"
domainLabel: "LLM 工程"
created: "2026-09-07"
updated: "2026-09-07"
type: "concept"
tags:
  - "loop"
  - "agent"
sources:
  - "https://zacharyxue.github.io/blog/loop-engineering/"
confidence: "high"
summary: "Loop Engineering 是控制论在 AI 工程的落地：LLM 是概率模型，复杂任务分治叠加让正确率指数衰减（单步 90% 六步后约 53%），必须用负反馈闭环修正累积概率损失；范式从「我指挥 AI 干活」迁移到「设计一个循环去 prompt agent、把人从流程中拔出来」，把负反馈提供者从人换成系统。"
---
## 一句话本质
**Loop Engineering 是控制论在 AI 工程的落地**：LLM 是概率模型，复杂任务分治叠加让正确率指数衰减（单步 90% 六步后约 53%），必须用负反馈闭环修正累积概率损失；范式从「我指挥 AI 干活」迁移到「设计一个循环去 prompt agent、把人从流程中拔出来」，把负反馈提供者从人换成系统。

## 范式迁移五世代（叠加而非替代）

Prompt Engineering（怎么问）→ Context Engineering（补背景）→ Harness Engineering（单次执行可控）→ **Loop Engineering**（自动化调度、无人值守）→ Graph Engineering（Loop 间编排）。Harness 是地基，Loop 是上层调度——没有 Harness 就没有 Loop。

## 为什么必须 Loop

LLM 核心动作是猜，概率累乘下复杂任务正确率指数崩塌——必须建立机制修正累积概率损失。对应控制论四大公理：
- **负反馈闭环**：输出反向影响输入（测试失败→修复→再测）
- **可观测性**：日志/测试报告/Lint 输出
- **可控性约束**：文件所有权边界、沙箱、权限
- **离散迭代纠偏**：每步检查是否偏航

**设计 Loop 的四个问题**：如何定义问题（目标函数）、如何定义开始（触发条件）、如何设计反馈（负反馈信号从哪来）、如何定义结束（防止无限烧 token）。最关键是设计反馈——让模型真会说「不」的机制，必须基于不可否认的硬事实而非提示词里的拒绝话术。

## 五大组件（缺一不可）

| 组件 | 作用 |
|---|---|
| Automations | 唤醒（人是流程中最慢的节点） |
| Worktrees | 沙箱（并行防文件覆盖污染） |
| Maker-Checker | 双校验（Checker 必须有硬证据才能否定 Maker） |
| Connectors | 通信（Loop 不能是孤岛） |
| Memory | 记忆（长流程防失忆） |

## 让模型说「不」的三种方法

- **TDD**：价值不是多写测试，而是把需求翻译成反馈信号——Red 定义对/错终态→Green 迭代到全过→Refactor 兜底优化，Red→Green→Refactor 就是最小 Loop。适用边界：业务规则/API 行为/数据转换/回归修复适合；纯体验/架构品味/产品决策不适合。
- **证据链追溯**：Checker 否决必须逐条举证——从需求提取可验证规则，每条规则在代码中找实现、在测试中找验证，形成「规则→代码→测试」三元组，断裂处=FAIL 并精确到行号。四重价值：可定位（第 X 条规则第 Y 行未实现而非「质量差」）、可仲裁（人一眼判断对错）、可度量（通过率=匹配三元组/总规则数）、防作弊（Maker 不能靠注释蒙混）。
- **预算思维**：模型分层（高价值任务用聪明贵模型、低价值重复用便宜模型）、退出机制（最大步骤+预算熔断）、上下文压缩守则——**核心规则全程人为把控不参与压缩，只压缩可损耗的过程信息**；用廉价模型对全量上下文反复重压缩会导致核心规则稀释+噪音累积。

## 三层 Loop 全局视角

技术 Loop（系统会不会收敛/停止/认错）⊂ 产品 Loop（是否持续创造用户价值）⊂ 用户 Loop（用户情绪如何回到产品）。实践路径：先跑通最小可收敛闭环→验证稳定可重复→逐步放大自治边界→建立闭环之间的联系，**大循环长在小循环上**。

## 记住点
你不是在 Prompt Agent，而是在设计一个 Loop 去 Prompt Agent——TDD 把需求翻译成反馈信号，Checker 靠「规则→代码→测试」三元组证据链说「不」。

## 相关
- [多 Agent 协作协议](/wiki/llm-eng/multi-agent-team-protocols)（Maker-Checker=独立评审门禁、Worktrees=文件互斥）
- [上下文压缩策略](/wiki/llm-eng/context-compression-strategies)（「核心规则不参与压缩」是两家的共同底线）