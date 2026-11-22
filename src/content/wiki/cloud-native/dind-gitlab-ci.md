---
title: "Docker in Docker：GitLab CI 的 service 模式原理"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-11-14"
updated: "2026-11-14"
type: "concept"
tags:
  - "容器"
  - "dind"
  - "gitlab-ci"
  - "网络"
  - "排障"
sources:
  - "https://docs.gitlab.com/ci/docker/docker_in_docker/"
  - "https://github.com/docker-library/docker/blob/master/dockerd-entrypoint.sh"
confidence: "high"
summary: "dind 不是「把 docker 塞进你的容器」，而是起第二个 dockerd 当独立服务；job 容器里的 docker 命令只是个 TCP/REST 客户端，docker 这个主机名来自 /etc/hosts 的一条记录（或网络别名）——全程没有端口映射。"
---
## 一句话本质
**dind 不是「把 docker 塞进你的容器」，而是起第二个 dockerd 当独立服务**；job 容器里的 `docker` 命令只是个 TCP/REST 客户端，`docker` 这个主机名来自 `/etc/hosts` 的一条记录（或网络别名）——**全程没有端口映射**。

## 机制拆解

### 拓扑：三个东西，两个 daemon，兄弟不同级
宿主机 dockerd 创建两个**平级**容器：job 容器（你的 image）和 service 容器（`docker:dind`）。service 容器里跑着一个**完全独立**的 dockerd，有自己的一套 `/var/lib/docker`；job 容器里只有 CLI，没有引擎。job 结束，service 容器的镜像层随之销毁。

### 名字解析：两条路，都不是端口映射
- **默认（`network_mode` 空 + 未开 `FF_NETWORK_PER_BUILD`）**：Runner 把 service 容器的 IP 拼成 `docker:172.17.0.x` 塞进 job 容器的 `ExtraHosts`，落成 `/etc/hosts` 的一条记录。所以 `getent hosts docker` 有结果、`nslookup docker` 失败——它根本不在 DNS 里。
- **开了 per-build 网络**：建 user-defined network，service 挂 `EndpointsConfig[nm].Aliases`，走 Docker 内嵌 DNS（127.0.0.11）。但 `extra_hosts` 那条**照写不误**，双保险。
- `EXPOSE 2375/2376` 只是元数据，被 Runner 的**独立健康检查容器**用来探活，不是对外发布端口。

### TLS 默认是开的
`docker:dind` 的基础镜像里有 `ENV DOCKER_TLS_CERTDIR=/certs`，所以 entrypoint 默认走 `dockerd --host=tcp://0.0.0.0:2376 --tlsverify`，**启动时现场生成 CA/服务端/客户端三套证书**（CN 约定 `docker:dind CA` / `server` / `client`，client key 特意 `chmod 0644` 以便共享）。只有显式 `DOCKER_TLS_CERTDIR=""` 才降级成明文 2375。

**证书不是挂载现成的，是 dind 自己造的**；Runner 提供的只是「一块共享存储」——config.toml 的 `volumes = ["/certs/client"]`（Docker executor，宿主路径同时挂给两个容器）或 `emptyDir`（K8s executor，同 Pod 共享）。

⚠️ **端口号不决定协议**。让 CLI 明文连 2376，它发的就是 `http://...:2376`。TLS 开关在 `DOCKER_TLS_VERIFY` + `DOCKER_CERT_PATH` 两个环境变量。

### job 容器与 service 容器 ↔ K8s 概念的对照
GitLab 的 `services:` **不是** K8s 的 Service 对象（ClusterIP/kube-proxy 一个字都没用到）。

| | Docker executor | K8s executor |
|---|---|---|
| service 是什么 | 同一网络里的**兄弟容器** | 同一个 Pod 里的 **sidecar** |
| `docker` 指向哪 | `/etc/hosts` 里写死的容器 IP | `hostAliases` 钉到 `127.0.0.1` |
| 为什么 | 两容器 IP 不同 | 同 Pod 共享 netns，共用一个 IP |

K8s 侧之所以用 `hostAliases → 127.0.0.1` 而不是让用户写 localhost：因为它要支持**用户自配的任意别名**（`alias: mydocker`、`db`），写死 localhost 等于废掉 `alias:` 功能；顺带让同一份 `.gitlab-ci.yml` 跨 executor 可移植。

推论（Pod 网络语义）：K8s executor 下同 Pod 的所有 service **共用一个 IP，只能靠端口区分**——两个 service 抢同一端口会冲突，Docker executor 不会。

### 客户端到 daemon 的链路就是 HTTP
`docker` 命令 = 一个带 TLS 的 REST 客户端。标准流程：读 `DOCKER_HOST` → 解析名字 → TCP+TLS 握手 → **`HEAD /_ping` 协商 API 版本**（服务端在响应头回 `Api-Version`，决定后续 URL 前缀 `/v1.51/`）→ 发 `POST /v1.x/build` 等 → dockerd 在它自己的 `/var/lib/docker` 落盘。没有私有协议，`curl` 一样能操作 daemon。

**可复用抽象**：换环境只换三样——`DOCKER_HOST`（去哪）+ 证书（怎么验）+ TCP 能不能通。命令本身永不变。

## 六类失败对照（排障的核心资产）

| 场景 | 耗时 | 报错特征 | 指向 |
|---|---|---|---|
| 名字查不到 | 立即 | `lookup xxx ... server misbehaving` | 解析失败 |
| 端口没人听（服务挂了） | **24 ms** | `Cannot connect to the Docker daemon` | 内核回 RST |
| 防火墙 REJECT | **27 ms** | 与上一行**完全相同** | 也是 RST，客户端分不出 |
| 网络 DROP / 陈旧 IP / **accept 队列满** | **32 s** | `dial tcp x.x.x.x:2376: i/o timeout` | 包发出去没人应答 |
| TCP 通但 HTTP 不回（daemon 卡死） | **永不超时** | **一个字都不报** | daemon 内部 |
| 协议对不上 | 立即 | `connection reset` / `first record does not look like a TLS handshake` | 看报错里的 `http://` vs `https://` |

### 三条铁律
1. **「服务没起来」是秒拒，不是卡住**——端口无监听时内核主动回 RST，24 毫秒结束。能让客户端等 32 秒的是连拒绝都不给的 DROP。
2. **「端口没开」与「防火墙 REJECT」在客户端完全无法区分**（报错逐字相同），只能进对端看 `ss -ltn` 或 iptables。而**超时反而不用进对端**，可从客户端直接断定「包没被处理」。
3. **「不报错」信息量最大**——六种里只有「TCP 通了、HTTP 不回」会安静卡住。

### 内核层：谁在回包
- **RST 是内核发的，不是进程**。进程死后内核把 socket 从监听表摘掉，新 SYN 到达查无匹配 → 按 TCP 协议回 RST（抓包可见 SYN 与 RST 间隔仅 14µs，而端口上已无任何进程）。
- **连接成功 ≠ 进程在处理**。只要进程调过 `listen()`，内核就替它完成三次握手并把连接放进 **accept 队列**；进程不来 `accept()`，连接就永远躺着不回数据。
- 队列满时，`tcp_abort_on_overflow=0`（默认）让内核**静默丢弃 SYN** → 客户端表现为**超时**，与网络 DROP 无法区分。→ 这就是「明明服务活着却连不上」的第三种成因。

### 排查工具的选择比命令数量重要
`nc` / `ping` 只回答「通不通」，通了就闭嘴；**`nc` 对「TCP 通但 HTTP 不回」会报 succeeded（假阳性）**。`curl -v --max-time N`、`openssl s_client`、`ss -ltn`、`tcpdump` 才能回答「卡在第几步」。

`curl -w` 的 `time_connect` 是区分「卡在连接」和「卡在响应」的杀手锏：DROP 场景 `time_connect=0.000000`，半死 daemon 场景 `time_connect=0.0005`（毫秒级建连）。两者退出码都是 28，只有这一列分得开。

`ss` 的 `Recv-Q` 有两套含义：**LISTEN 态** = accept 队列积压数（进程不来取）；**ESTABLISHED 态** = 已收未读的字节数（进程收了不处理）。

## 记住点
三个容器两个 daemon；`docker` 是 hosts 记录不是端口映射；TLS 默认开、证书 dind 自己造；秒拒是内核替死进程拒绝，卡住是内核替卡住的进程收了连接没人管；报错先看耗时和 scheme。

## 相关
- [容器镜像构建的四代演进](/wiki/cloud-native/container-build-evolution)（dind 的历史定位与被淘汰原因）
- [BuildKit 缓存机制](/wiki/cloud-native/buildkit-cache-mechanics)（dind 最致命的缺陷：每次全新 daemon = 缓存结构性失效）
- [DNS 解析流程](/wiki/cloud-native/dns-resolution)（`/etc/hosts` 优先于 DNS 是 name resolution 链路的第一跳）
- [网络分层与出网链路](/wiki/cloud-native/network-layer-stack)（RST / SYN 属于传输层，与「卡在响应」是不同层）
