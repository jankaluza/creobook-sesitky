"""Sudoku generation with unique-solution validation (4×4, 6×6, 9×9)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase


def _box_size(n: int) -> tuple[int, int]:
    if n == 4:
        return 2, 2
    if n == 6:
        return 2, 3
    if n == 9:
        return 3, 3
    raise ValueError(f"Unsupported sudoku size: {n}")


def _find_empty(grid: list[list[int]]) -> tuple[int, int] | None:
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 0:
                return r, c
    return None


def _valid(grid: list[list[int]], r: int, c: int, val: int) -> bool:
    n = len(grid)
    br, bc = _box_size(n)
    if any(grid[r][j] == val for j in range(n)):
        return False
    if any(grid[i][c] == val for i in range(n)):
        return False
    box_r, box_c = (r // br) * br, (c // bc) * bc
    for i in range(box_r, box_r + br):
        for j in range(box_c, box_c + bc):
            if grid[i][j] == val:
                return False
    return True


def count_solutions(grid: list[list[int]], limit: int = 2) -> int:
    g = deepcopy(grid)
    count = 0

    def solve() -> bool:
        nonlocal count
        if count >= limit:
            return True
        pos = _find_empty(g)
        if pos is None:
            count += 1
            return count >= limit
        r, c = pos
        for val in range(1, len(g) + 1):
            if _valid(g, r, c, val):
                g[r][c] = val
                if solve():
                    return True
                g[r][c] = 0
        return False

    solve()
    return count


def _fill_grid(n: int, rng) -> list[list[int]]:
    grid = [[0] * n for _ in range(n)]

    def fill() -> bool:
        pos = _find_empty(grid)
        if pos is None:
            return True
        r, c = pos
        vals = list(range(1, n + 1))
        rng.shuffle(vals)
        for val in vals:
            if _valid(grid, r, c, val):
                grid[r][c] = val
                if fill():
                    return True
                grid[r][c] = 0
        return False

    if not fill():
        raise RuntimeError("Failed to fill sudoku grid")
    return grid


def _clue_target(n: int, difficulty: Difficulty) -> int:
    cells = n * n
    if n == 4:
        return {Difficulty.easy: 10, Difficulty.medium: 8, Difficulty.hard: 6}[difficulty]
    if n == 6:
        return {Difficulty.easy: 22, Difficulty.medium: 18, Difficulty.hard: 14}[difficulty]
    return {Difficulty.easy: 40, Difficulty.medium: 32, Difficulty.hard: 26}[difficulty]


def dig_unique(grid: list[list[int]], rng, target_clues: int) -> list[list[int]]:
    n = len(grid)
    puzzle = deepcopy(grid)
    cells = [(r, c) for r in range(n) for c in range(n)]
    rng.shuffle(cells)
    clues = n * n

    # Phase 1: remove freely down to a soft buffer (fast), then verify uniqueness carefully.
    soft_floor = target_clues + (8 if n >= 9 else 4)
    for r, c in cells:
        if clues <= soft_floor:
            break
        puzzle[r][c] = 0
        clues -= 1

    rng.shuffle(cells)
    for r, c in cells:
        if clues <= target_clues:
            break
        if puzzle[r][c] == 0:
            continue
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        if count_solutions(puzzle, limit=2) != 1:
            puzzle[r][c] = backup
        else:
            clues -= 1

    # Repair if phase-1 over-removed uniqueness
    if count_solutions(puzzle, limit=2) != 1:
        puzzle = deepcopy(grid)
        clues = n * n
        rng.shuffle(cells)
        for r, c in cells:
            if clues <= target_clues:
                break
            backup = puzzle[r][c]
            puzzle[r][c] = 0
            if count_solutions(puzzle, limit=2) != 1:
                puzzle[r][c] = backup
            else:
                clues -= 1

    if count_solutions(puzzle, limit=2) != 1:
        raise ValueError("Sudoku puzzle does not have a unique solution")
    if sum(1 for row in puzzle for v in row if v) == 0:
        raise ValueError("Sudoku puzzle has zero clues")
    return puzzle


def size_for_difficulty(difficulty: Difficulty, size: int | None) -> int:
    if size in (4, 6, 9):
        return size
    return {Difficulty.easy: 4, Difficulty.medium: 6, Difficulty.hard: 9}[difficulty]


def puzzles_per_page(n: int) -> int:
    """How many sudokus of size n×n fill one A5 content area.

    Sized for handwriting (~1.5× denser packing). Layout (cols × rows):
    4×4 → 2×3, 6×6 → 2×2, 9×9 → 1×2.
    """
    return {4: 6, 6: 4, 9: 2}[n]


def layout_columns(n: int, count: int) -> int:
    if count <= 1:
        return 1
    if n == 9:
        return 1
    return 2


def resolve_count(n: int, params: dict[str, Any]) -> int:
    raw = params.get("count")
    if params.get("fill") or raw in ("auto", "fill"):
        return puzzles_per_page(n)
    if raw is None:
        return 1
    return max(1, int(raw))


@register
class SudokuGenerator(GameGenerator):
    kind = "sudoku"

    def generate(
        self,
        *,
        seed: int,
        difficulty: Difficulty,
        title: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> PuzzleBase:
        params = params or {}
        n = size_for_difficulty(difficulty, params.get("size"))
        count = resolve_count(n, params)
        cols = layout_columns(n, count)
        puzzles: list[dict[str, Any]] = []
        answers: list[dict[str, Any]] = []
        for i in range(count):
            # Independent stream per slot for stable seeds when count changes
            slot_rng = make_rng(seed + (i + 1) * 7919)
            solution = _fill_grid(n, slot_rng)
            puzzle = dig_unique(solution, slot_rng, _clue_target(n, difficulty))
            self.validate_grid(puzzle, solution)
            puzzles.append({"id": i + 1, "grid": puzzle})
            answers.append({"id": i + 1, "grid": solution})
        labels = {4: "4×4", 6: "6×6", 9: "9×9"}
        label = labels[n]
        if count > 1:
            default_title = f"Sudoku {label} · {count}×"
            instructions = (
                f"Na stránce je {count} sudoku {label}. "
                "Doplň čísla tak, aby se v žádném řádku, sloupci ani bloku neopakovala."
            )
        else:
            default_title = f"Sudoku {label}"
            instructions = (
                "Doplň čísla tak, aby se v žádném řádku, sloupci ani bloku "
                "neopakovala. Každé číslo použij právě jednou v každé skupině."
            )
        return PuzzleBase(
            kind=self.kind,
            title=title or default_title,
            instructions=instructions,
            difficulty=difficulty,
            seed=seed,
            data={
                "size": n,
                "box": list(_box_size(n)),
                "count": count,
                "cols": cols,
                "puzzles": puzzles,
                # Backward-compatible single-grid fields
                "grid": puzzles[0]["grid"],
            },
            answer={
                "puzzles": answers,
                "grids": [a["grid"] for a in answers],
                "grid": answers[0]["grid"],
            },
        )

    def validate_grid(self, puzzle: list[list[int]], solution: list[list[int]]) -> None:
        if count_solutions(puzzle, limit=2) != 1:
            raise ValueError("Sudoku must have exactly one solution")
        filled = deepcopy(puzzle)
        n = len(filled)
        for r in range(n):
            for c in range(n):
                if filled[r][c] == 0:
                    filled[r][c] = solution[r][c]
        if filled != solution:
            raise ValueError("Provided solution does not match unique solve")
        if count_solutions(solution, limit=2) != 1:
            raise ValueError("Solution grid itself is invalid")
