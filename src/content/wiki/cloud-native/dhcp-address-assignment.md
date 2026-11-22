---
title: "DHCP 地址分配"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-09-27"
updated: "2026-09-27"
type: "concept"
tags:
  - "网络"
  - "运维"
sources:
  - "计算机网络学习群 2026-09 DHCP 学习"
confidence: "high"
summary: "一句话本质：DHCP 把「IP + 掩码 + 网关 + DNS + 租期」整套配置自动送上门（DORA 四步），之后靠 T1/T2 定时续租维持——所以拿到的 IP 是「概率性固定」，不是真固定。"
---
**一句话本质**：DHCP 把「IP + 掩码 + 网关 + DNS + 租期」整套配置**自动送上门**（DORA 四步），之后靠 T1/T2 定时续租维持——所以拿到的 IP 是「概率性固定」，不是真固定。

## DORA 四步

| 步骤 | 方向 | 关键点 |
|---|---|---|
| ① **Discover** | 客户端 → 广播 | 源 `0.0.0.0:68` → 目 `255.255.255.255:67`。**0.0.0.0 因为还没 IP，广播因为不知服务器在哪**；携带 Client-ID 供服务器认人 |
| ② **Offer** | 服务器 → 客户端 | 「给你 X.X.X.X，租期 Y，附带网关/DNS」 |
| ③ **Request** | 客户端 → 广播 | 「我就要这个」（广播告知其他服务器：我没选你） |
| ④ **Ack** | 服务器 → 客户端 | 确认 + 全套参数落地（IP / 路由 `proto dhcp` / DNS） |

> DHCP 依赖**广播地址**（Discover 的 255.255.255.255）——这是广播地址存在的意义之一。

**两种广播别混淆**：

| 类型 | 地址 | 用在哪 | 特点 |
|---|---|---|---|
| **受限广播**（有限广播） | `255.255.255.255` | DHCP Discover 等"我还没有 IP"的场景 | 永远不跨路由器，只在本链路 |
| **子网广播**（定向广播） | 子网内全 1（如 `172.19.63.255`） | ARP 请求等 | 由「IP + 掩码」算出，指向特定子网 |

## 租期与续租（不是"探活"，是 T1/T2 定时器）

| 时点 | 动作 | 方式 |
|---|---|---|
| 正常使用 | 用着租来的 IP | — |
| **T1（租期 50%）** | 续租请求 | **单播**给原服务器 |
| **T2（租期 87.5%）** | 还没回应 → 找任何服务器 | **广播** |
| 租期到期仍未续 | 放弃该 IP，重走 DORA | — |

**续租一直成功 = 一直用同一个 IP**（看起来像固定，本质是不停续租）。

## Client-ID：DHCP 世界的身份证

服务器靠 Client-ID 查租约表，**优先把老 IP 还给同一个身份**。

```
/etc/machine-id  ← 装系统生成一次,永久不变（机器身份）
      ↓ 特定哈希派生（systemd 用企业号 43793）
DUID             ← 这台机器的全局唯一标识
      ↓ + IAID（4字节,网卡/接口级标识）
Client-ID        ← 每次请求带上
      ↓ 服务器查租约表
老 IP 优先还给你
```

| 格式 | 开头 | 身份绑定在 | 换网卡后 |
|---|---|---|---|
| 硬件地址型（老式） | `01` | MAC 地址 | **会变** ❌ |
| 节点特定型（RFC 4361，现代） | `ff` | IAID + DUID（存磁盘） | 通常**不变** ✅ |

| DUID 类型 | 基于 | 换网卡 |
|---|---|---|
| DUID-LLT (1) | MAC + 创建时间 | 变 |
| **DUID-EN (2)**（systemd 默认） | 企业号 + machine-id 派生 | **不变** |
| DUID-LL (3) | 纯 MAC | 变 |
| DUID-UUID (4) | 主板 UUID (SMBIOS) | 硬件级不变 |

## IP 什么时候真的会变

| 场景 | 原因 |
|---|---|
| 租期到期没续上（关机太久/断网超期） | IP 被回收分配给别人 |
| 换网卡（老式 `01`+MAC 型）、重装系统、云上重建实例 | 身份（DUID/IAID）变了，服务器认不出 |
| DHCP 服务器重启/迁移，租约表丢失 | 服务器"失忆" |
| 地址池耗尽 / 管理员重规划网段 | 没得给 |

**要真正固定**：① DHCP 静态绑定（按 Client-ID/MAC 预留）② 静态 IP ③ 云上弹性公网 IP。

**云环境特殊性**：厂商把租期设成近似永久（可长达 59 年），私网 IP 与实例生命周期绑定，实际不会经历续租失败。

## 排障命令

| 目的 | 命令 |
|---|---|
| IP 是否 DHCP 给的 | `ip addr`（找 `dynamic`） |
| DHCP 下发的路由 | `ip route`（找 `proto dhcp`） |
| 租约详情 | `cat /run/systemd/netif/leases/*` |
| DHCP 历史事件 | `journalctl -u systemd-networkd \| grep -i dhcp` |
| 网卡状态 / 手动续租 | `networkctl status eth0` / `networkctl renew eth0` |
| 机器身份 | `cat /etc/machine-id` |

## 相关

- [网络配置四件套与子网约束](/wiki/cloud-native/network-config-four-pieces)
- [CIDR 编址](/wiki/cloud-native/cidr-addressing)
- [环回地址](/wiki/cloud-native/loopback-address)
- [二层转发与交换机](/wiki/cloud-native/layer2-switching)