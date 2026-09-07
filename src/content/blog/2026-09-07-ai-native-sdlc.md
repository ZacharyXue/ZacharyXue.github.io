---
title: AI-Native SDLC：当代码不再是瓶颈，流程重构才是主战场
date: 2026-09-07
tags: [AI工程, SDLC, Agent, 软件工程, 上下文工程, spec-driven]
description: 从《AI-Native SDLC Playbook》出发，拆掉 Claude 专属外壳，提炼出跨所有 AI Agent 的通用软件开发范式：六阶段循环、工件即审计轨迹、仓库内 md 即上下文、校验闭环、分层 review 与治理。附 Claude 专属 → 通用等价物映射表。
---

> **主引用**：[The AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook)（Anthropic / Claude，2026）
> **跨厂佐证**：
> - [The AI-Native SDLC](https://sdlc.xeb.ai/)（独立研究综述，2026.07，逐条溯源 + 对抗性验证）
> - [Spec-driven development with AI](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)（GitHub Blog，2025.09，跨 Copilot/Claude Code/Gemini CLI）
> - [AGENTS.md](https://agents.md/)（open standard，Linux Foundation 旗下 Agentic AI Foundation 托管）
> - [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)（Anthropic，2025.09）

---

这篇文章要做的，是把 Anthropic 那份 Playbook 里**不依赖任何特定 Agent 品牌的通用范式**抽出来，还原成一份「任你手里是 Codex、Copilot、Cursor、Claude Code、Gemini CLI 还是 Hermes，都成立」的软件开发方法论。

`CLAUDE.md` 换成 `AGENTS.md`，`hook` 换成「任意 pre/post 命令门」，`plan mode` 换成「实现前先出可验收计划」——你会发现核心骨架一件没少。**Claude 只是这套范式第一个把所有部件拼齐的实现者，而不是定义者。**

---

## 一、代码不再是瓶颈（核心立论）

先记住这句话，全文都是它在展开：

> **当 AI 把「写代码」压缩到极限时，传统 SDLC 的瓶颈就从「实现」转移到了它两侧——左边的「需求/设计」和右边的「测试/部署/治理」。**

Anthropic 的原话：*Organizations have started using AI to write code at a speed unthinkable one year ago, yet the processes around the code haven't changed at the same pace.*（AI 已经开始以一年前难以想象的速度写代码，但围绕代码的那套流程没跟上。）

传统 SDLC 是六阶段线性接力：**Plan → Design → Build → Test → Deploy → Maintain**，每段由不同角色负责，靠「文档/ticket/签字」在阶段间传递。这套机制设计于「写代码最贵最慢」的时代——`PRD`、工时估算仪式、产品安全评审，都是为那几周甚至几个月的开发周期服务的。

当 `Build` 阶段从「以月计」缩到「以天甚至小时计」，三个后果立刻出现：

1. **瓶颈左移右移**。计划、评审/测试、部署还在以「人速」运转，成了新的卡点。
2. **旧控制失效**。逐行审查曾经有意义（因为是人写的），现在每行都是 agent 写的，靠人逐行 review 根本跟不上 diff 量。
3. **治理成本飙升**。例外事项还是要走周会/月会评审，反而拖慢了本就该提速的交付。

数据印证这件事早已发生，且是行业共识（非 Claude 独家）：

- **Claude Code 约 90% 的代码由 Claude Code 自己写，作者 Boris Cherny 每天靠约 5 个并行实例发 20–30 个 PR。**（自报）
- **Google 超 1/4 新代码 AI 生成**（Pichai，2024.10）、**Microsoft 仓库中 20–30% 代码 AI 写**（Nadella）、**Robinhood 约半数新代码 AI 生成**（Tenev）——注意这些都含自动补全接受率，是「AI 参与」而非「自主署名」。
- **GitHub 开源 Spec Kit**，明确把「spec 驱动」设为 agent 工作流的默认心法，且官方支持 Copilot / Claude Code / Gemini CLI 三种工具。
- **Gartner 预测到 2029 年 60% 组织会采用「微型软件工程团队」（4–5 人，部分 2–3 人）**，从 2026 年的 15% 涨上来，而且是「围绕 AI 重组」而非裁员。

## 二、范式转变：线性链 → 反馈环，工件即审计轨迹

传统 SDLC 是**接力赛**，AI-native SDLC 是**环**。这是本文最核心的一层认知。

Anthropic 的框架里，每个阶段结束于**提交一个工件到版本控制**，下一个阶段从**读这个工件**开始：

| 阶段 | 结束时的工件 | 下一阶段的触发 |
|------|-------------|---------------|
| Plan | `intent.md`（意图） | 产品 owner 审批 accept → 进入 Design |
| Design | `spec.md`（需求+设计规格） | owner 批准 → 进入 Build 的 plan 流程 |
| Build | `plan.md` + diff + 测试 + PR | agent 实现完成 → PR Review |
| Test | 评测结果 / eval 套件 | 测试通过 → 可合并 |
| Deploy | 发布记录 / 分层的 review 发现 | 合并触发流水线 |
| Maintain | 事故记录（写入新的 `intent.md`） | 控制带越界 → 触发新一轮 Plan，**闭环** |

早期阶段（Plan/Design）的工件以 `.md` 为主，因为**人和 agent 能读同一个文件、并基于它行动**；从 Build 起，工件变成代码和它的记录。

工件不只是在传递信息——**整条 commit 链本身就是审计轨迹**：谁要的（intent 作者）、agent 造了什么（diff）、谁批的（审批记录）。地地道道的「谁问了什么、AI 产出了什么、谁点头了」，全部留痕。

人还是对每个需要判断的决策负责，但注意力的位置变了：**从「盯每个阶段从头到尾」变成「守在每个门口 review agent 标记出来的东西」**。这是「人在环上」和「人在环里」的本质区别。

### 一件反直觉的事：agent 上下文文件成了最高杠杆工件

xeb 综述把这句话讲得很透：*The artifact hierarchy inverts: the spec and the agent-context file become load-bearing; the code becomes (partially) generated output.*（工件层级反转：**规格和 agent 上下文文件成了承重构件，代码成了（部分）生成产物。**）

这自然引出第三节——既然最高杠杆的工件是一张 md，那它到底是什么工程？

## 三、仓库内 md = 上下文工程（理论底座）

为什么一张 `AGENTS.md` 的作用这么大？因为这堆 md 本质上是**上下文工程**。

Anthropic 那篇《Effective context engineering》给了个关键区分：

- **Prompt engineering**：怎么写一段指令让单次推理输出更好。
- **Context engineering**：在有限的上下文窗口里，为每一轮推理**持续筛选、维护、配置最可能产生期望行为的那组 token**——包括系统指令、工具、MCP、外部数据、历史消息。

agent 是在一个 loop 里跑的，每一轮都在产生「可能对下一步有用的新数据」，这些信息必须被循环精炼。**仓库根目录的 `AGENTS.md` 就是「预先配置好的上下文」**——agent 每次会话第一步就读它，比什么提示词都稳定、都比塞历史省 token。

关键点：**`AGENTS.md` 已经是一个开放标准，不是任何一家的私有格式。**

- 源自 OpenAI Codex，后移交 **Linux Foundation 旗下的 Agentic AI Foundation** 托管（2026 Q2），中性多厂商共治。
- **Codex、Cursor、Cline、Windsurf、Gemini CLI、Claude Code、Jules、goose、opencode、Zed、Warp… 全部读取 `AGENTS.md`。**
- 你可以在仓库根放一份，所有工具都读到；各工具的私有配置（CLAUDE.md、.cursorrules）只放工具专属扩展，且可以用 `@AGENTS.md` 避免重复。
- 层级发现机制：全局（`~/.agents/AGENTS.md`）→ 项目根 → 子目录逐级串联，近者优先。
- **别写成长文**。xeb 引 Anthropic 原话：*bloated CLAUDE.md files cause Claude to ignore your actual instructions.*（臃肿的上下文文件会让 agent 无视你的真实指令。）它被整个塞进上下文窗口，任何过时内容都在白白烧 token。

这份文件该装什么（参照 CLAUDE.md / AGENTS.md 的标准骨架，通用化后依然成立）：
- **Commands**：`make build` / `make test` / `make lint` 及「健康输出的样子」
- **Conventions**：能阻止 agent 反复踩坑的团队约定（如「钱永远是 BigDecimal，绝不 double」）
- **Architecture**：目录职责一句话讲清
- **Things the agent gets wrong**：agent 反复犯的错，写进来一劳永逸

⚠️ 这条铁律对每个 agent 品牌通用：**「agent 犯两次错，就加成一句命令/约定进 AGENTS.md」**，而且它要像代码一样进 git、走 PR review、由团队共同维护。

## 四、六阶段通用化拆解

现在进入重头戏。下面六节把 Anthropic Playbook 的每个 stage 还原成**不绑定任何特定工具**的通用范式，每节统一口径：**阶段目标 / 关键工件 / 人类守门点 / play 细节**。

---

### ⚙️ Stage 1 · Plan：把「想法」写成可执行的意图

**目标**：把一个人脑中的模糊想法，转成他人/agent 都能读取的 `intent.md`。

**它解决的传统痛点**：过去一个想法要过「说服产品、写 PRD、开会 sign-off」才进得了开发管线；现在一个人直接跟 agent 头脑风暴，产出 proto-spec。

**通用流程**：
1. 创始人用自己的话描述问题（做不到什么、影响谁、好了会怎样、什么不在范围内），不需要正式语言。
2. 反复头脑风暴把想法谈具体——agent 问分析师该问的问题：范围、用户、约束、成功长什么样。
3. 让 agent 按团队模板写成 `intent.md`（模板可编码成 skill）——覆盖：问题、预期产出、受影响用户/系统、约束、开放问题。
4. **人校正 agent 理解错的地方**。
5. commit 到共享仓库。作者+时间戳进记录，产品 owner 从这里接手。

`intent.md` 可以有多种入口：人想出来的、ticket、或线上事故（从 Maintain 阶段回流）。

```markdown
# Intent: 理赔状态自助查询
Author: J. Ortiz（理赔运营）。Status: draft.

## Problem（问题）
客户打电话到联络中心问理赔进度。
坐席约有三分之一通话时长耗在「仅查状态」的请求上。

## Proposed outcome（预期产出）
客户在门户看到理赔状态、下一步和预计日期。

## Affected users and systems（受影响用户/系统）
理赔坐席、门户团队、claims-core API。

## Constraints（约束）
门户会话不新增 PII。仅用现有认证。

## Open questions（开放问题）
第三方理赔师是否需要访问权限？
```

**人类守门点**：产品 owner 审校、校正、然后 commit 或驳回。**证据就是 git 历史里的 `intent.md` 全量修订记录**。

---

### 🎨 Stage 2 · Design：从意图到「可规划、可构建的」spec

**目标**：把已接受的 `intent.md` 变成一份工程团队能据此规划的 `spec.md`。

**通用流程**：
1. 在**组织的 skills 约束下**（品牌、安全、合规、UX 标准都编码成 skill，写 spec 时实时套用），agent 从 `intent.md` 产出需求+设计规格。
2. **产品 owner 审，但不写**。审的是：这份 spec 是否解决了原问题？intent 里的开放问题是否都回答了或带下去了？
3. **先啃 flagged concerns**——那些是分析师会升级的点，owner 在工程看到前逐个和策略 owner 对齐。
4. commit `spec.md` 与 `intent.md` 成对。文件对记录「要了什么」和「定了什么」。
5. 产品 owner 决定是否推进到 build（高风险项咨询技术负责人）。**这个「推进」始终由人拍板**，accept spec 就是触发 build plan 流程的信号。

**治理红利**：策略是「写的时候就近生效」而不是「几周后评审才发现」——skill 版本、prompt、产出的 spec 都进版本控制，可审计。

---

### 🛠️ Stage 3 · Build：实现前先出计划，实现时给闭环

**这是全文重点展开的一节**，因为 Build 是所有「agent 能力手段」最密集的阶段。

#### 3.1 先计划，再动手（plan-first）

给 agent 已批准的 `spec.md`，让它**先产出 `plan.md`**：
- 列出会改哪些文件、工作顺序、用什么测试证明。
- **审计划要反问**：这个改动可能搞坏什么？哪一步最险？还有什么备选方案你主动放弃了？
- 迭代到「**一个从没见过这段对话的工程师，也能仅凭 plan 独立实现它**」为止。
- commit `plan.md`，与 spec/intent 一起进审计轨迹；**PR review 时拿最终 diff 对着 plan.md 查合规**。
- 实现一旦偏离计划，**改 plan.md 要在同一个 commit 里**（可以用 hook 强制两者同步）。

**为什么不直接让 agent 写**：GitHub Spec Kit 把那句话讲得最准——*treat coding agents more like literal-minded pair programmers. They excel at pattern recognition but still need unambiguous instructions.*（把 agent 当字面理解的结对程序员，而不是搜索引擎。它们擅长模式识别，但需要无歧义的指令。）

**一个节制的智慧（Anthropic 原话）**：**一句话的改动可以跳过 plan**。把计划当默认而不是仪式，是为了不让「为低价值改动做计划」变成新的摩擦力。

#### 3.2 反馈闭环：让 agent 能验证自己

一以贯之的铁律——**Always give the agent a way to verify its own work**（永远给 agent 一条能验证自己工作的路）：

- 把验证动作包成单一目标（`make test` / `npm test`），失败非零退出。
- 在 AGENTS.md 的 Commands 里写清每条命令 + 健康输出样貌。
- 设**可量化**目标让 agent 不求人：如「test_status.py 全绿」「截图和附的 mock 一致」「endpoint 200 带新字段」。
- **修 bug 用 TDD 左移**：先让 agent 把 bug 复现成一条失败测试，确认失败原因符合预期，**先 commit 这条测试**，再让它改代码使其通过——且**不许它改这条测试**（用 hook 锁测试文件）。一条「修复前就存在、agent 不能重写」的测试，才是 bug 真消失的证据。
- UI 类工作：给浏览器/截图工具，**实现→截图→对比→调整**，两三轮迭代收敛。
- **把「验证」写进「完成」的定义**：AGENTS.md 里写「报告完成任务前必须跑这三条命令并把输出贴出来」。

这一节的关键设计意图：**自检的 agent 会在你来 review 之前就发现并修掉自己的错。** 证据来自工具链的原始输出（`make test` 的日志、截图 diff、build log），不是 agent 的「我完成了」声明。

#### 3.3 并行会话与子任务

一个工程师可以同时驱动好几条流：

- **并行会话**：独立的完整 agent 实例，各在自己的 git worktree 里干活，互不知晓，共享的只有「指挥它们的工程师」。用法：用 plan 找出「改动不碰同一批文件」的独立任务 → 一人一条 worktree。
- **子任务（subagent）**：在单个会话内跑的**限权辅助**，有自己的上下文窗口和工具限制，适合跨任务复用的活——一个「验证器」跑起来检查行为、一个「简化器」在主 agent 结束后清掉多余复杂度、一个「研究型」探代码库而不淹没主上下文。

```markdown
---
name: verifier
description: 会话报告完成前，跑起应用并确认改动有效
tools: Bash, Read
---
用 make run 启动应用。运行被改动的那条行为，连同它相邻的两条流程。
报告你跑了什么、看到了什么、以及任何与 plan.md 不符的行为。
只报告，不动手修。
```

**治理**：更多会话 = 更多产出，所以控制一定要来自仓库里提交的配置（hooks / 权限设置），对所有会话一致生效。工程师是唯一的指挥者，也是唯一的 review 者。

#### 3.4 Build 期的护栏：从劝说到阻断

Anthropic 把控制分成两层——**skill 是「劝说层」，hook 是「阻断层」**。这个分层思维通用性极强：

- **Skill（能力/规范包）**：把一个「今天总执行不一致的策略」写成 `SKILL.md`——frontmatter 写「何时触发」，正文写「要做什么」。进仓库随代码走，策略变化时由 owner 签字、团队成员下次会话自动拿到新版本。
- **Hook（确定性护栏）**：skill 只让「违规变少」，hook 让「违规几乎不可能」。build 期 hook 的典型用途：
  - **阻断对受保护路径的编辑**（生成的类、冻结的包）
  - 每次编辑后自动跑格式化和 lint，让漂移永远不累积
  - 把凭据挡在 diff 之外

**铁律：凡是「必须无条件成立」的策略，背后一定要有确定性机制（hook/CI gate），不能只靠 skill 劝说。** skill 让违规变少，hook 让违规趋近零——前者的调用会被记录，后者的每次触发都被阻断。

#### 3.5 连续评测（eval）在 CI

eval 是「AI-native 版的阶段门 QA」。它不是敷衍地测 agent 的代码，而是**测「引导 agent 的那套配置」**：

- 平台工程师从近期真实工作收集 20–50 个任务及其「可接受产出」。
- 每个任务写成 eval：prompt + 判定可接受的一组检查（测试通过 / lint 干净 / 行为不变 / 策略遵守）。
- 套件非交互跑在 CI，**在每次 `AGENTS.md`/skills/hooks 等配置变更时**也触发——因为「引导 agent 的配置」和代码一样值得回归测试。
- **配置变更以 eval 结果做门禁**：skill 改完通过率掉，先 review 再 merge。
- **每个线上事故都要补一个 eval**，当回归测试永远留在套件里。

```yaml
name: Agent evals
on:
  pull_request:
    paths: ['AGENTS.md', '.agents/**']
  schedule:
    - cron: '0 2 * * *'
jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g <你的agent-cli>
      - name: Run eval suite
        run: |
          for eval in evals/*.json; do
            <agent-cli> -p "$(jq -r '.prompt' $eval)" \
              --allowedTools "Read,Edit,Bash(make test)" \
              --output-format json > result.json
            ./evals/check.sh "$eval" result.json
          done
```

**人类守门点**：实现由 agent 做，但计划（plan.md）、关键改动、eval 结果都要人审。`done` 的定义带证据，不是 agent 说完成。

---

### 🧪 Stage 4 · Test：把 QA 从「阶段门」变成「贯穿的评测」

**目标**：Agent 时代 QA 没消失，而是**换形态**——从「阶段边界的门禁」变成「编进实现过程的连续验证」。

Anthropic 的规则讲得最狠：**If you can't verify it, don't ship it.**（不验证，就别发布。）

#### 4.1 机器可查的验证环取代人工逐行检查

- **校验动作的原始输出就是证据**：测试日志、build exit code、截图 diff、浏览器自动化的流程。agent 必须「贴出它跑出来的」，而不是「说它做了」。
- **别做「单测剧场」（unit-test theater）**：这是 xeb 反复点名的失败模式——agent 单测全绿但功能根本不通。给 agent **端到端 / 浏览器级**验证工具，Anthropic 实测「给 agent 真正的 E2E 检查工具能显著提升长程 agent 的表现」。

#### 4.2 对抗性评审：用「全新上下文」审 agent 自己的 diff

一个极关键的设计：**让 agent 用全新上下文审自己刚写的代码**。

> *A fresh context improves code review since the agent won't be biased toward code it just wrote.*（新上下文能改进评审，因为 agent 不会偏向自己刚写的代码。）

- **Writer/Reviewer 分两个会话**。写完代码的那个会话去干别的，另开一个全新上下文的会话审 diff。
- **限制 Reviewer 的反馈范围**：对抗性 reviewer 有个毛病是**过度报告**（over-report），所以要限定它「只报影响正确性的问题」，别让它淹没在风格 nit 里。
- **人类评审自动上移一层**：从逐行读，变成「spec 符合性 + 架构 + 验证证据检查」——「show me the passing test / the screenshot」。

这套「写完代码的那个 agent 无权批准自己的代码」的**职责分离**，是贯穿 Deploy 阶段治理的骨架，也是 xeb 综述给「质量」开的第一味药：**no verification artifact, no merge**（没有验证工件，不许合并）。

#### 4.3 不可变的测试契约

Anthropic 长程 agent harness 里最硬的一条：initializer 写一份**feature list**，coding agent 只能翻转测试的 `passes` 字段，**绝不删测试**——*It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality.*（删除或改写测试不可接受，因为可能导致功能缺失或缺陷。**测试清单就是质量棘轮。**）

---

### 🚀 Stage 5 · Deploy：分层的自动评审 + 确定性批准门

**目标**：让部署跟上 agent 的产出速度，同时把「该复议的决定留给人」。

Anthropic 的核心主张（通用化）：**治理不是事后评审，而是在 agent 行动时实时执行，用 hooks 当批准门。**

#### 5.1 分层 review：自动评审 + 人只审风险和关键代码

- **让 agent 既发评审、也收评审**：它按组织的 review 策略审进来的 PR，也回评自己对 PR 的意见。工程师的精力集中到「**判断意图和风险**」。
- 技术负责人把评审策略写成 `REVIEW.md`，分 pass：
  - **Bugs**：逻辑错误、边界问题、细微回归
  - **Security**：注入风险、认证缺口、日志里的 PII
  - **Compliance**：改动是否和 spec.md / plan.md / 设计原则吻合
- `REVIEW.md` 里定义**「重要」vs「小问题」**：重要=会破坏行为、泄露数据、违规；风格命名是小问题。**限制每条评审最多报 5 个 nit**，其余折算成计数。
- **人类阈值**：自动评审的发现不单独批准/阻断 PR，**分支保护仍要求 code owner 人工批准**。没有「写了代码的 agent 能批自己代码」这条路——职责分离在此闭环。

#### 5.2 Hooks 当批准门：让「该留人的决定」留在人

- Build 阶段的 hook 是**无人审批的「允许/阻断」**；Deploy 阶段的 hook 多了一层：**可以「问」，暂停动作直到指定的人批准**。
- 工程领导（连同变更管理和合规）列出**必须存续的人工批准门**：变更管理签字、发布授权、受保护路径的编辑。
- 每个门表达成 hook：一个在 agent 动作前跑的脚本，能 `allow`（放行）/ `ask`（问人）/ `block`（阻断）。
- **团队 hook 进 git；不可商量的 hook 进受管配置**（MDM / 管理台），个人工程师无法关掉。
- **block 要会解释自己**：阻断时把原因和「找谁批、怎么批」一并喂回给 agent 的输出。

```yaml
# 受管 settings 示意（平台团队下发，工程师无法覆盖）
permissions:
  deny: [ "Read(.env*)", "Bash(curl *)", "WebFetch" ]
  allow: [ "Bash(git *)", "Bash(make build)", "Bash(make test)" ]
disableBypassPermissionsMode: disable   # 谁也加宽不了
sandbox:
  enabled: true
  failIfUnavailable: true                # 沙箱起不来就不开工
  network: { allowedDomains: ["git.internal.example.com"] }
  credentials:
    files: [{ path: "~/.aws/credentials", mode: "deny" }]
    envVars: [{ name: "GITHUB_TOKEN", mode: "deny" }]
allowManagedHooksOnly: true              # 只有平台门的 hook 能跑
allowManagedMcpServersOnly: true         # agent 的工具面由平台 allowlist
```

#### 5.3 CI/CD 集成：agent 作为构建步骤

- 从只读判断步骤起步：在流水线 job 里跑 agent triage 失败的 build、总结 flaky 测试、起草 changelog（`-p` 非交互模式）。
- 只读步骤通过现有门禁后，加写步骤（修 lint、更新生成文档、`@agent` 回评），**写操作一律以 PR 形式经分支保护落地，agent 没有直推 main 的路**。
- **agent job 要沙箱化**：容器 + 网络策略 + 短期 scoped token，默认不持生产凭据。
- **用 MCP 暴露部署**：deploy/status/rollback 变成按环境 scope 的工具，agent 的部署权是 allowlist 而非一个带凭据的 shell 脚本。
- **按环境分层自治**：dev 自由部署 → staging 中间态 → **prod 由 agent 准备发布、release manager 授权，hook 强制这道门**。
- **rollback 是整条流水线里最该排练的路径**：一条命令、agent 能跑、在 staging 定期演练——因为 Maintain 阶段一旦「控制带越界」就要靠它。

```yaml
- name: Triage failed build
  if: failure()
  run: >
    <agent-cli> -p "读 out/build.log，指出最可能的原因，
    判断失败更像 flaky 还是真实的，写三行摘要到 PR thread。"
```

**核心治理原则一句话**：**agent 可以干到生产门为止、不能越过它。** 分支保护把 agent 的写变成 PR，生产部署 hook 把发布锁定到 release manager 授权，每次非交互运行都在 agent 自己的身份下记日志——谁做的分得清。

---

### 🛰️ Stage 6 · Maintain：闭环与无人值守的「最后一公里」

**目标**：前五阶段都还是「人启动每个步骤」，这一阶段让 agent **自主运行、把环闭上**，把线上事故「写回」成一个新的 intent，走完整个循环。

#### 6.1 闭环：确定性监控 + 分级响应

设计精妙之处在于——**检测必须 100% 确定性、零模型介入**，模型用在「诊断」而不是「发现」：

1. 服务 owner 挑**一个带稳定滚动基线的指标**（CI 测试失败率、部署后 5xx 率、PR 周期）。检测脚本用 mean±std 滚动窗口 + Western Electric 规则，**版本化、可单测、完全确定，无模型参与**，既逮慢漂移也逮尖峰。
2. 分级响应在受管配置里（`bands.yaml`）：
   - **1σ**：只记日志
   - **2σ**：调 agent **只读诊断**
   - **3σ**：agent **可行动**——但只能通过「开 PR 进评审门」或「触发预先批准的 runbook」（如回滚）
3. 触发层：GitHub/GitLab 定时 workflow、现有监控的 webhook、或网内 Cron Job。agent **无状态**跑，要么是 CI runner 的非交互步骤，要么是沙箱里的 agent SDK 服务。
4. agent 把诊断写成 `intent.md`（Plan 格式），走正常管线。
5. 值班人 triage 队列：修 / 排期 / 驳回。**驳回在调带（tune the bands）、降噪。**
6. 修复上线后**补 eval**，防止同类事故复发。

```yaml
metric: ci_test_failure_rate
baseline: rolling_30d
rules: western_electric
tiers:
  1sigma: { action: log }
  2sigma: { action: diagnose, tools: "Read,Grep,Bash(gh run view *)" }
  3sigma:
    action: propose
    routes: [ pull_request, runbook:rollback-deploy ]
```

**能看出的典型闭环**：CI 失败率破 3σ → agent 隔离 flaky 测试或开 revert PR，评审门定夺；部署后 5xx 破 3σ 且窗口内有部署 → agent 触发回滚流水线；PR 周期触发漂移 → agent 给工程领导写报告（证明这套 harness 连流程指标都能管）。

**一条硬边界**：别幻想「完全无人值守的自治事故响应」。IBM ITBench 基准（ICML 2025）实测最先进的模型也只在 13.8% 的 SRE 场景里成功解决，所以「agent 处理事故」要读成 **assist 而非 replace**。

#### 6.2 周期性代码扫描（安全）

- 一次扫描是「某个模型对某个代码库的某一刻快照」，**两边都会过时**：代码每周变、新一代模型能发现上一版漏掉的洞。
- AI-native 的答案：**按计划跑，人类不进触发路径**，发现的东西和其他改动一样走评审门。
- 首次全扫当 **baseline**——第一遍几乎必然在「被认为干净的代码」里翻出东西来。
- 每个发现带**置信度**；驳回要带**理由**（记录在案，下轮不重复报）；修一个发现要**补对应配置的 eval**。
- 模型驱动扫描是**给现有静态分析/依赖扫描做增量**：确定性检查留在 CI，模型扫描专攻「依赖上下文的、现有检查设计上就找不出的漏洞」。
- **定域性强修改**（不止一个 patch 的架构弱点）→ 写回 `intent.md` 从 Plan 重新起。

#### 6.3 事件可以用多样入口到达

除了监控，事故还能从聊天工具来（Slack/Teams 的 incident channel）。通用化的做法是**让 agent 以自己身份加入线上群**，每起新事故有一个「第一响应者」，而对话本身成为后续事故的 memory——**事故响应本身就是环的一部分，是未来事故的语境**。

**人类守门点**：整个 Stage 6 里人类不挡在 agent 启动路径上，但**triaging 队列、审批 findings、批准 runbook、决定 prod 发布**都是人，且每次调用和判定都带时间戳留痕。

---

## 五、贯穿全文的六个范式（一句话记忆版）

把上面六百行压成六句，是这篇的「学到了什么能带走」：

1. **代码不是瓶颈了** → 瓶颈在它两侧的计划/评审/部署/治理，所以重构流程比换更多 agent 更值钱。
2. **SDLC 从线性接力变成环** → 每阶段提交一个工件，下一阶段读它；commit 链就是审计轨迹。
3. **仓库内 md 是最高杠杆工件** → `AGENTS.md`（开放标准，全工具读）是「预配的上下文」，像代码一样维护，臃肿即失效。
4. **先 spec 后 code，再验证闭环** → spec-driven 是所有 agent 品牌的默认心法；`if you can't verify it, don't ship it`。
5. **分层 review + 确定性门禁** → agent 用全新上下文对抗审自己，人只审 spec 符合性/架构/证据；必须无条件成立的策略背后放 hook（阻断层）而非 skill（劝说层）。
6. **把环闭上** → 确定性监控触发诊断，agent 把事故写回 intent，逐级自治升级，人守 triage 和审批。

## 六、落地路径（别一步上满自动驾驶）

Anthropic 强烈建议——**先别搭一个无人值守的生产环**。它的落地顺序是这个行业的共识：

1. **Pilot**：挑 20–50 个已经熟悉 AI 工具的开发者（他们是未来的 agentic coding 冠军）。
2. **Hackathon 启动**：org-wide 用一个启动黑客松，而不是分阶段铺开，pilot 用户做导师。
3. **内部专家规模化**：pilot 用户变成内部咨询师，自己开 agentic-coding workshop。

在一个项目上，从**一个低风险变更类型**跑通「intent → plan → 一键验证 → 硬边界」的完整闭环，用质量数据决定要不要扩大 agent 权限。一步一个循环，比一步到位自动驾驶稳得多。

## 七、风险与边界：AI 是放大器，不是修正器

xeb 综述里最清醒的一段独立研究必须摆出来，否则这篇就是又一次 hype。它有大量**反方证据**（都经过溯源）：

- **METR（2025.07 随机对照试验）**：有经验的开源开发者用早期 AI 工具在自己成熟的仓库里修真问题，**反而慢了 19%**——但他们预测会快 24%，事后仍相信自己快约 20%。**感知和实际的生产力背离。**
- **DORA（2024/2025）**：AI 是**放大器**——放大组织既有优势和失调；约 90% 从业者已在用 AI，但约 30% 对 AI 代码信任低。
- **GitClear（2.11 亿行变更）**：重构相关变更从 2021 年的 25% 掉到 2024 年的 10% 以下，而复制粘贴行从 8.3% 升到 12.3%，**AI 辅助代码库在向复制粘贴熵漂移**，除非用重构纪律对冲。
- **Stanford / Denisov-Blanch（600+ 公司，10 万+ 工程师）**：AI「远未接近」替代工程师；简单语言 +20~25%，复杂/单薄/老代码近乎持平甚至负。有公司 PR 涨 13.6% 但代码质量掉 9%、返工涨 2.6×，净产出只涨约 1%。
- **Replit 事故（2025.07）**：agent 在明确 code freeze 期间删了生产数据库，还先给了误导性恢复回答。这就是**沙箱、环境隔离、绝不授予 agent 常驻生产写权限**的教科书反面例子。
- **Klarna**：庆祝过「AI assistant 顶 700 个 agent」后 2025 年公开回调，恢复招人——CEO 承认成本导向「走太远」「质量掉下来」。

结论不是「别用 AI」，而是 xeb 那句最硬的总结：

> **Quality in an AI-native SDLC is an engineered property of the harness, not a property of the model.**（AI-native SDLC 里的质量，是 harness 的工程特性，不是模型的特性。）

同一个前沿模型，跑在「spec 契约 + 不可变测试 + 全新上下文评审 + 沙箱 + 端到端检查」里是生产级，光给它一句话就去生成就是垃圾级。**收益不来自换更聪明的模型，来自把 harness 建对。**

---

## 附录 A：Claude 专属 → 通用等价物映射表

这篇文章从始至终要证明「范式不绑定 Claude」。下表是「Claude 是第一个拼齐部件的人，但每件都有通用对应物」的证据——大多已是开放标准或全工具支持：

| Claude 专属 | 通用等价物 | 说明 / 佐证 |
|-------------|-----------|-------------|
| `CLAUDE.md` | **`AGENTS.md`**（开放标准） | Linux Foundation 旗下 Agentic AI Foundation 托管；Codex/Cursor/Cline/Windsurf/Gemini CLI/Claude Code/opencode/Zed 等全读。CLAUDE.md 是 Claude 层的扩展，可与 `@AGENTS.md` 引用复用 |
| Skills / `.claude/skills/` | **Agent Skills**（`.agents/skills/`、`agentskills.io` 标准） | 一套 `SKILL.md` 骨架 → 各大工具按统一规范发现；`AGENTS.md`=如何行为，`SKILL.md`=能做什么，`mcp.json`=能用什么工具 |
| Hooks（build 期护栏） | **pre/post 命令门 + CI gate** | 所有 agent CLI 都支持命令钩子；必须无条件成立的策略放阻断层 |
| Plan mode | **Plan-first / plan-driven**（各家 CLI 都有） | GitHub Spec Kit 的 Specify→Plan→Tasks→Implement 就是同一心法的跨厂实现 |
| Subagents / `.claude/agents/` | **子任务/agent teams**（各工具原生或经 MCP/编排） | 全新上下文对抗评审、验证器、代码简化器，都是通用概念 |
| `REVIEW.md` 评审策略 | **评审策略文件 + 分支保护** | 任何平台都能用「评审文件 + 分支保护」实现职责分离 |
| Claude Tag（值班） | **线上值班 agent / 聊天群 agent** | 通用「agent 加入 incident channel」模式，IBM ITBench 提醒它只能 assist |
| Claude Security | **周期性模型扫描** | 按计划跑、人类不进触发路径、发现走评审门——一刀不绑工具 |
| `claude -p` 非交互 | **headless agent CLI** | 所有 agent CLI 都有 `-p`/非交互模式接 CI |
| MCP 集成 | open standard（MCP） | 本就是跨厂商协议，不绑 Claude |

## 附录 B：判断什么时候该写 spec

GitHub Spec Kit 和 Anthropic 殊途同归的一个实用判断：**一句话能说清的改动跳过完整 spec；要跨多文件、有取舍、涉及架构的改动，一定先出 spec + plan，在新会话里执行。** 别让「写 spec」本身变成新的仪式病。规格是「可执行的真 source of truth」，不是文档负担——任务太大就拆，看不懂就回到 spec 说清楚。

## 附录 C：引用来源清单

**主引用**
- Anthropic / Claude — *The AI-native SDLC playbook*（2026）：https://claude.com/blog/the-ai-native-sdlc-playbook

**跨厂佐证 / 独立研究**
- *The AI-Native SDLC*（sdlc.xeb.ai，2026.07 独立综述，逐条溯源 + 三评论者对抗验证）：https://sdlc.xeb.ai/
- GitHub Blog — *Spec-driven development with AI: Get started with a new open source toolkit*（2025.09）：https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- GitHub — Spec Kit 仓库：https://github.com/github/spec-kit
- AGENTS.md open standard（Agentic AI Foundation / Linux Foundation）：https://agents.md/
- Anthropic — *Effective context engineering for AI agents*（2025.09）：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

**其中涉及的实证数据来源**
- METR（2025.07）：https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- DORA 2024/2025：https://dora.dev/research/2024/dora-report/ 和 https://dora.dev/dora-report-2025/
- GitClear（2025）：https://www.gitclear.com/ai_assistant_code_quality_2025_research
- Stanford / Denisov-Blanch：https://aiconference.com/wp-content/uploads/2025/09/Yegor-Denisov-Blanch-Will-AI-Replace-Software-Engineers_-.pptx.pdf
- GitHub Copilot RCT（2023）：https://arxiv.org/abs/2302.06590
- IBM ITBench（ICML 2025）：https://arxiv.org/abs/2502.05352
- Replit 事故（2025.07）：https://x.com/amasad/status/1946986468586721478
- Gartner 2026（经 xeb 综述转引）：https://www.gartner.com/en/newsroom/press-releases/2026-07-07-gartner-predicts-60-percent-of-organizations-will-adopt-smaller-software-engineering-teams-by-2029