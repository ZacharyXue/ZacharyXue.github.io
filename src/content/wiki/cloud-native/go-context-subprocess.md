---
title: "Go context 与子进程：cancel 到不了的地方"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-10-02"
updated: "2026-10-02"
type: "concept"
tags:
  - "go"
  - "架构"
  - "运维"
sources: []
confidence: "high"
summary: "context 是「协作式取消」——它只能通知那些主动监听它的代码，对不监听的协程、以及已经 exec 出去的操作系统进程没有任何约束力。「超时了」不等于「事情停了」。"
---
## 一句话本质
**context 是「协作式取消」——它只能通知那些主动监听它的代码，对不监听的协程、以及已经 exec 出去的操作系统进程没有任何约束力。「超时了」不等于「事情停了」。**

## 方法要点

- **三种写法的实际行为**（实跑验证）：
  | 写法 | ctx 超时后 |
  |---|---|
  | `exec.Command(...)` | **子进程照常运行**，ctx 完全管不到它，Go 侧只是不再等 |
  | `exec.CommandContext(ctx, ...)` | kill **直接子进程**，但不杀它 fork 出的后代 |
  | 后代进程（外壳脚本拉起的子命令） | **被 init 收养继续跑**（ppid 变 1） |
- **正确姿势**：`exec.CommandContext(ctx, …)` + `SysProcAttr{Setpgid: true}`（自成进程组）+ `Cancel: syscall.Kill(-pid, SIGKILL)`（杀整组）+ `WaitDelay`（等 IO 管道收口）。**只 kill 主进程不够**——外部命令（git / docker / 脚本）常自己 fork 辅助进程。
- **判据**：只要 Go 代码里 exec 了外部命令（git / docker / kubectl / ffmpeg / shell），就要检查这一层。**超时、取消、优雅退出，全都建立在"进程真的停了"之上。**
- **比 API 更重要的推论**：任何"超时即视为结束"的设计，都必须回答一个问题——**"你怎么知道它停了？"** 如果答案是"因为它被 cancel 了"，那这个问题就还没答完。
- **配套加固**：任务状态写入带**持有者校验**（CAS，`WHERE status='running' AND holder=me`），把"我不会覆盖别人"从推论变成约束，兜住时钟漂移 / 阈值被改 / GC 停顿。

## 记住点
context 只是喊话，不是刹车；杀进程要杀进程组；"超时"必须能证明"已停"。

## 相关
- [容器运行时链路](/wiki/cloud-native/container-runtime-chain)（同为"进程与生命周期"话题）
- [Linux 运维判据](/wiki/cloud-native/linux-ops-heuristics)（进程/端口/状态排障）
