"""把「right(原词)-> wrong(串)」对齐,并把每一步编辑归类到五类:
多 / 少 / 错 / 偏 / 颠。

基于带相邻换位的加权 OSA(DP + 回溯)。回溯需要完整矩阵,故单独实现;
距离口径与 distance.distance(真 DL)在常见编辑组合下一致,
但真 DL 允许子串被多次编辑,作为「打分/匹配」的最终口径更稳健,
而 OSA 更适合「诊断/还原」具体错在哪。
"""

from __future__ import annotations

from dataclasses import dataclass

from .distance import CostModel
from .keyboard import are_neighbors

# 五类错误名
EXTRA = "多"      # 插入:串里多了字符
MISSING = "少"    # 删除:串里少了字符
WRONG = "错"      # 任意替换
NEAR = "偏"       # 邻键替换
SWAP = "颠"       # 相邻换位


@dataclass(frozen=True)
class Edit:
    kind: str
    a_pos: int
    b_pos: int
    a_char: str
    b_char: str

    def __repr__(self) -> str:  # pragma: no cover - 便于阅读
        return f"<{self.kind} a[{self.a_pos}]={self.a_char!r} b[{self.b_pos}]={self.b_char!r}>"


def osa_distance(a: str, b: str, cost: CostModel | None = None) -> float:
    if cost is None:
        cost = CostModel()
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i * cost.dele
    for j in range(m + 1):
        dp[0][j] = j * cost.ins
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            bj = b[j - 1]
            best = min(
                dp[i - 1][j - 1] + cost.sub_cost(ai, bj),
                dp[i - 1][j] + cost.dele,
                dp[i][j - 1] + cost.ins,
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, dp[i - 2][j - 2] + cost.trans)
            dp[i][j] = best
    return dp[n][m]


def align(a: str, b: str, cost: CostModel | None = None,
          include_matches: bool = False) -> list[Edit]:
    """返回把 a 变成 b 的编辑序列(含每步类型与位置)。

    include_matches=True 时保留 '='(一致字符)步,便于逐字重放校验。"""
    if cost is None:
        cost = CostModel()
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i * cost.dele
    for j in range(m + 1):
        dp[0][j] = j * cost.ins
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            bj = b[j - 1]
            dp[i][j] = min(
                dp[i - 1][j - 1] + cost.sub_cost(ai, bj),
                dp[i - 1][j] + cost.dele,
                dp[i][j - 1] + cost.ins,
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + cost.trans)

    edits: list[Edit] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            edits.append(Edit("=", i - 1, j - 1, a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
            continue
        # 换位优先:相邻两字符恰好互为倒置
        if (
            i > 1 and j > 1
            and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]
            and abs(dp[i][j] - (dp[i - 2][j - 2] + cost.trans)) < 1e-9
        ):
            edits.append(Edit(SWAP, i - 2, j - 2, a[i - 2] + a[i - 1], b[j - 2] + b[j - 1]))
            i, j = i - 2, j - 2
            continue
        # 对角(错 / 偏)
        if i > 0 and j > 0:
            sc = cost.sub_cost(a[i - 1], b[j - 1])
            if abs(dp[i][j] - (dp[i - 1][j - 1] + sc)) < 1e-9 and a[i - 1] != b[j - 1]:
                kind = NEAR if are_neighbors(a[i - 1], b[j - 1]) else WRONG
                edits.append(Edit(kind, i - 1, j - 1, a[i - 1], b[j - 1]))
                i, j = i - 1, j - 1
                continue
        # 删除(a 有 b 无) => 少
        if i > 0 and abs(dp[i][j] - (dp[i - 1][j] + cost.dele)) < 1e-9:
            edits.append(Edit(MISSING, i - 1, j, a[i - 1], ""))
            i -= 1
            continue
        # 插入(b 有 a 无) => 多
        if j > 0 and abs(dp[i][j] - (dp[i][j - 1] + cost.ins)) < 1e-9:
            edits.append(Edit(EXTRA, i, j - 1, "", b[j - 1]))
            j -= 1
            continue
        raise RuntimeError("align backtrack failed")  # pragma: no cover
    edits.reverse()
    if include_matches:
        return edits
    return [e for e in edits if e.kind != "="]


def apply_edits(a: str, edits: list[Edit]) -> str:
    """把包含 '=' 的编辑序列逐字重放回 a,应精确还原出 b(校验对齐定位)。"""
    out: list[str] = []
    for e in edits:
        if e.kind == "=":
            out.append(e.a_char)
        elif e.kind in (EXTRA, WRONG, NEAR):
            out.append(e.b_char)
        elif e.kind == SWAP:
            out.append(e.b_char)   # 已交换后的双字符
        elif e.kind == MISSING:
            pass                    # 删除:不输出
    return "".join(out)


def classify(a: str, b: str, cost: CostModel | None = None) -> dict[str, int]:
    """统计 a->b 各类错误的次数(不含一致的 '=' 步)。"""
    counts = {EXTRA: 0, MISSING: 0, WRONG: 0, NEAR: 0, SWAP: 0}
    for e in align(a, b, cost):
        counts[e.kind] += 1
    return counts
