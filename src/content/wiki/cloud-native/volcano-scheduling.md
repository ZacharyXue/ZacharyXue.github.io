---
title: "Volcano 调度器：gang 调度与多调度器机制"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-09-07"
updated: "2026-09-07"
type: "concept"
tags:
  - "k8s"
  - "调度"
sources:
  - "https://zacharyxue.github.io/blog/volcano调度笔记/"
confidence: "high"
summary: "K8s 调度器不必是唯一的：Volcano 通过 Pod 的 schedulerName 字段从默认调度器手里「认领」Pod，用「定时拍快照、内存统一决策」（乐观并发控制）和「Action 管做什么、Plugin 管怎么判断」的分离设计，让 gang、DRF、binpack 等批量调度策略自由组合，解决分布式训练多 Pod 协同调度的死锁问题。"
---
## 一句话本质
**K8s 调度器不必是唯一的**：Volcano 通过 Pod 的 `schedulerName` 字段从默认调度器手里「认领」Pod，用「定时拍快照、内存统一决策」（乐观并发控制）和「Action 管做什么、Plugin 管怎么判断」的分离设计，让 gang、DRF、binpack 等批量调度策略自由组合，解决分布式训练多 Pod 协同调度的死锁问题。

## 机制拆解

- **多调度器共存**：K8s 允许同时存在多个调度器；Pod 的 `schedulerName` 默认 default-scheduler，设为 volcano 后默认调度器直接跳过；Volcano 的 Informer 用 FilteringResourceEventHandler 只接收 `schedulerName=volcano` 的 Pod——「认领」即使用权，是自定义调度器接入 K8s 的标准姿势。
- **两条数据流**：读方向是 Informer 长连接推送而非轮询（API Server 经 HTTP Chunked Stream 实时推送，每类资源绑定 Add/Update/Delete 回调）；写方向是调用标准 Binding API（POST /pods/{ns}/{name}/binding），Kubelet 看到绑定后启动容器。
- **gang 调度的本质**：一组 Pod 要么全部调度成功、要么全部等待（以 minMember/PodGroup 为单位判断），避免分布式训练中部分 worker 启动、部分卡 Pending 的死锁与资源空占——多 Pod 协同作业必须按「组」而非按「个」决策。
- **Session 快照模式**：调度不是「来一个 Pod 处理一个」，而是定时把全部 Pod+Node 状态拍成快照、内存里统一规划、一次性写回——与数据库事务同理的乐观并发控制，规避中途状态漂移的决策冲突。
- **Action-Plugin 分离（核心设计）**：Action 决定「做什么」（allocate/preempt/enqueue/reclaim），Plugin 决定「怎么判断」（gang 检查 minMember、DRF 算公平、priority 比优先级）；一个 Action 调用多个 Plugin，多个 Action 复合同一批 Plugin，策略通过配置即管道（`actions: [enqueue, allocate, preempt]`）任意组合。
- **DRF（主导资源公平）**：多维资源下「谁要的资源少、谁的优先级高」，实现不同资源画像作业间的公平分配；配合 binpack（塞满节点提利用率）、preempt/reclaim（高优先级抢占低优先级）构成完整调度策略族。
- **默认管道**：enqueue→allocate→backfill→preempt→reclaim（入队→分配→填补碎片→抢占→回收），每个 Action 按 Queue→Job→Task→Node 层级遍历并用 Plugin 判定可调度性。

## 记住点
Volcano = schedulerName 认领 Pod + 拍快照统一决策 + Action 管做什么、Plugin 管怎么判断；gang 就是「要么全上、要么全等」。

## 相关
- [容器运行时链路](/wiki/cloud-native/container-runtime-chain)（调度完成后 Pod 落地的下一跳）
- [Linux 运维判据](/wiki/cloud-native/linux-ops-heuristics)（Node 状态与排障上下文）