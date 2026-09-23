"""加权、无限制(真) Damerau-Levenshtein 距离。

统一刻画五类编辑,并允许任意组合 / 重复 / 混合频次:

  多  -> 插入          insertion
  少  -> 删除          deletion
  错  -> 任意替换      substitution (full cost)
  偏  -> 邻键替换      substitution (near-key, soft cost)
  颠  -> 相邻换位      adjacent transposition

「真」DL(Lowrance–Wagner 形式)使用 da 表回溯字符上一次出现位置,
因此允许同一段字符被多次编辑 —— 这正是组合/重叠错误下正确率的关键,
优于受限版 OSA(后者对同一子串只允许一次编辑,组合场景会低估)。
"""

from __future__ import annotations

from dataclasses import dataclass

from .keyboard import ADJACENCY, are_neighbors


@dataclass(frozen=True)
class CostModel:
    ins: float = 1.0
    dele: float = 1.0
    sub: float = 1.0          # 错:任意替换
    sub_near: float = 0.5     # 偏:邻键替换(软错误,代价更低)
    trans: float = 1.0        # 颠:相邻换位

    def sub_cost(self, a: str, b: str) -> float:
        """a->b 的替换代价;相等为 0,邻键为软代价,否则为全代价。"""
        if a == b:
            return 0.0
        if are_neighbors(a, b):
            return self.sub_near
        return self.sub


def distance(a: str, b: str, cost: CostModel | None = None,
             cap: float = float("inf")) -> float:
    """加权真 Damerau-Levenshtein 距离(O(n*m))。

    cap:提前放弃阈值。若为求「是否 <= cap」或排序剪枝,一旦某整行最小值已 > cap,
    即返回 cap+1(表示 > cap)。真值 <= cap 时结果精确不变(已随机验证)。"""
    if cost is None:
        cost = CostModel()
    if a == b:
        return 0.0
    n, m = len(a), len(b)
    dele, ins, sub, subn, trans = cost.dele, cost.ins, cost.sub, cost.sub_near, cost.trans
    if n == 0:
        return m * ins
    if m == 0:
        return n * dele

    neigh = ADJACENCY
    maxd = (n + m) * max(ins, dele, sub, trans) + 1
    # 网格 (n+2) x (m+2);d[i+1][j+1] 对应 a[:i], b[:j]
    d = [[0.0] * (m + 2) for _ in range(n + 2)]
    d0 = d[0]
    d0[0] = maxd
    for i in range(n + 1):
        d[i + 1][0] = maxd
        d[i + 1][1] = i * dele
    for j in range(m + 1):
        d0[j + 1] = maxd
        d[1][j + 1] = j * ins

    da: dict[str, int] = {}
    da_get = da.get
    for i in range(1, n + 1):
        prev = d[i]
        cur = d[i + 1]
        db = 0
        ai = a[i - 1]
        na = neigh.get(ai)
        di1_row = d[0]  # i1 恒 >= 0,先给合法初值避免未定义
        li1 = -1
        row_min = float("inf")
        for j in range(1, m + 1):
            bj = b[j - 1]
            i1 = da_get(bj, 0)
            j1 = db
            if ai == bj:
                sc = 0.0
                db = j
            elif na is not None and bj in na:
                sc = subn
            else:
                sc = sub
            if i1 != li1:
                di1_row = d[i1]
                li1 = i1
            # 四路取最小
            v = prev[j] + sc
            t = cur[j] + dele
            if t < v:
                v = t
            t = prev[j + 1] + ins
            if t < v:
                v = t
            t = di1_row[j1] + (i - i1 - 1) * dele + trans + (j - j1 - 1) * ins
            if t < v:
                v = t
            cur[j + 1] = v
            if v < row_min:
                row_min = v
        if row_min > cap:
            return cap + 1.0
        da[ai] = i
    return d[n + 1][m + 1]


def counts_vec(s: str) -> dict[str, int]:
    """任意 Unicode 串的字符多重集(覆盖 ASCII 与汉字)。"""
    d: dict[str, int] = {}
    for c in s:
        d[c] = d.get(c, 0) + 1
    return d


def multiset_lower_bound(cv1: dict[str, int], cv2: dict[str, int], dl: int,
                         cost: CostModel) -> float:
    """加权编辑距离的、与顺序无关的下界,用于排序剪枝。

    l1 = 字符多重集差异之和 = Σ|c1-c2|;dl = 长度差。恒有 l1 >= dl 且同奇偶。
    - dl 的长度差只能靠增删解决:每处至少 min(ins,dele);
    - 其余 (l1-dl)/2 处失衡,最便宜用「邻键替换」一次修 2,单价 min(sub,sub_near)。
    故 lb = (l1-dl)//2 * min_sub + dl * min_indel。
    换位不改多重集(计 0 更保守),故下界恒 <= 真值。"""
    l1 = 0
    keys = cv1 if len(cv1) >= len(cv2) else cv2
    small = cv2 if keys is cv1 else cv1
    for k, v in keys.items():
        d = small.get(k)
        l1 += v if d is None else (v - d if v >= d else d - v)
    for k, v in small.items():
        if k not in keys:
            l1 += v
    min_sub = min(cost.sub, cost.sub_near)
    min_indel = min(cost.ins, cost.dele)
    return ((l1 - dl) // 2) * min_sub + dl * min_indel


def similarity(a: str, b: str, cost: CostModel | None = None) -> float:
    """把距离归一化到 [0, 1] 的相似度(1 = 完全相同)。"""
    if cost is None:
        cost = CostModel()
    la, lb = len(a), len(b)
    if la == 0 and lb == 0:
        return 1.0
    d = distance(a, b, cost)
    scale = max(cost.sub, cost.ins, cost.dele, cost.trans)
    return max(0.0, 1.0 - d / (max(la, lb) * scale))
