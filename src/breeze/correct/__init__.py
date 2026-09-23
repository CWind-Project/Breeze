"""correct —— 针对「多/少/错/偏/颠」组合错误的加权模糊匹配算法。

导出:
  distance     加权真 Damerau-Levenshtein 距离(组合/重叠错误下最稳健)
  similarity   距离归一化到 [0,1]
  align        回溯出每步编辑并归类到五类
  Matcher      词库候选排序 / 自适应阈值判定
  inject       按次数注入五类错误生成测试串
"""

from .align import (EXTRA, MISSING, NEAR, SWAP, WRONG, Edit, align, apply_edits,
                    classify, osa_distance)
from .corpus import vocabulary
from .distance import CostModel, counts_vec, distance, multiset_lower_bound, similarity
from .inject import budget_errors, inject, random_errors
from .keyboard import are_neighbors, neighbors
from .matcher import Candidate, Matcher
from .synth import ASCII, CJK, ascii_vocab, cjk_vocab, make_vocab, rand_word

__all__ = [
    "EXTRA", "MISSING", "NEAR", "SWAP", "WRONG",
    "Edit", "align", "apply_edits", "classify", "osa_distance",
    "vocabulary",
    "CostModel", "distance", "similarity", "counts_vec", "multiset_lower_bound",
    "inject", "random_errors", "budget_errors",
    "are_neighbors", "neighbors",
    "Candidate", "Matcher",
    "ASCII", "CJK", "rand_word", "make_vocab", "ascii_vocab", "cjk_vocab",
]
