"""Turn a theme into a validated illustration plan."""

from __future__ import annotations

import json
import re

from creobook.coloring.models import ColoringConfig, ColoringError, IllustrationPlan
from creobook.coloring.prompts import find_flags, plan_prompt


def strip_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _tokens(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2}


def _too_similar(left: str, right: str) -> bool:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return False
    return len(a & b) / len(a | b) > 0.72


def apply_copyright_flags(plan: IllustrationPlan, config: ColoringConfig) -> IllustrationPlan:
    plan.theme_flags = find_flags(config.theme, config.title)
    for item in plan.illustrations:
        item.copyright_flags = find_flags(
            item.title,
            item.description,
            item.background,
            " ".join(item.subjects),
        )
    return plan


def validate_plan(plan: IllustrationPlan, config: ColoringConfig) -> None:
    """Raise when the plan cannot be drawn. Copyright hits are stored, not raised here."""
    errors: list[str] = []
    if plan.age_group != config.age_group:
        errors.append(
            f"plan age group {plan.age_group} does not match config {config.age_group}"
        )
    if len(plan.illustrations) != config.illustration_count:
        errors.append(
            f"plan has {len(plan.illustrations)} illustrations, config asks for {config.illustration_count}"
        )
    seen: set[str] = set()
    for item in plan.illustrations:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item.id):
            errors.append(f"id {item.id!r} must be a lowercase slug")
        if item.id in seen:
            errors.append(f"duplicate id {item.id}")
        seen.add(item.id)
        if len(item.description.strip()) < 12:
            errors.append(f"{item.id} description is too short")
        if not item.title.strip():
            errors.append(f"{item.id} is missing a title")
    descriptions = [item.description for item in plan.illustrations]
    for index, description in enumerate(descriptions):
        for other in descriptions[index + 1 :]:
            if _too_similar(description, other):
                errors.append("two illustrations are almost the same scene")
                break
    if errors:
        raise ColoringError("Illustration plan is not usable:\n" + "\n".join(errors))


def parse_plan(payload: str, config: ColoringConfig) -> IllustrationPlan:
    try:
        raw = json.loads(strip_json(payload))
    except json.JSONDecodeError as exc:
        raise ColoringError(f"Illustration plan is not valid JSON: {exc}") from exc
    try:
        plan = IllustrationPlan.model_validate(raw)
    except ValueError as exc:
        raise ColoringError(f"Illustration plan has the wrong shape: {exc}") from exc
    apply_copyright_flags(plan, config)
    validate_plan(plan, config)
    return plan


def request_plan(config: ColoringConfig, complete_text) -> IllustrationPlan:
    """Call the text model and validate the plan. ``complete_text`` returns a JSON string."""
    return parse_plan(complete_text(plan_prompt(config)), config)
