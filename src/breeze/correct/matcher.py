"""候选匹配器:在词库里为「串」找最可能的原词,并给出自适应阈值判定。"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .align import classify
from .distance import (CostModel, counts_vec, distance, multiset_lower_bound,
                        similarity)


@dataclass(frozen=True)
class Candidate:
    word: str
    distance: float
    similarity: float


class Matcher:
    def __init__(self, vocabulary: list[str], cost: CostModel | None = None):
        self.cost = cost or CostModel()
        self.vocab = sorted(set(vocabulary))
        # 预存长度与字符多重集,用于排序剪枝
        self._meta = [(w, len(w), counts_vec(w)) for w in self.vocab]

    def distance(self, right: str, wrong: str) -> float:
        return distance(right, wrong, self.cost)

    def distance_capped(self, right: str, wrong: str, cap: float) -> float:
        return distance(right, wrong, self.cost, cap)

    def is_match(self, right: str, wrong: str, ratio: float = 0.34) -> bool:
        """自适应阈值:允许绝对距离随长度线性增长,并为短串设下限。"""
        d = self.distance(right, wrong)
        n = max(len(right), len(wrong))
        return d <= max(2.0, math.ceil(n * ratio))

    def rank(self, wrong: str, topk: int = 5) -> list[Candidate]:
        """返回与 wrong 最接近的前 topk 候选(距离升序)。

        两级剪枝:
          1. 多重集下界 O(|Σ|) —— 明显远的直接跳过;
          2. 提前放弃 DP —— 以当前第 topk 名为 cap,候选真实距离若 > cap,
             几行内即返回 cap+1,省下大量 O(n·m) 常量。
        结果与「全部精算」严格一致(剪枝只剔除不可能进入前 topk 者)。
        """
        wv = counts_vec(wrong)
        lw = len(wrong)
        out: list[Candidate] = []
        worst = math.inf
        for w, ln, cv in self._meta:
            if multiset_lower_bound(cv, wv, abs(ln - lw), self.cost) > worst:
                continue
            d = distance(w, wrong, self.cost, worst)
            if d > worst:
                continue
            out.append(Candidate(w, d, similarity(w, wrong, self.cost)))
            if len(out) > topk:
                out.sort(key=lambda c: (c.distance, -len(c.word), c.word))
                out.pop()
                worst = out[-1].distance
        out.sort(key=lambda c: (c.distance, -len(c.word), c.word))
        return out[:topk]

    def best(self, wrong: str) -> Candidate | None:
        r = self.rank(wrong, topk=1)
        return r[0] if r else None

    def diagnose(self, right: str, wrong: str) -> dict[str, int]:
        """还原 right->wrong 的五类错误次数(多/少/错/偏/颠)。"""
        return classify(right, wrong, self.cost)
