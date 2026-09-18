"""Two-player paper game templates (no generated solutions)."""

from __future__ import annotations

from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase

VARIANTS = {
    "piskvorky": {
        "title": "Piškvorky",
        "instructions": "Hrajte střídavě křížky a kolečka. Vyhraje řada 5 v řadě.",
        "grid": 15,
    },
    "lode": {
        "title": "Lodě",
        "instructions": (
            "Umístěte flotilu (4,3,3,2,2,1,1) na vlastní mřížku. "
            "Pravá mřížka slouží k zaznamenání střel."
        ),
        "grid": 10,
        "dual": True,
    },
    "ctverecky": {
        "title": "Čtverečky",
        "instructions": "Střídavě spojujte body. Kdo uzavře čtverec, získá bod a hraje znovu.",
        "dots": 8,
    },
    "fotbal": {
        "title": "Papírový fotbal",
        "instructions": (
            "Posouvejte míček po čarách. Gól platí průchodem brankou soupeře."
        ),
        "field": True,
    },
    "sibenice": {
        "title": "Šibenice",
        "instructions": "Hádejte písmena českého slova. Za chybu přikreslete část panáčka.",
        "gallows": True,
    },
    "kategorie": {
        "title": "Kategorie",
        "instructions": (
            "Zvolte písmeno. Doplňte slova do kategorií. Bod za unikátní odpověď."
        ),
        "categories": ["Jméno", "Město", "Zvíře", "Rostlina", "Jídlo", "Značka"],
    },
}


@register
class TwoPlayerGenerator(GameGenerator):
    kind = "two_player"

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
        variant = params.get("variant") or "piskvorky"
        if variant not in VARIANTS:
            raise ValueError(f"Unknown two-player variant: {variant}")
        meta = VARIANTS[variant]
        _ = rng  # reserved for future random prompts
        return PuzzleBase(
            kind=self.kind,
            title=title or meta["title"],
            instructions=meta["instructions"],
            difficulty=difficulty,
            seed=seed,
            data={"variant": variant, **{k: v for k, v in meta.items() if k != "title"}},
            answer={},
        )
