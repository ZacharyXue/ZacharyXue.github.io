---
title: Daily Skills
url: https://github.com/ZacharyXue/Daily-Skills
tags: [开源, 工具, AI]
status: active
---

个人长期积累的 AI Agent 技能库（Hermes skill 集合）。以 Markdown 格式沉淀可复用的工作流，供 AI 代理在合适时机自动加载使用，涵盖职业复盘、源码阅读、数据跟踪等场景。所有技能按「数据层 → 领域层」分层：

- **统一数据源层** — 全库共用的数据获取底座：内置**数据源地图**（A股/港股/美股行情与K线、A股财报、美股财报、GitHub 仓库/Issues/PR/Release/搜索）+ **SQLite 缓存** + **Tier 路由降级** + 合规红线（限速、免付费 key、可追溯）。其他技能一律通过它取数，杜绝重复探索、拿错数据、烧 token。
- **career-coach** — 职业成长教练：复盘工作/学习、判断价值、规划发展路径
- **code-study** — 问题驱动的源码阅读：从用户可见行为追踪调用链，沉淀排查笔记
- **whale-holdings** — 大佬持仓跟踪：SEC 13F 机构持仓披露季度对比
- **etf-dashboard** — ETF 技术温度看板：5 年估值分位 + 技术面 + 实时行情，交叉生成加仓/分批/减仓信号
- **stock-analysis** — 股票基本面深度分析：财报提取 → 商业模式 → 财务三表 → 利润构成 → 风险排查 → 同行对比 → 估值
- **investment-mindset** — 投资/人生决策思维模型库（芒格 / 巴菲特 / 李录 / 段永平）
- **skill-creation-guide** — 自建 skill 的创建与管理引导

以 git 版本化管理，通过软链接入 AI 代理的 skill 目录。

> 📄 仓库地址：[GitHub](https://github.com/ZacharyXue/Daily-Skills)
