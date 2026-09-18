"""Procedural monochrome nonograms with derived clues."""

from __future__ import annotations

from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase


def _runs(line: list[int]) -> list[int]:
    out: list[int] = []
    run = 0
    for v in line:
        if v:
            run += 1
        elif run:
            out.append(run)
            run = 0
    if run:
        out.append(run)
    return out or []


def clues_for(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    rows = [_runs(row) for row in grid]
    cols = [_runs([grid[r][c] for r in range(len(grid))]) for c in range(len(grid[0]))]
    return rows, cols


def verify_clues(grid: list[list[int]], row_clues: list[list[int]], col_clues: list[list[int]]) -> None:
    r, c = clues_for(grid)
    if r != row_clues or c != col_clues:
        raise ValueError("Nonogram clues do not match image")


def _symbol_heart(n: int) -> list[list[int]]:
    g = [[0] * n for _ in range(n)]
    # Simple procedural heart-ish blob scaled to n
    for r in range(n):
        for c in range(n):
            x = (c + 0.5) / n * 2 - 1
            y = 1 - (r + 0.5) / n * 2
            # classic heart implicit curve
            a = x * x + y * y - 1
            if a * a * a - x * x * y * y * y <= 0.02:
                g[r][c] = 1
    return g


def _symbol_smiley(n: int) -> list[list[int]]:
    g = [[0] * n for _ in range(n)]
    cx = cy = (n - 1) / 2
    rad = n * 0.42
    for r in range(n):
        for c in range(n):
            d = ((r - cy) ** 2 + (c - cx) ** 2) ** 0.5
            if abs(d - rad) < 0.7 or d < rad * 0.15:
                g[r][c] = 1
            # eyes
            if abs(r - n * 0.35) < 0.6 and abs(c - n * 0.35) < 0.6:
                g[r][c] = 1
            if abs(r - n * 0.35) < 0.6 and abs(c - n * 0.65) < 0.6:
                g[r][c] = 1
            # smile arc
            if n * 0.55 <= r <= n * 0.72 and abs(c - cx) < rad * 0.45:
                if abs(((r - cy) ** 2 + (c - cx) ** 2) ** 0.5 - rad * 0.55) < 0.7:
                    g[r][c] = 1
    return g


def _symbol_tree(n: int) -> list[list[int]]:
    g = [[0] * n for _ in range(n)]
    mid = n // 2
    # crown triangles
    for level, top in enumerate((0.15, 0.35, 0.55)):
        width = int(n * (0.25 + level * 0.12))
        rr = int(n * top)
        for r in range(rr, min(n - 2, rr + max(2, n // 6))):
            span = width - (r - rr)
            for c in range(mid - span, mid + span + 1):
                if 0 <= c < n:
                    g[r][c] = 1
    # trunk
    for r in range(int(n * 0.7), n):
        for c in range(mid - max(1, n // 12), mid + max(1, n // 12) + 1):
            g[r][c] = 1
    return g


def _symbol_house(n: int) -> list[list[int]]:
    g = [[0] * n for _ in range(n)]
    mid = n // 2
    # roof
    for r in range(int(n * 0.15), int(n * 0.45)):
        span = r - int(n * 0.15) + 1
        for c in range(mid - span, mid + span + 1):
            if 0 <= c < n:
                g[r][c] = 1
    # body
    left, right = int(n * 0.25), int(n * 0.75)
    for r in range(int(n * 0.45), int(n * 0.9)):
        for c in range(left, right + 1):
            g[r][c] = 1
    # door hollow
    for r in range(int(n * 0.65), int(n * 0.9)):
        for c in range(mid - max(1, n // 10), mid + max(1, n // 10) + 1):
            g[r][c] = 0
    return g


SYMBOLS = {
    "heart": _symbol_heart,
    "smiley": _symbol_smiley,
    "tree": _symbol_tree,
    "house": _symbol_house,
}


def size_for(difficulty: Difficulty, params: dict[str, Any]) -> int:
    if params.get("size") in (5, 10, 15):
        return int(params["size"])
    return {Difficulty.easy: 5, Difficulty.medium: 10, Difficulty.hard: 15}[difficulty]


@register
class NonogramGenerator(GameGenerator):
    kind = "nonogram"

    def generate(
        self,
        *,
        seed: int,
        difficulty: Difficulty,
        title: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> PuzzleBase:
        params = params or {}
        rng = make_rng(seed)
        n = size_for(difficulty, params)
        name = params.get("symbol") or rng.choice(list(SYMBOLS))
        grid = SYMBOLS[name](n)
        # Ensure some filled cells
        if sum(sum(row) for row in grid) < n:
            grid = _symbol_house(n)
            name = "house"
        row_clues, col_clues = clues_for(grid)
        verify_clues(grid, row_clues, col_clues)
        return PuzzleBase(
            kind=self.kind,
            title=title or f"Nonogram {n}×{n}",
            instructions=(
                "Vybarvi políčka podle čísel u řádků a sloupců. "
                "Čísla udávají délky souvislých bloků."
            ),
            difficulty=difficulty,
            seed=seed,
            data={
                "size": n,
                "row_clues": row_clues,
                "col_clues": col_clues,
                "symbol": name,
            },
            answer={"grid": grid},
        )
