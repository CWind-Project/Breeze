"""合成测试种子:从字母表 / chr 任意拼词,构造「正确集」再变异得到大量样本。

要点:
- rand_word:按随机长度、随机数量从指定字母表拼装;
- make_vocab:生成彼此「充分分离」的词汇集 —— 保证任意两词的加权编辑距离
  >= min_gap,这样「变异查询」才存在唯一且正确的 top-1,准确率度量才有意义;
  (否则失败其实来自词库自身歧义,而非算法缺陷)
- ASCII 覆盖五类(含邻键「偏」);CJK(汉字)覆盖 多/少/错/颠(键盘邻键对汉字
  不适用,are_neighbors 返回 False,替换按「错」计价,逻辑天然退化正确)。
"""

from __future__ import annotations

import random

from .distance import CostModel, counts_vec, distance, multiset_lower_bound

ASCII = "abcdefghijklmnopqrstuvwxyz"
# 常用汉字区间(示例取一段连续码位;随机拼字即可覆盖大量组合)
CJK = "".join(chr(c) for c in range(0x4E00, 0x4E00 + 3000))


def rand_word(rng: random.Random, lo: int, hi: int,
              alphabet: str = ASCII) -> str:
    n = rng.randint(lo, hi)
    return "".join(rng.choice(alphabet) for _ in range(n))


def make_vocab(rng: random.Random, size: int, lo: int, hi: int,
               alphabet: str = ASCII, min_gap: int = 4,
               cost: CostModel | None = None, max_try: int = 20000) -> list[str]:
    """随机生成 size 个两两加权距离 >= min_gap 的词,作为互不歧义的「正确集」。

    先用与顺序无关的多重集下界 O(|Σ|) 排除明显过近者,仅当下界可能 < min_gap
    时才付 O(n·m) 精算,大词库构建因此可行。
    """
    if cost is None:
        cost = CostModel()
    vocab: list[str] = []
    meta: list[tuple[int, dict]] = []
    tries = 0
    while len(vocab) < size and tries < max_try:
        tries += 1
        w = rand_word(rng, lo, hi, alphabet)
        wl, wc = len(w), counts_vec(w)
        ok = True
        for idx, (vl, vc) in enumerate(meta):
            if multiset_lower_bound(vc, wc, abs(vl - wl), cost) < min_gap:
                if distance(w, vocab[idx], cost) < min_gap:
                    ok = False
                    break
        if not ok:
            continue
        vocab.append(w)
        meta.append((wl, wc))
    return vocab


def ascii_vocab(rng: random.Random, size: int = 60, lo: int = 7, hi: int = 12,
                min_gap: int = 4, cost: CostModel | None = None) -> list[str]:
    return make_vocab(rng, size, lo, hi, ASCII, min_gap, cost)


def cjk_vocab(rng: random.Random, size: int = 60, lo: int = 4, hi: int = 7,
              min_gap: int = 4, cost: CostModel | None = None) -> list[str]:
    return make_vocab(rng, size, lo, hi, CJK, min_gap, cost)
