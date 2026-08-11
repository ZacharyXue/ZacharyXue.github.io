---
title: 石子游戏 II — 从一道题学会博弈型动态规划
date: 2026-08-11
tags: [算法, 动态规划, 博弈, LeetCode]
description: 从 LeetCode 1140「石子游戏 II」出发，拆解博弈型 DP 的识别技巧、核心公式与通用模板，覆盖官方题解分析与 Stone Game 系列举一反三。
---

## 题目

[**1140. 石子游戏 II**](https://leetcode.cn/problems/stone-game-ii/)（中等）

Alice 和 Bob 玩石子游戏。石子**排成一行**，每堆有正整数颗石子 `piles[i]`，游戏以谁手中的石子最多决出胜负。

- Alice 先手，初始 `M = 1`
- 每回合，当前玩家可以拿走剩下的**前** `X` 堆（`1 ≤ X ≤ 2M`）
- 然后令 `M = max(M, X)`
- 双方都采取**最优策略**，求 Alice 能得到的最大石子数

```
输入：piles = [2,7,9,4,4]
输出：10
解释：Alice 取 1 堆(2) → Bob 取 2 堆(7,9) → Alice 取 2 堆(4,4)，得 2+4+4=10
```

## 第一步：这题为什么是 DP？

拿到题目，最重要的不是直接写状态转移方程，而是**判断它属于哪类问题**。

### 识别路径：暴力 → 重叠子问题 → DP

先想暴力怎么做：

```
当前玩家在位置 i，M = m，枚举所有合法取法 X：
  → 取前 X 堆
  → 对手在位置 i+X 继续，M = max(m, X)
  → 我要最大化我的收益
```

关键问题：`dfs(3, 2)` 这个状态会被反复调用吗？**会**——从不同路径都能走到同一个状态。一旦暴力递归有大量重复计算，DP 就自然浮出来了。

> 实操技巧：给暴力递归加 `@lru_cache`，如果瞬间变快，就是重叠子问题多 → **这就是 DP**。

### DP 的四个信号

| 信号 | 含义 |
|---|---|
| 「最优/最大/最小」 | 要求最优解 |
| 「轮流」「都发挥最佳水平」 | 双方都最优 → 博弈 DP |
| 「排成一行」 | 天然的顺序结构，状态可以用位置 i |
| 决策只依赖当前位置和 M，不依赖历史 | **无后效性** — DP 的前提 |

这题四个信号全中。

## 第二步：记忆化搜索 = 自顶向下 DP

很多人觉得 DP 必须写 `for` 循环填表。其实**记忆化搜索本身就是 DP**——LeetCode 上完全能过。

路径是：

```
暴力递归 → 发现重复计算 → 加 @lru_cache → 完成
```

## 第三步：官方题解分析 —— 差值法

> [官方题解](https://leetcode.cn/problems/stone-game-ii/solution/shi-zi-you-xi-ii-by-leetcode-solution-3pwv/) 用的是**记忆化搜索**。

### 状态定义

`dfs(i, m)` = 当前玩家**比对方多拿**的石头数（score difference）

为什么用差值而不是总数？因为**零和博弈**中，「你多就是我少」——用差值天然简化转移：

```
diff = x − (sum − x) = 2x − sum
  ↓
x = (diff + sum) / 2
```

Alice 的总数就是 `(dfs(0, 1) + total_sum) / 2`。

### 转移方程

```
dfs(i, m) = max{ prefixSum[i+x] − prefixSum[i] − dfs(i+x, max(m, x)) }
             1 ≤ x ≤ 2m
```

三部分拆开看：

- `prefixSum[i+x] − prefixSum[i]`：**我这轮拿的**
- `dfs(i+x, max(m, x))`：**对手比我多拿的**
- **两数相减**：我这轮拿的减去对手的优势 = **我比对手多拿的**

### 官方 Python 代码

```python
class Solution:
    def stoneGameII(self, piles: List[int]) -> int:
        # 1. 前缀和
        prefixSum = [0]
        for a in piles:
            prefixSum.append(prefixSum[-1] + a)

        # 2. 记忆化搜索
        @lru_cache(None)
        def dfs(i, m):
            if i == len(piles):       # 边界：没石子了
                return 0
            mx = -inf
            for x in range(1, 2 * m + 1):   # 3. 枚举合法选择
                if i + x > len(piles):
                    break
                mx = max(mx, prefixSum[i + x] - prefixSum[i] - dfs(i + x, max(m, x)))
            return mx

        # 4. 差值 → 总数
        return (prefixSum[-1] + dfs(0, 1)) // 2
```

### 复杂度

- 时间：**O(n³)**，状态数 O(n²) × 每个状态枚举 O(n)，n ≤ 100 可过
- 空间：**O(n²)**，记忆化状态存储

## 第四步：两种状态定义对比

博弈 DP 有两种核心定义方式：

| 定义方式 | `dfs(i, m)` 含义 | 转移核心 | 最终答案 |
|---------|-----------------|---------|---------|
| **差值法** | 当前玩家**比对方多拿的** | `我拿的 − dfs(子问题)` | `(dfs + sum) / 2` |
| **总数法** | 当前玩家能拿的**总数** | `sumRest − min{dfs(子问题)}` | 直接返回 |

**推荐差值法**——天然契合零和博弈的「你多就是我少」，转移最简洁。

## 第五步：博弈 DP 通用模板

把上面的分析抽象成套路，遇到新题直接套：

```python
class Solution:
    def gameDP(self, piles: List[int]) -> int:
        n = len(piles)
        # ① 前缀和
        prefix = [0]
        for v in piles:
            prefix.append(prefix[-1] + v)

        # ② 记忆化搜索
        @lru_cache(None)
        def dfs(i, m):            # i: 当前位置, m: 当前参数
            if i == n:            # 边界：拿完了
                return 0

            best = -inf
            # ③ 枚举合法选择 → 递归 → 取最优
            for x in range(1, 2 * m + 1):
                if i + x > n:
                    break
                take = prefix[i + x] - prefix[i]    # 这轮拿的
                best = max(best, take - dfs(i + x, max(m, x)))
            return best

        # ④ 差值 → 总数
        return (prefix[-1] + dfs(0, 1)) // 2
```

### 固定三件套

1. **前缀和** — 快速求区间和
2. **记忆化搜索** — `dfs + @lru_cache`
3. **枚举合法选择** → 递归 → max

**口诀**：「我挑一个，让对手剩下的局面最烂」→ `我这轮拿的 − 对手最优`

## 第六步：举一反三 — Stone Game 系列

Stone Game 系列几乎都可以用同一套框架解决：

| 题目 | 核心变化 | 状态 | 难度 |
|------|---------|------|------|
| [Stone Game I](https://leetcode.cn/problems/stone-game/) | 只能从两端拿 | `dp[l][r]` 区间 DP | 中等 |
| **Stone Game II** | 拿前 X 堆，M 动态更新 | `dfs(i, m)` | **中等** |
| [Stone Game III](https://leetcode.cn/problems/stone-game-iii/) | 拿 1~3 堆 | `dfs(i)` 一维 | 困难 |
| [Stone Game IV](https://leetcode.cn/problems/stone-game-iv/) | 拿平方数个 | `dfs(n)` 布尔型 | 困难 |
| [Stone Game V](https://leetcode.cn/problems/stone-game-v/) | 拿两端，分裂石子 | `dp[l][r]` 区间 DP | 困难 |
| [Stone Game VI](https://leetcode.cn/problems/stone-game-vi/) | 两人各选一堆，贪心 | 排序 + 贪心 | 中等 |
| [Stone Game VII](https://leetcode.cn/problems/stone-game-vii/) | 拿两端，得分是剩余和 | `dp[l][r]` 区间 DP | 中等 |

共同点：**差值法 + 记忆化搜索** 全部可套。

---

## 总结

```
博弈 DP = 前缀和 + 记忆化搜索 +「我这轮拿的 − 对手最优」
```

拿到一道新题时，走这个 checklist：

1. 是不是博弈？（双方轮流 + 最优策略）
2. 是不是零和？（你多就是我少，总和固定）→ 差值法
3. 状态参数有哪些？（位置 i + 限制参数 M）
4. 边界是什么？（拿完了 / 能一次全拿走）
5. 转移：枚举所有合法选择 → 递归 → max
6. 套前缀和 + `@lru_cache`

> 不要试图「一眼看出是 DP」——**先想暴力，发现重叠，加缓存，这就是 DP。**

---

*本文基于力扣第 1140 题「石子游戏 II」及[官方题解](https://leetcode.cn/problems/stone-game-ii/solution/shi-zi-you-xi-ii-by-leetcode-solution-3pwv/)整理。*
