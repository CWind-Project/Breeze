"""
License: BSD-3-Clause
Copyright (c) 2026 StarWindv, CWind-Project
"""


# noinspection unused-local
class WordVector[T](list):
    def __sub__(self, other) -> int:
        return len(self) - len(other)


class NonEnglishError(TypeError): pass


class FuzzinessCalculator:
    """
    一种另类的编辑距离算法实现,
    以键盘排布顺序为主来计算两个词被无意识 "按错字母" 的概率有多大
    """
    ordered_alphabet: dict[str, int] = {
        chr(i): i - 96 if i >= 97 else i - 64
        for i in list(range(97, 123)) + list(range(65, 91))
    }
    alphabet: dict[str, float] = {
        'q': 4,
        'w': 3,
        'e': 2,
        'r': 1,
        't': 1,
        'y': 2,
        'u': 3,
        'i': 1,
        'o': 2,
        'p': 3,

        'a': 3,
        's': 2,
        'd': 1,
        'f': 0,
        'g': 1,
        'h': 1,
        'j': 0,
        'k': 1,
        'l': 2,

        'z': 3,
        'x': 2,
        'c': 1,
        'v': 1,
        'b': 2,
        'n': 1,
        'm': 1
    }
    alphabet.update(
        {k.upper(): v for k, v in alphabet.copy().items()}
    )
    alphabet = {k: (v / 6) * 26 for k, v in alphabet.copy().items()}

    @classmethod
    def word_to_vector(cls, word: str) -> WordVector[int]:
        result: list[float] = []
        for ch in word:
            if ch not in cls.alphabet: raise NonEnglishError
            result.append(cls.alphabet[ch])
        return WordVector(result)

    @staticmethod
    def calc_similarity(
        vec1: WordVector[int],
        vec2: WordVector[int]
    ) -> float | int:
        result, quotient = 0.0, vec1 - vec2
        if quotient < 0: vec1, vec2 = vec2, vec1
        vec2, length = WordVector[int](vec2 + [0] * abs(quotient)), len(vec1)
        # if length < 5:
        #     import random
        #     random.seed(114514)
        #     tmp1, tmp2 = (
        #         [random.randint(1,   8) for _ in range(6-length)],
        #         [random.randint(20, 27) for _ in range(6-length)]
        #     )
        #     tmp1.extend(vec1); tmp2.extend(vec2)
        #     # length = len(tmp1)
        # else:
        #     tmp1, tmp2 = vec1, vec2
        tmp1, tmp2 = vec1, vec2
        for idx, (a, b) in enumerate(
            zip(
                tmp1,
                tmp2
            ), start=1
        ):
            result += abs(a - b)  # * idx / length
        return float(100 - result)  # return 1 / ( 1 + (result / 100) )

    @classmethod
    def quick_calc(cls, word1: str, word2: str) -> float:
        vec1 = cls.word_to_vector(word1)
        vec2 = cls.word_to_vector(word2)
        return cls.calc_similarity(vec1, vec2)

    @classmethod
    def char_to_bitmap(cls, ch: str) -> WordVector[int]:
        if len(ch) != 1: raise ValueError
        if ch not in cls.ordered_alphabet: raise NonEnglishError
        idx = cls.ordered_alphabet[ch]
        return WordVector[int](
            [0] * (idx - 1) + [1] + [0] * ( 26 - idx )
        )

    @classmethod
    def word_to_bitmap(cls, word: str) -> WordVector[int]:
        result: list[int] = [0] * 26
        for ch in word:
            if ch not in cls.ordered_alphabet: raise NonEnglishError
            idx = cls.ordered_alphabet[ch]
            result[idx-1] = 1
        return WordVector(result)
