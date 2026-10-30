"""Perfect rectangular mazes with difficulty scoring and validation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase

GENERATOR_VERSION = "1.0.0"
ALGORITHM = "recursive_backtracker"

# Wall bits: N E S W
N, E, S, W = 1, 2, 4, 8
DELTA = {N: (-1, 0), E: (0, 1), S: (1, 0), W: (0, -1)}
OPPOSITE = {N: S, E: W, S: N, W: E}
DIR_ORDER = (N, E, S, W)

# cols × rows per difficulty (spec)
DIFFICULTY_GRIDS: dict[Difficulty, tuple[int, int]] = {
    Difficulty.easy: (12, 16),
    Difficulty.medium: (18, 24),
    Difficulty.hard: (26, 34),
}

MAX_ATTEMPTS = 80
MIN_CELL_MM = 3.5
# Usable drawing area on A5 after margins/header/footer (approx.)
USABLE_WIDTH_MM = 126.0
USABLE_HEIGHT_MM = 155.0

SCORE_WEIGHTS = {
    "solution_length": 0.25,
    "turns": 0.20,
    "dead_ends": 0.15,
    "branch_depth": 0.20,
    "decision_points": 0.15,
    "visual_density": 0.05,
}

# Tuned windows after difficulty baseline offset
SCORE_RANGES: dict[Difficulty, tuple[float, float]] = {
    Difficulty.easy: (0.15, 0.45),
    Difficulty.medium: (0.42, 0.72),
    Difficulty.hard: (0.68, 0.98),
}

SCORE_BASELINE: dict[Difficulty, float] = {
    Difficulty.easy: 0.05,
    Difficulty.medium: 0.28,
    Difficulty.hard: 0.52,
}


class MazeCell(BaseModel):
    north_wall: bool = True
    east_wall: bool = True
    south_wall: bool = True
    west_wall: bool = True


class DifficultyMetrics(BaseModel):
    total_cells: int
    solution_length: int
    solution_length_ratio: float
    turn_count: int
    dead_end_count: int
    dead_end_ratio: float
    average_branch_depth: float
    maximum_branch_depth: int
    decision_point_count: int
    long_straight_segments: int
    visual_density: float
    component_scores: dict[str, float] = Field(default_factory=dict)
    difficulty_score: float


@dataclass
class ScoredMaze:
    cols: int
    rows: int
    walls: list[list[int]]
    start: tuple[int, int]
    goal: tuple[int, int]
    start_opening: Literal["N", "E", "S", "W"]
    goal_opening: Literal["N", "E", "S", "W"]
    path: list[list[int]]
    metrics: DifficultyMetrics
    attempt: int
    base_seed: int
    attempt_seed: int


def _size(difficulty: Difficulty, params: dict[str, Any]) -> tuple[int, int]:
    """Return (rows, cols)."""
    if "rows" in params and "cols" in params:
        return int(params["rows"]), int(params["cols"])
    cols, rows = DIFFICULTY_GRIDS[difficulty]
    return rows, cols


def generate_maze(rows: int, cols: int, rng) -> list[list[int]]:
    """DFS recursive backtracker; each cell stores wall bit flags."""
    grid = [[N | E | S | W for _ in range(cols)] for _ in range(rows)]
    visited = [[False] * cols for _ in range(rows)]
    sr, sc = rng.randrange(rows), rng.randrange(cols)
    stack = [(sr, sc)]
    visited[sr][sc] = True
    while stack:
        r, c = stack[-1]
        neighbors = []
        dirs = list(DIR_ORDER)
        rng.shuffle(dirs)
        for wall in dirs:
            dr, dc = DELTA[wall]
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
    rows, cols = len(grid), len(grid[0])
    edges: list[dict[str, int]] = []
    for r in range(rows):
        for c in range(cols):
            w = grid[r][c]
            if w & N:
                edges.append({"x0": c, "y0": r, "x1": c + 1, "y1": r})
            if w & W:
                edges.append({"x0": c, "y0": r, "x1": c, "y1": r + 1})
            # Outer S / E only once per outer edge; inner shared walls via N/W of neighbor
            if r == rows - 1 and (w & S):
                edges.append({"x0": c, "y0": r + 1, "x1": c + 1, "y1": r + 1})
            if c == cols - 1 and (w & E):
                edges.append({"x0": c + 1, "y0": r, "x1": c + 1, "y1": r + 1})
    return edges


def walls_to_cells(grid: list[list[int]]) -> list[list[dict[str, bool]]]:
    return [
        [
            {
                "north_wall": bool(cell & N),
                "east_wall": bool(cell & E),
                "south_wall": bool(cell & S),
                "west_wall": bool(cell & W),
            }
            for cell in row
        ]
        for row in grid
    ]


def open_passages(grid: list[list[int]], r: int, c: int) -> list[int]:
    return [wall for wall in DIR_ORDER if not (grid[r][c] & wall)]


def count_openings(grid: list[list[int]], r: int, c: int) -> int:
    return len(open_passages(grid, r, c))


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


def _edge_count(grid: list[list[int]]) -> int:
    """Count undirected open passages between adjacent cells."""
    rows, cols = len(grid), len(grid[0])
    edges = 0
    for r in range(rows):
        for c in range(cols):
            if not (grid[r][c] & E) and c + 1 < cols:
                edges += 1
            if not (grid[r][c] & S) and r + 1 < rows:
                edges += 1
    return edges


def _reachable_count(grid: list[list[int]], start: tuple[int, int]) -> int:
    rows, cols = len(grid), len(grid[0])
    seen = {start}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for wall, (dr, dc) in DELTA.items():
            if grid[r][c] & wall:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
    return len(seen)


def validate_topology(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    path: list[list[int]],
) -> None:
    rows, cols = len(grid), len(grid[0])
    total = rows * cols
    if _reachable_count(grid, start) != total:
        raise ValueError("Maze has unreachable cells")
    if _edge_count(grid) != total - 1:
        raise ValueError("Maze is not a perfect spanning tree")
    # Neighbor wall consistency
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                a = bool(grid[r][c] & E)
                b = bool(grid[r][c + 1] & W)
                if a != b:
                    raise ValueError("Inconsistent E/W walls")
            if r + 1 < rows:
                a = bool(grid[r][c] & S)
                b = bool(grid[r + 1][c] & N)
                if a != b:
                    raise ValueError("Inconsistent S/N walls")
    if not path or path[0] != list(start) or path[-1] != list(goal):
        raise ValueError("Solution endpoints mismatch")
    for i in range(1, len(path)):
        r0, c0 = path[i - 1]
        r1, c1 = path[i]
        dr, dc = r1 - r0, c1 - c0
        if abs(dr) + abs(dc) != 1:
            raise ValueError("Solution step not adjacent")
        wall = {( -1, 0): N, (1, 0): S, (0, -1): W, (0, 1): E}[(dr, dc)]
        if grid[r0][c0] & wall:
            raise ValueError("Solution crosses a wall")
    # Uniqueness: BFS parents — only one path in a tree
    alt = solve_maze(grid, start, goal)
    if alt != path:
        raise ValueError("Solution path not unique / unstable")


def _boundary_cells(rows: int, cols: int) -> list[tuple[int, int, str]]:
    """(r, c, preferred_opening) on outer boundary."""
    cells: list[tuple[int, int, str]] = []
    for c in range(cols):
        cells.append((0, c, "N"))
        cells.append((rows - 1, c, "S"))
    for r in range(1, rows - 1):
        cells.append((r, 0, "W"))
        cells.append((r, cols - 1, "E"))
    return cells


def select_entrance_exit(
    grid: list[list[int]],
    rows: int,
    cols: int,
    rng,
    *,
    prefer_long: bool = False,
) -> tuple[tuple[int, int], tuple[int, int], str, str]:
    boundary = _boundary_cells(rows, cols)
    starts = [b for b in boundary if b[2] in ("N", "W")]
    goals = [b for b in boundary if b[2] in ("S", "E")]
    rng.shuffle(starts)
    rng.shuffle(goals)
    candidates: list[tuple[float, tuple, tuple, str, str]] = []
    for sr, sc, so in starts[:30]:
        for gr, gc, go in goals[:30]:
            if (sr, sc) == (gr, gc):
                continue
            geom = float(abs(sr - gr) + abs(sc - gc))
            if so == go:
                geom *= 0.5
            if geom < 4:
                continue
            path_len = 0.0
            if prefer_long:
                try:
                    path_len = float(len(solve_maze(grid, (sr, sc), (gr, gc))))
                except ValueError:
                    continue
            score = path_len * 2.0 + geom if prefer_long else geom
            candidates.append((score, (sr, sc), (gr, gc), so, go))
    if not candidates:
        return (0, 0), (rows - 1, cols - 1), "N", "S"
    candidates.sort(key=lambda x: x[0], reverse=True)
    # Pick among top few with seeded tie-break
    top = candidates[: max(1, min(8, len(candidates)))]
    pick = rng.choice(top)
    return pick[1], pick[2], pick[3], pick[4]


def open_boundary(
    grid: list[list[int]], r: int, c: int, opening: str
) -> None:
    bit = {"N": N, "E": E, "S": S, "W": W}[opening]
    grid[r][c] &= ~bit


def count_external_openings(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    n = 0
    for c in range(cols):
        if not (grid[0][c] & N):
            n += 1
        if not (grid[rows - 1][c] & S):
            n += 1
    for r in range(rows):
        if not (grid[r][0] & W):
            n += 1
        if not (grid[r][cols - 1] & E):
            n += 1
    return n


def _turn_count(path: list[list[int]]) -> int:
    if len(path) < 3:
        return 0
    turns = 0
    for i in range(2, len(path)):
        dr0 = path[i - 1][0] - path[i - 2][0]
        dc0 = path[i - 1][1] - path[i - 2][1]
        dr1 = path[i][0] - path[i - 1][0]
        dc1 = path[i][1] - path[i - 1][1]
        if (dr0, dc0) != (dr1, dc1):
            turns += 1
    return turns


def _long_straights(path: list[list[int]], min_len: int = 5) -> int:
    if len(path) < 2:
        return 0
    count = 0
    run = 1
    prev = (path[1][0] - path[0][0], path[1][1] - path[0][1])
    for i in range(2, len(path)):
        cur = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        if cur == prev:
            run += 1
        else:
            if run >= min_len:
                count += 1
            run = 1
            prev = cur
    if run >= min_len:
        count += 1
    return count


def _dead_ends(
    grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]
) -> list[tuple[int, int]]:
    rows, cols = len(grid), len(grid[0])
    out = []
    for r in range(rows):
        for c in range(cols):
            if (r, c) in (start, goal):
                continue
            if count_openings(grid, r, c) == 1:
                out.append((r, c))
    return out


def _decision_points_on_path(
    grid: list[list[int]], path: list[list[int]]
) -> int:
    n = 0
    for r, c in path:
        # Internal junctions: more than 2 passages
        if count_openings(grid, r, c) >= 3:
            n += 1
    return n


def _branch_depths(
    grid: list[list[int]], path: list[list[int]]
) -> tuple[float, int]:
    path_set = {(p[0], p[1]) for p in path}
    depths: list[int] = []
    rows, cols = len(grid), len(grid[0])
    for r, c in path:
        for wall, (dr, dc) in DELTA.items():
            if grid[r][c] & wall:
                continue
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if (nr, nc) in path_set:
                continue
            # BFS depth into off-path branch until dead end / path
            seen = {(r, c), (nr, nc)}
            q = deque([(nr, nc, 1)])
            max_d = 1
            while q:
                cr, cc, d = q.popleft()
                max_d = max(max_d, d)
                for w2, (dr2, dc2) in DELTA.items():
                    if grid[cr][cc] & w2:
                        continue
                    rr, rc = cr + dr2, cc + dc2
                    if not (0 <= rr < rows and 0 <= rc < cols):
                        continue
                    if (rr, rc) in seen or (rr, rc) in path_set:
                        continue
                    seen.add((rr, rc))
                    q.append((rr, rc, d + 1))
            depths.append(max_d)
    if not depths:
        return 0.0, 0
    return sum(depths) / len(depths), max(depths)


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_metrics(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    path: list[list[int]],
    *,
    difficulty: Difficulty,
) -> DifficultyMetrics:
    rows, cols = len(grid), len(grid[0])
    total = rows * cols
    sol_len = len(path)
    ratio = sol_len / total
    turns = _turn_count(path)
    dead = _dead_ends(grid, start, goal)
    dead_ratio = len(dead) / total
    avg_branch, max_branch = _branch_depths(grid, path)
    decisions = _decision_points_on_path(grid, path)
    straights = _long_straights(path)
    visual = _clamp01(1.0 - (straights / max(1, turns + straights + 1)))

    # Difficulty-relative normalization so hard grids can still score high
    if difficulty == Difficulty.easy:
        sol_score = _clamp01((ratio - 0.12) / 0.35)
        turn_score = _clamp01(turns / 45.0)
        dead_score = _clamp01(dead_ratio / 0.28)
        branch_score = _clamp01(avg_branch / 6.0 * 0.5 + max_branch / 20.0 * 0.5)
        decision_score = _clamp01(decisions / 25.0)
    elif difficulty == Difficulty.medium:
        sol_score = _clamp01((ratio - 0.18) / 0.40)
        turn_score = _clamp01(turns / 120.0)
        dead_score = _clamp01(dead_ratio / 0.30)
        branch_score = _clamp01(avg_branch / 10.0 * 0.5 + max_branch / 35.0 * 0.5)
        decision_score = _clamp01(decisions / 55.0)
    else:
        sol_score = _clamp01((ratio - 0.22) / 0.45)
        turn_score = _clamp01(turns / 220.0)
        dead_score = _clamp01(dead_ratio / 0.32)
        branch_score = _clamp01(avg_branch / 14.0 * 0.5 + max_branch / 55.0 * 0.5)
        decision_score = _clamp01(decisions / 100.0)

    visual_score = visual
    components = {
        "solution_length": sol_score,
        "turns": turn_score,
        "dead_ends": dead_score,
        "branch_depth": branch_score,
        "decision_points": decision_score,
        "visual_density": visual_score,
    }
    raw = sum(components[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
    raw = _clamp01(raw - 0.02 * straights)
    score = _clamp01(SCORE_BASELINE[difficulty] + 0.48 * raw)

    return DifficultyMetrics(
        total_cells=total,
        solution_length=sol_len,
        solution_length_ratio=ratio,
        turn_count=turns,
        dead_end_count=len(dead),
        dead_end_ratio=dead_ratio,
        average_branch_depth=avg_branch,
        maximum_branch_depth=max_branch,
        decision_point_count=decisions,
        long_straight_segments=straights,
        visual_density=visual,
        component_scores=components,
        difficulty_score=score,
    )


def assert_cell_size_printable(cols: int, rows: int) -> None:
    cell = min(USABLE_WIDTH_MM / cols, USABLE_HEIGHT_MM / rows)
    if cell < MIN_CELL_MM:
        raise ValueError(
            f"Maze {cols}×{rows} cell {cell:.2f}mm below minimum {MIN_CELL_MM}mm"
        )


def generate_scored_maze(
    *,
    seed: int,
    difficulty: Difficulty,
    params: dict[str, Any] | None = None,
) -> ScoredMaze:
    params = params or {}
    rows, cols = _size(difficulty, params)
    assert_cell_size_printable(cols, rows)
    lo, hi = SCORE_RANGES[difficulty]
    last_err = "no candidate"
    best: ScoredMaze | None = None

    for attempt in range(MAX_ATTEMPTS):
        attempt_seed = seed * 1009 + attempt * 9176 + 13
        rng = make_rng(attempt_seed)
        grid = generate_maze(rows, cols, rng)
        prefer_long = difficulty != Difficulty.easy
        start, goal, so, go = select_entrance_exit(
            grid, rows, cols, rng, prefer_long=prefer_long
        )
        open_boundary(grid, start[0], start[1], so)
        open_boundary(grid, goal[0], goal[1], go)
        if count_external_openings(grid) != 2:
            last_err = "boundary openings != 2"
            continue
        try:
            path = solve_maze(grid, start, goal)
            validate_topology(grid, start, goal, path)
        except ValueError as exc:
            last_err = str(exc)
            continue
        metrics = compute_metrics(
            grid, start, goal, path, difficulty=difficulty
        )
        scored = ScoredMaze(
            cols=cols,
            rows=rows,
            walls=grid,
            start=start,
            goal=goal,
            start_opening=so,  # type: ignore[arg-type]
            goal_opening=go,  # type: ignore[arg-type]
            path=path,
            metrics=metrics,
            attempt=attempt + 1,
            base_seed=seed,
            attempt_seed=attempt_seed,
        )
        if lo <= metrics.difficulty_score <= hi:
            return scored
        # Keep closest candidate as fallback diagnostic
        if best is None or abs(metrics.difficulty_score - (lo + hi) / 2) < abs(
            best.metrics.difficulty_score - (lo + hi) / 2
        ):
            best = scored
        last_err = (
            f"score {metrics.difficulty_score:.3f} outside [{lo}, {hi}]"
        )

    if best is not None and params.get("allow_nearest"):
        return best
    raise ValueError(
        f"Could not generate {difficulty.value} maze after {MAX_ATTEMPTS} attempts "
        f"(seed={seed}): {last_err}"
    )


def scored_to_puzzle(
    scored: ScoredMaze,
    *,
    difficulty: Difficulty,
    title: str | None = None,
    maze_number: int | None = None,
) -> PuzzleBase:
    marker = {
        Difficulty.easy: "●○○",
        Difficulty.medium: "●●○",
        Difficulty.hard: "●●●",
    }[difficulty]
    label = {
        Difficulty.easy: "LEHKÁ",
        Difficulty.medium: "STŘEDNÍ",
        Difficulty.hard: "TĚŽKÁ",
    }[difficulty]
    wall_pt = {
        Difficulty.easy: 0.80,
        Difficulty.medium: 0.70,
        Difficulty.hard: 0.55,
    }[difficulty]
    return PuzzleBase(
        kind="maze",
        title=title or (f"Bludiště {maze_number}" if maze_number else "Bludiště"),
        instructions=(
            "Najděte cestu od START k CÍLI. Čáru veďte pouze volnými průchody."
        ),
        difficulty=difficulty,
        seed=scored.base_seed,
        data={
            "rows": scored.rows,
            "cols": scored.cols,
            "walls": scored.walls,
            "cells": walls_to_cells(scored.walls),
            "edges": maze_edges(scored.walls),
            "start": list(scored.start),
            "goal": list(scored.goal),
            "start_opening": scored.start_opening,
            "goal_opening": scored.goal_opening,
            "maze_number": maze_number,
            "difficulty_marker": marker,
            "difficulty_label_cs": label,
            "wall_pt": wall_pt,
            "maze_style": "rectangular",
            "metrics": scored.metrics.model_dump(mode="json"),
            "generation": {
                "algorithm": ALGORITHM,
                "base_seed": scored.base_seed,
                "attempt_seed": scored.attempt_seed,
                "attempts": scored.attempt,
            },
        },
        answer={"path": scored.path},
    )


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
        params = dict(params or {})
        # Single-page / pack: allow nearest if strict window fails (keeps CI fast)
        params.setdefault("allow_nearest", True)
        scored = generate_scored_maze(seed=seed, difficulty=difficulty, params=params)
        return scored_to_puzzle(scored, difficulty=difficulty, title=title)
