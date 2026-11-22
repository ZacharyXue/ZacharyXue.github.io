---
title: "BuildKit 缓存机制：三层结构与并发冲突"
domain: "cloud-native"
domainLabel: "云原生"
created: "2026-11-14"
updated: "2026-11-14"
type: "concept"
tags:
  - "容器"
  - "buildkit"
  - "缓存"
  - "io"
  - "并发"
sources:
  - "https://raw.githubusercontent.com/moby/buildkit/master/frontend/dockerfile/docs/reference.md"
  - "https://docs.docker.com/build/cache/backends/"
  - "https://docs.docker.com/build/ci/github-actions/cache/"
confidence: "high"
summary: "构建缓存分三层（本地镜像层 / cache mount / 远程导出），三层的生命周期和导出能力完全不同——cache mount 不进镜像、也不随 --cache-to 导出，因此一次性 runner 上它天然为空；并发读写冲突由 sharing 三档参数管理，而默认 shared 之所以安全，是因为现代包管理器自己做了原子写。"
---
## 一句话本质
构建缓存分**三层**（本地镜像层 / cache mount / 远程导出），三层的**生命周期和导出能力完全不同**——cache mount 不进镜像、也不随 `--cache-to` 导出，因此一次性 runner 上它天然为空；并发读写冲突由 `sharing` 三档参数管理，而**默认 `shared` 之所以安全，是因为现代包管理器自己做了原子写**。

## 机制拆解

### 三层缓存，别混为一谈
| 层 | 是什么 | 进镜像？ | 随 `--cache-to` 导出？ |
|---|---|---|---|
| 1. 镜像层缓存 | 你 build 出来的每一层（内容哈希做 key） | ✅ | ✅ 主要就是它 |
| 2. **cache mount** | 包管理器目录（`/root/.npm`、`/go/pkg/mod`） | ❌ 永远不进 | ❌ **不会** |
| 3. 远程导出 | 把 1 存到 registry / GHA / S3 | — | 就是这一层 |

**第 2 层是最容易被忽略、却最影响速度的那层**——改一行代码重跑，`npm install` 那步虽层缓存没命中，但包不用重新下载。

### cache mount 的两个视角与一个限制
- **容器内**：你写的 `target` 路径
- **宿主上**：存在 **builder 自己的本地存储**（`buildkitd` worker 目录，默认 `/var/lib/buildkit`；rootless 是 `~/.local/share/buildkit`）。宿主机上找不到同名目录，它是 BuildKit 内部管理的快照
- **限制（文档原文）**：*Cache mounts are stored in the builder's local storage. They are not included in exported build cache (`--cache-to`), and are not restored by `--cache-from`.* → **一次性 runner 上它每个构建都是空的**，GitHub Actions 需要 `buildkit-cache-dance` 这类 workaround 才能跨 job 保留。

### 并发冲突：`sharing` 三档
| 值 | 行为（文档原文） |
|---|---|
| **`shared`（默认）** | 多个写者**并发使用**，不保证一致性 |
| `private` | 有多个写者时，**各给一份新副本** |
| `locked` | **第二个写者暂停**，等第一个释放 |

**实测对照**（两个「构建」并发各写 4MB 到同一缓存文件）：

| 策略 | 最终文件 |
|---|---|
| 直接覆盖写 | **内容交错、损坏**（两个写者的字节混在一起） |
| 临时文件 + **原子 rename** | ✅ 完整 |
| `flock` 独占串行 | ✅ 完整 |

### 为什么默认 `shared` 是安全的
因为**现代包管理器本身就用了「临时文件 + 原子 rename」**：npm/yarn（content-addressable，包按内容哈希命名）、pip、Go module cache 都是这个模式。两个构建下同一个包各写各的临时文件、最后原子 rename，**文件永远是完整的**，只是谁先到谁生效。

**但 apt 不行**——官方文档专门举例：*Apt needs exclusive access to its data*，因为 apt 会**原地修改索引文件**（`/var/lib/apt/lists`），没有原子写保护，所以必须 `sharing=locked`。

**判据只有一条**：看包管理器会不会「原地修改」文件。会 → `locked`；不会（内容寻址 + 原子写）→ `shared` 就够。

### 一句必须记住的官方提醒
> *Your build should work with any contents of the cache directory*, as another build may overwrite the files or **GC may clean it** if more storage space is needed.

**缓存随时可能被别的构建覆盖、或被 GC 清空。构建必须在「缓存是任意状态」下都能正确完成。** cache mount 只能用来提速，绝不能存「必须存在」的中间产物。

### IO 带宽：并发不涨总吞吐
实测（机械盘 `ROTA=1`）：

| 场景 | 结果 |
|---|---|
| 顺序写 200MB（O_DIRECT） | 524 MB/s |
| 2000 个 4KB 小文件（npm 缓存的典型形态） | **63.5 MB/s**（16,260 文件/秒） |
| 单个写 50MB | 137 MB/s |
| **4 个并发各写 50MB** | 总吞吐 **135 MB/s** |

**抢带宽比 0.99x：4 个构建同时跑，总带宽一点没涨，每个只拿到原来的 1/4。**

三条推论：
1. **共享 buildkitd 的扩展性有物理天花板**——所有构建的缓存读写打在同一块盘上，不是配置问题
2. **小文件是灾难**——4KB 随机写只有顺序写的 1/8，而包管理器缓存目录**全是海量小文件**
3. 这与「编译场景海量小文件随机读压死 Nydus 收益」是**同一个病根**：镜像层和缓存层最后都撞在「小文件 IOPS」这堵墙上

### GC 策略必须配（不配一定爆盘）
```toml
[worker.oci]
  gc = true
  gckeepstorage = "32GB"
  # 重建代价高的缓存（cache mount / git checkout）留久一点
  [[worker.oci.gcpolicy]]
    filters      = ["type==source.local","type==exec.cachemount","type==source.git.checkout"]
    keepBytes    = "16GB"
    keepDuration = 604800      # 7 天
  [[worker.oci.gcpolicy]]
    all       = true
    keepBytes = "32GB"         # 其他一律硬上限
```
思路是**按重建代价分档保留**：`exec.cachemount` 重建最贵，值得留 7 天；普通镜像层丢了就丢了。

### 缓存的作用域与投毒
- `scope` 参数默认 `buildkit`，**多个镜像共用一个 scope 会互相覆盖**
- 多个团队共享长期存活的 buildkitd 时，**谁都能往缓存里塞东西** → BuildKit 0.33.1 修过专门的**缓存投毒 CVE**
- GitHub 因此默认**不给来自 PR 的 workflow 写缓存权限**（只读）

### `mode=min` vs `mode=max`：不是越大越好
实测一个 8 步的多阶段 Node 服务：

| 策略 | 单次构建 | 拉回缓存量 |
|---|---|---|
| 无缓存（冷构建） | 79.0 s | — |
| `inline` / `registry mode=min` | **约 20 s** | 26 MB |
| `registry mode=max` | **132.4 s ← 更慢** | 196.8 MB |

`mode=max` 会导出所有中间阶段的缓存，导出压缩多花约 19 秒、每次拉 196MB，**该场景反而比 min 慢**。**缓存策略要按自己的 Dockerfile 实测，不能照抄网上的 `mode=max`。**

## 记住点
三层缓存生命周期各不相同，cache mount 不进镜像也不随 cache-to 走；`shared` 安全是因为包管理器原子写，apt 这类原地改文件的必须 `locked`；IO 带宽严格共享，并发只是切蛋糕；小文件 IOPS 是共同瓶颈。

## 相关
- [容器镜像构建的四代演进](/wiki/cloud-native/container-build-evolution)（这些缓存能力属于第 4 代）
- [Docker in Docker](/wiki/cloud-native/dind-gitlab-ci)（dind 结构性地拿不到第 1 层缓存）
- [镜像供应链证明](/wiki/cloud-native/image-attestation)（`--cache-to` 导出与 attestation 的取舍关系）
