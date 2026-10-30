"""Tests for maze generation, scoring, and booklet PDF."""

from __future__ import annotations

from pathlib import Path

import pytest

from creobook.games.maze import (
    DIFFICULTY_GRIDS,
    MAX_ATTEMPTS,
    SCORE_RANGES,
    _edge_count,
    _reachable_count,
    compute_metrics,
    count_external_openings,
    generate_scored_maze,
    validate_topology,
)
from creobook.games.maze_booklet import (
    build_maze_booklet_pages,
    compile_maze_booklet,
)
from creobook.games.models import Difficulty
from creobook.games.validation import validate_puzzle
from creobook.games.word_search_booklet import EXPECTED_SPREADS
from creobook.imposition import booklet_spreads
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
    extract_page_text,
)


@pytest.mark.parametrize("difficulty", [Difficulty.easy, Difficulty.medium, Difficulty.hard])
def test_maze_topology_and_solution(difficulty):
    scored = generate_scored_maze(seed=20270101 + ord(difficulty.value[0]), difficulty=difficulty)
    cols, rows = DIFFICULTY_GRIDS[difficulty]
    assert scored.cols == cols and scored.rows == rows
    grid = scored.walls
    total = rows * cols
    assert _reachable_count(grid, scored.start) == total
    assert _edge_count(grid) == total - 1
    assert count_external_openings(grid) == 2
    validate_topology(grid, scored.start, scored.goal, scored.path)
    lo, hi = SCORE_RANGES[difficulty]
    assert lo <= scored.metrics.difficulty_score <= hi
    assert scored.attempt <= MAX_ATTEMPTS


def test_metrics_recalculable():
    scored = generate_scored_maze(seed=11, difficulty=Difficulty.medium)
    again = compute_metrics(
        scored.walls,
        scored.start,
        scored.goal,
        scored.path,
        difficulty=Difficulty.medium,
    )
    assert again.solution_length == scored.metrics.solution_length
    assert again.turn_count == scored.metrics.turn_count
    assert abs(again.difficulty_score - scored.metrics.difficulty_score) < 1e-9


def test_reproducible_mazes():
    a = generate_scored_maze(seed=20270101, difficulty=Difficulty.easy)
    b = generate_scored_maze(seed=20270101, difficulty=Difficulty.easy)
    c = generate_scored_maze(seed=20270102, difficulty=Difficulty.easy)
    assert a.walls == b.walls
    assert a.path == b.path
    assert a.start == b.start and a.goal == b.goal
    assert a.walls != c.walls or a.path != c.path


def test_difficulty_ordering_averages():
    avgs = {}
    for d in (Difficulty.easy, Difficulty.medium, Difficulty.hard):
        scores = [
            generate_scored_maze(seed=1000 + i * 31 + ord(d.value[0]), difficulty=d).metrics.difficulty_score
            for i in range(4)
        ]
        avgs[d.value] = sum(scores) / len(scores)
    assert avgs["easy"] < avgs["medium"] < avgs["hard"]


def test_booklet_structure():
    pages, meta = build_maze_booklet_pages(seed=20270101)
    assert len(pages) == 24
    assert pages[0]["kind"] == "maze_cover"
    assert pages[0]["data"]["edition_date"] == "01. 01. 2027"
    mazes = [p for p in pages if p["kind"] == "maze"]
    assert len(mazes) == 18
    assert sum(1 for p in mazes if p["difficulty"] == "easy") == 6
    assert sum(1 for p in mazes if p["difficulty"] == "medium") == 6
    assert sum(1 for p in mazes if p["difficulty"] == "hard") == 6
    assert booklet_spreads(24) == EXPECTED_SPREADS
    assert meta["generation_stats"]["average_scores"]["easy"] < meta["generation_stats"]["average_scores"]["hard"]


def test_maze_booklet_pdf(tmp_path):
    pages_pdf = tmp_path / "maze-a5.pdf"
    booklet_pdf = tmp_path / "maze-a4.pdf"
    json_path = tmp_path / "maze.json"
    result = compile_maze_booklet(
        seed=20270101,
        pages_output=pages_pdf,
        output=booklet_pdf,
        json_output=json_path,
    )
    assert check_page_count(pages_pdf, 24).ok
    assert check_a5_pages(pages_pdf).ok
    assert check_content_within_media_box(pages_pdf).ok
    assert check_page_count(booklet_pdf, 12).ok
    assert check_a4_landscape_sheets(booklet_pdf).ok
    assert json_path.exists()
    texts = extract_page_text(pages_pdf)
    assert "BLUDIŠTĚ" in texts[0]
    assert "Vydání: 01. 01. 2027" in texts[0]
    # One maze per page — no overflow spill onto blank following pages
    maze_pages = texts[1:19]
    assert len(maze_pages) == 18
    for i, text in enumerate(maze_pages, start=1):
        assert f"Bludiště {i}" in text
        assert "START" in text
        assert "CÍL" in text
    assert all("Bludiště" not in t or "Řešení" in t for t in texts[19:])
