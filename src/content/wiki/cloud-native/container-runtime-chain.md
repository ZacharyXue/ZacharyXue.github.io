---
title: "容器运行时链路：从 Pod 到隔离的进程"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-09-07"
updated: "2026-09-07"
type: "concept"
tags:
  - "容器"
  - "containerd"
sources:
  - "https://zacharyxue.github.io/blog/containerd原理剖析与实战笔记/"
confidence: "high"
summary: "容器不是轻量虚拟机，而是「被隔离的进程 + 资源限制 + rootfs」；一个 Pod 从创建到运行经过 kubelet→CRI→containerd→shim→runc 的清晰链路，其中 shim 的进程隔离、snapshot/lease/GC 的内容寻址存储与 cgroup 单一写者原则，分别解释了「containerd 重启容器不死」「删容器 root…"
---
## 一句话本质
**容器不是轻量虚拟机，而是「被隔离的进程 + 资源限制 + rootfs」**；一个 Pod 从创建到运行经过 kubelet→CRI→containerd→shim→runc 的清晰链路，其中 shim 的进程隔离、snapshot/lease/GC 的内容寻址存储与 cgroup 单一写者原则，分别解释了「containerd 重启容器不死」「删容器 rootfs 秒级重建」「node 磁盘为什么总满」三个日常现象。

## 机制拆解

- **容器本质**：一组被隔离的进程 + 资源限制 + 文件系统，没有虚拟化层，宿主机 ps 直接可见容器进程；六大 namespace 分别隔离 PID/Mount/Network/UTS/IPC/cgroup 视图（缺哪个，容器就能看到宿主机对应的什么）。
- **Pod 创建标准链路**：kubectl→API Server→Scheduler→kubelet→（CRI gRPC）→containerd CRI Plugin→containerd Core→containerd-shim→runc→容器进程；排查任何「Pod 起不来」都沿这条链逐层定位。
- **运行时两层分工极简**：高级运行时（containerd）负责镜像传输、配置编排、进程管理；低级运行时（runc）只按 OCI Spec 执行一次 clone()+配置 namespace/cgroup，做完即退出不常驻。
- **shim 层三个价值**：进程隔离（独立进程，containerd 重启 shim 不跟着死，容器不受影响）；状态中继（runc 退出后 shim 代收 exit code，与 containerd 间走 ttrpc 省内存）；运行时适配（不同 shim 屏蔽 runc/kata/gVisor 差异）。
- **cgroup 驱动单一写者原则**：systemd 本身就是 cgroup 的管理者，kubelet 若再启用 cgroupfs 驱动，两个管理者写同一棵树会互相覆盖、资源限制丢失——统一 systemd 驱动；v2 用单层级树解决 v1 各子系统各自一棵树、互不知晓的硬伤。
- **snapshot/lease/GC 模型**：镜像每一层先存为 sha256 内容寻址的 content，再解压成只读 committed snapshot 链，容器启动在最上方挂一层 active 可写层（COW）；删除容器只删 active 层、底层链不动，rootfs 秒级重建、无需重拉镜像；lease 是「谁在用」的引用计数，带 TTL 由后台 GC 定期清理——**node 磁盘满十有八九是 snapshot 泄漏或 GC 未工作**。
- **CRI 设计要点**：两个 gRPC 服务（RuntimeService 管 PodSandbox/容器、ImageService 管镜像）；PodSandbox 与 Pod 一一对应，本质是「创建网络 namespace + 配 CNI 网络」的容器；exec 是新起进程、attach 连容器 PID 1（Ctrl+C 会杀容器），API Server 在 exec/attach 中扮演反向代理而非直连容器。
- **CNI 选型**：同二层且规模小→Flannel host-gw（next hop 依赖 ARP 广播解析，跨 VLAN 即废）；跨子网有 BGP 经验→Calico BGP；否则 VXLAN 最稳。
- **NRI vs Hook**：Hook 是「执行完通知你」，NRI 是「执行前让我改参数」（改 OCI Spec 注入 cpuset 等，可做 K8s 原生不支持的 NUMA/CPU 绑定）。

## 记住点
容器=隔离的进程；链路=CRI→shim(保命)→runc(一次执行)；node 磁盘满先看 snapshot 泄漏与 lease；cgroup 驱动只能有一个写者。

## 相关
- [Linux 运维判据](/wiki/cloud-native/linux-ops-heuristics)（Node 磁盘满→snapshot/lease 泄漏 与 df/du/inode 判据构成排障闭环）
- [Volcano 调度](/wiki/cloud-native/volcano-scheduling)（调度完成后 Pod 的落地下游）