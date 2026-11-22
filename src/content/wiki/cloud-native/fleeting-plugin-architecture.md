---
title: "Fleeting 插件架构（GitLab Runner 云厂商适配）"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-10-10"
updated: "2026-10-10"
type: "concept"
tags:
  - "k8s"
  - "架构"
  - "CI/CD"
sources:
  - "gitlab.com/gitlab-org/fleeting/fleeting（provider/interface.go、DESIGN.md、plugin/）"
  - "gitlab.com/gitlab-org/fleeting/taskscaler（taskscaler.go、schedule.go、options.go）"
  - "GitLab Docs: Instance executor / runner autoscaling"
confidence: "high"
summary: "插件是「翻译官 + 眼睛」，不是「大脑」：它把云厂商的机器池翻译成 Runner 能指挥的标准接口， 每次汇报云上实况；决定要几台的是 taskscaler，记住状态的是 fleeting 库，插件自己无状态。"
---
## 一句话本质
**插件是「翻译官 + 眼睛」，不是「大脑」**：它把云厂商的机器池翻译成 Runner 能指挥的标准接口，
每次汇报云上实况；**决定要几台的是 taskscaler，记住状态的是 fleeting 库**，插件自己无状态。

## 三层职责（谁决定、谁记住、谁执行）

```
┌─ GitLab Runner ─────────────────────────────────┐
│  taskscaler：规划「要几台」                      │
│  · 策略 Schedule{IdleCount, IdleTime,           │
│      ScaleFactor, ScaleFactorLimit, Periods}    │
│  · task 生命周期：Reserve → Acquire → Release   │
│  · 有状态：storage 持久化 task→instance 分配     │
└────────────────┬────────────────────────────────┘
                 │ 期望容量
┌────────────────▼────────────────────────────────┐
│  fleeting.Provisioner（官方库，宿主侧）          │
│  · 实例状态机 + 意图对账（reconcile）            │
│  · demand = len(request)，上限                   │
│      MaxSize − pending − instances              │
│  · 有状态（内存 + 状态机）                       │
└────────────────┬────────────────────────────────┘
                 │ 接口调用
┌────────────────▼────────────────────────────────┐
│  provider.InstanceGroup（插件实现）★             │
│  · 无状态：每次现问云 API 要全量                 │
└────────────────┬────────────────────────────────┘
                 │ HTTPS OpenAPI
            云厂商（ECS/EC2/GCE…）
```

## 插件契约：InstanceGroup 接口（9 个方法）

| 方法 | 何时被调 | 职责 | 语义要点 |
|---|---|---|---|
| `Init` | 插件启动一次 | 解析配置、初始化云客户端 | 返回 `ProviderInfo{MaxSize, Capabilities}` |
| **`Update`** | **每个对账周期** | 拉全量实例、逐个回调状态 | **全量快照**，不是增量 |
| `Increase(n)` | 要扩容 | 创建 n 台，返回**成功台数** | 部分成功是常态 |
| `Decrease(ids)` | 要缩容 | 删指定实例，返回**成功 ID 列表** | 部分成功是常态 |
| `ConnectInfo(id)` | 要连上去跑 job | 返回 IP/用户/密钥 | 用户提供 + 插件发现 + 生成 |
| `Heartbeat(id)` | 健康检查 | 异常返回 error | 抢占式实例被回收等 |
| `Suspend`/`Resume` | 可选能力 | 停机/开机 | **fire-and-forget**，不等完成 |
| `Shutdown` | 插件退出 | 清理 | — |

**状态枚举**：`creating` / `running` / `deleting` / `deleted` / `timeout` / `suspending` / `suspended` / `resuming`

**接口语义推出的两条硬约束**：
1. **必须幂等**——`Increase`/`Decrease` 返回部分成功，未成功项**下轮重试**
2. **必须能「认领自己的实例」**——`Update` 是全量列举，不打标签就会把同账号下别人的机器当成自己的

## 状态归属：谁是事实来源（关键认知）

| 层 | 状态 | 谁持有 |
|---|---|---|
| 云厂商 | **真实世界** | 云（最终事实来源） |
| 插件 | **无状态** | 不存——每次问云 API |
| fleeting 库 | 实例状态机、意图标记（removing/suspending） | 库（内存） |
| taskscaler | task→instance 分配 | taskscaler（持久化 storage） |

**推论**：插件不存状态，所以**不存在「两份状态要同步」的问题**。

## 为什么是「全量快照」而不是「增量上报」

这是整套设计最值得记住的权衡链：

```
前提：宿主与插件同机（HashiCorp go-plugin 假设「本地可靠网络」）
        ↓ 传输几乎免费
不需要增量优化 → 插件不用记住上次状态 → 插件可完全无状态
        ↓
状态只有一处（库侧）= 单一事实来源 → 无一致性问题

若改走增量：插件必须持久化 → 出现第二份状态 → 失败时两边不一致
        → 需要 ACK/重传/序号/补偿 → 复杂度爆炸
```

**全量快照另外两个白送的好处**：
- **天然容错**：某轮 Update 失败，下一轮自动纠正，**不需要补偿逻辑**
- **能发现「你不知道的存在」**：有人在云控制台手动开机（out-of-band），全量下一轮就看见（对应 `Cause = Unexpected`）；增量方案永远发现不了

**边界**：插件**可以**缓存**信号**（如「spot 实例被中断过」留给下次 Heartbeat 用），但不可缓存**状态权威**。

## 跨进程机制：回调其实是 gRPC 流

`Update(ctx, fn)` 里的「回调」在跨进程时**不是本地函数调用**：

```proto
rpc Update(Empty) returns (stream UpdateResponse);   // server-streaming
message UpdateResponse { string instance = 1; State state = 2; }
```

| 位置 | `fn` 实际是什么 |
|---|---|
| 插件侧（收到） | 发流消息的 stub（闭包，内部 `stream.Send()`）|
| 宿主侧（传入） | 库自己的对账处理逻辑 |

**一次 Update = 一次「云实况」全量快照推流**，插件遍历完返回 → 流 EOF → 宿主循环退出。

## 插件如何启动

- 独立**进程**（不是库、不是 sidecar），HashiCorp go-plugin 握手 + gRPC 通信
- 安装：`gitlab-runner fleeting install` 把插件二进制放到 `/plugins/<repo>/<version>/`
- 配置引用：`[runners.autoscaler] plugin = "aws"` + `plugin_config`（插件自定义 JSON）

## 一句话记住
> **taskscaler 决定「要几台」，fleeting 库管「状态机和对账」，插件只管「把指令翻译成云 API + 报实况」**——
> 插件无状态不是偷懒，是用「声明式全量快照」换掉了「增量 + 两份状态 + 一致性难题」。

## 相关
- [Volcano 调度器](/wiki/cloud-native/volcano-scheduling) — 另一个「调度器如何决定放哪/放几」的对照系统
- [容器运行时链路](/wiki/cloud-native/container-runtime-chain) — 同样关注「进程边界与接口契约」的分层设计
- [K8s Label 与 Annotation](/wiki/cloud-native/k8s-label-vs-annotation) — 插件「认领自己实例」依赖标签，与 label 的可选择性语义同源
