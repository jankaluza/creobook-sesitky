"""Spot-the-difference from procedural vector scenes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase

ObjectDict = dict[str, Any]


def _base_scene(rng) -> list[ObjectDict]:
    objects: list[ObjectDict] = [
        {"id": "sky", "type": "rect", "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.45, "pattern": "none"},
        {"id": "ground", "type": "rect", "x": 0.05, "y": 0.55, "w": 0.9, "h": 0.4, "pattern": "none"},
        {"id": "sun", "type": "circle", "x": 0.78, "y": 0.18, "r": 0.07, "pattern": "none"},
        {"id": "cloud1", "type": "cloud", "x": 0.22, "y": 0.16, "s": 1.0, "pattern": "none"},
        {"id": "cloud2", "type": "cloud", "x": 0.48, "y": 0.22, "s": 0.8, "pattern": "none"},
        {"id": "house", "type": "house", "x": 0.22, "y": 0.48, "s": 1.0, "mirror": False, "pattern": "none"},
        {"id": "tree1", "type": "tree", "x": 0.62, "y": 0.48, "s": 1.0, "mirror": False, "pattern": "none"},
        {"id": "tree2", "type": "tree", "x": 0.78, "y": 0.52, "s": 0.75, "mirror": False, "pattern": "none"},
        {"id": "star1", "type": "star", "x": 0.15, "y": 0.12, "s": 0.5, "pattern": "none"},
        {"id": "star2", "type": "star", "x": 0.35, "y": 0.1, "s": 0.4, "pattern": "none"},
        {"id": "car", "type": "car", "x": 0.55, "y": 0.72, "s": 1.0, "mirror": False, "pattern": "stripes"},
        {"id": "creature", "type": "creature", "x": 0.38, "y": 0.7, "s": 0.9, "mirror": False, "pattern": "none"},
        {"id": "flower1", "type": "flower", "x": 0.14, "y": 0.78, "s": 0.7, "pattern": "none"},
        {"id": "flower2", "type": "flower", "x": 0.88, "y": 0.76, "s": 0.7, "pattern": "none"},
    ]
    # Stable order; rng reserved for difference choice
    _ = rng
    return objects


DIFF_COUNT = {
    Difficulty.easy: 5,
    Difficulty.medium: 7,
    Difficulty.hard: 10,
}


def _apply_difference(scene: list[ObjectDict], kind: str, target_id: str, rng) -> dict[str, Any]:
    obj = next(o for o in scene if o["id"] == target_id)
    meta = {"id": target_id, "type": kind, "x": obj.get("x", 0.5), "y": obj.get("y", 0.5)}
    if kind == "remove":
        scene[:] = [o for o in scene if o["id"] != target_id]
    elif kind == "size":
        obj["s"] = round(obj.get("s", 1.0) * rng.choice([0.6, 1.45]), 3)
    elif kind == "mirror":
        obj["mirror"] = not obj.get("mirror", False)
    elif kind == "move":
        obj["x"] = round(min(0.9, max(0.08, obj["x"] + rng.choice([-0.12, 0.12]))), 3)
        obj["y"] = round(min(0.88, max(0.08, obj["y"] + rng.choice([-0.08, 0.08]))), 3)
        meta["x"], meta["y"] = obj["x"], obj["y"]
    elif kind == "detail":
        # add or remove a small star near object
        if any(o["id"] == f"detail-{target_id}" for o in scene):
            scene[:] = [o for o in scene if o["id"] != f"detail-{target_id}"]
        else:
            scene.append(
                {
                    "id": f"detail-{target_id}",
                    "type": "star",
                    "x": obj["x"] + 0.06,
                    "y": obj["y"] - 0.06,
                    "s": 0.35,
                    "pattern": "none",
                }
            )
    elif kind == "pattern":
        obj["pattern"] = "dots" if obj.get("pattern") != "dots" else "stripes"
    else:
        raise ValueError(kind)
    return meta


@register
class SpotDifferenceGenerator(GameGenerator):
    kind = "spot_difference"

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
        left = _base_scene(rng)
        right = deepcopy(left)
        n = int(params.get("differences") or DIFF_COUNT[difficulty])
        mutable = [
            o["id"]
            for o in right
            if o["type"] not in ("rect",) and not o["id"].startswith("sky")
        ]
        rng.shuffle(mutable)
        kinds = ["remove", "size", "mirror", "move", "detail", "pattern"]
        changes: list[dict[str, Any]] = []
        used_ids: set[str] = set()
        i = 0
        while len(changes) < n and i < 200:
            i += 1
            tid = mutable[len(changes) % len(mutable)]
            if tid in used_ids and len(used_ids) < len(mutable):
                continue
            kind = kinds[len(changes) % len(kinds)]
            # skip remove if object already gone
            if kind == "remove" and not any(o["id"] == tid for o in right):
                continue
            if not any(o["id"] == tid for o in right) and kind != "detail":
                continue
            try:
                meta = _apply_difference(right, kind, tid, rng)
            except StopIteration:
                continue
            used_ids.add(tid)
            changes.append(meta)
        if len(changes) != n:
            raise ValueError(f"Expected {n} differences, got {len(changes)}")
        return PuzzleBase(
            kind=self.kind,
            title=title or "Najdi rozdíly",
            instructions=(
                f"Porovnej levý a pravý obrázek. Najdi {n} rozdílů a zakroužkuj je."
            ),
            difficulty=difficulty,
            seed=seed,
            data={"left": left, "right": right, "difference_count": n},
            answer={"changes": changes},
        )
