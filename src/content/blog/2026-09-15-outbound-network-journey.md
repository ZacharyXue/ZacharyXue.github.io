---
title: 从敲下网址到数据到达：一次完整的出网旅程
date: 2026-09-15
tags: [技术, 网络]
description: 从浏览器输入域名到数据到达服务器，整条链路的完整拆解——重点讲清本机用户态↔内核态的穿越、DNS 解析、TCP 握手、路由决策、ARP 寻址与交换机逐跳，附每环节对应的配置文件和排障命令。
draft: false
---

> 一句话：**在浏览器敲下网址后，你的数据要穿过「用户态 → 内核态 → 物理网络 → 对方内核态 → 对方用户态」五道门**。本文把每一道门拆开看。

## 全景：一条数据的完整旅程

```mermaid
flowchart TD
    A[浏览器输入 www.baidu.com] --> B{DNS 解析}
    B -->|命中缓存/hosts| C[拿到 IP<br/>103.235.46.102]
    B -->|未命中| D[询问 DNS 服务器<br/>递归查询]
    D --> C
    C --> E[TCP 三次握手<br/>与 443 端口建立连接]
    E --> F{查路由表判定下一跳}
    F -->|同子网| G[下一跳 = 目标服务器<br/>ARP 问它要 MAC]
    F -->|跨子网| H[下一跳 = 默认网关<br/>ARP 问网关要 MAC]
    G --> I[封装帧出网卡]
    H --> I
    I --> J[交换机定向转发]
    J --> K[路由器逐跳接力]
    K --> L[到达服务器网卡<br/>内核协议栈逆处理]
    L --> M[应用进程 recv 收到数据]
```

| 阶段 | 走哪 | 主角 |
|---|---|---|
| ① 本机出发 | 用户态 ↔ 内核态 | 系统调用 + 协议栈 |
| ② 传输途中 | 物理网络 | 交换机 / 路由器 |
| ③ 到达服务器 | 内核态 → 用户态 | 网卡中断 + socket 队列 |

下面**重点拆①**，这是数据离你机器前经历的全部。

---

## 一、本机出发：用户态 ↔ 内核态 的三次穿越

### 地图：谁是用户态，谁是内核态

```mermaid
flowchart LR
    subgraph 用户态[用户态]
        APP[应用进程<br/>浏览器 / curl / 你的程序]
    end
    subgraph 内核态[内核态]
        SYS[系统调用层<br/>getaddrinfo / socket / connect / send / recv]
        STACK[协议栈<br/>TCP 分段 → IP 封装 → 路由查表 → ARP]
        DRV[网卡驱动 + 硬件中断]
    end
    APP <-->|① 人话→系统调用| SYS
    SYS --> STACK --> DRV
    DRV -.->|物理线路| NEXT[下一台设备]
```

**本质**：你的程序跑在用户态，**碰不到网卡、看不到协议栈**——它想联网，必须通过系统调用把请求交给内核，内核干完活再把结果交还给你。数据在你这台机器上，**用户态→内核态→用户态 一共穿越三次**：

1. **getaddrinfo()**：问 DNS，「baidu.com 的 IP 是多少？」
2. **socket() + connect()**：建连接，「我要连这个 IP 的 443 端口」
3. **send() / recv()**：发数据、收数据

---

### 穿越 ①：DNS 解析 —— getaddrinfo()

你访问的是域名，网络只认 IP。查 IP 的顺序：

```mermaid
flowchart TD
    A[应用调用 getaddrinfo] --> B{本机缓存命中?}
    B -->|是| Z[直接返回 IP]
    B -->|否| C{/etc/hosts 命中?}
    C -->|是| Z
    C -->|否| D[/etc/nsswitch.conf 决定顺序<br/>默认: files → dns/]
    D --> E[读 /etc/resolv.conf<br/>拿到 DNS 服务器地址]
    E --> F[UDP 发给 DNS 服务器<br/>递归查询直至权威服务器]
    F --> Z
    Z --> G[用户态拿到 IP<br/>继续下一步]
```

| 配置 | 作用 | 排障命令 |
|---|---|---|
| `/etc/hosts` | 手动指定 域名→IP，**优先级最高** | `cat /etc/hosts` |
| `/etc/nsswitch.conf` | 决定查询顺序（files 先还是 dns 先） | `grep ^hosts /etc/nsswitch.conf` |
| `/etc/resolv.conf` | 指定 DNS 服务器地址 | `cat /etc/resolv.conf` |
| — | 实际解析结果 | `getent hosts baidu.com` / `dig` |

> ⚠️ 你 ECS 上的 `/etc/resolv.conf` 指向 `127.0.0.53`——这是 systemd-resolved 的本地转发器，它再替你去上游递归。看到 `127.0.0.x` 别慌，是本地 DNS stub。

---

### 穿越 ②：建立连接 —— socket() + connect()

拿到 IP 后，程序创建 socket（内核返回一个文件描述符 fd），然后 connect()。**三次握手全程在内核完成**，应用只看到「连接成功/失败」：

```mermaid
sequenceDiagram
    participant APP as 应用(用户态)
    participant K as 内核 TCP(内核态)
    participant S as 服务器(远程)
    APP->>K: socket() 创建 fd<br/>connect(IP:443)
    K->>S: SYN (seq=x)
    S-->>K: SYN+ACK (seq=y, ack=x+1)
    K->>S: ACK (ack=y+1)
    K-->>APP: connect 返回成功
    Note over K,S: 连接建立，双方各自维护状态
```

关键点：**fd 是用户态唯一拿到的"会话凭证"**。之后 send/recv 都凭这个 fd 告诉内核「我要跟哪个连接说话」——这就是之前学的 TCP「端口」在编程层的体现。

---

### 穿越 ③：发送数据 —— send() → 协议栈

数据进入内核后，被**层层加工**：

```mermaid
flowchart TD
    A[应用 send 数据] --> B[TCP 层<br/>切分报文段 + 包头<br/>源端口→目的端口]
    B --> C[IP 层<br/>封装 IP 头<br/>源 IP→目的 IP]
    C --> D{查路由表}
    D -->|目的 IP 在本机子网?| E1[下一跳 = 目的 IP]
    D -->|否| E2[下一跳 = 默认网关]
    E1 --> F[ARP 查下一跳 MAC]
    E2 --> F
    F --> G[链路层封装帧<br/>MAC头 + IP头 + TCP头 + 数据]
    G --> H[网卡驱动发出]
```

这三层头部，就是之前学的四层模型：

```
┌────────────────────────────────────────────┐
│ 帧头: 源MAC → 下一跳MAC    ← 每跳换         │
│ IP头: 源IP → 目的IP        ← 全程不变       │
│ TCP头: 源端口 → 目的端口    ← 决定交给谁     │
│ 数据: HTTP 请求体          ← 业务内容       │
└────────────────────────────────────────────┘
```

**路由决策**是这步的核心，判定依据是 CIDR 最长前缀匹配：

| 目的 IP | 路由表匹配 | 下一跳 | ARP 问谁 | 帧的目的 MAC |
|---|---|---|---|---|
| 同子网（如 172.19.50.5） | 直连路由（无 via） | 目标自己 | 目标服务器 | 目标 MAC |
| 跨子网/公网 | 默认路由（via 网关） | 网关 | 网关 | 网关 MAC |

**排障命令**：`ip route get <IP>` 立刻告诉你「下一跳是谁」——这是定位「为什么连不上」的第一手信息。

---

## 二、传输途中：离开网卡之后

包从小网卡出去，接下来每一步都是「换 MAC、看 IP」的接力：

```mermaid
flowchart LR
    A[你的网卡] --> B[交换机<br/>查 MAC 表定向转发]
    B --> C[路由器 R1<br/>拆帧看 IP → 查路由表 → 换 MAC 转发]
    C --> D[路由器 R2<br/>重复同样动作]
    D --> E[目标服务器网卡]
```

| 设备 | 层 | 干的事 |
|---|---|---|
| 交换机 | 二层 | 只认 MAC，端口间**定向分拣**（不干扰其他机器） |
| 路由器 | 三层 | 认 IP，查路由表决定**下一跳**，逐跳接力 |
| 集线器（已淘汰） | 二层共享 | 人人收到，共享带宽 |

**两个贯穿全程的铁律**：
- **IP 不变**：终点站，从你到服务器永远写的是 103.235.46.102
- **MAC 每跳换**：车票，每一段链路都要换成下一站的 MAC

---

## 三、到达服务器：逆过程

对方机器收到包后，**完全对称地逆处理**：

```mermaid
flowchart TD
    A[服务器网卡收到帧] --> B[网卡 DMA 到内存<br/>触发硬件中断]
    B --> C[内核协议栈<br/>剥 MAC 头 → 剥 IP 头 → 剥 TCP 头]
    C --> D{TCP 校验通过?}
    D -->|是| E[数据送入对应 socket 的接收队列]
    D -->|否| F[丢弃 / 要求重传]
    E --> G[应用 recv 系统调用<br/>从队列取数据<br/>用户态拿到 HTTP 请求]
```

> 注意：服务器进程**不是**被中断唤醒后直接拿数据——内核把数据放上 socket 队列，应用**主动 recv 取走**。这就是「内核态 → 用户态」的第四次穿越（在对方机器上）。

---

## 四、特例：环回地址（不出物理网络）

如果目标是 `127.0.0.1`，旅程**大幅缩短**——内核内部直接折返：

```mermaid
flowchart TD
    A[应用 connect 127.0.0.1] --> B[TCP 层封装]
    B --> C[IP 层查路由表<br/>命中 local 表项 dev lo]
    C --> D[交给 lo 逻辑接口]
    D --> E[loopback 特技:<br/>直接塞回本机接收队列]
    E --> F[协议栈逆处理<br/>应用 recv 拿到]
    F --> G[全程不出内核<br/>不碰网卡/线路/ARP]
```

用途与安全：
- 本地测试、本机进程间通信、协议栈自检
- **`bind 127.0.0.1` = 只本机能访问；`bind 0.0.0.0` = 所有接口可访问（暴露风险）**
- 实测：ping 127.0.0.1 ≈ 0.05ms，ping 公网 ≈ 0.9ms——差 20 倍就是「少了物理世界那一截」

---

## 附录：全链路配置与命令索引

排障时按需取用：

| 环节 | 配置文件 | 命令 |
|---|---|---|
| DNS | `/etc/hosts`、`/etc/nsswitch.conf`、`/etc/resolv.conf` | `getent hosts`、`dig`、`nslookup` |
| 连接 | `/proc/sys/net/ipv4/*`（如 tcp_syncookies） | `ss -lntp`（看绑定地址）、`strace -e trace=network` |
| 路由 | 内核路由表 | `ip route`、`ip route get <IP>` |
| ARP | 内核 ARP 表 | `ip neigh`、`arp -a` |
| 网卡 | netplan / NetworkManager | `ip addr`、`ethtool` |
| 抓包 | — | `tcpdump -i eth0`、`traceroute` |

---

## 一句话记忆版

> **IP 是终点站（全程不变），MAC 是车票（每跳作废）**；DNS 把网名翻成终点站，路由表决定下一站，ARP 把下一站翻成车票，交换机负责把车票送到对应车厢。
> 而这一切的起点和终点，都是**用户态应用叫一声系统调用、内核埋头干完活、再把结果交给应用**。