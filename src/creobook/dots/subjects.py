"""Original side-view subjects. Names on the answer page are Czech; prompts are English."""

from __future__ import annotations

from creobook.coloring.workflow import slugify

Subject = tuple[str, str]

_CATALOG: dict[str, tuple[Subject, ...]] = {
    "animals": (
        ("Liška", "a friendly fox in side view with pointed ears and a bushy tail"),
        ("Ježek", "a hedgehog in side view with a rounded spiny back and a small snout"),
        ("Králík", "a rabbit in side view with two long ears"),
        ("Veverka", "a squirrel in side view with a large curled tail"),
        ("Sova", "an owl in side view with a round head and a short tail"),
        ("Želva", "a turtle in side view with a domed shell and four legs"),
        ("Kachna", "a duck in side view with a broad beak"),
        ("Medvěd", "a bear in side view standing on four paws"),
    ),
    "dinosaurs": (
        ("Brontosaurus", "a long-necked dinosaur in side view with a long tail"),
        ("Triceratops", "a triceratops in side view with a wide frill and three horns"),
        ("Stegosaurus", "a stegosaurus in side view with a row of plates on its back"),
        ("Tyranosaurus", "a tyrannosaurus in side view standing on two legs with a thick tail"),
        ("Pterodaktyl", "a pterosaur in side view with outstretched wings"),
        ("Ankylosaurus", "an ankylosaurus in side view with an armored back and a club tail"),
        ("Parasaurolophus", "a duck-billed dinosaur in side view with a long crest"),
        ("Vejce dinosaura", "a large oval dinosaur egg with a small crack"),
    ),
    "vehicles": (
        ("Auto", "a simple passenger car in side view"),
        ("Náklaďák", "a truck in side view with a cab and a rectangular cargo box"),
        ("Autobus", "a bus in side view with a row of windows"),
        ("Kolo", "a bicycle in side view"),
        ("Lokomotiva", "a steam locomotive in side view"),
        ("Letadlo", "a small airplane in side view"),
        ("Traktor", "a tractor in side view with large rear wheels"),
        ("Loď", "a sailboat in side view with one sail"),
    ),
    "space": (
        ("Raketa", "a rocket standing upright with fins"),
        ("Létající talíř", "a flying saucer with a small dome"),
        ("Astronaut", "an astronaut in side view wearing a round helmet and a backpack"),
        ("Planeta", "a round planet with a thin ring"),
        ("Družice", "a satellite with a body and two rectangular panels"),
        ("Kometa", "a comet with a round head and a long tail"),
        ("Měsíc", "a crescent moon"),
        ("Rover", "a small space rover in side view with wheels"),
    ),
    "fairy-tales": (
        ("Hrad", "a simple castle with three towers"),
        ("Drak", "a friendly dragon in side view with wings and a long tail"),
        ("Koruna", "a royal crown with three points"),
        ("Truhla", "a closed treasure chest in side view"),
        ("Koště", "a witch broom standing upright"),
        ("Muchomůrka", "a toadstool with a spotted cap"),
        ("Klobouk kouzelníka", "a pointed wizard hat"),
        ("Klíč", "an old key in side view"),
    ),
    "sea": (
        ("Ryba", "a fish in side view with a tail fin"),
        ("Velryba", "a whale in side view"),
        ("Delfín", "a dolphin in side view leaping"),
        ("Krab", "a crab seen from above with two claws"),
        ("Mořský koník", "a seahorse in side view"),
        ("Žralok", "a shark in side view"),
        ("Hvězdice", "a five-armed starfish"),
        ("Mušle", "a seashell in side view"),
    ),
    "nature": (
        ("Strom", "a tree with a trunk and a round crown"),
        ("Jedle", "a pine tree with a triangular crown"),
        ("Květina", "a flower with a stem and five petals"),
        ("Houba", "a mushroom with a thick stem and a wide cap"),
        ("Slunce", "a sun disk with short triangular rays"),
        ("Mrak", "a fluffy cloud"),
        ("List", "a single leaf with a stem"),
        ("Hora", "a mountain with two peaks"),
    ),
    "everyday": (
        ("Hrnek", "a mug in side view with a handle"),
        ("Bota", "a shoe in side view"),
        ("Deštník", "an open umbrella in side view"),
        ("Jablko", "an apple with a short stem"),
        ("Židle", "a simple chair in side view"),
        ("Lampa", "a table lamp in side view"),
        ("Klobouk", "a hat with a brim"),
        ("Hodiny", "a round alarm clock with two bells"),
    ),
}

_ALIASES = {
    "animals": "animals",
    "animal": "animals",
    "zvirata": "animals",
    "zviratka": "animals",
    "dinosaurs": "dinosaurs",
    "dinosaur": "dinosaurs",
    "dinosauri": "dinosaurs",
    "dinosaures": "dinosaurs",
    "vehicles": "vehicles",
    "vehicle": "vehicles",
    "auta": "vehicles",
    "doprava": "vehicles",
    "space": "space",
    "vesmir": "space",
    "fairy-tales": "fairy-tales",
    "fairytales": "fairy-tales",
    "fairy": "fairy-tales",
    "pohadky": "fairy-tales",
    "sea": "sea",
    "sea-creatures": "sea",
    "more": "sea",
    "nature": "nature",
    "priroda": "nature",
    "everyday": "everyday",
    "everyday-objects": "everyday",
    "veci": "everyday",
    "predmety": "everyday",
}


def subjects_for(theme: str, count: int) -> list[Subject]:
    key = _ALIASES.get(slugify(theme))
    if key is None:
        base = theme.strip() or "object"
        return [
            (f"Obrázek {index}", f"a simple side-view {base}, variation {index}, one filled silhouette")
            for index in range(1, count + 1)
        ]
    catalog = _CATALOG[key]
    chosen: list[Subject] = []
    for index in range(count):
        name, prompt = catalog[index % len(catalog)]
        if index >= len(catalog):
            prompt = f"{prompt}, alternate pose {index // len(catalog) + 1}"
            name = f"{name} {index // len(catalog) + 1}"
        chosen.append((name, prompt))
    return chosen


def image_prompt(english: str) -> str:
    return (
        "A filled black silhouette of "
        f"{english}, for a children's connect-the-dots puzzle. "
        "One solid black shape, a single continuous outer contour, recognizable side view. "
        "No shading, no texture, no interior lines, no eyes, no text, no numbers, no dots, "
        "no background details. Pure white background. The shape is centered with a wide white margin."
    )
