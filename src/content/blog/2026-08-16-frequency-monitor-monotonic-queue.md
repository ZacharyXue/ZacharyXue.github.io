---
title: 滑动窗口最大值 —— 单调队列入门与避坑
date: 2026-08-16
tags: [算法, 数据结构, 队列, Python]
description: 从一道有界序列工具题出发，拆解单调队列（Monotonic Queue）的 3 个经典 bug，附正确实现与单调栈全家桶进阶路线。
---

## 问题

实现一个有界序列处理工具 `FrequencyMonitor`，维护最近 `window_size` 个值：

```python
class FrequencyMonitor:
    def __init__(self, window_size=5):
        ...
    def add(self, value: float) -> None:   # 加入新值，只保留最近 window_size 个
    def average(self) -> float:            # 最近窗口平均值，无数据返回 0
    def max(self) -> float:                # 最近窗口最大值
```

本质是 **「滑动窗口 + 实时最大值/平均值」**，经典解法是**单调队列（Monotonic Queue）**：

- **普通队列 `queue`**：存窗口内所有值 → 维护 `sum` 算平均值
- **单调递减队列 `mono`**：队首永远是窗口最大值 → O(1) 取 max

## 错误实现与 3 个 bug

平均值部分好写，难点全在单调队列上。一个典型的错误实现（也是我最初踩坑的版本）：

```python
def add(self, value: float) -> None:
    self.size += 1
    self.sum += value
    self.queue.append(value)

    if self.max_list and self.max_list[-1] <= value:
        while self.max_list and self.max_list[-1] < value:
            self.max_list.pop()
        self.max_list.append(value)
    elif not self.max_list:
        self.max_list.append(value)

    if self.size > self.window_size:
        self.sum -= self.queue[0]
        if self.max_list[-1] == self.queue[0]:
            self.max_list.pop()
        self.queue.popleft()
        self.size -= 1
```

用序列 `10, 2, 5, 3, 4, 5, 4, 6`（window=5）跑出来的结果：窗口 `[2,5,3,4,5]` 时 `max_list` 竟然是空的。

### Bug 1（致命）：新值比队尾小时根本没入队

```python
if self.max_list and self.max_list[-1] <= value:
    ...
elif not self.max_list:
    ...
```

当 `max_list[-1] > value` 时两个分支都不进，**value 直接丢了**。推演：

| 操作 | max_list（错误） | 应该是什么 |
|------|-----------------|-----------|
| add(10) | [10] | [10] |
| add(2) | 还是 [10]（2 丢了） | [10, 2] |
| add(5) | 还是 [10]（5 丢了） | [10, 5] |
| add(5) 触发弹 10 | **pop 后 = []（空了）** | [5, 5] |

**正确做法**：新值**无条件入队**，只是入队前先弹掉所有比它小的队尾。小值现在不是最大值，但它排在队尾，等大值过期后要"接班"——丢了它，队列就断了。

```python
while self.mono and self.mono[-1] < value:
    self.mono.pop()
self.mono.append(value)   # ← 无条件 append！
```

### Bug 2：头和尾搞反了

单调递减队列（队首最大）：

- 取 max → 应该用 **`mono[0]`**（队首），错误版用了 `[-1]`（队尾）
- 元素过期 → 应该判断 **`mono[0] == queue[0]`** 然后 `popleft()`，错误版用了 `[-1]` + `pop()`

即使 Bug 1 修好，`max()` 返回的也是窗口**最小**值。

### Bug 3：空窗口处理

- `average()`：size=0 时 `sum/0` 崩溃，题目明确要求**返回 0**
- `max()`：空队列取 `[-1]` 直接 IndexError

## 正确实现

```python
import collections

class FrequencyMonitor:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.queue = collections.deque()   # 窗口内所有值
        self.mono = collections.deque()    # 单调递减队列，队首 = 当前最大值
        self.sum = 0

    def add(self, value: float) -> None:
        self.queue.append(value)
        self.sum += value
        while self.mono and self.mono[-1] < value:  # 弹掉小的
            self.mono.pop()
        self.mono.append(value)                     # 无条件入队
        if len(self.queue) > self.window_size:      # 窗口超限
            old = self.queue.popleft()
            self.sum -= old
            if self.mono[0] == old:                 # 过期的是最大值
                self.mono.popleft()

    def average(self) -> float:
        return self.sum / len(self.queue) if self.queue else 0

    def max(self) -> float:
        return self.mono[0] if self.mono else 0
```

## 为什么入队用 `<` 而不是 `<=`

**核心是"值相等时，过期判断会产生歧义"**。

用 `<`（保留相等值）：
```
窗口 [5, 5]，mono = [5, 5]（两个 5 都在）
第一个 5 过期 → mono[0] == 5 == old → popleft → mono = [5] ✓
```

用 `<=`（弹掉相等值）：
```
add(5): mono = [5]
add(5): 5 <= 5 → 弹掉旧的 → mono = [5]（只剩"第二个 5"）
第一个 5 过期 → mono[0] == 5 == old → 误判！→ popleft → mono = [] ✗
```

窗口还剩一个 5，max 应该是 5，队列却空了。一旦弹掉相等的旧值，`mono[0] == old` 就无法区分"该弹"和"不该弹"——**`<=` 破坏了"值 → 元素"的一一对应**。

最稳的写法是**存下标**（`mono` 里存 index，下标唯一），过期判断变成 `mono[0] < i - window + 1`，完全绕开相等歧义。LeetCode 239 的标准题解都用下标版。

## 复杂度

每个元素**入队恰好 1 次**，出队至多 1 次（要么被单调性弹掉，要么窗口过期弹出）。n 个元素总共 O(n) 操作，**均摊到每次 add 是 O(1)**。空间 O(window_size)。

## 举一反三：单调栈/单调队列全家桶

同一个思想——**用单调性淘汰"永远不可能成为答案"的候选**：

| 题目 | 数据结构 | 淘汰规则 |
|------|---------|---------|
| [239. 滑动窗口最大值](https://leetcode.cn/problems/sliding-window-maximum/) | 单调递减队列（存下标） | 比你小且比你老的，淘汰 |
| [496. 下一个更大元素 I](https://leetcode.cn/problems/next-greater-element-i/) | 单调递减栈 | 遇到更大的，弹出结算 |
| [739. 每日温度](https://leetcode.cn/problems/daily-temperatures/) | 单调递减栈（存下标） | 同 496，算距离 |
| [84. 柱状图中最大的矩形](https://leetcode.cn/problems/largest-rectangle-in-histogram/) | 单调递增栈 + 哨兵 | 弹栈时结算区间面积 |
| [85. 最大矩形](https://leetcode.cn/problems/maximal-rectangle/) | 84 的二维版 | 逐行压扁成柱状图 |
| [862. 和至少为 K 的最短子数组](https://leetcode.cn/problems/shortest-subarray-with-sum-at-least-k/) | 前缀和 + 单调递增队列 | 前缀和上的淘汰规则要重推 |

### 进阶路线（待完成 ✅ 标记为后续练习）

```
入门 ──→ 239 ──→ 739 ──→ 84 ──→ 85 / 862
存值     存下标    算距离   区间结算  前缀和+队列
```

**每次升级只加一个新概念**：239 加"下标"，739 加"距离"，84 加"区间结算"，862 加"前缀和"。

#### 练习 1：LeetCode 239 滑动窗口最大值（存下标版）

```python
# 输入 nums=[1,3,-1,-3,5,3,6,7], k=3
# 输出 [3,3,5,5,6,7]
```

要求：`mono` 里存**下标**，队首下标小于 `i-k+1` 就 popleft。注意入队/过期的先后顺序。

#### 练习 2：LeetCode 84 柱状图中最大的矩形

```python
# 输入 heights=[2,1,5,6,2,3]
# 输出 10  ← 5*2 的矩形
```

要点：弹栈时结算"以该柱为高"的矩形，宽度 = `i - stack[-1] - 1`；栈弹空时宽度 = `i`；前后补 0 哨兵。

#### 练习 3：LeetCode 862 和至少为 K 的最短子数组

```python
# 输入 nums=[2,-1,2], k=3
# 输出 2  ← 子数组 [2,1]（下标 1 到 2）
```

要点：在 prefix 数组上维护**递增**队列——新前缀更小则弹掉队尾（又大又老的永远不是最优）；`prefix[j] - prefix[队首] >= k` 时结算并弹出队首。

## 一句话总结

单调队列的精髓：**哪些文件必须审由程序决定，哪些候选可以淘汰由单调性决定**——把"谁最大/谁最小/谁可能是答案"这种开放问题，变成确定性的淘汰规则，让 LLM（这里是模型）只做真正需要推理的部分。
