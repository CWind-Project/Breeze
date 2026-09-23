"""
License: BSD-3-Clause
Copyright (c) 2026 StarWindv, CWind-Project
"""

from dataclasses import dataclass

from ..correct import similarity


@dataclass(frozen=True)
class BreezeWordVector:
    word: str


class BreezeNonEnglishError(TypeError):
    pass


class BreezeFuzzinessCalculator:
    @classmethod
    def word_to_vector(cls, word: str) -> BreezeWordVector:
        return BreezeWordVector(word)

    @staticmethod
    def calc_similarity(
            vec1: BreezeWordVector,
            vec2: BreezeWordVector,
    ) -> float:
        return similarity(vec1.word, vec2.word) * 100.0

    @classmethod
    def quick_calc(cls, word1: str, word2: str) -> float:
        return similarity(word1, word2) * 100.0
