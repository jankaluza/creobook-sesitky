"""Game generator protocol and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from random import Random
from typing import Any, Callable

from creobook.games.models import Difficulty, PageSpec, PuzzleBase


class GameGenerator(ABC):
    kind: str

    @abstractmethod
    def generate(
        self,
        *,
        seed: int,
        difficulty: Difficulty,
        title: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> PuzzleBase:
        raise NotImplementedError

    def validate(self, puzzle: PuzzleBase) -> None:
        """Raise ValueError if puzzle is invalid. Default: no-op."""


_REGISTRY: dict[str, GameGenerator] = {}


def register(cls_or_gen: type[GameGenerator] | GameGenerator) -> type[GameGenerator] | GameGenerator:
    """Register a generator instance or class (class is instantiated once)."""
    gen: GameGenerator
    if isinstance(cls_or_gen, type):
        gen = cls_or_gen()
    else:
        gen = cls_or_gen
    if not getattr(gen, "kind", None):
        raise ValueError("generator.kind is required")
    _REGISTRY[gen.kind] = gen
    return cls_or_gen


def get_generator(kind: str) -> GameGenerator:
    if kind not in _REGISTRY:
        raise KeyError(f"Unknown game kind: {kind!r}. Registered: {sorted(_REGISTRY)}")
    return _REGISTRY[kind]


def registered_kinds() -> list[str]:
    return sorted(_REGISTRY)


def make_rng(seed: int) -> Random:
    return Random(seed)


def resolve_difficulty(
    page: PageSpec,
    pack_default: Difficulty,
    index: int,
) -> Difficulty:
    if page.difficulty is not None and page.difficulty != Difficulty.mixed:
        return page.difficulty
    if pack_default != Difficulty.mixed:
        return pack_default
    cycle = [Difficulty.easy, Difficulty.medium, Difficulty.hard]
    return cycle[index % len(cycle)]


GeneratorFactory = Callable[[], GameGenerator]
