---
title: "WebSocket 协议机制"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-11-14"
updated: "2026-11-14"
type: "concept"
tags:
  - "网络"
  - "架构"
  - "运维"
sources:
  - "https://www.rfc-editor.org/rfc/rfc6455"
  - "https://nginx.org/en/docs/ngx_core_module.html#worker_shutdown_timeout"
confidence: "high"
summary: "WebSocket 不是新协议，是\"从 HTTP 原地换车\"——先用一个假的 HTTP 请求商量好，服务端回 101 Switching Protocols，从此这条 TCP 连接脱离 HTTP 语义，变成双向对等的字节流。"
---
## 一句话本质

**WebSocket 不是新协议，是"从 HTTP 原地换车"**——先用一个假的 HTTP 请求商量好，服务端回 `101 Switching Protocols`，从此这条 TCP 连接脱离 HTTP 语义，变成双向对等的字节流。

## 一、为什么必须"借" HTTP 的壳

浏览器只会说 HTTP/HTTPS，80/443 是唯一穿得过中间设备的口子。所以设计者的做法是：**先假扮一个普通 HTTP 请求，跟服务端商量"换个说话方式行不行"**，服务端同意后就不再是 HTTP 了。这就是**协议升级（Upgrade）**。

RFC 原文对关系的定性（§1.7）：
> The WebSocket Protocol is an independent TCP-based protocol. **Its only relationship to HTTP is that its handshake is interpreted by HTTP servers as an Upgrade request.**

## 二、101 升级的逐字段过程

```
① 客户端 → 服务端（伪装成一个普通 GET）
GET /ws/terminal HTTP/1.1
Host: proxy.internal
Connection: Upgrade              ← 我要升级
Upgrade: websocket               ← 升到 websocket
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==     ← 随机 16 字节 base64
Sec-WebSocket-Version: 13

② 服务端 → 客户端（注意：不是 200，是 101）
HTTP/1.1 101 Switching Protocols
Connection: Upgrade
Upgrade: websocket
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

**任何非 101 的状态码都意味着握手失败，HTTP 语义继续有效。**

## 三、Sec-WebSocket-Key / Accept 到底在防什么（常被讲错）

它**不是鉴权**，是**双向身份确认**。

算法：`Accept = base64( SHA1(客户端的Key + 固定GUID "258EAFA5-E914-47DA-95CA-C5AB0DC85B11") )`

RFC 给的正式动机（§1.6）原文：
> the server has to prove to the client that it received the client's WebSocket handshake, so that **the server doesn't accept connections that are not WebSocket connections**. This prevents an attacker from tricking a WebSocket server by sending it carefully crafted packets using XMLHttpRequest or a form submission.
>
> It is similarly intended to **fail to establish a connection when data from other protocols, especially HTTP, is sent to a WebSocket server**... fields starting with `Sec-` **cannot be set by an attacker from a web browser using only HTML and JavaScript APIs**.

三句话概括：

| 要点 | 说明 |
|---|---|
| **判官是客户端** | 客户端校验服务端返回的 Accept；对不上**客户端自己断开**，不会发任何帧 |
| **证明"对面读懂了"** | 普通网页（纯 HTML+JS）**无法伪造** `Sec-` 开头的头，所以算出正确 Accept = 对面确实是 WebSocket 实现 |
| **不是 wss 相关** | `ws` 与 `wss` 是同一协议，区别只在有没有套 TLS，与这个头无关 |

### ⚠️ 与 Masking 别搞混（两个层次的安全机制）

| 层 | 机制 | 防什么 |
|---|---|---|
| 握手层 | `Sec-WebSocket-Key` / `Accept` | **跨协议误判**：XHR/表单伪装握手；中间代理把 WS 请求当普通 GET 返回 200 |
| 数据层 | **Masking**（客户端→服务端每帧用随机 key 掩码） | **代理缓存投毒**（RFC §10.3）：攻击者无法控制数据在线上长什么样，就构造不出"看起来像 HTTP 请求"的内容去污染中间缓存 |

## 四、收到 101 那一刻，连接"变性"了

```
升级前：TCP 上跑的是「请求→响应」问答语义，服务端不能主动说话
收到 101 后：HTTP 语义当场作废，同一条 TCP 上跑 WebSocket 帧
             变成双向对等——谁都能在任何时刻发数据
```

**升级做的唯一一件事：把一条 TCP 连接从 HTTP 状态机手里抢过来，交给应用自己管。**

Go 里这个过程叫 **Hijack（劫持）**：

```go
conn, buf, _ := w.(http.Hijacker).Hijack()   // 从 net/http 手里拿到裸 TCP
go io.Copy(backend, conn)                    // 客户端 → 后端
io.Copy(conn, backend)                       // 后端 → 客户端
```

`httputil.ReverseProxy` 从 Go 1.12 起内置支持 upgrade，不用自己写。

**为什么普通 HTTP 代理做不了**：不是"解析不了"，是**生命周期模型不允许**。HTTP 代理的心智模型是「一个请求 → 一个响应 → 交还连接」，天生假设连接有终点；WebSocket 要求连接被独占、双向对拷、不设超时——在它的模型里是个"永不结束的请求"。

## 五、帧结构

每帧头只有 2–14 字节：`FIN(1) | RSV(3) | opcode(4) | MASK(1) | payload len(7) | [ext len] | [masking key] | payload`

| opcode | 名称 | 用途 |
|---|---|---|
| `0x1` | Text | 文本消息 |
| `0x2` | Binary | 二进制消息 |
| `0x8` | **Close** | **关闭握手**（带状态码，如 1000 Normal） |
| `0x9` | **Ping** | **探活请求** |
| `0xA` | **Pong** | **探活应答** |

`Ping/Pong/Close` 是**控制帧**，可插在任何数据帧之间，且必须先处理。

## 六、"探活"有三种，含义完全不同

| Wireshark 里看到 | 是什么 | 谁发的 |
|---|---|---|
| `WebSocket Ping` → `Pong` | 协议层控制帧 | 客户端/服务端库（如 xterm.js、GitLab 前端） |
| 加密的 Application Data，大小与周期固定 | 应用层心跳（如 `{"type":"heartbeat"}`） | 业务代码 |
| `[TCP Keep-Alive]` / `[ACK]` | TCP keepalive，Linux 默认 **7200s** 才有一次 | 内核 |

**心跳为什么存在**：中间的 NAT / LB / 代理普遍有空闲超时，一段时间无数据就回收连接。心跳的作用是**制造流量，让连接看起来还活着**。

> ⚠️ 但心跳**只能对抗空闲超时**，对"进程回收式断连"完全无效（见 [长连接在中间层的生命周期](/wiki/cloud-native/long-connection-lifecycle)）。

**抓包提示**：WSS 是加密的，Wireshark 默认只看到 TLS Application Data。要看到 WebSocket 帧，需在客户端配置 `SSLKEYLOGFILE` 导出 TLS 密钥，或在集群内抓明文 `ws`。

## 七、断连的三种"死法"

```
① 优雅关闭（双方讲规矩）
   一方发 Close 帧(0x8, 如 1000) → 对方回 Close 帧
   → TLS close_notify alert → TCP FIN/ACK 四次挥手
   客户端表现：onclose code=1000

② 只关 TCP，不发 Close 帧（对方进程被 kill / socket 被内核关闭）
   → 直接 FIN；若接收缓冲区仍有未读数据则 RST
   客户端表现：no close frame received or sent / 1006 Abnormal Closure

③ RST 强制重置
   进程崩溃、设备重置
   客户端表现：ECONNRESET
```

**判据**：看最后几个包——

| 抓到什么 | 结论 |
|---|---|
| `WebSocket Close` 帧 | 应用层主动关闭（死法①） |
| 只有 `FIN, ACK`，无 Close 帧 | **不是应用层发起的优雅关闭**（死法②）—— 但不能确定"谁关的" |
| `RST, ACK` | 强制重置（死法③） |

> 死法②的结论边界很重要：**它只能排除"应用层主动关闭"这一类嫌疑，不能定位到具体哪一跳**。要定位还得靠分层剥离 + 抓包（见 [长连接在中间层的生命周期](/wiki/cloud-native/long-connection-lifecycle)）。

## 一句话记住

**101 不是"成功响应"，是"协议切换点"**——从这一刻起 HTTP 退场，连接归应用所有；`Sec-WebSocket-Accept` 不是鉴权而是双向身份确认。

## 相关

- [长连接在中间层的生命周期](/wiki/cloud-native/long-connection-lifecycle) — 为什么长连接会被 LB/ingress 杀掉、怎么归因
- [代理是管道不是解析器](/wiki/cloud-native/proxy-as-pipeline) — 只知道开头才能与协议解耦
- [用户态与内核态的网络路径](/wiki/cloud-native/user-kernel-network-path) — fd 是会话凭证，hijack 之后交的就是这个

## 原始输出留档（子皓 2026-11-14）

> 1 这里在防止协议劫持，也就是服务端不支持 wss 协议；2 普通 http 解析不了 wss 协议，控制权从 http 中拿到直接解析原始的 tcp 报文；3 这里不是主动要求关闭的，这里说明不是服务端、客户端主动发起的断联；

（原文一字未改。对应纠正见正文第三节「判官是客户端 / 与 Masking 别搞混」、第四节「生命周期模型」、第七节「结论边界」。）
