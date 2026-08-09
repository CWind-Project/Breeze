"""
License: BSD-3-Clause
Copyright (c) 2026 StarWindv, CWind-Project
"""


# noinspection unused-local
class BreezeWordVector[T](list):
    def __sub__(self, other) -> int:
        return len(self) - len(other)


class BreezeNonEnglishError(TypeError): pass


class BreezeFuzzinessCalculator:
    ordered_alphabet: dict[str, int] = { # impl for v0.1.0
        chr(i): i - 96 if i >= 97 else i - 64
        for i in list(range(97, 123)) + list(range(65, 91))
    }
    alphabet: dict[str, float] = {
        '-': 1, '_': 0, '=': 1, '+': 0, ' ': 0,
        'q': 4, 'w': 3, 'e': 2, 'r': 1, 't': 1, 'y': 2, 'u': 3, 'i': 1, 'o': 2, 'p': 3,
        'a': 3, 's': 2, 'd': 1, 'f': 0, 'g': 1, 'h': 1, 'j': 0, 'k': 1, 'l': 2,
        'z': 3, 'x': 2, 'c': 1, 'v': 1, 'b': 2, 'n': 1, 'm': 1
    }
    alphabet.update(
        {k.upper(): v for k, v in alphabet.copy().items()}
    )
    alphabet = {k: (v / 6) * 26 for k, v in alphabet.copy().items()}

    @classmethod
    def word_to_vector(cls, word: str) -> BreezeWordVector[int]:
        result: list[float] = []
        for ch in word:
            if ch not in cls.alphabet: raise BreezeNonEnglishError
            result.append(cls.alphabet[ch])
        return BreezeWordVector(result)

    @staticmethod
    def calc_similarity(
        vec1: BreezeWordVector[int],
        vec2: BreezeWordVector[int]
    ) -> float | int:
        result, quotient = 0.0, vec1 - vec2
        if quotient < 0: vec1, vec2 = vec2, vec1
        vec2, length = BreezeWordVector[int](vec2 + [0] * abs(quotient)), len(vec1)
        tmp1, tmp2 = vec1, vec2
        for idx, (a, b) in enumerate(
            zip(
                tmp1,
                tmp2
            ), start=1
        ):
            result += abs(a - b)  # * idx / length # impl for v0.1.0 ~ v0.2.0
        return float(100 - result)
