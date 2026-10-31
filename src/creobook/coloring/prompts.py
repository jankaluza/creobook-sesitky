"""Prompt templates and a lightweight copyright screen for coloring plans."""

from __future__ import annotations

import re

from creobook.coloring.models import AgeGroup, ColoringConfig, Illustration

# Obvious franchise, character, and brand names. This is a precaution, not legal clearance.
_PROTECTED = (
    "mickey mouse",
    "minnie mouse",
    "disney",
    "elsa",
    "frozen",
    "moana",
    "encanto",
    "marvel",
    "spider-man",
    "spiderman",
    "batman",
    "superman",
    "harry potter",
    "hogwarts",
    "hermione",
    "pokemon",
    "pokémon",
    "pikachu",
    "ash ketchum",
    "mario",
    "nintendo",
    "hello kitty",
    "barbie",
    "paw patrol",
    "peppa pig",
    "peppa",
    "star wars",
    "darth vader",
    "spongebob",
    "transformers",
    "bluey",
    "coca-cola",
    "coca cola",
    "mcdonald",
    "nike",
)

AGE_PROMPTS: dict[AgeGroup, str] = {
    "3-5": (
        "Very thick, even black outlines. One primary subject. Very large enclosed "
        "coloring regions. Minimal background, lots of white space, almost no small details."
    ),
    "6-8": (
        "Medium-weight black outlines. A few recognizable objects. Moderate scene "
        "complexity, a simple background, and clearly separated coloring regions."
    ),
    "9-12": (
        "More detailed black line art with a richer environment. Fantasy or adventure "
        "composition when it fits the theme. Smaller enclosed regions are allowed, but "
        "every region must stay clearly closed. No micro-detail and no visual noise."
    ),
}

_AVOID = """
Strictly avoid: color, grayscale, shading, gradients, shadows, textures, crosshatching,
photorealism, solid black fills except tiny necessary details such as eyes, decorative clutter,
text, letters, numbers, captions, watermarks, logos, page borders, frames, copyrighted
characters, franchise designs, brand marks, and imitations of a particular living artist.
The background outside the drawing is pure white.
""".strip()

_BASE = """
Professional children's coloring-book illustration. Pure black outlines on a pure white
background. Clean, smooth, closed contours. Friendly recognizable shapes. Large regions
that a child can color. Objects do not overlap into tangled lines. Balanced composition.
Consistent pen style across the booklet: the same line weight and the same simple character design.
Standalone drawing only, with no page, margin, or caption.
""".strip()


def find_flags(*texts: str) -> list[str]:
    blob = " ".join(texts).lower()
    found: list[str] = []
    for term in _PROTECTED:
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", blob):
            found.append(term)
    return found


def plan_prompt(config: ColoringConfig) -> str:
    return f"""
Create a coloring-book illustration plan as JSON.
Theme: {config.theme}
Booklet title: {config.title}
Age group: {config.age_group}
Number of illustrations: {config.illustration_count}

Return only JSON with this shape:
{{
  "theme": "{config.theme}",
  "age_group": "{config.age_group}",
  "illustrations": [
    {{
      "id": "short-slug",
      "title": "short title in the same language as the booklet title",
      "description": "detailed English visual description of one original scene",
      "complexity": "simple" | "medium" | "detailed",
      "subjects": ["english noun", "..."],
      "background": "english background, or an empty string"
    }}
  ]
}}

Rules:
- Exactly {config.illustration_count} unique illustrations.
- ids are lowercase ascii slugs and unique.
- Vary the subjects, actions, and compositions. Do not repeat the same pose.
- Original generic subjects only. No copyrighted characters, franchises, brands, or living artists.
- complexity simple for ages 3-5, medium for ages 6-8, detailed for ages 9-12.
- Descriptions are concrete enough to draw, without style instructions (those are added later).
""".strip()


def image_prompt(item: Illustration, age_group: AgeGroup) -> str:
    subjects = ", ".join(item.subjects) if item.subjects else "the subject described below"
    background = item.background.strip() or "mostly empty white space"
    return "\n\n".join(
        (
            _BASE,
            f"Age group {age_group}. {AGE_PROMPTS[age_group]}",
            f"Scene: {item.description.strip()}",
            f"Include: {subjects}.",
            f"Background: {background}.",
            _AVOID,
        )
    )
