---
title: "上下文压缩策略：续跑 vs 防僵尸——任务形态与成本模型双根因"
domain: "llm-eng"
domainLabel: "LLM 工程"
created: "2026-09-07"
updated: "2026-09-07"
type: "concept"
tags:
  - "上下文压缩"
  - "agent"
sources:
  - "https://zacharyxue.github.io/blog/opencodereview-hermes-context-compression/"
confidence: "high"
summary: "两个 agent 解决同一个问题（长 tool-use 对话撑爆上下文窗口）给出几乎处处相反的设计，分叉根因只有两条：任务形态（连续长跑 vs 随时转向）决定摘要语义（续跑 vs 防僵尸）；prompt cache 成本模型（神圣 vs 无顾虑）决定谁做摘要（aux 小模型 vs 主模型）和敢不敢后台异步。看穿这两条，任何 agent 的上下文管理策略都能读…"
---
## 一句话本质
**两个 agent 解决同一个问题（长 tool-use 对话撑爆上下文窗口）给出几乎处处相反的设计，分叉根因只有两条**：任务形态（连续长跑 vs 随时转向）决定摘要语义（续跑 vs 防僵尸）；prompt cache 成本模型（神圣 vs 无顾虑）决定谁做摘要（aux 小模型 vs 主模型）和敢不敢后台异步。看穿这两条，任何 agent 的上下文管理策略都能读出「出身」。

## 共同前提

context window 是硬上限不是安全用量——输出也占 token、本地 BPE 估算可能低估真超窗、失败代价（整轮崩）≫ 压缩代价（一次便宜调用）、tool-use loop 每轮累积任一轮溢出就炸；所以「拖到 100% 再压」是必输策略，要在远低于窗口的预算点提前压。**「预算怎么定、谁来压、压完模型怎么看待总结」才是分叉点。**

## 五轴对比

| 轴 | 派别 A | 派别 B |
|---|---|---|
| 预算来源 | 固定预算（与模型无关，保守值，省维护） | 按模型真实 window 动态算（context−max_tokens 预留输出） |
| 触发依据 | 本地 BPE 估算（简单但可能低估） | API 真实 prompt_tokens（排除 completion_tokens——thinking 类 reasoning 会把 completion 撑虚高导致过早压缩） |
| 谁来摘要 | 主模型（无 cache 顾虑时最省事） | 独立便宜 aux 模型（per-conversation prompt caching is sacred 时，保主模型 cache 前缀纹丝不动） |
| 摘要语义（任务形态决定） | **续跑**：连续任务 agent 失忆后要想起「评到哪、发现哪些问题、还缺哪些」，五维结构化摘要塞回 user 消息 | **防僵尸**：通用对话 agent 随时转向，总结只是背景参考，只响应总结之后的最新用户消息，话题相似也不 resume |
| 工具结果压缩 | 免费层优先（确定性+保关键字段） | 同左——清成 [cleared] 是零信息，LLM 摘要是最后手段 |

## 执行细节

- **压缩三区**：frozen（前 2 条按位置保留，不可压缩）/ compress（中间历史）/ active（尾部倒推装得下的最近 K 个完整 round）；一个 round = assistant 消息 + 跟随的 tool 结果，**保证不切断 tool_call/tool_result 对**。
- **防僵尸是三代生产 bug 逼出来的演进**：resume exactly 产生僵尸任务 → carveout 仍被话题 hijack → 强 REFERENCE ONLY + tools remain active 补丁。
- **免费层阶梯**：L1 确定性模板按工具类型保留关键字段（terminal 退出码/read_file 行数/搜索命中数），L2 折叠截断（超长文本 head+tail、图片剥离）零成本先行，LLM 摘要是最后手段。
- **失败兜底**：两家均以「防超窗」为硬约束，失败保守兜底（保留原消息/静态截取锚点+冷却）。

## 方法论输出（分析任何 agent 的上下文策略）

先问两个问题：①任务形态是连续长跑还是随时转向？（推出摘要语义和触发时机）②它的 prompt cache 成本模型是什么？（推出谁来摘要和敢不敢异步）。再对照五轴即可反推系统设计出身。

## 记住点
任务形态决定摘要语义（续跑 vs 防僵尸），prompt cache 成本模型决定谁做摘要和敢不敢异步——看穿这两条根因，任何 agent 的上下文策略都能读出「出身」。

## 相关
- [确定性工程 × Agent 混合](/wiki/llm-eng/deterministic-agent-hybrid)（同源同项目，本篇承续其 60%/80% 压缩点）
- [Loop Engineering](/wiki/llm-eng/loop-engineering)（「核心规则不参与压缩只压过程信息」正是两家的共同底线）