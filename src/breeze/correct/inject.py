"""把五类错误按指定次数注入原词,生成「串」。

- 单次遍历:先选位置、生成操作,再按起始位置从右到左一次性应用,位置不漂移;
- 各操作覆盖的字符区间互不相交 => 注入步都是「最小代价」编辑,便于:
    * 与 aligner 诊断比对(尤其单类/轻量组合);
    * 断言 distance(word, 串) <= 注入加权代价(算法不劣于已知脚本)。
  注意:组合下真 DL 可能找到更廉价的重叠解释,故 distance 作为上界而非恒等。
- letters 决定「错/多」取材字母表:ASCII 覆盖全五类;传入汉字集则邻键自动跳过。
"""

from __future__ import annotations

import random

from .align import EXTRA, MISSING, NEAR, SWAP, WRONG
from .distance import CostModel
from .keyboard import neighbors

_TYPES = (EXTRA, MISSING, WRONG, NEAR, SWAP)
_ASCII = "abcdefghijklmnopqrstuvwxyz"


def random_errors(rng: random.Random, max_each: int = 2, min_len: int = 5) -> dict[str, int]:
    """随机给每类错误 0..max_each 次(至少 1 次)。"""
    while True:
        spec = {t: rng.randint(0, max_each) for t in _TYPES}
        if sum(spec.values()) >= 1 and (min_len + sum(spec.values()) >= 5):
            return spec


def budget_errors(rng: random.Random, budget: int) -> dict[str, int]:
    """在总编辑数 budget 内,按随机偏置分配到五类(体现频次不同 / 可重复)。"""
    spec = {t: 0 for t in _TYPES}
    weights = [rng.randint(1, 3) for _ in _TYPES]
    total = rng.randint(1, budget)
    for _ in range(total):
        t = rng.choices(_TYPES, weights=weights, k=1)[0]
        spec[t] += 1
    return spec


def inject(word: str, spec: dict[str, int], rng: random.Random,
           cost: CostModel | None = None,
           letters: str = _ASCII) -> tuple[str, dict[str, int]]:
    """返回 (注入错误后的串, 实际注入次数字典)。"""
    if cost is None:
        cost = CostModel()
    ops: list[tuple[int, int, list[str]]] = []  # (start, width, [kind, a, b])
    used: set[int] = set()
    actual = {t: 0 for t in _TYPES}

    def claim(idx: list[int]) -> bool:
        return all(x not in used for x in idx)

    def take(idx: list[int]) -> None:
        used.update(idx)

    n = len(word)

    for _ in range(spec.get(SWAP, 0)):  # 颠
        cand = [p for p in range(n - 1) if word[p] != word[p + 1] and claim([p, p + 1])]
        if not cand:
            break
        p = rng.choice(cand)
        take([p, p + 1])
        ops.append((p, 2, [SWAP, word[p] + word[p + 1], word[p + 1] + word[p]]))
        actual[SWAP] += 1

    for _ in range(spec.get(NEAR, 0)):  # 偏
        cand = [p for p in range(n) if neighbors(word[p]) and claim([p])]
        if not cand:
            break
        p = rng.choice(cand)
        take([p])
        c = rng.choice(sorted(neighbors(word[p])))
        ops.append((p, 1, [NEAR, word[p], c]))
        actual[NEAR] += 1

    for _ in range(spec.get(WRONG, 0)):  # 错
        cand = [p for p in range(n) if claim([p])]
        if not cand:
            break
        p = rng.choice(cand)
        take([p])
        ok = [c for c in letters if c != word[p] and c not in neighbors(word[p])]
        c = rng.choice(ok)
        ops.append((p, 1, [WRONG, word[p], c]))
        actual[WRONG] += 1

    for _ in range(spec.get(MISSING, 0)):  # 少
        cand = [p for p in range(n) if claim([p])]
        if not cand:
            break
        p = rng.choice(cand)
        take([p])
        ops.append((p, 1, [MISSING, word[p], ""]))
        actual[MISSING] += 1

    ins_taken: set[int] = set()

    def ins_claim(p: int) -> bool:
        return p not in ins_taken and claim([p - 1]) and (p == n or claim([p]))

    for _ in range(spec.get(EXTRA, 0)):  # 多
        cand = [p for p in range(n + 1) if ins_claim(p)]
        if not cand:
            break
        p = rng.choice(cand)
        ins_taken.add(p)
        used.update({p - 1, p})
        c = rng.choice(letters)
        ops.append((p, 0, [EXTRA, "", c]))
        actual[EXTRA] += 1

    s = list(word)
    for start, width, (_kind, _a, b) in sorted(ops, key=lambda o: -o[0]):
        if width == 0:
            s.insert(start, b)
        else:
            s[start:start + width] = list(b)
    return "".join(s), actual
