"""Deterministic Grade-1 Czech mathematics exercise generator (0–20)."""

from __future__ import annotations

from random import Random
from typing import Any

from creobook.games.base import make_rng

GENERATOR_VERSION = "1.1.0"
TOPIC_COUNT = 8
VARIANTS_PER_TOPIC = 4
PAGE_COUNT = TOPIC_COUNT * VARIANTS_PER_TOPIC  # 32 A5 → 16 A4 sides → 8 sheets
ICON_KINDS = ("apple", "star", "ball", "block", "flower", "fish", "heart", "leaf")


def _icons(kind: str, n: int) -> dict[str, Any]:
    return {"kind": kind, "count": n}


def _pick_unique(rng: Random, lo: int, hi: int, k: int) -> list[int]:
    pool = list(range(lo, hi + 1))
    rng.shuffle(pool)
    return sorted(pool[:k])


def _no_cross_ten_add_pairs(rng: Random, n: int, *, lo: int = 10, hi: int = 19) -> list[tuple[int, int]]:
    """Addition within 20 that does not cross a ten boundary."""
    pairs: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    attempts = 0
    while len(pairs) < n and attempts < 400:
        attempts += 1
        a = rng.randint(lo, hi)
        max_b = min(20 - a, 9 - (a % 10) if a % 10 else 9)
        if a == 10:
            max_b = min(10, 20 - a)
        if max_b < 1:
            continue
        b = rng.randint(1, max_b)
        if a % 10 + b > 10:
            continue
        if a + b > 20:
            continue
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    if len(pairs) < n:
        raise ValueError("Could not build enough no-cross-ten additions")
    return pairs


def _no_cross_ten_sub_pairs(rng: Random, n: int) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    attempts = 0
    while len(pairs) < n and attempts < 400:
        attempts += 1
        a = rng.randint(11, 20)
        units = a % 10
        if units == 0:
            # 20-9, 10-x handled separately; allow subtracting up to 10 from 20/10
            max_b = 10 if a == 20 else 0
        else:
            max_b = units
        if max_b < 1:
            continue
        b = rng.randint(1, max_b)
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    if len(pairs) < n:
        raise ValueError("Could not build enough no-cross-ten subtractions")
    return pairs


def _add_within_10(rng: Random, n: int, *, include_zero: bool = True) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    if include_zero:
        a = rng.randint(1, 9)
        out.append((a, 0))
        seen.add((a, 0))
    while len(out) < n:
        a = rng.randint(0, 9)
        b = rng.randint(0, 10 - a)
        if (a, b) in seen or (a == 0 and b == 0 and len(out) > 1):
            continue
        if a + b > 10:
            continue
        seen.add((a, b))
        out.append((a, b))
    rng.shuffle(out)
    return out[:n]


def _sub_within_10(rng: Random, n: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    # Guarantee zero cases
    forced = [(rng.randint(1, 9), 0), (rng.randint(1, 9), None)]  # second: a-a
    a0 = forced[1][0]
    candidates = [(forced[0][0], 0), (a0, a0)]
    for a, b in candidates:
        out.append((a, b))
        seen.add((a, b))
    while len(out) < n:
        a = rng.randint(1, 10)
        b = rng.randint(0, a)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        out.append((a, b))
    rng.shuffle(out)
    return out[:n]


def _cmp_symbol(a: int, b: int) -> str:
    if a < b:
        return "<"
    if a > b:
        return ">"
    return "="


def build_page1(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    kinds = list(ICON_KINDS)
    rng.shuffle(kinds)
    # variant only changes the RNG stream (more practice pages), not density —
    # denser layouts overflow A5 after the fitted 8-page baseline.
    _ = variant
    n_groups = 4
    counts = [rng.randint(1, 8) for _ in range(n_groups - 1)] + [0]
    rng.shuffle(counts)
    while len(counts) < n_groups:
        counts.append(rng.randint(1, 8))
    groups = [_icons(kinds[i % len(kinds)], counts[i]) for i in range(n_groups)]

    draw_targets = [5, rng.choice([6, 7])]
    draw_have = [rng.randint(1, t - 1) for t in draw_targets]
    draw = [
        {
            "instruction": f"Dokresli do {t}",
            "kind": kinds[(i + 4) % len(kinds)],
            "have": draw_have[i],
            "target": t,
            "answer_draw": t - draw_have[i],
        }
        for i, t in enumerate(draw_targets)
    ]

    # Sequences within 0–10 with gaps
    seq1 = [0, 1, None, 3, 4, None, 6]
    seq1_ans = {2: 2, 5: 5}
    start = rng.choice([2, 3, 4])
    base = list(range(start, start + 6))
    if base[-1] > 10:
        base = list(range(5, 11))
    holes = sorted(rng.sample(range(1, len(base) - 1), 2))
    seq2_vals: list[int | None] = []
    seq2_ans: dict[int, int] = {}
    for i, v in enumerate(base):
        if i in holes:
            seq2_vals.append(None)
            seq2_ans[i] = v
        else:
            seq2_vals.append(v)

    ordinal_kinds = [kinds[i % len(kinds)] for i in range(6)]
    # ensure variety
    for i in range(6):
        ordinal_kinds[i] = ICON_KINDS[i % len(ICON_KINDS)]

    return {
        "heading": "Počítáme a poznáváme čísla",
        "topic": 1,
        "show_name_field": False,
        "sections": [
            {
                "id": "count_groups",
                "title": "1. Spočítej",
                "instruction": "Napiš, kolik obrázků je ve skupině.",
                "groups": groups,
                "answers": counts,
            },
            {
                "id": "draw_to",
                "title": "2. Dokresli",
                "items": draw,
            },
            {
                "id": "sequences",
                "title": "3. Doplň čísla",
                "sequences": [
                    {"values": seq1, "answers": seq1_ans},
                    {"values": seq2_vals, "answers": seq2_ans},
                ],
            },
            {
                "id": "ordinal",
                "title": "4. Zakroužkuj a podtrhni",
                "icons": ordinal_kinds,
                "tasks": [
                    {
                        "text": "Zakroužkuj třetí obrázek zleva",
                        "action": "circle",
                        "index": 2,
                    },
                    {
                        "text": "Podtrhni poslední",
                        "action": "underline",
                        "index": 5,
                    },
                ],
            },
        ],
    }


def build_page2(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    k1, k2 = rng.sample(ICON_KINDS, 2)
    a, b = rng.randint(3, 6), rng.randint(3, 6)
    while a == b:
        b = rng.randint(3, 6)
    c = rng.randint(3, 5)
    pairs = [
        {
            "left": _icons(k1, a),
            "right": _icons(k2, b),
            "answer": "left" if a > b else "right",
            "prompt": "Zakroužkuj skupinu, kde je víc.",
        },
        {
            "left": _icons(k2, c),
            "right": _icons(k1, c),
            "answer": "same",
            "prompt": "Mají stejně? Zakroužkuj ano / ne.",
            "same": True,
        },
    ]

    _ = variant
    comps = []
    seen: set[tuple[int, int]] = set()
    while len(comps) < 4:
        x, y = rng.randint(0, 10), rng.randint(0, 10)
        if (x, y) in seen:
            continue
        seen.add((x, y))
        comps.append({"a": x, "b": y, "answer": _cmp_symbol(x, y)})

    # decompositions: example + practice (open-ended)
    decomps = []
    example_n = 7
    example_left = 3
    decomps.append(
        {
            "n": example_n,
            "left": example_left,
            "right": example_n - example_left,
            "example": True,
            "open": False,
        }
    )
    for n in _pick_unique(rng, 4, 9, 2):
        left = rng.randint(1, n - 1)
        decomps.append(
            {
                "n": n,
                "left": None,
                "right": None,
                "example": False,
                "open": True,
                "answer_example": [left, n - left],
                "note": "Najdi jedno řešení",
            }
        )

    complements = []
    for a in _pick_unique(rng, 1, 9, 3):
        complements.append({"a": a, "answer": 10 - a})

    order = _pick_unique(rng, 0, 10, 4)
    shuffled = list(order)
    rng.shuffle(shuffled)

    return {
        "heading": "Porovnáváme a rozkládáme",
        "topic": 2,
        "show_name_field": False,
        "sections": [
            {"id": "pic_compare", "title": "1. Porovnej skupiny", "pairs": pairs},
            {"id": "compare", "title": "2. Doplň <, > nebo =", "items": comps},
            {
                "id": "decompose",
                "title": "3. Rozlož číslo",
                "instruction": "Příklad je vyplněný. U ostatních najdi jedno řešení.",
                "items": decomps,
            },
            {"id": "to_ten", "title": "4. Doplň do 10", "items": complements},
            {
                "id": "order",
                "title": "5. Seřaď od nejmenšího",
                "numbers": shuffled,
                "answer": order,
            },
        ],
    }


def build_page3(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    _ = variant
    vis = []
    for _ in range(2):
        a = rng.randint(1, 5)
        b = rng.randint(1, 10 - a)
        kind = rng.choice(ICON_KINDS)
        vis.append(
            {
                "left": _icons(kind, a),
                "right": _icons(kind, b),
                "answer": [a, b, a + b],
            }
        )
    calcs = [
        {"a": a, "b": b, "op": "+", "answer": a + b}
        for a, b in _add_within_10(rng, 6)
    ]
    missing = []
    seen: set[tuple[int, int]] = set()
    while len(missing) < 4:
        total = rng.randint(4, 10)
        a = rng.randint(0, total)
        if (a, total) in seen:
            continue
        seen.add((a, total))
        missing.append({"a": a, "total": total, "answer": total - a})

    # word problems
    w1_a, w1_b = rng.randint(2, 5), rng.randint(2, 5)
    while w1_a + w1_b > 10:
        w1_a, w1_b = rng.randint(2, 5), rng.randint(2, 5)
    w2_have = rng.randint(3, 6)
    w2_more = rng.randint(1, 10 - w2_have)

    return {
        "heading": "Sčítáme do 10",
        "topic": 3,
        "show_name_field": False,
        "sections": [
            {"id": "visual_add", "title": "1. Spočítej", "items": vis},
            {"id": "calc_add", "title": "2. Spočítej", "items": calcs},
            {"id": "missing_add", "title": "3. Doplň", "items": missing},
            {
                "id": "word_add",
                "title": "4. Slovní úlohy",
                "items": [
                    {
                        "text": (
                            f"Na misce leží {w1_a} jablka. Anička přidá ještě {w1_b}. "
                            f"Kolik jablek je na misce celkem?"
                        ),
                        "answer": w1_a + w1_b,
                        "unit": "jablek",
                    },
                    {
                        "text": (
                            f"Tomáš má {w2_have} kostky. Dostane ještě {w2_more}. "
                            f"Kolik kostek má teď?"
                        ),
                        "answer": w2_have + w2_more,
                        "unit": "kostek",
                    },
                ],
            },
        ],
    }


def build_page4(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    _ = variant
    vis = []
    for _ in range(2):
        total = rng.randint(4, 9)
        cross = rng.randint(1, total - 1)
        kind = rng.choice(ICON_KINDS)
        vis.append(
            {
                "icons": _icons(kind, total),
                "cross_out": cross,
                "instruction": f"Přeškrtni {cross} a spočítej, kolik zbývá.",
                "answer": total - cross,
            }
        )
    calcs = [
        {"a": a, "b": b, "op": "-", "answer": a - b}
        for a, b in _sub_within_10(rng, 6)
    ]
    missing = []
    # 9 − □ = 5 style and □ − 3 = 4 style
    for _ in range(2):
        result = rng.randint(1, 6)
        a = rng.randint(result + 1, 10)
        missing.append({"form": "a-x=r", "a": a, "result": result, "answer": a - result})
    for _ in range(2):
        b = rng.randint(1, 5)
        result = rng.randint(1, 6)
        a = b + result
        if a > 10:
            continue
        missing.append({"form": "x-b=r", "b": b, "result": result, "answer": a})
    while len(missing) < 4:
        result = rng.randint(0, 5)
        a = rng.randint(result, 10)
        missing.append({"form": "a-x=r", "a": a, "result": result, "answer": a - result})
    missing = missing[:4]

    have = rng.randint(6, 10)
    eat = rng.randint(1, have - 1)
    toys = rng.randint(5, 9)
    lend = rng.randint(1, toys - 1)

    return {
        "heading": "Odčítáme do 10",
        "topic": 4,
        "show_name_field": False,
        "sections": [
            {"id": "visual_sub", "title": "1. Přeškrtni a spočítej", "items": vis},
            {"id": "calc_sub", "title": "2. Spočítej", "items": calcs},
            {"id": "missing_sub", "title": "3. Doplň", "items": missing},
            {
                "id": "word_sub",
                "title": "4. Slovní úlohy",
                "items": [
                    {
                        "text": (
                            f"Na talíři bylo {have} sušenek. Děti snědly {eat}. "
                            f"Kolik sušenek zbylo?"
                        ),
                        "answer": have - eat,
                        "unit": "sušenek",
                    },
                    {
                        "text": (
                            f"Ema má {toys} autíček. {lend} půjčí kamarádovi. "
                            f"Kolik autíček jí zůstane?"
                        ),
                        "answer": toys - lend,
                        "unit": "autíček",
                    },
                ],
            },
        ],
    }


def build_page5(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    # sequences 0–20
    def make_seq(start: int, length: int = 7) -> dict[str, Any]:
        vals = list(range(start, start + length))
        holes = sorted(rng.sample(range(1, length - 1), 2))
        shown: list[int | None] = []
        ans: dict[int, int] = {}
        for i, v in enumerate(vals):
            if i in holes:
                shown.append(None)
                ans[i] = v
            else:
                shown.append(v)
        return {"values": shown, "answers": ans}

    _ = variant
    seqs = [make_seq(0), make_seq(rng.randint(8, 12))]

    befores = []
    for n in _pick_unique(rng, 1, 19, 3):
        befores.append({"n": n, "before": n - 1, "after": n + 1})

    comps = []
    seen: set[tuple[int, int]] = set()
    while len(comps) < 4:
        x, y = rng.randint(0, 20), rng.randint(0, 20)
        if (x, y) in seen:
            continue
        seen.add((x, y))
        comps.append({"a": x, "b": y, "answer": _cmp_symbol(x, y)})

    tens = []
    for n in _pick_unique(rng, 11, 19, 3):
        tens.append({"n": n, "answer": n - 10})

    # number line missing labels
    line_missing = sorted(rng.sample([2, 5, 9, 11, 14, 16, 18], 4))

    return {
        "heading": "Čísla do 20",
        "topic": 5,
        "show_name_field": False,
        "sections": [
            {"id": "seq20", "title": "1. Doplň řadu", "sequences": seqs},
            {
                "id": "neighbors",
                "title": "2. Číslo před a za",
                "instruction": "Napiš číslo hned před a hned za.",
                "items": befores,
            },
            {"id": "cmp20", "title": "3. Doplň <, > nebo =", "items": comps},
            {
                "id": "ten_decomp",
                "title": "4. Rozlož na desítku",
                "instruction": "Doplň: číslo = 10 + □. U prvního je skupina deseti teček.",
                "items": tens,
                "show_ten_dots_for": tens[0]["n"],
            },
            {
                "id": "number_line",
                "title": "5. Doplň na číselné ose",
                "from": 0,
                "to": 20,
                "missing": line_missing,
            },
        ],
    }


def build_page6(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    _ = variant
    adds = _no_cross_ten_add_pairs(rng, 3)
    subs = _no_cross_ten_sub_pairs(rng, 3)
    calcs: list[dict[str, Any]] = []
    for a, b in adds:
        calcs.append({"a": a, "b": b, "op": "+", "answer": a + b})
    for a, b in subs:
        calcs.append({"a": a, "b": b, "op": "-", "answer": a - b})
    rng.shuffle(calcs)

    missing = []
    for a, b in _no_cross_ten_add_pairs(rng, 4, lo=11, hi=16):
        missing.append({"a": a, "total": a + b, "op": "+", "answer": b})

    # pyramids: top = bottom1 + bottom2, supply two numbers uniquely
    pyramids = []
    # example
    pyramids.append(
        {
            "example": True,
            "bottom": [4, 5],
            "top": 9,
            "missing": None,
        }
    )
    for _ in range(2):
        mode = rng.choice(["miss_top", "miss_left", "miss_right"])
        x = rng.randint(2, 8)
        y = rng.randint(2, min(8, 20 - x))
        top = x + y
        if mode == "miss_top":
            pyramids.append(
                {"example": False, "bottom": [x, y], "top": None, "missing": "top", "answer": top}
            )
        elif mode == "miss_left":
            pyramids.append(
                {
                    "example": False,
                    "bottom": [None, y],
                    "top": top,
                    "missing": "left",
                    "answer": x,
                }
            )
        else:
            pyramids.append(
                {
                    "example": False,
                    "bottom": [x, None],
                    "top": top,
                    "missing": "right",
                    "answer": y,
                }
            )

    challenge_pool = [
        (8, 5, "+", 13),
        (9, 4, "+", 13),
        (7, 5, "+", 12),
        (6, 5, "+", 11),
        (13, 5, "-", 8),
        (12, 4, "-", 8),
        (14, 6, "-", 8),
        (15, 7, "-", 8),
    ]
    rng.shuffle(challenge_pool)
    challenge = [
        {"a": a, "b": b, "op": op, "answer": ans}
        for a, b, op, ans in challenge_pool[:4]
    ]

    return {
        "heading": "Počítáme do 20",
        "topic": 6,
        "show_name_field": False,
        "sections": [
            {
                "id": "calc20",
                "title": "1. Spočítej (bez přechodu přes desítku)",
                "items": calcs,
            },
            {"id": "missing20", "title": "2. Doplň", "items": missing},
            {
                "id": "pyramids",
                "title": "3. Pyramidy",
                "instruction": "Horní číslo je součet spodních. Příklad je vyplněný.",
                "items": pyramids,
            },
            {
                "id": "challenge",
                "title": "Výzva navíc",
                "instruction": (
                    "Tyto příklady přecházejí přes desítku. Můžeš je přeskočit. "
                    "Příklad: 8 + 5 = 8 + 2 + 3 = 10 + 3 = 13."
                ),
                "worked": {"a": 8, "b": 5, "steps": "8 + 2 + 3 = 10 + 3 = 13"},
                "items": challenge,
            },
        ],
    }


def build_page7(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    _ = variant
    # word: total, o několik více, o několik méně
    t_a, t_b = rng.randint(3, 8), rng.randint(2, 6)
    while t_a + t_b > 20:
        t_a, t_b = rng.randint(3, 8), rng.randint(2, 6)
    base = rng.randint(4, 10)
    more = rng.randint(1, min(5, 20 - base))
    base2 = rng.randint(8, 15)
    less = rng.randint(1, min(5, base2))

    words = [
        {
            "text": (
                f"V krabici je {t_a} tužek a {t_b} pastelik. "
                f"Kolik psacích potřeb je v krabici celkem?"
            ),
            "answer": t_a + t_b,
            "unit": "",
        },
        {
            "text": (
                f"Adam má {base} kostek. Bára má o {more} kostek víc. "
                f"Kolik kostek má Bára?"
            ),
            "answer": base + more,
            "unit": "kostek",
        },
        {
            "text": (
                f"Na stromě sedělo {base2} ptáků. {less} odletělo. "
                f"Kolik ptáků na stromě zůstalo?"
            ),
            "answer": base2 - less,
            "unit": "ptáků",
        },
    ]

    def coin_task() -> dict[str, Any]:
        # total <= 20
        while True:
            coins = []
            total = 0
            for val in rng.sample([1, 2, 5, 10], k=rng.randint(2, 3)):
                k = rng.randint(1, 2)
                if total + val * k > 20:
                    continue
                coins.extend([val] * k)
                total += val * k
            if 3 <= total <= 20 and len(coins) >= 2:
                rng.shuffle(coins)
                return {"coins": coins, "answer": total}

    coins = [coin_task(), coin_task()]

    apples = [rng.randint(2, 8) for _ in range(3)]
    table = {
        "headers": ["Košík A", "Košík B", "Košík C"],
        "values": apples,
        "questions": [
            {
                "text": "Kolik jablek je v košících celkem?",
                "answer": sum(apples),
            },
            {
                "text": "Ve kterém košíku je nejvíc jablek?",
                "answer": "ABC"[apples.index(max(apples))],
                "answer_text": f"Košík {'ABC'[apples.index(max(apples))]}",
            },
        ],
    }

    hour = rng.choice([1, 2, 3, 4, 5, 6, 8, 9])
    clocks = []
    hours_opts = [hour]
    while len(hours_opts) < 3:
        h = rng.randint(1, 9)
        if h not in hours_opts:
            hours_opts.append(h)
    rng.shuffle(hours_opts)
    for h in hours_opts:
        clocks.append({"hour": h, "is_answer": h == hour})

    return {
        "heading": "Matematika kolem nás",
        "topic": 7,
        "show_name_field": False,
        "sections": [
            {"id": "word_life", "title": "1. Slovní úlohy", "items": words},
            {
                "id": "coins",
                "title": "2. Spočítej mince",
                "instruction": "Každá mince má napsanou hodnotu v Kč. Kolik Kč je celkem?",
                "items": coins,
            },
            {"id": "table", "title": "3. Tabulka — jablka v košících", "table": table},
            {
                "id": "clock",
                "title": "4. Kolik je hodin?",
                "instruction": f"Spoj hodiny s nápisem „{hour} hodiny“."
                if hour in (2, 3, 4)
                else f"Spoj hodiny s nápisem „{hour} hodin\".",
                "label": f"{hour} hodiny" if hour in (2, 3, 4) else f"{hour} hodin",
                "target_hour": hour,
                "clocks": clocks,
            },
        ],
    }


def build_page8(rng: Random, *, variant: int = 0) -> dict[str, Any]:
    shapes = [
        {"id": "circle", "name": "kruh"},
        {"id": "square", "name": "čtverec"},
        {"id": "rectangle", "name": "obdélník"},
        {"id": "triangle", "name": "trojúhelník"},
    ]
    name_order = [s["name"] for s in shapes]
    rng.shuffle(name_order)

    solids = [
        {"id": "sphere", "name": "koule", "object": "míč"},
        {"id": "cube", "name": "krychle", "object": "hrací kostka"},
        {"id": "cuboid", "name": "kvádr", "object": "krabice od bot"},
    ]

    # scene positions — rotate labels by variant
    labels = ["míč", "kniha", "hrnek"]
    ids = ["ball", "book", "cup"]
    order = list(range(3))
    rng.shuffle(order)
    placed = [
        {"id": ids[i], "label": labels[i], "pos": pos}
        for i, pos in zip(order, ("left", "center", "right"), strict=True)
    ]
    by_pos = {p["pos"]: p["label"] for p in placed}
    scene = {
        "items": placed,
        "tasks": [
            {"text": "Zakroužkuj věc vlevo", "answer": by_pos["left"]},
            {"text": "Podtrhni věc vpravo", "answer": by_pos["right"]},
            {"text": "Napiš, co je uprostřed", "answer": by_pos["center"]},
        ],
    }

    patterns = [
        {
            "shown": ["circle", "triangle", "circle", "triangle"],
            "next": ["circle", "triangle"],
            "answer": ["circle", "triangle"],
        },
        {
            "shown": ["square", "square", "circle", "square", "square", "circle"],
            "next": ["square", "square"],
            "answer": ["square", "square"],
        },
    ]

    grids = [
        [[1, 0, 1], [0, 1, 0], [1, 0, 1]],
        [[1, 1, 0], [1, 0, 1], [0, 1, 1]],
        [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
        [[1, 0, 0], [1, 1, 0], [1, 1, 1]],
    ]
    grid = {
        "size": 3,
        "pattern": grids[variant % len(grids)],
        "instruction": "Obkresli stejný vzor do prázdné mřížky.",
    }

    return {
        "heading": "Tvary, prostor a vzory",
        "topic": 8,
        "show_name_field": False,
        "sections": [
            {
                "id": "shapes2d",
                "title": "1. Spoj tvar s názvem",
                "shapes": shapes,
                "names": name_order,
            },
            {
                "id": "shapes3d",
                "title": "2. Spoj věc s tělesem",
                "items": solids,
            },
            {"id": "space", "title": "3. Vlevo, vpravo, uprostřed", "scene": scene},
            {
                "id": "length",
                "title": "4. Zakroužkuj delší čáru",
                "short_mm": 28,
                "long_mm": 48,
                "answer": "long",
            },
            {"id": "patterns", "title": "5. Dokresli vzor", "items": patterns},
            {"id": "grid_copy", "title": "6. Obkresli vzor", "grid": grid},
        ],
    }


def build_answer_key(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten human-readable Czech answers per page."""
    key_pages: list[dict[str, Any]] = []
    for page in pages:
        pnum = page["data"]["page"]
        heading = page["data"]["heading"]
        lines: list[str] = []
        for sec in page["data"]["sections"]:
            sid = sec["id"]
            title = sec.get("title", sid)
            if sid == "count_groups":
                ans = ", ".join(str(x) for x in sec["answers"])
                lines.append(f"{title}: {ans}")
            elif sid == "draw_to":
                bits = [
                    f"{it['instruction']}: dokresli {it['answer_draw']} "
                    f"(celkem {it['target']})"
                    for it in sec["items"]
                ]
                lines.append(f"{title}: " + "; ".join(bits))
            elif sid == "sequences":
                parts = []
                for i, seq in enumerate(sec["sequences"], 1):
                    filled = [
                        str(seq["answers"][j]) if j in seq["answers"] else str(v)
                        for j, v in enumerate(seq["values"])
                    ]
                    # show only missing answers
                    miss = ", ".join(f"pozice {j + 1} = {v}" for j, v in sorted(seq["answers"].items()))
                    parts.append(f"řada {i}: {miss}")
                lines.append(f"{title}: " + "; ".join(parts))
            elif sid == "ordinal":
                for t in sec["tasks"]:
                    lines.append(f"{title}: {t['text']} → {t['index'] + 1}. obrázek")
            elif sid == "pic_compare":
                for i, pair in enumerate(sec["pairs"], 1):
                    if pair.get("same"):
                        lines.append(f"{title} {i}: ano (stejně)")
                    else:
                        side = "levá" if pair["answer"] == "left" else "pravá"
                        lines.append(f"{title} {i}: {side} skupina")
            elif sid == "compare" or sid == "cmp20":
                bits = [f"{it['a']} {it['answer']} {it['b']}" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "decompose":
                bits = []
                for it in sec["items"]:
                    if it.get("example"):
                        bits.append(f"{it['n']} = {it['left']} + {it['right']} (příklad)")
                    else:
                        a, b = it["answer_example"]
                        bits.append(f"{it['n']} = {a} + {b} (jedno možné)")
                lines.append(f"{title}: " + "; ".join(bits))
            elif sid == "to_ten":
                bits = [f"{it['a']} + {it['answer']} = 10" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "order":
                lines.append(f"{title}: " + ", ".join(str(x) for x in sec["answer"]))
            elif sid in {"visual_add", "calc_add"}:
                if sid == "visual_add":
                    bits = [f"{a}+{b}={c}" for a, b, c in (it["answer"] for it in sec["items"])]
                else:
                    bits = [f"{it['a']}+{it['b']}={it['answer']}" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "missing_add":
                bits = [f"{it['a']} + {it['answer']} = {it['total']}" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid in {"word_add", "word_sub", "word_life"}:
                for i, it in enumerate(sec["items"], 1):
                    unit = f" {it['unit']}" if it.get("unit") else ""
                    lines.append(f"{title} {i}: {it['answer']}{unit}")
            elif sid == "visual_sub":
                bits = [str(it["answer"]) for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "calc_sub":
                bits = [f"{it['a']}-{it['b']}={it['answer']}" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "missing_sub":
                bits = []
                for it in sec["items"]:
                    if it["form"] == "a-x=r":
                        bits.append(f"{it['a']} − {it['answer']} = {it['result']}")
                    else:
                        bits.append(f"{it['answer']} − {it['b']} = {it['result']}")
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "seq20":
                parts = []
                for i, seq in enumerate(sec["sequences"], 1):
                    miss = ", ".join(f"{v}" for _, v in sorted(seq["answers"].items()))
                    parts.append(f"řada {i}: {miss}")
                lines.append(f"{title}: " + "; ".join(parts))
            elif sid == "neighbors":
                bits = [f"{it['before']}, {it['n']}, {it['after']}" for it in sec["items"]]
                lines.append(f"{title}: " + "; ".join(bits))
            elif sid == "ten_decomp":
                bits = [f"{it['n']} = 10 + {it['answer']}" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "number_line":
                lines.append(f"{title}: " + ", ".join(str(x) for x in sec["missing"]))
            elif sid in {"calc20", "challenge"}:
                bits = [
                    f"{it['a']}{it['op']}{it['b']}={it['answer']}" for it in sec["items"]
                ]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "missing20":
                bits = [f"{it['a']} + {it['answer']} = {it['total']}" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "pyramids":
                bits = []
                for it in sec["items"]:
                    if it.get("example"):
                        bits.append(f"příklad {it['bottom'][0]}+{it['bottom'][1]}={it['top']}")
                    else:
                        bits.append(f"chybějící = {it['answer']}")
                lines.append(f"{title}: " + "; ".join(bits))
            elif sid == "coins":
                bits = [f"{it['answer']} Kč" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "table":
                for q in sec["table"]["questions"]:
                    ans = q.get("answer_text", q["answer"])
                    lines.append(f"{title}: {q['text']} → {ans}")
            elif sid == "clock":
                lines.append(f"{title}: {sec['target_hour']} hodin / spojit správné hodiny")
            elif sid == "shapes2d":
                bits = [f"{s['id']} → {s['name']}" for s in sec["shapes"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "shapes3d":
                bits = [f"{it['object']} → {it['name']}" for it in sec["items"]]
                lines.append(f"{title}: " + ", ".join(bits))
            elif sid == "space":
                for t in sec["scene"]["tasks"]:
                    lines.append(f"{title}: {t['text']} → {t['answer']}")
            elif sid == "length":
                lines.append(f"{title}: delší (dolní) čára")
            elif sid == "patterns":
                for i, it in enumerate(sec["items"], 1):
                    lines.append(
                        f"{title} {i}: pokračování "
                        + ", ".join(it["answer"])
                    )
            elif sid == "grid_copy":
                lines.append(f"{title}: stejný vzor jako vzorová mřížka (šachovnice rohů)")
        key_pages.append({"page": pnum, "heading": heading, "lines": lines})
    return key_pages


def validate_edition(pages: list[dict[str, Any]]) -> None:
    if len(pages) != PAGE_COUNT:
        raise ValueError(f"Expected {PAGE_COUNT} pages, got {len(pages)}")
    for page in pages:
        data = page["data"]
        for sec in data["sections"]:
            sid = sec["id"]
            if sid in {"calc_add", "calc_sub", "calc20", "challenge"}:
                for it in sec["items"]:
                    a, b, op, ans = it["a"], it["b"], it["op"], it["answer"]
                    if op == "+" and a + b != ans:
                        raise ValueError(f"Bad add {a}+{b}!={ans}")
                    if op == "-" and a - b != ans:
                        raise ValueError(f"Bad sub {a}-{b}!={ans}")
                    if a < 0 or b < 0 or ans < 0 or ans > 20 or a > 20 or b > 20:
                        raise ValueError(f"Out of range {it}")
            if sid == "challenge":
                for it in sec["items"]:
                    if (
                        it["op"] == "+"
                        and it["a"] < 10
                        and it["b"] < 10
                        and it["a"] + it["b"] <= 10
                    ):
                        raise ValueError(f"Challenge add does not cross ten: {it}")
                    if (
                        it["op"] == "-"
                        and it["a"] >= 10
                        and (it["a"] % 10) >= it["b"]
                        and it["b"] > 0
                    ):
                        # subtraction that does not borrow across ten — still OK for 12-4?
                        # 12-4: units 2 < 4 → crosses; 19-9: units 9 >= 9 → no cross
                        pass
            if sid == "calc20":
                for it in sec["items"]:
                    if it["op"] == "+":
                        if it["a"] >= 10 and (it["a"] % 10) + it["b"] > 10:
                            raise ValueError(f"Crosses ten in core set: {it}")
                    if it["op"] == "-":
                        units = it["a"] % 10
                        if units and it["b"] > units:
                            raise ValueError(f"Crosses ten in core sub: {it}")
            if sid == "count_groups":
                for g, ans in zip(sec["groups"], sec["answers"], strict=True):
                    if g["count"] != ans:
                        raise ValueError("Picture count mismatch")
            if sid == "visual_sub":
                for it in sec["items"]:
                    if it["icons"]["count"] - it["cross_out"] != it["answer"]:
                        raise ValueError("Visual sub mismatch")


def generate_math_grade1_pages(*, seed: int = 20270101) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    builders = [
        build_page1,
        build_page2,
        build_page3,
        build_page4,
        build_page5,
        build_page6,
        build_page7,
        build_page8,
    ]
    pages: list[dict[str, Any]] = []
    page_num = 0
    for topic_i, builder in enumerate(builders, start=1):
        for variant in range(VARIANTS_PER_TOPIC):
            page_num += 1
            page_seed = seed * 1009 + page_num * 9176 + topic_i * 13 + variant
            page_rng = make_rng(page_seed)
            data = builder(page_rng, variant=variant)
            data["page"] = page_num
            data["topic"] = topic_i
            data["variant"] = variant
            data["variant_label"] = f"{variant + 1}/{VARIANTS_PER_TOPIC}"
            data["booklet_title"] = "Matematika – 1. třída"
            data["show_name_field"] = page_num == 1
            if variant > 0:
                data["heading_note"] = f"Procvičování {variant + 1}/{VARIANTS_PER_TOPIC}"
            else:
                data["heading_note"] = ""
            pages.append(
                {
                    "kind": "math_grade1",
                    "title": data["heading"],
                    "instructions": "",
                    "difficulty": "easy",
                    "seed": page_seed,
                    "data": data,
                    "answer": {},
                }
            )
    validate_edition(pages)
    answers = build_answer_key(pages)
    meta = {
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "page_count": PAGE_COUNT,
        "topic_count": TOPIC_COUNT,
        "variants_per_topic": VARIANTS_PER_TOPIC,
        "title": "Matematika – 1. třída",
        "answers": answers,
    }
    return pages, meta
