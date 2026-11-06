"""Parse and check a scene plan. The text model is called by the workflow."""

from __future__ import annotations

import json
import re

from creobook.coloring.planner import strip_json
from creobook.coloring.prompts import find_flags
from creobook.coloring.workflow import slugify
from creobook.slon.models import SceneSpec, SlonConfig, SlonError
from creobook.slon.prompts import plan_prompt

_ELEPHANT = re.compile(r"elephant|slon", re.IGNORECASE)


def mentions_elephant(scene: SceneSpec) -> bool:
    blob = " ".join(
        [
            scene.title,
            scene.description,
            scene.composition,
            *scene.objects,
            *scene.hiding_spots,
        ]
    )
    return _ELEPHANT.search(blob) is not None


def parse_plan(text: str, config: SlonConfig) -> list[SceneSpec]:
    try:
        payload = json.loads(strip_json(text))
    except json.JSONDecodeError as exc:
        raise SlonError(f"Scene plan is not valid JSON: {exc}") from exc
    raw_scenes = payload.get("scenes") if isinstance(payload, dict) else None
    if not isinstance(raw_scenes, list):
        raise SlonError("Scene plan must contain a scenes list")
    used: set[str] = set()
    scenes: list[SceneSpec] = []
    for item in raw_scenes:
        if not isinstance(item, dict):
            raise SlonError("Each scene must be an object")
        scene = SceneSpec.model_validate(item)
        scene.id = _unique_id(scene.id, used)
        scenes.append(scene)
    if len(scenes) != config.puzzle_count:
        raise SlonError(
            f"Plan has {len(scenes)} scenes, configuration asks for {config.puzzle_count}."
        )
    titles = [scene.title.strip().lower() for scene in scenes]
    if len(set(titles)) != len(titles):
        raise SlonError("Scene titles must be unique")
    return scenes


def _unique_id(raw: str, used: set[str]) -> str:
    base = slugify(raw)
    candidate = base
    number = 2
    while candidate in used:
        candidate = f"{base}-{number}"
        number += 1
    used.add(candidate)
    return candidate


def request_plan(config: SlonConfig, complete) -> list[SceneSpec]:
    return parse_plan(complete(plan_prompt(config)), config)


def copyright_hits(config: SlonConfig, scenes: list[SceneSpec]) -> list[str]:
    hits = [f"theme: {flag}" for flag in find_flags(config.theme, config.title)]
    for scene in scenes:
        flags = find_flags(
            scene.title,
            scene.description,
            scene.composition,
            " ".join(scene.objects),
            " ".join(scene.hiding_spots),
        )
        hits.extend(f"{scene.id}: {flag}" for flag in flags)
    return hits


def elephant_hits(scenes: list[SceneSpec]) -> list[str]:
    return [scene.id for scene in scenes if mentions_elephant(scene)]
