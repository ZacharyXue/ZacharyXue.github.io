---
title: "容器镜像构建的四代演进与主流形态"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-11-14"
updated: "2026-11-14"
type: "concept"
tags:
  - "容器"
  - "构建"
  - "buildkit"
  - "ci"
sources:
  - "https://docs.gitlab.com/ci/docker/using_buildkit/"
  - "https://github.com/moby/buildkit"
  - "https://docs.docker.com/build/cache/backends/"
confidence: "high"
summary: "镜像构建的演进主线只有一条：在「隔离性」和「缓存复用」之间找平衡——dind 买到隔离却丢了缓存，Dokanless 构建丢掉特权却仍无跨机缓存，BuildKit 的远程缓存导出才是真正的分水岭，因为它把缓存从「本机行为」变成了可外置、可分发的基础设施。"
---
## 一句话本质
镜像构建的演进主线只有一条：**在「隔离性」和「缓存复用」之间找平衡**——dind 买到隔离却丢了缓存，Dokanless 构建丢掉特权却仍无跨机缓存，**BuildKit 的远程缓存导出才是真正的分水岭**，因为它把缓存从「本机行为」变成了可外置、可分发的**基础设施**。

## 机制拆解

### 一切部署形态的前提：BuildKit 的构建不在客户端跑
```
buildctl（客户端）  ──gRPC──▶  buildkitd（守护进程）
   在 CI runner 上              真正执行 Dockerfile 的地方
   只发上下文、收日志            拉基础镜像、跑 RUN、组装层
```
**「构建客户端」与「构建执行体」天生分离**，才有后面所有玩法。`docker buildx` 本质就是 BuildKit 的客户端插件。`buildkitd` 默认监听 unix socket，也可监听 TCP（gRPC），官方明确建议 daemon 和客户端都配 **mTLS**。

### 四代演进
| 代 | 方案 | 代表 | 被取代的原因 |
|---|---|---|---|
| 1 | **dind** | `docker:dind` service | 必须 privileged（安全红线）+ **每次全新 daemon = 缓存结构性失效** |
| 2 | **DooD**（挂宿主 docker.sock） | `-v /var/run/docker.sock` | 更快，但**直接把宿主 root 交出去**，隔离更差 |
| 3 | **无守护进程构建** | Kaniko、Buildah、img | 解决特权问题，未解决跨机共享缓存 |
| 4 | **BuildKit + 远程缓存** | buildkitd、buildx | ← 当前事实标准 |

**dind 最致命的缺陷不是慢，是「结构上不具备跨 job 复用构建层的能力」**——每个 job 一个新 daemon，`/var/lib/docker` 都是空的，`RUN npm install` 昨天跑过今天还得重跑。**缓存比 CPU 贵**，这才是大厂抛弃它的核心理由。

### 四种主流部署形态
1. **一次性 builder（K8s driver / dind）**：每 job 现起现销毁，隔离干净但冷启动 + 缓存空。dind 的现代化版本只解决了特权问题，缓存问题原封不动。
2. **常驻共享 buildkitd（remote driver）← 企业主流**：起一批长期存活的 `buildkitd`，CI job 当客户端连过去。**K8s driver 与 remote driver 的取舍**：K8s driver 要求 CI 系统有「创建任意 Pod」的权限，很多团队为安全选 remote（自己管 Deployment，资源可调、监控可控）。
3. **无守护进程（Buildah）**：一次构建一个普通进程，OpenShift/RedHat 系标准答案。**kaniko 已死**——Google 于 2025-06 归档 `GoogleContainerTools/kaniko`，两个 fork 续命；GitLab 已弃用其支持。
4. **语言级构建器（被严重低估）**：ko（Go）、Jib（Java）、Buildpacks。**不需要 daemon、不需要 RUN 沙箱、不需要特权**，还能交叉编译做多架构、自带 SBOM。对纯 Go/Java 项目，这能把大部分镜像**彻底移出特权问题域**。

### 「rootless」不等于「什么都不用放宽」
K8s 里跑 rootless BuildKit，除了 `runAsUser` 非 root，仍然需要：
```yaml
securityContext:
  seccompProfile:  { type: Unconfined }
  appArmorProfile: { type: Unconfined }
args: ["--oci-worker-no-process-sandbox"]
```
且实测过：没有 `newuidmap` 和 subordinate IDs 时，rootless BuildKit **能启动但解不开基础镜像、跑不了 RUN**。测试必须用真实基础镜像，空跑通过不代表可用。

### 共享构建服务的三条真实局限
来自提供构建加速服务的团队的公开复盘：
1. **没有自动伸缩**：高峰期资源争抢、甚至 OOM
2. **成本**：常驻大机型长期空转
3. **安全**：单一共享实例，项目间隔离不充分，**有凭据泄露与交叉污染风险**（缓存投毒的土壤，见 [buildkit-cache-mechanics](/wiki/cloud-native/buildkit-cache-mechanics)）

### 供应链的硬约束反过来限制架构
SLSA 3 的三条硬要求之一是「**各次构建之间不能互相影响**」——这条直接判了共享 builder 的死刑。所以追求高 SLSA 等级的组织，反而要回到「每次构建一个隔离环境 + 外部签名」。

### 一个运维必踩的坑
**BuildKit 收到 SIGTERM 会立即终止，不等正在跑的构建结束。** K8s 滚动更新、节点缩容时，正在构建的 job 会被直接掐死。自运维 buildkitd 必须写 pre-stop hook。

### 决策速查
| 场景 | 起点 | 要盯的坑 |
|---|---|---|
| VM/专用 runner 跑 Docker CI | Buildx + BuildKit + **registry 缓存** | daemon socket 权限；BuildKit 保持新版（缓存投毒 CVE） |
| K8s CI，Pod 可放宽 | BuildKit/Buildah in Pod + `hostUsers: false` | idmap 支持；用真实镜像测 |
| K8s CI，Pod 必须严格限制 | kaniko fork（过渡）或**语言级构建器** | 一 Pod 一次构建；fork 成熟度 |
| RedHat / OpenShift | **Buildah + chroot isolation** | SCC 配置 |
| 多团队共享中心构建服务 | **BuildKit，按信任级别分独立 daemon** | 共享缓存投毒；前端 pin 版本 |
| 主要是 Go / Java | **ko / Jib** | 基础镜像选择、SBOM 覆盖 |

## 记住点
四代演进 = 隔离与缓存的跷跷板；BuildKit 的客户端/守护分离是全部玩法的前提；kaniko 已死、Buildah 接力；Go/Java 项目首选语言级构建器绕开特权；BuildKit 遇 SIGTERM 立即死。

## 相关
- [Docker in Docker 原理](/wiki/cloud-native/dind-gitlab-ci)（第 1 代的完整机制与排障）
- [BuildKit 缓存机制](/wiki/cloud-native/buildkit-cache-mechanics)（第 4 代的关键能力：缓存三层与并发冲突）
- [镜像供应链证明](/wiki/cloud-native/image-attestation)（SBOM 与 provenance 如何反过来约束构建架构）

## 边界
构建决定的**产物形态**（层数、大小、是否多阶段）会直接决定拉取期能否加速——海量小文件的镜像对内容分块型加速方案天然不友好，大文件顺序读则几乎完美。这一层属于「分发」环节，与本文的「构建」环节接续但不重叠。
