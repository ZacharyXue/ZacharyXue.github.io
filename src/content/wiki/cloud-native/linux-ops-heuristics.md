---
title: "Linux 运维判据与排障方法论"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-09-07"
updated: "2026-09-07"
type: "concept"
tags:
  - "监控"
  - "运维"
sources:
  - "https://zacharyxue.github.io/blog/linux-ops-commands/"
confidence: "high"
summary: "命令会忘、判据不会：能沉淀的是不随日期失效的排障判断框架——inode 消耗光也会报 No space、内存看 available 而非 free、si/so 非零说明在 swap、2>&1 是值拷贝而非引用绑定、grep/awk/sed 三剑客的分工心智模型；具体命令清单留博客。"
---
## 一句话本质
**命令会忘、判据不会**：能沉淀的是不随日期失效的排障判断框架——inode 消耗光也会报 No space、内存看 available 而非 free、si/so 非零说明在 swap、2>&1 是值拷贝而非引用绑定、grep/awk/sed 三剑客的分工心智模型；具体命令清单留博客。

## 关键判据

- **Shell 重定向顺序陷阱（真原理）**：`2>&1` 做的是「值拷贝」不是「引用绑定」，Shell 从左到右逐条解析、遇到即生效——`command 2>&1 > file` 时 fd2 已拷走旧的 fd1（终端），故 stderr 不进文件；必须先 `> file` 再 `2>&1`。
- **磁盘双重判据**：`df -h` 显示空间没满却报 No space left，八成是 inode 耗尽（`df -i` 验证，/var 下小文件海量最常触发）；`du -sh *` + `sort -h` 是定位吃盘元凶的标准动作。
- **内存判据**：`free` 只看 available 不看 free（buffer/cache 可回收）；`vmstat` 中 si/so 持续非零 = 系统在 swap；`ps aux --sort=-%rss` 定位吃内存进程。
- **负载判据**：load average ≈ CPU 核数算正常，远高于核数说明任务排队；配合 `mpstat -P ALL`、`pidstat` 区分单核瓶颈还是整体过载。
- **文本三剑客分工**：grep 是筛子（过滤/搜行）、awk 是计算器（按列拆分+统计，流式「读取→按 FS 拆列→pattern{action}」）、sed 是编辑器（批量替换/行操作）——先想清楚要「找行、算列、还是改内容」。

## 排障方法论（固定顺序）

**整体→进程→端口→落盘→错误**：`uptime+free -h+df -h` 看整体 → `ps aux --sort` 找 TOP 进程 → `ss -tlnp/lsof -i` 查端口 → `iotop` 看磁盘写入 → `journalctl -p err` 看近期错误，5 分钟内完成一轮排障。

## 记住点
三板判据：inode 也会爆、内存看 available、2>&1 是值拷贝（先改 fd1 再拷）；排查按「整体→进程→端口→落盘→错误」顺序走。

## 相关
- [容器运行时链路](/wiki/cloud-native/container-runtime-chain)（Node 磁盘满→snapshot/lease 泄漏 与 df/du/inode 判据互证）
- [Volcano 调度](/wiki/cloud-native/volcano-scheduling)（Node 状态与集群排障上下文）