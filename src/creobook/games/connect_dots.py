"""Connect-the-dots from parametric original vector shapes."""

from __future__ import annotations

import math
from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase


def _point_count(difficulty: Difficulty, params: dict[str, Any]) -> int:
    if params.get("points") in (20, 40, 70):
        return int(params["points"])
    return {Difficulty.easy: 20, Difficulty.medium: 40, Difficulty.hard: 70}[difficulty]


def _star_polygon(n_points: int, spikes: int = 5) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(n_points):
        t = 2 * math.pi * i / n_points - math.pi / 2
        # modulate radius for a soft star / flower outline without self-cross for low spikes
        wave = 0.18 * math.cos(spikes * t)
        r = 0.78 + wave
        pts.append((0.5 + r * 0.42 * math.cos(t), 0.5 + r * 0.42 * math.sin(t)))
    return pts


def _house_outline(n_points: int) -> list[tuple[float, float]]:
    # Key corners then densify along perimeter
    corners = [
        (0.2, 0.85),
        (0.2, 0.45),
        (0.5, 0.18),
        (0.8, 0.45),
        (0.8, 0.85),
        (0.2, 0.85),
    ]
    return _resample(corners, n_points)


def _cat_outline(n_points: int) -> list[tuple[float, float]]:
    corners = [
        (0.35, 0.75),
        (0.25, 0.55),
        (0.28, 0.35),
        (0.22, 0.18),
        (0.38, 0.32),
        (0.5, 0.28),
        (0.62, 0.32),
        (0.78, 0.18),
        (0.72, 0.35),
        (0.75, 0.55),
        (0.65, 0.75),
        (0.55, 0.82),
        (0.45, 0.82),
        (0.35, 0.75),
    ]
    return _resample(corners, n_points)


def _resample(corners: list[tuple[float, float]], n: int) -> list[tuple[float, float]]:
    # Cumulative length
    segs = []
    total = 0.0
    for i in range(len(corners) - 1):
        x0, y0 = corners[i]
        x1, y1 = corners[i + 1]
        d = math.hypot(x1 - x0, y1 - y0)
        segs.append((x0, y0, x1, y1, d))
        total += d
    if total == 0:
        return [(0.5, 0.5)] * n
    out: list[tuple[float, float]] = []
    for k in range(n):
        target = (k / n) * total
        acc = 0.0
        for x0, y0, x1, y1, d in segs:
            if acc + d >= target or (x0, y0, x1, y1, d) == segs[-1]:
                t = 0 if d == 0 else (target - acc) / d
                t = min(1.0, max(0.0, t))
                out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
                break
            acc += d
    return out


SHAPES = {
    "star": _star_polygon,
    "house": _house_outline,
    "cat": _cat_outline,
}


@register
class ConnectDotsGenerator(GameGenerator):
    kind = "connect_dots"

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
        n = _point_count(difficulty, params)
        shape = params.get("shape") or rng.choice(list(SHAPES))
        if shape == "star":
            pts = _star_polygon(n, spikes=5)
        else:
            pts = SHAPES[shape](n)
        # Tiny jitter for uniqueness without crossings
        pts = [
            (
                min(0.98, max(0.02, x + rng.uniform(-0.004, 0.004))),
                min(0.98, max(0.02, y + rng.uniform(-0.004, 0.004))),
            )
            for x, y in pts
        ]
        numbered = [{"n": i + 1, "x": round(x, 5), "y": round(y, 5)} for i, (x, y) in enumerate(pts)]
        if [p["n"] for p in numbered] != list(range(1, n + 1)):
            raise ValueError("Connect-the-dots numbering invalid")
        return PuzzleBase(
            kind=self.kind,
            title=title or "Spojovačka",
            instructions=(
                f"Spoj body od 1 do {n} v pořadí. Vznikne obrázek. "
                "Pracuj tužkou a pomalu."
            ),
            difficulty=difficulty,
            seed=seed,
            data={"points": numbered, "shape": shape, "count": n},
            answer={"points": numbered, "closed": True},
        )
