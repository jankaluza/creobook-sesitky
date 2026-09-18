"""Perfect rectangular maze generation (randomized DFS) with solution path."""

from __future__ import annotations

from collections import deque
from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase

# Wall bits: N E S W
N, E, S, W = 1, 2, 4, 8
DELTA = {N: (-1, 0), E: (0, 1), S: (1, 0), W: (0, -1)}
OPPOSITE = {N: S, E: W, S: N, W: E}


def _size(difficulty: Difficulty, params: dict[str, Any]) -> tuple[int, int]:
    if "rows" in params and "cols" in params:
        return int(params["rows"]), int(params["cols"])
    return {
        Difficulty.easy: (8, 6),
        Difficulty.medium: (12, 9),
        Difficulty.hard: (16, 12),
    }[difficulty]


def generate_maze(rows: int, cols: int, rng) -> list[list[int]]:
    """Each cell stores bit flags for walls still present (start all walls)."""
    grid = [[N | E | S | W for _ in range(cols)] for _ in range(rows)]
    visited = [[False] * cols for _ in range(rows)]
    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        r, c = stack[-1]
        neighbors = []
        for wall, (dr, dc) in DELTA.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                neighbors.append((wall, nr, nc))
        if not neighbors:
            stack.pop()
            continue
        wall, nr, nc = rng.choice(neighbors)
        grid[r][c] &= ~wall
        grid[nr][nc] &= ~OPPOSITE[wall]
        visited[nr][nc] = True
        stack.append((nr, nc))
    return grid


def maze_edges(grid: list[list[int]]) -> list[dict[str, int]]:
    """Export wall segments as unit-cell edges for Typst (no bit ops needed)."""
    rows, cols = len(grid), len(grid[0])
    edges: list[dict[str, int]] = []
    for r in range(rows):
        for c in range(cols):
            w = grid[r][c]
            if w & N:
                edges.append({"x0": c, "y0": r, "x1": c + 1, "y1": r})
            if w & W:
                edges.append({"x0": c, "y0": r, "x1": c, "y1": r + 1})
            if w & S:
                edges.append({"x0": c, "y0": r + 1, "x1": c + 1, "y1": r + 1})
            if w & E:
                edges.append({"x0": c + 1, "y0": r, "x1": c + 1, "y1": r + 1})
    return edges


def solve_maze(
    grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]
) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])
    q = deque([start])
    prev: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            break
        for wall, (dr, dc) in DELTA.items():
            if grid[r][c] & wall:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in prev:
                prev[(nr, nc)] = (r, c)
                q.append((nr, nc))
    if goal not in prev:
        raise ValueError("Maze has no path from START to CÍL")
    path: list[list[int]] = []
    cur: tuple[int, int] | None = goal
    while cur is not None:
        path.append([cur[0], cur[1]])
        cur = prev[cur]
    path.reverse()
    return path


@register
class MazeGenerator(GameGenerator):
    kind = "maze"

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
        rows, cols = _size(difficulty, params)
        grid = generate_maze(rows, cols, rng)
        start = (0, 0)
        goal = (rows - 1, cols - 1)
        path = solve_maze(grid, start, goal)
        return PuzzleBase(
            kind=self.kind,
            title=title or "Bludiště",
            instructions="Najdi cestu od START k CÍL. Tužkou si cestu vyznač.",
            difficulty=difficulty,
            seed=seed,
            data={
                "rows": rows,
                "cols": cols,
                "walls": grid,
                "edges": maze_edges(grid),
                "start": list(start),
                "goal": list(goal),
            },
            answer={"path": path},
        )
