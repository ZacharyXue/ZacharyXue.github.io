---
title: Daily Skills
url: https://github.com/ZacharyXue/Daily-Skills
tags: [开源, 工具, AI]
status: active
---

个人长期积累的 AI Agent 技能库（Hermes skill 集合）。以 Markdown 格式沉淀可复用的工作流，供 AI 代理在合适时机自动加载使用。所有技能按「**数据层 → 领域层**」分层，分组如下：

## 📦 基础设施层

所有取数、样式、标准都收在这层，是其他 skill 的底座，杜绝重复探索、拿错数据、烧 token。

- **data-source-router** — 统一数据源层（全网取数唯一入口）｜内置**数据源地图**（A股/港股/美股行情与K线、A股财报、美股财报、GitHub 仓库/Issues/PR/Release/搜索）+ **SQLite 缓存** + **Tier 路由降级** + 合规红线（限速、免付费 key、可追溯）。其他 skill 一律通过它取数。
- **dashboard-style** — 看板统一的 HTML 风格/模板 + 数据规范，所有看板（行业/ETF/个股）共享同一套自包含 HTML 范式。
- **skill-creation-guide** — 自建 skill 的创建与管理引导，判断哪些 skill 值得入库、目录结构、最佳实践。

## 📊 投资分析

股票/基金/大佬持仓的基本面与思维模型分析。

- **investment-mindset** — 投资/人生决策思维模型库（**芒格 / 巴菲特 / 李录 / 段永平 / 聂夫 / 马克斯 / 孙宇晨** 七维框架）｜从多位大佬角度对标的做多视角评估，避免单一视角偏颇。⚠️ 孙宇晨为反面参照+风险警示。
- **stock-analysis** — 股票基本面深度分析｜财报提取 → 商业模式 → 财务三表 → 利润构成 → 风险排查 → 同行对比 → 估值。**只做基本面**，不内置具体大师；用户需「从大佬角度评估」时转调 investment-mindset。
- **whale-holdings** — 大佬持仓跟踪｜SEC 13F 机构持仓披露季度对比（巴菲特/李录/迈克尔·伯里等），加仓/减仓/清仓一目了然。
- **industry-monitor-dashboard** — 行业/商品 + 龙头公司的定期刷新监测看板（价格趋势/盈利底/成本/估值/技术面多维）。

## 🎯 个人成长

职业复盘与源码深读。

- **career-coach** — 职业成长教练｜复盘工作/学习、判断价值、深挖技术深度、对齐业界实践、纠正方向偏差、规划发展路径。
- **code-study** — 问题驱动的源码阅读系统｜从用户可见行为出发追踪真实问题的源码调用链，产出排查笔记。

## 🛠 工具使用

日常工具的正确打开方式。

- **ttskill-headless** — 无桌面服务器（ECS/云主机）上安装天天基金 CLI 并远程扫码登录。
- **zacharyxue-blog** — 维护 ZacharyXue.github.io Astro v5 博客：发文章、项目、修渲染 bug、统一风格。

---

以 git 版本化管理，通过软链接入 AI 代理的 skill 目录。

> 📄 仓库地址：[GitHub](https://github.com/ZacharyXue/Daily-Skills)
