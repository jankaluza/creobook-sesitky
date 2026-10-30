"""CreoBook pencil-and-paper game generators."""

from creobook.games import (
    cipher,
    connect_dots,
    crossword,
    maze,
    nonogram,
    spot_difference,
    sudoku,
    two_player,
    word_search,
)
from creobook.games.base import get_generator, register, registered_kinds

# Import side-effects register generators
_ = (
    sudoku,
    maze,
    word_search,
    crossword,
    nonogram,
    connect_dots,
    spot_difference,
    cipher,
    two_player,
)

__all__ = [
    "get_generator",
    "register",
    "registered_kinds",
]
