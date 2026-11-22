---
title: "镜像供应链证明：SBOM 与 provenance"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-11-14"
updated: "2026-11-14"
type: "concept"
tags:
  - "容器"
  - "供应链"
  - "sbom"
  - "slsa"
  - "安全"
sources:
  - "https://docs.docker.com/build/metadata/attestations/"
  - "https://docs.docker.com/build/metadata/attestations/sbom/"
  - "https://docs.docker.com/build/metadata/attestations/slsa-provenance/"
  - "https://slsa.dev/how-to/get-started"
confidence: "high"
summary: "两个 attestation 回答两个不同的问题：SBOM = 这个镜像里有什么（成分表），provenance = 它是怎么被造出来的（生产记录）；两者都以 in-toto JSON 包成 OCI 元数据挂在镜像上、可被 cosign 签名。provenance 默认就是开着的，而它的 mode=max 会暴露 build args 的值——这是最容易踩的…"
---
## 一句话本质
两个 attestation 回答两个不同的问题：**SBOM = 这个镜像里有什么（成分表）**，**provenance = 它是怎么被造出来的（生产记录）**；两者都以 in-toto JSON 包成 OCI 元数据挂在镜像上、可被 cosign 签名。**provenance 默认就是开着的**，而它的 `mode=max` **会暴露 build args 的值**——这是最容易踩的雷。

## 机制拆解

### 两者对照
| | SBOM | provenance |
|---|---|---|
| 回答 | **里面有什么** | **怎么造出来的** |
| 类比 | 食品配料表 | 生产溯源记录 |
| 内容 | 软件构件清单 + 版本 + 许可证 | 时间戳、构建参数、VCS 元数据、源码、消费的材料、（max 时）LLB 定义与 Dockerfile 全文 |
| 格式 | **SPDX**（BuildKit 默认）/ CycloneDX | in-toto + **SLSA provenance**（v0.2 默认，可选 v1） |
| 默认生成？ | ❌ 要 `--sbom=true` | ✅ **自动（见下）** |

### provenance 的默认行为（很多人不知道自己在产出它）
`docker/build-push-action` 会自动加：
- **公开仓库 → `mode=max`**
- **私有仓库 → `mode=min`**

| | `mode=min` | `mode=max` |
|---|---|---|
| 时间戳 / 前端 / 材料 / 源仓库与 revision / 平台 | ✅ | ✅ |
| LLB 定义（完整构建步骤） | ❌ | ✅ |
| Dockerfile 全文（base64） | ❌ | ✅ |
| 构建步骤与镜像层的源映射 | ❌ | ✅ |
| **build args 的值** | ❌ | **✅ 会暴露** |

### 🚨 最危险的踩雷点
文档原文：*mode=max exposes the values of build arguments.*

把密码写成这样，**它就被写进了随镜像一起发布的 attestation 里，谁都能读**：
```dockerfile
ARG NPM_TOKEN                                                                   # ❌
RUN npm config set //registry.npmjs.org/:_authToken=$NPM_TOKEN
```
正确做法是 secret mount——**它不会离开构建过程，也永远不会出现在 provenance 里**：
```dockerfile
RUN --mount=type=secret,id=npmtoken \
    NPM_TOKEN=$(cat /run/secrets/npmtoken) npm ci
```

### 为什么 SBOM 要在构建时生成，而不是事后扫镜像
Docker 文档给的理由：构建期索引能发现**你在构建中用到的软件，而这些可能根本不出现在最终镜像里**——多阶段构建的 builder 阶段就是典型：工具链留在 builder 层被丢弃，但它带的漏洞事后扫最终镜像**扫不出来**。

### 可复现构建需要两样东西
1. `SOURCE_DATE_EPOCH` —— 固定时间戳
2. `rewrite-timestamp=true` —— exporter 参数

**只做第一样不够**：实测 config 的时间对了，但 digest 每次仍会变。

⚠️ 还有个陷阱：**provenance 会让 image index 的 digest 每次不同**（因为记录了构建时间与 invocation ID）。校验可复现性时要比对 **platform manifest digest，不是 index digest**。

### SLSA 等级：反过来约束构建架构
**SLSA 3 的三条硬要求**：
1. 在产生并签名 provenance 的托管平台上构建
2. **各次构建之间不能互相影响**
3. 生成的签名 provenance 可验证

第 2 条直接否掉了「多团队共享一个长期 buildkitd」的方案——这就是为什么追求高 SLSA 的组织反而要回到「每次构建一个隔离环境 + 外部签名」。

### 实际用途
供应链出事的场景（比如某依赖爆出严重漏洞）：
- 有 **SBOM** → 几分钟内查出「我们哪个镜像受影响」
- 有 **provenance** → 能证明「这个镜像是从哪个 commit、经哪条流水线出来的、没被人动过手脚」

## 记住点
SBOM 是成分表、provenance 是生产记录；provenance 默认开、公开仓默认 max、max 会泄 build args，密码必须走 secret mount；SBOM 必须构建时生成才看得到 builder 阶段的依赖；SLSA 3 要求构建之间互不影响。

## 相关
- [容器镜像构建的四代演进](/wiki/cloud-native/container-build-evolution)（SLSA 3 如何反过来限制构建架构）
- [BuildKit 缓存机制](/wiki/cloud-native/buildkit-cache-mechanics)（attestation 与 cache 导出都是 `--cache-to` 体系的兄弟）
- [Docker in Docker](/wiki/cloud-native/dind-gitlab-ci)（旧一代构建方式不产生任何 attestation）
