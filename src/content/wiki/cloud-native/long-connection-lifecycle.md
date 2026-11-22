---
title: "长连接在中间层的生命周期"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-11-14"
updated: "2026-11-14"
type: "concept"
tags:
  - "网络"
  - "k8s"
  - "运维"
  - "架构"
sources:
  - "https://kubernetes.github.io/ingress-nginx/how-it-works/"
  - "https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/"
  - "https://nginx.org/en/docs/ngx_core_module.html#worker_shutdown_timeout"
confidence: "high"
summary: "长连接穿过负载均衡/入口网关时，会撞上两个完全独立的问题：路由（这条连接该打到哪个实例）和寿命（这条连接能活多久）。归因时必须先分清是哪一类，否则会在错误的层上折腾。"
---
## 一句话本质

长连接穿过负载均衡/入口网关时，会撞上**两个完全独立的问题**：**路由**（这条连接该打到哪个实例）和**寿命**（这条连接能活多久）。归因时必须先分清是哪一类，否则会在错误的层上折腾。

## 一、问题一：路由 —— 有状态会话 × 无状态 LB

典型场景：进程把会话状态放在**自己内存**里（session 只活在"持有它的那个实例"上），但对外只有一个 Service / CLB。

```
客户端 → Service/CLB → 无状态转发 → 可能落到任意副本
                                      ↓
                          落到「没有这个 session」的副本 → 失败
```

**根本矛盾**：需要**会话粘性**，但负载均衡只做**无状态转发**。

| 解法 | 做法 | 适用/代价 |
|---|---|---|
| LB 层会话亲和 | sticky cookie / source IP hash | 只在会话建立时可路由；实例重启后仍会打偏 |
| 状态外置 | session 存 Redis/DB，任意副本都能服务 | 要改造有状态组件，很多现成服务改不了 |
| **自建路由层** | 自己维护「会话 → 实例地址」映射表，代理按标识查表转发 | 把路由权从 LB 拿回自己手里；代价是自研一个代理 |

> 第三种是"**有状态路由表 + 无状态数据面**"：路由表放 Redis（多副本共享），代理本身无状态可横向扩。**粘性由应用自己做，不对 LB 抱期望。**

## 二、问题二：寿命 —— 中间层会杀连接，原因有四种

| # | 原因 | 特征 | 心跳能否救 |
|---|---|---|---|
| 1 | **空闲超时**（`proxy-read-timeout`、LB idle timeout） | 有流量就不断；安静一段时间才断 | ✅ 能 |
| 2 | **进程回收**（worker/实例被重启） | 与活跃度**无关**，到点就断 | ❌ **不能** |
| 3 | **配置重载引发的优雅退出** | 与活跃度无关，且**频率与配置变更频率正相关** | ❌ **不能** |
| 4 | RST / 进程崩溃 | 立即断，无 Close 帧 | ❌ 不能 |

**关键区分**：1 是「安静太久」，2/3 是「**到期处决**」。**心跳只对 1 有效**。这就是"加了心跳、加了打印，问题依旧"的常见原因。

## 三、ingress-nginx：配置重载如何杀掉长连接（机制全文）

三段机制拼起来才完整：

**① 什么时候 reload**（ingress-nginx 官方 "When a reload is required"）
> ① **New Ingress Resource Created** ② TLS 段被加到已有 Ingress ③ 影响 upstream 之外的 annotation 变更 ④ path 增删 ⑤ Ingress/Service/Secret 被删 ⑥ Secret 更新

注意：**Endpoint 变化已由 Lua 实现免 reload**，但**新建 Ingress 资源仍然必须 reload**。

**② reload 时旧 worker 怎么了**
reload 不是"立即换"，新旧 worker 并存，旧 worker 进入 **graceful shutdown**，继续服务已建立的连接。

**③ 到点强制关闭**（nginx 官方 `worker_shutdown_timeout`）
> Configures a timeout for a graceful shutdown of worker processes. **When the time expires, nginx will try to close all the connections currently open** to facilitate shutdown.

ingress-nginx 把它默认设成 **`240s`**。

### 完整因果链

```
每建一条新路由（Ingress 资源）
   → controller 重建 nginx 模型 → reload
   → 旧 worker 进入 graceful shutdown，继续端着 WebSocket
   → 240s 到点 → 强制关闭该 worker 上所有打开的连接
   → 长连接被砍（客户端侧：无 Close 帧的突断）
```

**"断开时长非常规律"的数学解释**：断开时刻 = 最近一次 reload + 240s。**reload 越密集，连接建立到被杀的时长越稳定地收敛到 240s**。所以"3–5 分钟且极其规律"不是巧合，而是 reload 频率足够高时的必然结果。

### 最反直觉的一点

如果业务模式是「**每个任务创建一条动态路由**」，那么**业务自己就是 reload 的持续制造者**——高频路由变更 × 共享 ingress controller 的 reload 模型，是**结构性不相容**，不是配置能调好的问题。

三条"救法"及其代价：

| 救法 | 代价 |
|---|---|
| 调大 `worker-shutdown-timeout` | 旧 worker 无法回收，持续 reload 下 draining worker 堆积 → 内存上涨甚至 OOM |
| 给长连接单独部署一套 ingress controller | 只减少 reload，触发源仍在；多一套 controller 运维成本 |
| 客户端自动重连 | 治标，会话状态丢失 |

→ 结论：**把长连接从"配置重载模型"里解放出来，自建代理持有连接**，才是对症的结构性解法。

## 四、归因方法：先排除应用层，再逐层剥离

```
第 1 步：现象定性
   「到点就断、与活跃度无关」 ⇒ 立刻怀疑"进程/连接回收"，而不是空闲超时
   在应用层加打印 ⇒ 断开不在业务逻辑（但仅此不足以定位）

第 2 步：分层剥离（每层单独验证，逐层排除）
   · 集群内直连后端        ← 绕过入口
   · 集群内走 Service       ← 只测负载均衡
   · 集群外直连入口 IP      ← 测入口
   · 去掉 LB 直连 NodePort  ← 把 LB 摘掉

第 3 步：抓包坐实
   看最后几个包：有 Close 帧 = 应用层主动；只有 FIN = 不是应用层；RST = 强制
   （机制细节见 [WebSocket 协议机制](/wiki/cloud-native/websocket-protocol)）

第 4 步：对齐时间戳
   断连时刻 − 最近一次 reload/config 变更时刻 ≈ 240s ？ ⇒ 坐实是 reload 导致
   命令：kubectl logs <controller-pod> | grep "Backend successfully reloaded"
        kubectl exec <controller-pod> -- grep worker_shutdown_timeout /etc/nginx/nginx.conf
```

**结论边界**：「没有 Close 帧」只能排除"应用层主动关闭"，**不能定位是哪一跳关的**。必须配合分层剥离才能落到具体组件。

## 一句话记住

**长连接被断，先问"是安静太久，还是到期处决"**——前者加心跳，后者只能换架构；**配置重载型入口天生不适合承载高频动态路由下的长连接**。

## 相关

- [WebSocket 协议机制](/wiki/cloud-native/websocket-protocol) — 101 升级、Hijack、帧与控制帧、三种关闭形态
- [代理是管道不是解析器](/wiki/cloud-native/proxy-as-pipeline) — 自建代理为什么不解析协议才能与协议解耦
- [Fleeting 插件架构](/wiki/cloud-native/fleeting-plugin-architecture) — 同一套"有状态 vs 无状态"的权衡在另一个场景的应用
- [降级即告警](/wiki/cloud-native/alerting-on-degradation) — 兜底让故障静默，长连接重连成功也会掩盖问题

## 原始输出留档（子皓 2026-11-14）

> webshell 之前是不支持上去环境排查的，原因这里需要细讲一下，gitlab runner 在 k8s 中的部署是多个 runner manager副本同时向 gitlab 请求 job，然后获取到 job 的时候会上报到 gitlab 对应的session id。但是因为多个副本共用一个 service，暴露为一个 clb，因此当 gitlab 想要访问 对应job的wss连接时，可能被 service 路由到错误的 runner manager 副本，然后找不到对应的 session。因此我一开始的做法是让 runner 上报session对应的 manager 副本 cluster ip 到 ingress 资源，由 nginx ingress 进行路由，这里是能够成功连接了，但是连接时长维持在三五分钟。因为十分规律，且在 webterminal 中加打印，不是组件逻辑。后续分别加测试，从集群内与job wss连接、从集群内与runner manager连接、集群外脱离前后端界面直接与 clb 连接、去掉clb与nodeport建联，同时学习使用 wireshark抓包检查建联情况。最后定位到是 nginx 侧的断联问题，查询相关资料发现nginx ingress 会定期关闭连接资源，防止资源浪费，导致需要长连接的 websocket 被动触发断联。发现之后便放弃了使用 ingress nginx 的方式，转而采用上报到一个集群服务，然后由这个服务对外暴露ip，然后由这个服务进行路由建立WebSocket连接。

（原文一字未改。本文补的是「240s = worker_shutdown_timeout 默认值 + reload 触发条件」这条精确机制，以及第四节的通用归因流程——当时只查到"nginx 会定期关闭连接"这一层。）
