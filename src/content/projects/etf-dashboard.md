---
title: ETF 技术温度看板
url: /exports/etf-dashboard.html
tags: [理财, ETF, 看板, 工具]
status: active
---

实时更新的 **ETF 技术温度看板**：综合 5 年估值分位（中证官网历史 PE 自算）、技术面（MA20 / BIAS / 回撤 / N 日涨跌）、实时行情，交叉生成「加仓 / 分批 / 过热减仓」信号，并给出此刻可执行的操作建议。

- **标的**：中证红利、红利低波、港股央企红利、中证电池主题（可编辑 `etf-dashboard/watchlist.json` 增删品种）
- **数据源**：中证官网（5年 PE 分位）+ 天天基金（估值/ROE）+ 腾讯行情/K线
- **更新方式**：手动触发 `cd etf-dashboard && python3 update.py`，每日收盘后跑一次即可
- **判断逻辑**：技术面（回撤/MA/BIAS）× 估值面（PE 5年分位）双视角交叉，兼顾「低位买入机会」与「高位过热预警」

> ⚠️ 本看板为个人研究工具，数据仅供参考，不构成投资建议。

📊 [查看实时看板](/exports/etf-dashboard.html)
