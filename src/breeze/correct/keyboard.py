"""QWERTY 键盘物理邻接模型:用于刻画「偏」(打错到相邻键) 这类软错误。"""

from __future__ import annotations

ROWS = (
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
)

_ROW_Y = (0.0, 1.0, 2.0)
_ROW_X0 = (0.0, 0.5, 1.5)


def _coords() -> dict[str, tuple[float, float]]:
    pos: dict[str, tuple[float, float]] = {}
    for r, row in enumerate(ROWS):
        for c, key in enumerate(row):
            pos[key] = (_ROW_X0[r] + c, _ROW_Y[r])
    return pos


COORDS = _coords()

ADJACENCY: dict[str, frozenset[str]] = {}


def _build_adjacency(threshold: float = 1.25) -> None:
    keys = list(COORDS)
    for a in keys:
        ax, ay = COORDS[a]
        neigh = set()
        for b in keys:
            if a == b:
                continue
            bx, by = COORDS[b]
            if ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5 <= threshold:
                neigh.add(b)
        ADJACENCY[a] = frozenset(neigh)


_build_adjacency()


def are_neighbors(a: str, b: str) -> bool:
    """两个字符在键盘上是否相邻(互为「偏」候选)。"""
    return b in ADJACENCY.get(a, frozenset())


def neighbors(a: str) -> frozenset[str]:
    return ADJACENCY.get(a, frozenset())
