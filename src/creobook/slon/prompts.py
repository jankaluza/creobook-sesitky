"""Prompts for the elephant asset, the scene plan, and the busy line-art scenes."""

from __future__ import annotations

from creobook.slon.models import AgeGroup, SceneSpec, SlonConfig

_STYLE = """
Professional children's coloring-book line art for ages 6–8.
Pure white background. Clean, smooth, even black outlines. Enclosed regions a child can color.
No color. No grayscale. No shading. No gradients. No shadows. No crosshatching.
No photographic texture. No large solid black areas. No watermark. No text.
No letters. No numbers. No logo. No decorative page border. No frame.
""".strip()

_AGE: dict[AgeGroup, str] = {
    "3-5": "Keep objects large and clearly separated. Fewer tiny parts.",
    "6-8": "Many recognizable objects, each large enough to color on A5 paper. No microscopic detail.",
    "9-12": "A richer scene with more objects, still drawn with the same clean line weight. No visual noise.",
}

_DENSITY: dict[str, str] = {
    "easy": (
        "A busy but readable scene with clear gaps between groups of objects. "
        "Leave several open white areas among the objects, each large enough for a small character to stand."
    ),
    "medium": (
        "A full, busy scene with many activities and objects spread across the whole picture. "
        "Leave a few open white areas among the objects, large enough for a small character to stand."
    ),
    "hard": (
        "Wide view from much farther away, as if the viewer stepped back from the place. "
        "The picture is crowded with many people and many separate objects in the foreground, middle, and background. "
        "Add a crowd of visitors, workers, or performers that fits the place, and extra props beyond the listed ones. "
        "The description is only the core of the location, not the full contents. "
        "Figures are smaller than on an easy page, but each person and object stays recognizable and colorable. "
        "Do not use hatching, texture, or tiny unreadable marks to fake busyness. "
        "Leave one smaller open white area among the crowd, still large enough for a small character to stand."
    ),
}

_ACCESSORIES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("cirkus", "circus"), "a small simple bow tie"),
    (("továr", "tovar", "factory"), "simple overalls with two straps"),
    (("pirát", "pirat", "pirate"), "a simple pirate hat"),
    (("vesmír", "vesmir", "space"), "a simple round space helmet that leaves the trunk visible"),
    (("hrad", "castle", "rytíř", "rytir", "knight"), "a small simple knight helmet"),
)


def accessory_for(theme: str) -> str:
    text = theme.lower()
    for keys, accessory in _ACCESSORIES:
        if any(key in text for key in keys):
            return accessory
    return ""


def elephant_prompt(config: SlonConfig) -> str:
    accessory = accessory_for(config.theme)
    costume = (
        f"One simple accessory: {accessory}. It must not hide the ears or the trunk."
        if accessory
        else "No clothes and no accessories."
    )
    return f"""
Draw one original cartoon elephant character for a children's coloring book.
Theme of the booklet: {config.theme}. {costume}
Cute and friendly. Full body. A simple standing pose. Large ears and a clear trunk.
The same character will be shown very small, so the silhouette must stay obvious.
{_STYLE}
Centered, with a wide empty white margin around the elephant. No background scene.
No other animals. No ground line. No props except the one accessory above.
""".strip()


def plan_prompt(config: SlonConfig) -> str:
    return f"""
Create a seek-and-find coloring-book plan as JSON.
Theme: {config.theme}
Booklet title: {config.title}
Age group: {config.age_group}
Number of scenes: {config.puzzle_count}
Difficulty of each scene, in order:
{chr(10).join(f"{index}. {level}" for index, level in enumerate(config.page_difficulties(), start=1))}

Easy scenes have fewer, larger objects and several open areas.
Medium scenes are fuller.
Hard scenes are wide views from a distance, packed with a crowd of people and many extra objects. Describe that crowd. Keep one small open space between them.
Do not draw that open area as an empty rectangle. It is just space between objects.

Every scene is a different place, activity, or moment inside this theme.
Do not reuse the same composition. Do not hardcode a fixed list of locations from another theme.
Invent original locations that fit only this theme.

Do not mention elephants, elephant statues, elephant toys, elephant pictures, or elephant shapes.
The elephant is added later by the program. Scene text must not contain the words elephant or slon.

Return only JSON:
{{
  "theme": "{config.theme}",
  "scenes": [
    {{
      "id": "short-slug",
      "title": "short title in the same language as the booklet title",
      "description": "detailed English description of one original busy scene",
      "objects": ["english noun"],
      "hiding_spots": ["a place among the objects, without naming an elephant"],
      "complexity": "medium",
      "composition": "slightly elevated or isometric view, what fills the foreground and background"
    }}
  ]
}}

Use exactly {config.puzzle_count} scenes. ids are unique lowercase slugs.
No copyrighted characters, franchises, or brands.
""".strip()


def scene_prompt(config: SlonConfig, scene: SceneSpec, difficulty: str | None = None) -> str:
    level = difficulty or config.difficulty
    objects = ", ".join(scene.objects) if scene.objects else "many theme-related objects"
    composition = scene.composition or "slightly elevated view, balanced and full"
    if level == "hard":
        shared = (
            "Shared booklet style: the same line thickness and the same character proportions. "
            "This page shows more people and more objects because the view is farther away, not because the lines are denser."
        )
    else:
        shared = (
            "Shared booklet style: the same line thickness, the same character proportions, the same amount of detail.\n"
            "This is a coloring page, not a finished picture. The picture is busy because it contains many different objects, not because of line texture."
        )
    return f"""
{_STYLE}
{_AGE[config.age_group]}
{_DENSITY[level]}
{shared}

Theme: {config.theme}
Scene title: {scene.title}
Scene: {scene.description}
Include these recognizable objects, kept separate: {objects}
Composition: {composition}

Do not include any elephants, elephant statues, elephant toys, elephant pictures, elephant-shaped decorations, or elephant silhouettes.
No other hidden animals that could be confused with an elephant.
""".strip()
