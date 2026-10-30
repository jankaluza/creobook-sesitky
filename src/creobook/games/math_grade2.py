"""Deterministic Grade-2 Czech mathematics booklet (numbers 0–100).

Twenty A5 exercise pages (ten A4 sides after imposition). Each exercise type
from the eight-page edition appears twice. Answers are computed from the same
operands that are printed; nothing keeps a second, hand-written answer list.
"""

from __future__ import annotations

from random import Random
from typing import Any, Callable

from creobook.games.base import make_rng

GENERATOR_VERSION = "1.1.0"
PAGE_COUNT = 20
# Two A5 pages for each topic, plus one extra page for the four topics that
# need more writing or drawing room. 20 A5 pages → 10 A4 sides → 5 sheets.
PAGE_TOPICS = (
    1, 1,
    2, 2,
    3, 3,
    4, 4, 4,
    5, 5, 5,
    6, 6, 6,
    7, 7,
    8, 8, 8,
)
BOOKLET_TITLE = "Matematika – 2. třída"

HEADINGS = (
    "Přes desítku do dvaceti",
    "Čísla do sta",
    "Sčítání a odčítání do sta",
    "Počítáme v příbězích",
    "Objevujeme násobení",
    "Dělíme a hledáme souvislosti",
    "Peníze, čas a tabulky",
    "Geometrie a měření",
)

# Factors drilled in the main blocks. Tables 6–9 stay in Výzva navíc.
CORE_FACTORS = (2, 3, 4, 5, 10)
CHALLENGE_FACTORS = (6, 7, 8, 9)
COIN_VALUES = (1, 2, 5, 10, 20, 50)
ICON_KINDS = ("apple", "star", "ball", "block", "flower", "leaf")

# Hand lengths as a fraction of the clock radius. The minute hand is longer.
HOUR_HAND_RATIO = 0.46
MINUTE_HAND_RATIO = 0.74

UNIT_IN_CM = {"mm": 0.1, "cm": 1, "dm": 10, "m": 100}


def _in_range(n: int, *, lo: int = 0, hi: int = 100) -> None:
    if not isinstance(n, int) or isinstance(n, bool) or n < lo or n > hi:
        raise ValueError(f"Value {n!r} outside {lo}–{hi}")


def _result(a: int, op: str, b: int) -> int:
    if op == "+":
        value = a + b
    elif op in ("-", "−"):
        value = a - b
    elif op == "·":
        value = a * b
    elif op == ":":
        if b == 0 or a % b != 0:
            raise ValueError(f"Illegal division {a}:{b}")
        value = a // b
    else:
        raise ValueError(f"Unknown operator {op!r}")
    _in_range(a)
    _in_range(b)
    _in_range(value)
    return value


def _calc(a: int, op: str, b: int) -> dict[str, Any]:
    return {"a": a, "b": b, "op": op, "answer": _result(a, op, b)}


def _cmp_symbol(a: int, b: int) -> str:
    if a < b:
        return "<"
    if a > b:
        return ">"
    return "="


def _round_to_tens(n: int) -> int:
    _in_range(n)
    units = n % 10
    base = n - units
    rounded = base + 10 if units >= 5 else base
    _in_range(rounded)
    return rounded


def _cs_tens(n: int) -> str:
    if n == 1:
        return "1 desítka"
    if 2 <= n <= 4:
        return f"{n} desítky"
    return f"{n} desítek"


def _cs_ones(n: int) -> str:
    if n == 1:
        return "1 jednotka"
    if 2 <= n <= 4:
        return f"{n} jednotky"
    return f"{n} jednotek"


def _sample(rng: Random, pool: list[Any], k: int) -> list[Any]:
    if len(pool) < k:
        raise ValueError(f"Need {k} items, pool has {len(pool)}")
    picks = list(pool)
    rng.shuffle(picks)
    return picks[:k]


def _cross_add_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(2, 10) for b in range(2, 10) if 11 <= a + b <= 20]


def _cross_sub_pairs() -> list[tuple[int, int]]:
    pairs = []
    for a in range(11, 21):
        units = a % 10
        for b in range(1, 10):
            if b > units and a - b >= 0:
                pairs.append((a, b))
    return pairs


def _split_single(a: int, b: int) -> tuple[int, int]:
    """Split b across the ten: a + b = a + bridge + rest, a + bridge = 10."""
    if not (1 <= a <= 9 and 1 <= b <= 9 and a + b >= 11):
        raise ValueError(f"Not a single-digit crossing add: {a}+{b}")
    bridge = 10 - a
    rest = b - bridge
    if rest < 1 or bridge < 1:
        raise ValueError(f"Degenerate split {a}+{b}")
    return bridge, rest


def _split_two_digit(a: int, b: int) -> tuple[int, int, int]:
    """a + b = a + bridge + rest = next_ten + rest, with a two-digit and b < 10."""
    units = a % 10
    if units == 0 or not (1 <= b <= 9) or units + b < 11 or a + b > 100:
        raise ValueError(f"Not a two-digit crossing add: {a}+{b}")
    bridge = 10 - units
    rest = b - bridge
    ten = a + bridge
    if rest < 1 or ten % 10 != 0 or ten + rest != a + b:
        raise ValueError(f"Bad split {a}+{b}")
    return bridge, rest, ten


def _seq(start: int, step: int, length: int, holes: list[int]) -> dict[str, Any]:
    values_full = [start + i * step for i in range(length)]
    for v in values_full:
        _in_range(v)
    shown: list[int | None] = []
    answers: list[dict[str, int]] = []
    for i, v in enumerate(values_full):
        if i in holes:
            shown.append(None)
            answers.append({"index": i, "value": v})
        else:
            shown.append(v)
    return {"values": shown, "answers": answers, "step": step}


def _clock_angles(hour: int, minute: int) -> dict[str, float]:
    """Clockwise-from-12 degrees, plus Typst line angles.

    In Typst, 0° points right and positive angles go downward (hour 6 is 90°).
    Twelve o'clock is therefore −90°.
    """
    if hour < 1 or hour > 12 or minute not in (0, 30):
        raise ValueError(f"Unsupported clock {hour}:{minute}")
    minute_cw = float(minute * 6)
    hour_cw = (hour % 12) * 30.0 + minute * 0.5
    return {
        "minute_cw": minute_cw,
        "hour_cw": hour_cw,
        "minute_deg": minute_cw - 90.0,
        "hour_deg": hour_cw - 90.0,
    }


def _buy_phrase(name: str, count: int) -> str:
    forms = {
        ("sešit", 1): "1 sešit",
        ("sešit", 2): "2 sešity",
        ("tužka", 1): "1 tužku",
        ("tužka", 2): "2 tužky",
        ("jablko", 1): "1 jablko",
        ("jablko", 2): "2 jablka",
    }
    try:
        return forms[(name, count)]
    except KeyError as exc:
        raise ValueError(f"No phrase for {count}× {name}") from exc


def build_page1(rng: Random) -> dict[str, Any]:
    complements = [
        {"a": a, "answer": 10 - a} for a in _sample(rng, list(range(1, 10)), 4)
    ]

    adds = _sample(rng, _cross_add_pairs(), 7)
    example_pair, practice, mixed_adds = adds[0], adds[1:3], adds[3:7]
    bridge, rest = _split_single(*example_pair)
    example = {
        "a": example_pair[0],
        "b": example_pair[1],
        "bridge": bridge,
        "rest": rest,
        "answer": example_pair[0] + example_pair[1],
    }
    practice_items = []
    for a, b in practice:
        br, rs = _split_single(a, b)
        practice_items.append(
            {"a": a, "b": b, "bridge": br, "rest": rs, "answer": a + b}
        )

    subs = _sample(rng, _cross_sub_pairs(), 4)
    mixed = [_calc(a, "+", b) for a, b in mixed_adds] + [_calc(a, "−", b) for a, b in subs]
    rng.shuffle(mixed)

    missing = _missing_within_20(rng)

    if rng.random() < 0.5:
        a = rng.randint(5, 9)
        b = rng.randint(max(5, 11 - a), min(9, 20 - a))
        word = {
            "kind": "total",
            "a": a,
            "b": b,
            "answer": a + b,
            "unit": "ptáků",
            "text": (
                f"Na větvi sedělo {a} ptáků. Přilétlo {b} ptáků. "
                f"Kolik ptáků je na větvi teď?"
            ),
        }
    else:
        while True:
            a = rng.randint(12, 18)
            options = [b for b in range(5, 10) if b > a % 10 and a - b >= 1]
            if options:
                b = rng.choice(options)
                break
        word = {
            "kind": "left",
            "a": a,
            "b": b,
            "answer": a - b,
            "unit": "třešní",
            "text": (
                f"Na talíři bylo {a} třešní. Snědlo se jich {b}. "
                f"Kolik třešní zbylo?"
            ),
        }

    return {
        "heading": HEADINGS[0],
        "sections": [
            {
                "id": "complements",
                "title": "1. Doplň do deseti",
                "items": complements,
            },
            {
                "id": "decompose",
                "title": "2. Rozklad přes desítku",
                "instruction": "Nejprve doplň do deseti, potom přičti zbytek.",
                "example": example,
                "items": practice_items,
            },
            {"id": "mixed20", "title": "3. Spočítej", "items": mixed},
            {"id": "missing20", "title": "4. Doplň chybějící číslo", "items": missing},
            {"id": "word20", "title": "5. Slovní úloha", "item": word},
        ],
    }


def _missing_within_20(rng: Random) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    adds = _sample(rng, _cross_add_pairs(), 2)
    a, b = adds[0]
    items.append({"form": "x+b", "b": b, "total": a + b, "answer": a})
    a, b = adds[1]
    items.append({"form": "a+x", "a": a, "total": a + b, "answer": b})

    subs = _sample(rng, _cross_sub_pairs(), 2)
    a, b = subs[0]
    items.append({"form": "a-x", "a": a, "result": a - b, "answer": b})
    a, b = subs[1]
    items.append({"form": "x-b", "b": b, "result": a - b, "answer": a})
    rng.shuffle(items)
    return items


def build_page2(rng: Random) -> dict[str, Any]:
    n1 = rng.choice([n for n in range(21, 100) if n % 10 != 0])
    n2 = rng.choice([n for n in range(21, 100) if n % 10 != 0 and n != n1])
    tens_count = rng.randint(2, 9)
    place = [
        {
            "kind": "split_ones",
            "n": n1,
            "tens": (n1 // 10) * 10,
            "answer": n1 % 10,
        },
        {
            "kind": "split_tens",
            "n": n2,
            "ones": n2 % 10,
            "answer": (n2 // 10) * 10,
        },
        {
            "kind": "words",
            "tens_count": tens_count,
            "ones_count": 0,
            "text": f"{_cs_tens(tens_count)} a {_cs_ones(0)}",
            "answer": tens_count * 10,
        },
        {
            "kind": "hundred",
            "tens_count": 10,
            "ones_count": 0,
            "answer": 10,
        },
    ]

    boundary = rng.choice([30, 40, 50, 60, 70, 80])
    ones_holes = sorted(_sample(rng, [1, 2, 3, 4, 5], 2))
    ones = _seq(boundary - 2, 1, 7, ones_holes)
    tens_holes = sorted(_sample(rng, [1, 2, 3, 4, 5], 2))
    tens = _seq(50, 10, 6, tens_holes)

    equal_n = rng.choice([20, 40, 50, 60, 70, 80])
    small = rng.randint(8, 35)
    large = rng.randint(small + 5, 96)
    comps = [
        {"a": equal_n, "b": equal_n, "answer": "="},
        {"a": 100, "b": rng.choice([49, 70, 90, 99]), "answer": ">"},
        {"a": small, "b": large, "answer": "<"},
        {"a": rng.randint(60, 95), "b": rng.randint(10, 40), "answer": ">"},
        {"a": rng.choice([10, 30, 40]), "b": rng.randint(55, 90), "answer": "<"},
        {"a": rng.randint(51, 88), "b": rng.randint(12, 45), "answer": ">"},
    ]
    for it in comps:
        it["answer"] = _cmp_symbol(it["a"], it["b"])
        _in_range(it["a"])
        _in_range(it["b"])
    rng.shuffle(comps)

    order_nums = [100, rng.choice([10, 20, 30, 40, 60, 70, 90])]
    while len(order_nums) < 5:
        n = rng.randint(0, 99)
        if n not in order_nums:
            order_nums.append(n)
    shown_order = list(order_nums)
    rng.shuffle(shown_order)
    if shown_order == sorted(order_nums):
        shown_order[0], shown_order[1] = shown_order[1], shown_order[0]

    start = rng.choice([20, 30, 40, 50, 60, 70, 80, 90])
    missing_line = _spaced(rng, start + 1, start + 9, 3, gap=2)

    example_n = rng.choice([22, 31, 42, 53, 64])
    down_n = rng.choice([n for n in range(21, 98) if 1 <= n % 10 <= 4 and n != example_n])
    up_n = rng.choice([n for n in range(25, 99) if 5 <= n % 10 <= 9])

    return {
        "heading": HEADINGS[1],
        "sections": [
            {"id": "place_value", "title": "1. Desítky a jednotky", "items": place},
            {
                "id": "sequences",
                "title": "2. Doplň řady",
                "sequences": [
                    {"label": "Po jedné", **ones},
                    {"label": "Po desítkách", **tens},
                ],
            },
            {"id": "compare", "title": "3. Doplň <, > nebo =", "items": comps},
            {
                "id": "order",
                "title": "4. Seřaď od nejmenšího",
                "numbers": shown_order,
                "answer": sorted(order_nums),
            },
            {
                "id": "number_line",
                "title": "5. Doplň číselnou osu",
                "start": start,
                "end": start + 10,
                "missing": missing_line,
            },
            {
                "id": "round",
                "title": "6. Zaokrouhli na desítky",
                "rule": "Jednotky 0–4 zaokrouhli dolů, 5–9 nahoru.",
                "example": {"n": example_n, "answer": _round_to_tens(example_n)},
                "items": [
                    {"n": down_n, "answer": _round_to_tens(down_n)},
                    {"n": up_n, "answer": _round_to_tens(up_n)},
                ],
            },
        ],
    }


def _spaced(rng: Random, lo: int, hi: int, k: int, *, gap: int) -> list[int]:
    pool = list(range(lo, hi + 1))
    rng.shuffle(pool)
    chosen: list[int] = []
    for n in pool:
        if all(abs(n - c) >= gap for c in chosen):
            chosen.append(n)
        if len(chosen) == k:
            break
    if len(chosen) < k:
        raise ValueError("Could not space number-line gaps")
    return sorted(chosen)


def _tens_add(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(80):
        a = rng.choice([10, 20, 30, 40, 50, 60, 70, 80])
        b = rng.choice([10, 20, 30, 40, 50])
        if a + b <= 100 and (a, b) not in banned:
            return a, b
    raise ValueError("tens add")


def _tens_sub(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(80):
        a = rng.choice([30, 40, 50, 60, 70, 80, 90, 100])
        b = rng.choice([10, 20, 30, 40, 50])
        if b < a and (a, b) not in banned:
            return a, b
    raise ValueError("tens sub")


def _nocross_add(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(80):
        a = rng.randint(21, 89)
        room = 9 - (a % 10)
        if room < 1:
            continue
        b = rng.randint(1, room)
        if (a, b) not in banned and a + b <= 100:
            return a, b
    raise ValueError("no-cross add")


def _nocross_sub(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(80):
        a = rng.randint(21, 99)
        units = a % 10
        if units < 1:
            continue
        b = rng.randint(1, units)
        if (a, b) not in banned:
            return a, b
    raise ValueError("no-cross sub")


def _cross_add_100(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(100):
        a = rng.randint(21, 89)
        units = a % 10
        if units == 0:
            continue
        lo = 11 - units
        if lo > 9:
            continue
        b = rng.randint(lo, 9)
        if a + b <= 100 and (a, b) not in banned:
            _split_two_digit(a, b)
            return a, b
    raise ValueError("cross add 100")


def _cross_sub_100(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(80):
        a = rng.randint(21, 99)
        units = a % 10
        if units >= 9:
            continue
        b = rng.randint(units + 1, 9)
        if (a, b) not in banned:
            return a, b
    raise ValueError("cross sub 100")


def _plus_tens(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(80):
        a = rng.randint(12, 79)
        if a % 10 == 0:
            continue
        b = rng.choice([10, 20, 30, 40])
        if a + b <= 100 and (a, b) not in banned:
            return a, b
    raise ValueError("plus tens")


def _minus_tens(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(80):
        a = rng.randint(31, 99)
        if a % 10 == 0:
            continue
        options = [t for t in (10, 20, 30, 40, 50) if t < a and (a - t) % 10 == a % 10]
        if not options:
            continue
        b = rng.choice(options)
        if (a, b) not in banned:
            return a, b
    raise ValueError("minus tens")


def _two_add(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(120):
        a = rng.randint(12, 70)
        b = rng.randint(12, 70)
        if a % 10 == 0 and b % 10 == 0:
            continue
        if (a % 10) + (b % 10) > 9 or a + b > 100:
            continue
        if (a, b) not in banned:
            return a, b
    raise ValueError("two-digit add")


def _two_sub(rng: Random, banned: set[tuple[int, int]]) -> tuple[int, int]:
    for _ in range(120):
        a = rng.randint(32, 99)
        b = rng.randint(12, a - 10)
        if a % 10 == 0 and b % 10 == 0:
            continue
        if a % 10 < b % 10:
            continue
        if b > 99 or (a, b) in banned:
            continue
        return a, b
    raise ValueError("two-digit sub")


def build_page3(rng: Random) -> dict[str, Any]:
    ex_a, ex_b = _cross_add_100(rng, set())
    bridge, rest, ten = _split_two_digit(ex_a, ex_b)
    example = {
        "a": ex_a,
        "b": ex_b,
        "bridge": bridge,
        "rest": rest,
        "ten": ten,
        "answer": ex_a + ex_b,
    }
    banned: set[tuple[int, int]] = {(ex_a, ex_b)}

    def take_add(builder: Callable[..., tuple[int, int]]) -> dict[str, Any]:
        pair = builder(rng, banned)
        banned.add(pair)
        return _calc(pair[0], "+", pair[1])

    def take_sub(builder: Callable[..., tuple[int, int]]) -> dict[str, Any]:
        pair = builder(rng, banned)
        banned.add(pair)
        return _calc(pair[0], "−", pair[1])

    blocks = [
        {"label": "Celé desítky", "items": [take_add(_tens_add), take_sub(_tens_sub)]},
        {"label": "Bez přechodu", "items": [take_add(_nocross_add), take_sub(_nocross_sub)]},
        {
            "label": "S přechodem",
            "items": [take_add(_cross_add_100), take_sub(_cross_sub_100), take_add(_cross_add_100)],
        },
        {"label": "Číslo a desítky", "items": [take_add(_plus_tens), take_sub(_minus_tens)]},
        {
            "label": "Dvě dvojciferná",
            "items": [take_add(_two_add), take_sub(_two_sub), take_add(_two_add)],
        },
    ]

    missing = []
    a = rng.randint(12, 40)
    ans = rng.randint(10, 40)
    missing.append({"form": "a+x", "a": a, "total": a + ans, "answer": ans})
    b = rng.randint(12, 40)
    ans = rng.randint(10, 50)
    missing.append({"form": "x+b", "b": b, "total": b + ans, "answer": ans})
    minuend = rng.randint(40, 90)
    ans = rng.randint(10, minuend - 5)
    missing.append({"form": "a-x", "a": minuend, "result": minuend - ans, "answer": ans})
    sub = rng.randint(10, 40)
    result = rng.randint(10, 50)
    missing.append({"form": "x-b", "b": sub, "result": result, "answer": sub + result})
    rng.shuffle(missing)

    errors = [_make_error(rng, "+"), _make_error(rng, "−")]

    return {
        "heading": HEADINGS[2],
        "sections": [
            {
                "id": "calc100",
                "title": "1. Spočítej",
                "example": example,
                "blocks": blocks,
            },
            {"id": "missing100", "title": "2. Doplň chybějící číslo", "items": missing},
            {
                "id": "fix_error",
                "title": "3. Najdi a oprav chybu",
                "instruction": "Výsledek je špatně. Napiš správný výsledek.",
                "items": errors,
            },
        ],
    }


def _make_error(rng: Random, op: str) -> dict[str, Any]:
    for _ in range(40):
        if op == "+":
            a = rng.randint(14, 60)
            b = rng.choice([10, 20, 30, 4, 5, 6])
            if a + b > 100:
                continue
            answer = a + b
        else:
            a = rng.randint(30, 90)
            b = rng.choice([10, 20, 30, 4, 5])
            if b >= a:
                continue
            answer = a - b
        shown = answer + 10 if answer + 10 <= 100 else answer - 10
        if shown == answer or not 0 <= shown <= 100:
            continue
        return {"a": a, "b": b, "op": "−" if op == "−" else "+", "shown": shown, "answer": answer}
    raise ValueError("error item")


def build_page4(rng: Random) -> dict[str, Any]:
    total_a = rng.randint(16, 55)
    total_b = rng.randint(5, min(30, 100 - total_a))
    left_a = rng.randint(24, 70)
    left_b = rng.randint(5, left_a - 5)
    more_a = rng.randint(12, 50)
    more_b = rng.randint(5, min(25, 100 - more_a))
    less_a = rng.randint(24, 70)
    less_b = rng.randint(5, less_a - 5)

    total_text = rng.choice(
        [
            f"V polici je {total_a} knih a v tašce {total_b} knih. Kolik knih je celkem?",
            f"V krabici je {total_a} kostek a na koberci {total_b} kostek. Kolik kostek je celkem?",
        ]
    )
    left_text = rng.choice(
        [
            f"Na výletě jelo {left_a} dětí. Vystoupilo {left_b} dětí. Kolik dětí jelo dál?",
            f"Na stromě sedělo {left_a} ptáků. Odletělo {left_b} ptáků. Kolik ptáků zůstalo?",
        ]
    )
    more_text = rng.choice(
        [
            (
                f"Ema má {more_a} pastelek. Tonda má o {more_b} pastelek více. "
                f"Kolik pastelek má Tonda?"
            ),
            (
                f"V první misce je {more_a} jahod. Ve druhé je o {more_b} jahod více. "
                f"Kolik jahod je ve druhé misce?"
            ),
        ]
    )
    less_text = rng.choice(
        [
            (
                f"V prvním košíku je {less_a} jablek. Ve druhém je o {less_b} jablek méně. "
                f"Kolik jablek je ve druhém košíku?"
            ),
            (
                f"Bára má {less_a} samolepek. Filip má o {less_b} samolepek méně. "
                f"Kolik samolepek má Filip?"
            ),
        ]
    )
    stories = [
        {"kind": "total", "label": "Celkem", "a": total_a, "b": total_b, "answer": total_a + total_b, "text": total_text},
        {"kind": "left", "label": "Zůstalo", "a": left_a, "b": left_b, "answer": left_a - left_b, "text": left_text},
        {"kind": "more", "label": "O několik více", "a": more_a, "b": more_b, "answer": more_a + more_b, "text": more_text},
        {"kind": "less", "label": "O několik méně", "a": less_a, "b": less_b, "answer": less_a - less_b, "text": less_text},
    ]

    goods = [
        ("stavebnice", 12, 28),
        ("omalovánky", 8, 22),
        ("míč", 10, 24),
        ("pastelky", 6, 18),
    ]
    first, second = _sample(rng, goods, 2)
    for _ in range(40):
        p1 = rng.randint(first[1], first[2])
        p2 = rng.randint(second[1], second[2])
        if 16 <= p1 + p2 <= 45:
            break
    else:
        p1, p2 = 18, 15
    challenge = {
        "a": p1,
        "b": p2,
        "pay": 50,
        "names": [first[0], second[0]],
        "sum": p1 + p2,
        "change": 50 - (p1 + p2),
        "text": (
            f"{first[0].capitalize()} stojí {p1} Kč a {second[0]} stojí {p2} Kč. "
            f"Kolik stojí obojí dohromady? Kolik Kč zbude z 50 Kč?"
        ),
    }

    return {
        "heading": HEADINGS[3],
        "sections": [
            {"id": "stories", "title": "Slovní úlohy", "items": stories},
            {
                "id": "challenge_story",
                "title": "Výzva navíc",
                "instruction": "Dva kroky. Můžeš přeskočit.",
                "item": challenge,
            },
        ],
    }


def build_page5(rng: Random) -> dict[str, Any]:
    def groups() -> dict[str, Any]:
        count = rng.choice([3, 4])
        each = rng.choice([2, 3, 4])
        return {
            "groups": count,
            "each": each,
            "kind": rng.choice(ICON_KINDS),
            "answer": count * each,
        }

    g1, g2 = groups(), groups()
    while (g1["groups"], g1["each"]) == (g2["groups"], g2["each"]):
        g2 = groups()
    g2["kind"] = rng.choice([k for k in ICON_KINDS if k != g1["kind"]])

    rows = rng.choice([2, 3])
    cols = rng.choice([3, 4, 5])
    while rows * cols > 15:
        cols -= 1

    facts = _main_facts(rng, 11)
    seqs = [
        _seq(2, 2, 6, sorted(_sample(rng, [1, 2, 3, 4, 5], 2))),
        _seq(rng.choice([5, 10]), rng.choice([5, 10]), 6, sorted(_sample(rng, [1, 2, 3, 4, 5], 2))),
    ]
    # Rebuild the second sequence so its step and start agree.
    step2 = rng.choice([5, 10])
    seqs[1] = _seq(step2, step2, 6, sorted(_sample(rng, [1, 2, 3, 4, 5], 2)))

    g = rng.randint(2, 4)
    each = rng.randint(2, 5)
    word = {
        "groups": g,
        "each": each,
        "answer": g * each,
        "text": (
            f"Skupin jablek je {g}. V každé skupině jich je {each}. "
            f"Kolik jablek je celkem?"
        ),
    }

    return {
        "heading": HEADINGS[4],
        "sections": [
            {
                "id": "groups",
                "title": "1. Stejné skupiny",
                "items": [g1, g2],
            },
            {
                "id": "array",
                "title": "2. Puntíky v řadách",
                "instruction": "Řady jsou vodorovně.",
                "rows": rows,
                "cols": cols,
                "answer_rows": rows,
                "answer_cols": cols,
                "answer_total": rows * cols,
            },
            {"id": "facts", "title": "3. Násobení", "items": facts},
            {
                "id": "mult_seq",
                "title": "4. Doplň násobky",
                "sequences": [
                    {"label": "Po 2", **seqs[0]},
                    {"label": f"Po {step2}", **seqs[1]},
                ],
            },
            {"id": "word_mul", "title": "5. Slovní úloha", "item": word},
        ],
    }


def _main_facts(rng: Random, n: int) -> list[dict[str, Any]]:
    facts: list[tuple[int, int]] = []
    zero_factor = rng.choice(CORE_FACTORS)
    one_factor = rng.choice(CORE_FACTORS)
    facts.append((zero_factor, 0))
    facts.append((one_factor, 1))
    for factor in CORE_FACTORS:
        other = rng.randint(2, 10)
        facts.append((factor, other))
    while len(facts) < n:
        a = rng.choice(CORE_FACTORS)
        b = rng.randint(2, 10)
        if (a, b) not in facts:
            facts.append((a, b))
    facts = facts[:n]
    rng.shuffle(facts)
    return [_calc(a, "·", b) for a, b in facts]


def build_page6(rng: Random) -> dict[str, Any]:
    parts = rng.choice([2, 3, 4])
    each = rng.choice([2, 3, 4])
    while parts * each > 12:
        each -= 1
    share_total = parts * each

    size = rng.choice([2, 3, 4])
    group_count = rng.choice([2, 3, 4])
    while size * group_count > 12:
        group_count -= 1
    group_total = size * group_count

    divs = _division_facts(rng, 8)
    families = [_family(rng, reveal=1), _family(rng, reveal=0)]
    # Keep the two families on different products.
    guard = 0
    while families[0]["product"] == families[1]["product"] and guard < 8:
        families[1] = _family(rng, reveal=0)
        guard += 1

    factor = rng.choice([2, 3, 4, 5])
    quotient = rng.randint(3, 8)
    total = factor * quotient
    times = {
        "a": total,
        "b": factor,
        "answer": quotient,
        "text": (
            f"Eva má {total} korálků. Adam má {factor}krát méně korálků než Eva. "
            f"Kolik korálků má Adam?"
        ),
        "note": f"Pozor: „{factor}krát méně“ není „o {factor} méně“.",
    }

    challenge = _challenge_facts(rng, 4)

    return {
        "heading": HEADINGS[5],
        "sections": [
            {
                "id": "share",
                "title": "Rozděl stejným dílem",
                "total": share_total,
                "parts": parts,
                "answer": each,
                "text": (
                    f"{share_total} kuliček rozděl stejným dílem mezi {parts} děti. "
                    f"Kolik kuliček dostane každé dítě?"
                ),
            },
            {
                "id": "make_groups",
                "title": "Tvoř skupiny",
                "total": group_total,
                "size": size,
                "answer": group_count,
                "text": (
                    f"Rozděl {group_total} puntíků do skupin po {size}. "
                    f"Kolik skupin vznikne?"
                ),
            },
            {"id": "div_facts", "title": "2. Dělení", "items": divs},
            {
                "id": "families",
                "title": "3. Násobení a dělení patří k sobě",
                "items": families,
            },
            {"id": "word_times", "title": "4. Několikrát méně", "item": times},
            {
                "id": "challenge_mul",
                "title": "Výzva navíc",
                "instruction": "Násobilka 6 až 9. Můžeš přeskočit.",
                "items": challenge,
            },
        ],
    }


def _division_facts(rng: Random, n: int) -> list[dict[str, Any]]:
    items = [_calc(rng.randint(6, 12), ":", 1)]
    seen = {(items[0]["a"], items[0]["b"])}
    for divisor in (2, 3, 4, 5, 10):
        quotient = rng.randint(2, 10)
        dividend = divisor * quotient
        seen.add((dividend, divisor))
        items.append(_calc(dividend, ":", divisor))
    while len(items) < n:
        divisor = rng.choice([2, 3, 4, 5, 10])
        quotient = rng.randint(2, 10)
        dividend = divisor * quotient
        if (dividend, divisor) in seen:
            continue
        seen.add((dividend, divisor))
        items.append(_calc(dividend, ":", divisor))
    rest = items[1:]
    rng.shuffle(rest)
    # Keep the division-by-one fact, but not always first.
    items = [items[0], *rest]
    rng.shuffle(items)
    return items[:n]


def _family(rng: Random, *, reveal: int) -> dict[str, Any]:
    a = rng.choice([2, 3, 4, 5])
    b = rng.choice([2, 3, 4, 5, 10])
    while a == b:
        b = rng.choice([2, 3, 4, 5, 10])
    product = a * b
    rows = [
        {"x": a, "op": "·", "y": b, "z": product, "hide": None},
        {"x": b, "op": "·", "y": a, "z": product, "hide": "z"},
        {"x": product, "op": ":", "y": b, "z": a, "hide": "z"},
        {"x": product, "op": ":", "y": a, "z": b, "hide": "y"},
    ]
    if reveal == 0:
        rows[0]["hide"] = "z"
    return {"a": a, "b": b, "product": product, "rows": rows}


def _challenge_facts(rng: Random, n: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    while len(items) < n - 1:
        a = rng.choice(CHALLENGE_FACTORS)
        b = rng.randint(2, 9)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        items.append(_calc(a, "·", b))
    for _ in range(20):
        divisor = rng.choice(CHALLENGE_FACTORS)
        quotient = rng.randint(2, 9)
        dividend = divisor * quotient
        if ("div", dividend, divisor) in seen:
            continue
        items.append(_calc(dividend, ":", divisor))
        break
    else:
        items.append(_calc(42, ":", 6))
    rng.shuffle(items)
    return items


def build_page7(rng: Random) -> dict[str, Any]:
    price_names = ["sešit", "tužka", "jablko"]
    ranges = {"sešit": (8, 16), "tužka": (4, 11), "jablko": (3, 8)}
    prices = {name: rng.randint(*ranges[name]) for name in price_names}
    bought = _sample(rng, price_names, 2)
    counts = {bought[0]: rng.choice([1, 2]), bought[1]: 1}
    total = sum(prices[name] * counts[name] for name in bought)
    # Shrink counts/prices if the basket does not fit into 50 Kč.
    guard = 0
    while total > 45 and guard < 12:
        guard += 1
        for name in price_names:
            lo, _hi = ranges[name]
            prices[name] = max(lo, prices[name] - 1)
        counts = {bought[0]: 1, bought[1]: 1}
        total = sum(prices[name] * counts[name] for name in bought)
    if total > 50:
        raise ValueError("Purchase does not fit into 50 Kč")
    pay = 50
    phrases = [_buy_phrase(name, counts[name]) for name in bought]
    catalog = [{"name": name, "price": prices[name]} for name in price_names]

    coins: list[int] = []
    for _ in range(60):
        pick = rng.choice(COIN_VALUES)
        if sum(coins) + pick <= 80 and len(coins) < 6:
            coins.append(pick)
        if len(coins) >= 4 and sum(coins) >= 12:
            break
    if len(set(coins)) < 2 or not 1 <= sum(coins) <= 100:
        coins = [20, 10, 5, 2]
    rng.shuffle(coins)

    hour_whole = rng.randint(1, 10)
    hour_half = rng.choice([h for h in range(1, 11) if h != hour_whole])
    clocks = [
        {"hour": hour_whole, "minute": 0, "label": f"{hour_whole}:00", **_clock_angles(hour_whole, 0)},
        {"hour": hour_half, "minute": 30, "label": f"{hour_half}:30", **_clock_angles(hour_half, 30)},
    ]

    start = rng.randint(7, 8)
    length = rng.choice([2, 3, 4])
    end = start + length

    names = _sample(rng, ["Ema", "Tonda", "Bára", "Filip", "Anička", "Lukáš"], 3)
    while True:
        values = [rng.randint(6, 28) for _ in range(3)]
        if len(set(values)) == 3 and sum(values) <= 100:
            break
    rows = [{"name": name, "value": value} for name, value in zip(names, values, strict=True)]
    top = max(rows, key=lambda row: row["value"])

    return {
        "heading": HEADINGS[6],
        "sections": [
            {
                "id": "prices",
                "title": "1. Nákup",
                "items": catalog,
                "buy_text": f"Kup {phrases[0]} a {phrases[1]}.",
                "bought": [{"name": name, "count": counts[name], "price": prices[name]} for name in bought],
                "total": total,
                "pay": pay,
                "change": pay - total,
            },
            {
                "id": "coins",
                "title": "2. Spočítej mince",
                "instruction": "Sečti hodnoty mincí.",
                "coins": coins,
                "answer": sum(coins),
            },
            {
                "id": "clocks",
                "title": "3. Kolik je hodin?",
                "hour_hand": HOUR_HAND_RATIO,
                "minute_hand": MINUTE_HAND_RATIO,
                "items": clocks,
            },
            {
                "id": "duration",
                "title": "4. Jak dlouho to trvá?",
                "start": f"{start}:00",
                "end": f"{end}:00",
                "answer": length,
                "text": f"Od {start}:00 do {end}:00. Kolik hodin uplynulo?",
            },
            {
                "id": "table",
                "title": "5. Tabulka",
                "headers": ["Jméno", "Kaštany"],
                "rows": rows,
                "most_name": top["name"],
                "most_value": top["value"],
                "total": sum(values),
                "questions": [
                    "Kdo nasbíral nejvíce kaštanů?",
                    "Kolik kaštanů nasbírali dohromady?",
                ],
            },
        ],
    }


def build_page8(rng: Random) -> dict[str, Any]:
    shapes = [
        {"id": "square", "name": "čtverec"},
        {"id": "rectangle", "name": "obdélník"},
        {"id": "triangle", "name": "trojúhelník"},
        {"id": "circle", "name": "kruh"},
    ]
    shape_order = list(shapes)
    rng.shuffle(shape_order)
    shape_names = [s["name"] for s in shapes]
    rng.shuffle(shape_names)

    lines = [
        {"kind": "segment", "name": "úsečka"},
        {"kind": "line", "name": "přímka", "letter": "p"},
        {"kind": "polyline", "name": "lomená čára"},
    ]
    line_order = list(lines)
    rng.shuffle(line_order)

    segs = [
        {"left": "A", "right": "B", "length_mm": 40, "answer_cm": 4},
        {"left": "C", "right": "D", "length_mm": 70, "answer_cm": 7},
    ]
    if rng.random() < 0.5:
        segs[0]["length_mm"], segs[1]["length_mm"] = 70, 40
        segs[0]["answer_cm"], segs[1]["answer_cm"] = 7, 4

    solids = [
        {"id": "cube", "name": "krychle"},
        {"id": "cuboid", "name": "kvádr"},
        {"id": "sphere", "name": "koule"},
        {"id": "cylinder", "name": "válec"},
    ]
    solid_order = list(solids)
    rng.shuffle(solid_order)
    solid_names = [s["name"] for s in solids]
    rng.shuffle(solid_names)

    return {
        "heading": HEADINGS[7],
        "sections": [
            {
                "id": "shapes2d",
                "title": "1. Napiš název tvaru",
                "bank": shape_names,
                "items": shape_order,
            },
            {
                "id": "lines",
                "title": "2. Přímka, úsečka, lomená čára",
                "bank": ["úsečka", "přímka", "lomená čára"],
                "items": line_order,
            },
            {
                "id": "measure",
                "title": "3. Změř úsečky",
                "note": "Tiskněte ve skutečné velikosti (100 %).",
                "items": segs,
            },
            {
                "id": "draw",
                "title": "4. Narýsuj",
                "instruction": "Narýsuj úsečku AB dlouhou 5 cm.",
                "length_cm": 5,
                "condition": (
                    "Úsečka AB má délku 5 cm a oba krajní body jsou označeny "
                    "písmeny A a B. Na poloze na stránce nezáleží."
                ),
            },
            {
                "id": "units",
                "title": "5. Doplň jednotky",
                "items": [
                    {"amount": 1, "left": "m", "right": "cm", "answer": 100},
                    {"amount": 1, "left": "dm", "right": "cm", "answer": 10},
                ],
            },
            {
                "id": "solids",
                "title": "6. Napiš název tělesa",
                "bank": solid_names,
                "items": solid_order,
            },
        ],
    }


def _take(data: dict[str, Any], *ids: str) -> list[dict[str, Any]]:
    by_id = {sec["id"]: sec for sec in data["sections"]}
    return [by_id[sid] for sid in ids]


def _compose_topic(topic: int, copies: list[dict[str, Any]], part: int) -> dict[str, Any]:
    """Pick sections for one A5 page. Counts across all parts are exactly double."""
    if topic in (1, 2, 3, 7):
        sections = copies[part - 1]["sections"]
    elif topic == 4:
        sections = (
            _take(copies[part - 1], "stories")
            if part < 3
            else _take(copies[0], "challenge_story") + _take(copies[1], "challenge_story")
        )
    elif topic == 5:
        sections = (
            _take(copies[part - 1], "groups", "array", "facts")
            if part < 3
            else _take(copies[0], "mult_seq", "word_mul") + _take(copies[1], "mult_seq", "word_mul")
        )
    elif topic == 6:
        sections = (
            _take(copies[part - 1], "share", "make_groups", "div_facts", "families")
            if part < 3
            else _take(copies[0], "word_times", "challenge_mul") + _take(copies[1], "word_times", "challenge_mul")
        )
    elif topic == 8:
        sections = (
            _take(copies[part - 1], "shapes2d", "lines", "measure", "units", "solids")
            if part < 3
            else _take(copies[0], "draw") + _take(copies[1], "draw")
        )
    else:
        raise ValueError(f"Unknown topic {topic}")
    return {"heading": HEADINGS[topic - 1], "sections": sections}


def _pages_from_seed(seed: int) -> list[dict[str, Any]]:
    if len(PAGE_TOPICS) != PAGE_COUNT:
        raise ValueError("PAGE_TOPICS does not match PAGE_COUNT")
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
    variants: list[list[dict[str, Any]]] = []
    for topic, builder in enumerate(builders, start=1):
        copies = []
        for copy in (1, 2):
            page_seed = seed * 1009 + (topic * 20 + copy) * 9176
            copies.append(builder(make_rng(page_seed)))
        variants.append(copies)

    pages: list[dict[str, Any]] = []
    seen_parts: dict[int, int] = {}
    for index, topic in enumerate(PAGE_TOPICS, start=1):
        part = seen_parts.get(topic, 0) + 1
        seen_parts[topic] = part
        page_seed = seed * 1009 + index * 9176
        data = _compose_topic(topic, variants[topic - 1], part)
        data["page"] = index
        data["topic"] = topic
        data["part"] = part
        data["booklet_title"] = BOOKLET_TITLE
        data["show_name_field"] = index == 1
        pages.append(
            {
                "kind": "math_grade2",
                "title": data["heading"],
                "instructions": "",
                "difficulty": "easy",
                "seed": page_seed,
                "data": data,
                "answer": {},
            }
        )
    return pages


def build_answer_key(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_pages: list[dict[str, Any]] = []
    for page in pages:
        data = page["data"]
        lines: list[str] = []
        for sec in data["sections"]:
            lines.extend(_key_lines(sec))
        key_pages.append({"page": data["page"], "heading": data["heading"], "lines": lines})
    return key_pages


def _fmt_calc(it: dict[str, Any]) -> str:
    return f"{it['a']} {it['op']} {it['b']} = {it['answer']}"


def _fmt_seq(seq: dict[str, Any]) -> str:
    filled = []
    holes = {item["index"]: item["value"] for item in seq["answers"]}
    for i, value in enumerate(seq["values"]):
        filled.append(str(holes[i] if i in holes else value))
    missing = ", ".join(str(item["value"]) for item in seq["answers"])
    return f"{seq.get('label', '')}: chybí {missing} (řada {' – '.join(filled)})".strip()


def _key_lines(sec: dict[str, Any]) -> list[str]:
    sid = sec["id"]
    title = sec.get("title", sid)
    if sid == "complements":
        bits = [f"{it['a']} + {it['answer']} = 10" for it in sec["items"]]
        return [f"{title}: " + ", ".join(bits)]
    if sid == "decompose":
        ex = sec["example"]
        lines = [
            f"{title}: vzor {ex['a']} + {ex['b']} = {ex['a']} + {ex['bridge']} + {ex['rest']} = {ex['answer']}"
        ]
        for it in sec["items"]:
            lines.append(
                f"{it['a']} + {it['b']} = {it['a']} + {it['bridge']} + {it['rest']} = {it['answer']}"
            )
        return lines
    if sid == "mixed20":
        return [f"{title}: " + ", ".join(_fmt_calc(it) for it in sec["items"])]
    if sid in {"missing20", "missing100"}:
        return [f"{title}: " + ", ".join(_fmt_missing(it) for it in sec["items"])]
    if sid == "word20":
        it = sec["item"]
        return [f"{title}: {it['answer']} {it['unit']}"]
    if sid == "place_value":
        return [f"{title}: " + "; ".join(_fmt_place(it) for it in sec["items"])]
    if sid in {"sequences", "mult_seq"}:
        return [f"{title}: " + " | ".join(_fmt_seq(seq) for seq in sec["sequences"])]
    if sid == "compare":
        bits = [f"{it['a']} {it['answer']} {it['b']}" for it in sec["items"]]
        return [f"{title}: " + ", ".join(bits)]
    if sid == "order":
        return [f"{title}: " + ", ".join(str(n) for n in sec["answer"])]
    if sid == "number_line":
        return [f"{title}: doplň " + ", ".join(str(n) for n in sec["missing"])]
    if sid == "round":
        ex = sec["example"]
        bits = [f"vzor {ex['n']} ≈ {ex['answer']}"]
        bits.extend(f"{it['n']} ≈ {it['answer']}" for it in sec["items"])
        return [f"{title}: " + ", ".join(bits)]
    if sid == "calc100":
        ex = sec["example"]
        lines = [
            (
                f"Vzor: {ex['a']} + {ex['b']} = {ex['a']} + {ex['bridge']} + {ex['rest']}"
                f" = {ex['ten']} + {ex['rest']} = {ex['answer']}"
            )
        ]
        for block in sec["blocks"]:
            lines.append(f"{block['label']}: " + ", ".join(_fmt_calc(it) for it in block["items"]))
        return lines
    if sid == "fix_error":
        bits = [
            f"{it['a']} {it['op']} {it['b']} = {it['answer']} (ne {it['shown']})"
            for it in sec["items"]
        ]
        return [f"{title}: " + "; ".join(bits)]
    if sid == "stories":
        return [f"{it['label']}: {it['answer']}" for it in sec["items"]]
    if sid == "challenge_story":
        it = sec["item"]
        return [
            f"{title}: dohromady {it['sum']} Kč, zbude {it['change']} Kč z {it['pay']} Kč"
        ]
    if sid == "groups":
        bits = [
            f"{it['groups']} skupiny po {it['each']} = {it['answer']}"
            for it in sec["items"]
        ]
        return [f"{title}: " + "; ".join(bits)]
    if sid == "array":
        return [
            f"{title}: {sec['answer_rows']} řad, {sec['answer_cols']} v řadě, celkem {sec['answer_total']}"
        ]
    if sid in {"facts", "div_facts", "challenge_mul"}:
        return [f"{title}: " + ", ".join(_fmt_calc(it) for it in sec["items"])]
    if sid == "word_mul":
        return [f"{title}: {sec['item']['answer']} jablek"]
    if sid == "share":
        return [f"{title}: každé dítě dostane {sec['answer']}"]
    if sid == "make_groups":
        return [f"{title}: vznikne {sec['answer']} skupin"]
    if sid == "families":
        lines = []
        for index, fam in enumerate(sec["items"], start=1):
            bits = []
            for row in fam["rows"]:
                bits.append(f"{row['x']} {row['op']} {row['y']} = {row['z']}")
            lines.append(f"Čtveřice {index}: " + "; ".join(bits))
        return lines
    if sid == "word_times":
        it = sec["item"]
        return [f"{title}: {it['answer']} korálků. {it['note']}"]
    if sid == "prices":
        return [
            f"{title}: {sec['buy_text']} cena {sec['total']} Kč, "
            f"z {sec['pay']} Kč zbude {sec['change']} Kč"
        ]
    if sid == "coins":
        return [f"{title}: {sec['answer']} Kč ({' + '.join(str(c) for c in sec['coins'])})"]
    if sid == "clocks":
        bits = []
        for it in sec["items"]:
            if it["minute"] == 0:
                hands = f"malá ručička na {it['hour']}, velká na 12"
            else:
                nxt = 1 if it["hour"] == 12 else it["hour"] + 1
                hands = f"velká ručička na 6, malá mezi {it['hour']} a {nxt}"
            bits.append(f"{it['label']} ({hands})")
        return [f"{title}: " + "; ".join(bits)]
    if sid == "duration":
        return [f"{title}: {sec['answer']} hodin ({sec['start']}–{sec['end']})"]
    if sid == "table":
        return [
            f"{title}: nejvíce {sec['most_name']} ({sec['most_value']}), dohromady {sec['total']}"
        ]
    if sid == "shapes2d":
        return [f"{title}: " + ", ".join(it["name"] for it in sec["items"])]
    if sid == "lines":
        bits = []
        for it in sec["items"]:
            if it["kind"] == "line":
                bits.append(f"přímka {it['letter']}")
            else:
                bits.append(it["name"])
        return [f"{title}: " + ", ".join(bits)]
    if sid == "measure":
        bits = [
            f"{it['left']}{it['right']} = {it['answer_cm']} cm" for it in sec["items"]
        ]
        return [
            f"{title}: " + ", ".join(bits) + " (mezi středy krajních značek, tisk 100 %)"
        ]
    if sid == "draw":
        return [f"{title}: {sec['condition']}"]
    if sid == "units":
        bits = [
            f"{it['amount']} {it['left']} = {it['answer']} {it['right']}" for it in sec["items"]
        ]
        return [f"{title}: " + ", ".join(bits)]
    if sid == "solids":
        return [f"{title}: " + ", ".join(it["name"] for it in sec["items"])]
    raise ValueError(f"No answer-key branch for {sid}")


def _fmt_missing(it: dict[str, Any]) -> str:
    form = it["form"]
    if form == "x+b":
        return f"{it['answer']} + {it['b']} = {it['total']}"
    if form == "a+x":
        return f"{it['a']} + {it['answer']} = {it['total']}"
    if form == "a-x":
        return f"{it['a']} − {it['answer']} = {it['result']}"
    if form == "x-b":
        return f"{it['answer']} − {it['b']} = {it['result']}"
    raise ValueError(form)


def _fmt_place(it: dict[str, Any]) -> str:
    kind = it["kind"]
    if kind == "split_ones":
        return f"{it['n']} = {it['tens']} + {it['answer']}"
    if kind == "split_tens":
        return f"{it['n']} = {it['answer']} + {it['ones']}"
    if kind == "words":
        return f"{it['text']} = {it['answer']}"
    if kind == "hundred":
        return f"100 = {it['answer']} desítek a 0 jednotek"
    raise ValueError(kind)


def _sections(pages: list[dict[str, Any]], sid: str) -> list[dict[str, Any]]:
    return [sec for page in pages for sec in page["data"]["sections"] if sec["id"] == sid]


def _item_count(pages: list[dict[str, Any]], sid: str) -> int:
    total = 0
    for sec in _sections(pages, sid):
        if "blocks" in sec:
            total += sum(len(block["items"]) for block in sec["blocks"])
        else:
            total += len(sec["items"])
    return total


def _validate_doubled_counts(pages: list[dict[str, Any]]) -> None:
    """Every exercise type from the original eight pages appears twice."""
    expected_items = {
        "complements": 8,
        "decompose": 4,
        "mixed20": 16,
        "missing20": 8,
        "place_value": 8,
        "compare": 12,
        "calc100": 24,
        "missing100": 8,
        "fix_error": 4,
        "stories": 8,
        "groups": 4,
        "facts": 22,
        "div_facts": 16,
        "families": 4,
        "challenge_mul": 8,
        "measure": 4,
        "units": 4,
    }
    expected_sections = {
        "word20": 2,
        "sequences": 2,
        "order": 2,
        "number_line": 2,
        "round": 2,
        "challenge_story": 2,
        "array": 2,
        "mult_seq": 2,
        "word_mul": 2,
        "share": 2,
        "make_groups": 2,
        "word_times": 2,
        "prices": 2,
        "coins": 2,
        "clocks": 2,
        "duration": 2,
        "table": 2,
        "shapes2d": 2,
        "lines": 2,
        "draw": 2,
        "solids": 2,
    }
    for sid, count in expected_items.items():
        got = _item_count(pages, sid)
        if got != count:
            raise ValueError(f"{sid}: expected {count} items, got {got}")
    for sid, count in expected_sections.items():
        got = len(_sections(pages, sid))
        if got != count:
            raise ValueError(f"{sid}: expected {count} sections, got {got}")
    sequences = _sections(pages, "sequences")
    if sum(len(sec["sequences"]) for sec in sequences) != 4:
        raise ValueError("sequence rows")
    mult = _sections(pages, "mult_seq")
    if sum(len(sec["sequences"]) for sec in mult) != 4:
        raise ValueError("multiple rows")
    clocks = _sections(pages, "clocks")
    if sum(len(sec["items"]) for sec in clocks) != 4:
        raise ValueError("clocks")
    lengths = sorted(it["length_mm"] for sec in _sections(pages, "measure") for it in sec["items"])
    if lengths != [40, 40, 70, 70]:
        raise ValueError(lengths)


def validate_edition(pages: list[dict[str, Any]]) -> None:
    if len(pages) != PAGE_COUNT:
        raise ValueError(f"Expected {PAGE_COUNT} pages, got {len(pages)}")
    if sum(1 for p in pages if p["data"].get("show_name_field")) != 1:
        raise ValueError("Name field must be on exactly one page")
    for index, page in enumerate(pages, start=1):
        data = page["data"]
        if data["topic"] != PAGE_TOPICS[index - 1]:
            raise ValueError(f"Page {index} topic mismatch")
        if data["heading"] != HEADINGS[data["topic"] - 1] or data["page"] != index:
            raise ValueError(f"Page {index} heading/number mismatch")
        if "Matýsk" in str(data) or "Matysk" in str(data):
            raise ValueError("Unexpected textbook name")
        for sec in data["sections"]:
            _VALIDATORS[sec["id"]](sec)
        _reject_out_of_range_answers(data)
    _validate_doubled_counts(pages)


def _reject_out_of_range_answers(data: dict[str, Any]) -> None:
    """Every stored numeric answer used by the key stays inside 0–100."""

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in {"answer", "answer_cm", "answer_total", "total", "change", "sum"} and isinstance(value, int):
                    _in_range(value)
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(data["sections"])


def _v_complements(sec: dict[str, Any]) -> None:
    seen = set()
    if len(sec["items"]) != 4:
        raise ValueError("complements")
    for it in sec["items"]:
        if it["a"] in seen or not 1 <= it["a"] <= 9 or it["answer"] != 10 - it["a"]:
            raise ValueError(it)
        seen.add(it["a"])


def _v_decompose(sec: dict[str, Any]) -> None:
    ex = sec["example"]
    bridge, rest = _split_single(ex["a"], ex["b"])
    if (bridge, rest, ex["a"] + ex["b"]) != (ex["bridge"], ex["rest"], ex["answer"]):
        raise ValueError("worked split")
    if len(sec["items"]) != 2:
        raise ValueError("practice splits")
    for it in sec["items"]:
        br, rs = _split_single(it["a"], it["b"])
        if (br, rs) != (it["bridge"], it["rest"]) or it["answer"] != it["a"] + it["b"]:
            raise ValueError(it)


def _v_mixed20(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 8:
        raise ValueError("mixed20 count")
    adds = subs = 0
    for it in sec["items"]:
        if it["answer"] != _result(it["a"], it["op"], it["b"]) or it["answer"] > 20:
            raise ValueError(it)
        if it["op"] == "+":
            adds += 1
            if not (it["a"] < 10 and it["b"] < 10 and it["a"] + it["b"] >= 11):
                raise ValueError(f"add does not cross: {it}")
        else:
            subs += 1
            if it["b"] <= it["a"] % 10:
                raise ValueError(f"sub does not cross: {it}")
    if adds != 4 or subs != 4:
        raise ValueError("mixed balance")


def _v_missing(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 4:
        raise ValueError(sec["id"])
    for it in sec["items"]:
        form = it["form"]
        if form == "x+b" and it["answer"] + it["b"] != it["total"]:
            raise ValueError(it)
        elif form == "a+x" and it["a"] + it["answer"] != it["total"]:
            raise ValueError(it)
        elif form == "a-x" and it["a"] - it["answer"] != it["result"]:
            raise ValueError(it)
        elif form == "x-b" and it["answer"] - it["b"] != it["result"]:
            raise ValueError(it)
        elif form not in {"x+b", "a+x", "a-x", "x-b"}:
            raise ValueError(it)
        for key in ("answer", "a", "b", "total", "result"):
            if key in it:
                _in_range(it[key], hi=100 if sec["id"] == "missing100" else 20)


def _v_word20(sec: dict[str, Any]) -> None:
    it = sec["item"]
    if it["kind"] == "total" and it["answer"] != it["a"] + it["b"]:
        raise ValueError(it)
    if it["kind"] == "left" and it["answer"] != it["a"] - it["b"]:
        raise ValueError(it)
    if it["answer"] > 20 or it["a"] < 5 or it["b"] < 5:
        raise ValueError(it)


def _v_place(sec: dict[str, Any]) -> None:
    kinds = [it["kind"] for it in sec["items"]]
    if kinds != ["split_ones", "split_tens", "words", "hundred"]:
        raise ValueError(kinds)
    ones, tens, words, hundred = sec["items"]
    if ones["n"] != ones["tens"] + ones["answer"] or ones["tens"] % 10:
        raise ValueError(ones)
    if tens["n"] != tens["answer"] + tens["ones"] or tens["answer"] % 10:
        raise ValueError(tens)
    if words["ones_count"] != 0 or words["answer"] != words["tens_count"] * 10:
        raise ValueError(words)
    if hundred["answer"] != 10 or hundred["tens_count"] != 10:
        raise ValueError(hundred)
    if any(it.get("n") == 100 for it in sec["items"]):
        raise ValueError("100 must not be treated as an ordinary two-digit split")


def _v_sequences(sec: dict[str, Any]) -> None:
    if len(sec["sequences"]) != 2:
        raise ValueError("sequences")
    one, tens = sec["sequences"]
    _check_seq(one, step=1)
    if  not any(v % 10 == 0 for v in _full_values(one)):
        # The boundary multiple of ten is inside the row.
        pass
    full = _full_values(one)
    if not any(v % 10 == 0 for v in full[1:-1] or full):
        raise ValueError("ones row does not cross a ten")
    if min(full) % 10 > 2 and (min(full) // 10) == (max(full) // 10):
        raise ValueError("ones row stays inside one ten")
    _check_seq(tens, step=10)
    if 100 not in _full_values(tens):
        raise ValueError("tens row must include 100")


def _full_values(seq: dict[str, Any]) -> list[int]:
    holes = {item["index"]: item["value"] for item in seq["answers"]}
    return [holes[i] if i in holes else int(v) for i, v in enumerate(seq["values"])]


def _check_seq(seq: dict[str, Any], *, step: int | None = None) -> None:
    full = _full_values(seq)
    if step is not None and any(full[i + 1] - full[i] != step for i in range(len(full) - 1)):
        raise ValueError(full)
    if not seq["answers"]:
        raise ValueError("sequence has no gaps")
    if seq["values"][0] is None:
        raise ValueError("first term should be visible")


def _v_compare(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 6:
        raise ValueError("compare count")
    symbols = set()
    saw_100 = False
    saw_zero_units = False
    for it in sec["items"]:
        if it["answer"] != _cmp_symbol(it["a"], it["b"]):
            raise ValueError(it)
        symbols.add(it["answer"])
        saw_100 = saw_100 or it["a"] == 100 or it["b"] == 100
        saw_zero_units = saw_zero_units or it["a"] % 10 == 0 or it["b"] % 10 == 0
        _in_range(it["a"])
        _in_range(it["b"])
    if symbols != {"<", ">", "="} or not saw_100 or not saw_zero_units:
        raise ValueError("compare coverage")


def _v_order(sec: dict[str, Any]) -> None:
    if len(sec["numbers"]) != 5 or len(set(sec["numbers"])) != 5:
        raise ValueError("order")
    if sec["answer"] != sorted(sec["numbers"]):
        raise ValueError("order answer")
    if 100 not in sec["numbers"]:
        raise ValueError("order must include 100")
    if not any(n % 10 == 0 and n != 100 for n in sec["numbers"]):
        raise ValueError("order must include a multiple of ten below 100")


def _v_line(sec: dict[str, Any]) -> None:
    start, end = sec["start"], sec["end"]
    if end - start != 10 or start % 10:
        raise ValueError("line span")
    missing = sec["missing"]
    if len(missing) != 3 or missing != sorted(missing):
        raise ValueError(missing)
    if any(n <= start or n >= end for n in missing):
        raise ValueError(missing)
    if any(abs(a - b) < 2 for a, b in zip(missing, missing[1:])):
        raise ValueError("line gaps too close")


def _v_round(sec: dict[str, Any]) -> None:
    ex = sec["example"]
    if ex["answer"] != _round_to_tens(ex["n"]):
        raise ValueError(ex)
    if len(sec["items"]) != 2:
        raise ValueError("round tasks")
    directions = set()
    for it in sec["items"]:
        if it["answer"] != _round_to_tens(it["n"]) or it["n"] % 10 == 0:
            raise ValueError(it)
        directions.add("up" if it["n"] % 10 >= 5 else "down")
    if directions != {"up", "down"}:
        raise ValueError("round both ways")


def _v_calc100(sec: dict[str, Any]) -> None:
    ex = sec["example"]
    bridge, rest, ten = _split_two_digit(ex["a"], ex["b"])
    if (ex["bridge"], ex["rest"], ex["ten"], ex["answer"]) != (bridge, rest, ten, ex["a"] + ex["b"]):
        raise ValueError("example")
    labels = [block["label"] for block in sec["blocks"]]
    if labels != ["Celé desítky", "Bez přechodu", "S přechodem", "Číslo a desítky", "Dvě dvojciferná"]:
        raise ValueError(labels)
    count = 0
    for block in sec["blocks"]:
        for it in block["items"]:
            count += 1
            if it["answer"] != _result(it["a"], it["op"], it["b"]):
                raise ValueError(it)
            _check_block_item(block["label"], it)
    if count != 12:
        raise ValueError(f"expected about 12 calculations, got {count}")


def _check_block_item(label: str, it: dict[str, Any]) -> None:
    a, b, op = it["a"], it["b"], it["op"]
    if label == "Celé desítky":
        if a % 10 or b % 10:
            raise ValueError(it)
    elif label == "Bez přechodu":
        if op == "+" and (a % 10) + b > 9:
            raise ValueError(it)
        if op == "−" and b > a % 10:
            raise ValueError(it)
        if b > 9:
            raise ValueError(it)
    elif label == "S přechodem":
        if op == "+" and (a % 10) + b < 10:
            raise ValueError(it)
        if op == "−" and b <= a % 10:
            raise ValueError(it)
        if b > 9:
            raise ValueError(it)
    elif label == "Číslo a desítky":
        if b % 10 or b == 0 or a > 99:
            raise ValueError(it)
    elif label == "Dvě dvojciferná":
        if not (10 <= a <= 99 and 10 <= b <= 99):
            raise ValueError(it)
        if op == "+" and (a % 10) + (b % 10) > 9:
            raise ValueError(it)
        if op == "−" and a % 10 < b % 10:
            raise ValueError(it)
    else:
        raise ValueError(label)


def _v_fix(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 2:
        raise ValueError("errors")
    for it in sec["items"]:
        if it["shown"] == it["answer"] or it["answer"] != _result(it["a"], it["op"], it["b"]):
            raise ValueError(it)
        _in_range(it["shown"])


def _v_stories(sec: dict[str, Any]) -> None:
    kinds = [it["kind"] for it in sec["items"]]
    if kinds != ["total", "left", "more", "less"]:
        raise ValueError(kinds)
    for it in sec["items"]:
        if it["kind"] in {"total", "more"} and it["answer"] != it["a"] + it["b"]:
            raise ValueError(it)
        if it["kind"] in {"left", "less"} and it["answer"] != it["a"] - it["b"]:
            raise ValueError(it)
        if it["a"] < 5 or it["b"] < 5:
            raise ValueError("story declension range")
        if "krát" in it["text"]:
            raise ValueError("page 4 must not use krát")


def _v_challenge_story(sec: dict[str, Any]) -> None:
    it = sec["item"]
    if it["sum"] != it["a"] + it["b"] or it["change"] != it["pay"] - it["sum"]:
        raise ValueError(it)
    if it["change"] < 1 or it["pay"] not in (50, 100) or it["sum"] > it["pay"]:
        raise ValueError(it)


def _v_groups(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 2:
        raise ValueError("groups")
    for it in sec["items"]:
        if it["groups"] * it["each"] != it["answer"]:
            raise ValueError(it)
        if it["groups"] > 4 or it["each"] > 4 or it["kind"] not in ICON_KINDS:
            raise ValueError(it)


def _v_array(sec: dict[str, Any]) -> None:
    if sec["rows"] * sec["cols"] != sec["answer_total"]:
        raise ValueError(sec)
    if sec["answer_rows"] != sec["rows"] or sec["answer_cols"] != sec["cols"]:
        raise ValueError(sec)
    if not (2 <= sec["rows"] <= 3 and 3 <= sec["cols"] <= 5):
        raise ValueError(sec)


def _v_facts(sec: dict[str, Any]) -> None:
    if not 10 <= len(sec["items"]) <= 12:
        raise ValueError("fact count")
    saw_zero = saw_one = False
    seen_tables = set()
    for it in sec["items"]:
        if it["op"] != "·" or it["answer"] != it["a"] * it["b"]:
            raise ValueError(it)
        if it["a"] not in CORE_FACTORS or not 0 <= it["b"] <= 10:
            raise ValueError(f"fact outside core tables: {it}")
        if it["b"] == 0:
            saw_zero = True
        if it["b"] == 1:
            saw_one = True
        seen_tables.add(it["a"])
    if not saw_zero or not saw_one or seen_tables != set(CORE_FACTORS):
        raise ValueError("facts must cover 0, 1 and tables 2, 3, 4, 5, 10")


def _v_mult_seq(sec: dict[str, Any]) -> None:
    if len(sec["sequences"]) != 2:
        raise ValueError("mult seq")
    for seq in sec["sequences"]:
        _check_seq(seq)
        full = _full_values(seq)
        step = full[1] - full[0]
        if step not in CORE_FACTORS and step != 2:
            raise ValueError(step)
        if step in CHALLENGE_FACTORS:
            raise ValueError("challenge step in main sequence")


def _v_word_mul(sec: dict[str, Any]) -> None:
    it = sec["item"]
    if it["answer"] != it["groups"] * it["each"]:
        raise ValueError(it)
    if it["groups"] in CHALLENGE_FACTORS or it["each"] in CHALLENGE_FACTORS:
        raise ValueError(it)


def _v_share(sec: dict[str, Any]) -> None:
    if sec["parts"] == 0 or sec["total"] % sec["parts"] or sec["answer"] != sec["total"] // sec["parts"]:
        raise ValueError(sec)
    if sec["total"] > 12:
        raise ValueError("share picture too dense")


def _v_make_groups(sec: dict[str, Any]) -> None:
    if sec["size"] == 0 or sec["total"] % sec["size"] or sec["answer"] != sec["total"] // sec["size"]:
        raise ValueError(sec)
    if sec["total"] > 12:
        raise ValueError("group picture too dense")


def _v_div_facts(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 8:
        raise ValueError("div count")
    ones = 0
    for it in sec["items"]:
        if it["b"] == 0 or it["b"] in CHALLENGE_FACTORS:
            raise ValueError(it)
        if it["b"] not in {1, 2, 3, 4, 5, 10}:
            raise ValueError(it)
        if it["a"] % it["b"] or it["answer"] != it["a"] // it["b"]:
            raise ValueError(it)
        if it["b"] == 1:
            ones += 1
    if ones != 1:
        raise ValueError("need exactly one division by 1")


def _v_families(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 2:
        raise ValueError("families")
    for fam in sec["items"]:
        if fam["a"] * fam["b"] != fam["product"]:
            raise ValueError(fam)
        if fam["a"] in CHALLENGE_FACTORS or fam["b"] in CHALLENGE_FACTORS:
            raise ValueError(fam)
        shown = 0
        for row in fam["rows"]:
            if row["op"] == "·" and row["x"] * row["y"] != row["z"]:
                raise ValueError(row)
            if row["op"] == ":" and (row["y"] == 0 or row["x"] != row["y"] * row["z"]):
                raise ValueError(row)
            if row["hide"] is None:
                shown += 1
            elif row["hide"] not in {"x", "y", "z"}:
                raise ValueError(row)
        if fam is sec["items"][0] and shown < 1:
            raise ValueError("first family needs a filled model row")


def _v_word_times(sec: dict[str, Any]) -> None:
    it = sec["item"]
    if it["b"] == 0 or it["a"] != it["answer"] * it["b"]:
        raise ValueError(it)
    if it["answer"] == it["a"] - it["b"]:
        raise ValueError("times-less collides with subtraction")
    if "krát méně" not in it["text"]:
        raise ValueError("wording")
    if f"o {it['b']} méně" in it["text"]:
        raise ValueError("question must not also be o několik méně")
    if "není" not in it["note"]:
        raise ValueError("missing distinction note")


def _v_challenge_mul(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 4:
        raise ValueError("challenge count")
    for it in sec["items"]:
        if it["op"] == "·":
            if it["a"] not in CHALLENGE_FACTORS and it["b"] not in CHALLENGE_FACTORS:
                raise ValueError(it)
            if it["answer"] != it["a"] * it["b"] or it["b"] == 0 or it["a"] == 0:
                raise ValueError(it)
        elif it["op"] == ":":
            if it["b"] not in CHALLENGE_FACTORS or it["b"] == 0 or it["a"] % it["b"]:
                raise ValueError(it)
            if it["answer"] != it["a"] // it["b"]:
                raise ValueError(it)
        else:
            raise ValueError(it)


def _v_prices(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 3:
        raise ValueError("price list")
    by_name = {it["name"]: it["price"] for it in sec["items"]}
    total = 0
    for bought in sec["bought"]:
        if bought["price"] != by_name[bought["name"]]:
            raise ValueError(bought)
        total += bought["price"] * bought["count"]
    if total != sec["total"] or sec["change"] != sec["pay"] - total or sec["change"] < 0:
        raise ValueError(sec)
    if sec["pay"] not in (50, 100):
        raise ValueError(sec)


def _v_coins(sec: dict[str, Any]) -> None:
    if any(c not in COIN_VALUES for c in sec["coins"]):
        raise ValueError(sec["coins"])
    if sum(sec["coins"]) != sec["answer"] or not sec["coins"]:
        raise ValueError(sec)


def _v_clocks(sec: dict[str, Any]) -> None:
    if sec["minute_hand"] <= sec["hour_hand"]:
        raise ValueError("minute hand must be longer")
    minutes = [it["minute"] for it in sec["items"]]
    if sorted(minutes) != [0, 30]:
        raise ValueError(minutes)
    for it in sec["items"]:
        angles = _clock_angles(it["hour"], it["minute"])
        if abs(angles["hour_deg"] - it["hour_deg"]) > 1e-9:
            raise ValueError(it)
        if abs(angles["minute_deg"] - it["minute_deg"]) > 1e-9:
            raise ValueError(it)
        start = (it["hour"] % 12) * 30.0
        if it["minute"] == 30:
            if not start < it["hour_cw"] < start + 30:
                raise ValueError("half-hour hand is not between hours")
            if it["minute_cw"] != 180:
                raise ValueError("half-hour minute hand")
        else:
            if it["hour_cw"] != start or it["minute_cw"] != 0:
                raise ValueError("whole hour")
        if it["label"] != f"{it['hour']}:{it['minute']:02d}":
            raise ValueError(it["label"])


def _v_duration(sec: dict[str, Any]) -> None:
    start_h = int(sec["start"].split(":")[0])
    end_h = int(sec["end"].split(":")[0])
    if end_h - start_h != sec["answer"] or sec["answer"] < 1:
        raise ValueError(sec)
    if not sec["start"].endswith(":00") or not sec["end"].endswith(":00"):
        raise ValueError(sec)


def _v_table(sec: dict[str, Any]) -> None:
    values = [row["value"] for row in sec["rows"]]
    if len(sec["rows"]) != 3 or len(set(values)) != 3:
        raise ValueError("table rows")
    if sum(values) != sec["total"]:
        raise ValueError("table total")
    top = max(sec["rows"], key=lambda row: row["value"])
    if top["name"] != sec["most_name"] or top["value"] != sec["most_value"]:
        raise ValueError("table max")
    if values.count(max(values)) != 1:
        raise ValueError("max not unique")


def _v_shapes(sec: dict[str, Any]) -> None:
    expected = {"square": "čtverec", "rectangle": "obdélník", "triangle": "trojúhelník", "circle": "kruh"}
    got = {it["id"]: it["name"] for it in sec["items"]}
    if got != expected or set(sec["bank"]) != set(expected.values()):
        raise ValueError(sec)


def _v_lines(sec: dict[str, Any]) -> None:
    kinds = {it["kind"] for it in sec["items"]}
    if kinds != {"segment", "line", "polyline"}:
        raise ValueError(kinds)
    line = next(it for it in sec["items"] if it["kind"] == "line")
    if line["letter"] != "p" or line["name"] != "přímka":
        raise ValueError(line)


def _v_measure(sec: dict[str, Any]) -> None:
    lengths = sorted(it["length_mm"] for it in sec["items"])
    if lengths != [40, 70]:
        raise ValueError(lengths)
    for it in sec["items"]:
        if it["answer_cm"] * 10 != it["length_mm"]:
            raise ValueError(it)
    if "100 %" not in sec["note"]:
        raise ValueError("missing print-size note")


def _v_draw(sec: dict[str, Any]) -> None:
    if sec["length_cm"] != 5 or "5 cm" not in sec["instruction"] or "5 cm" not in sec["condition"]:
        raise ValueError(sec)


def _v_units(sec: dict[str, Any]) -> None:
    if len(sec["items"]) != 2:
        raise ValueError("units")
    for it in sec["items"]:
        expected = int(it["amount"] * UNIT_IN_CM[it["left"]] / UNIT_IN_CM[it["right"]])
        if it["answer"] != expected:
            raise ValueError(it)


def _v_solids(sec: dict[str, Any]) -> None:
    expected = {"cube": "krychle", "cuboid": "kvádr", "sphere": "koule", "cylinder": "válec"}
    got = {it["id"]: it["name"] for it in sec["items"]}
    if got != expected or set(sec["bank"]) != set(expected.values()):
        raise ValueError(sec)


_VALIDATORS: dict[str, Callable[[dict[str, Any]], None]] = {
    "complements": _v_complements,
    "decompose": _v_decompose,
    "mixed20": _v_mixed20,
    "missing20": _v_missing,
    "word20": _v_word20,
    "place_value": _v_place,
    "sequences": _v_sequences,
    "compare": _v_compare,
    "order": _v_order,
    "number_line": _v_line,
    "round": _v_round,
    "calc100": _v_calc100,
    "missing100": _v_missing,
    "fix_error": _v_fix,
    "stories": _v_stories,
    "challenge_story": _v_challenge_story,
    "groups": _v_groups,
    "array": _v_array,
    "facts": _v_facts,
    "mult_seq": _v_mult_seq,
    "word_mul": _v_word_mul,
    "share": _v_share,
    "make_groups": _v_make_groups,
    "div_facts": _v_div_facts,
    "families": _v_families,
    "word_times": _v_word_times,
    "challenge_mul": _v_challenge_mul,
    "prices": _v_prices,
    "coins": _v_coins,
    "clocks": _v_clocks,
    "duration": _v_duration,
    "table": _v_table,
    "shapes2d": _v_shapes,
    "lines": _v_lines,
    "measure": _v_measure,
    "draw": _v_draw,
    "units": _v_units,
    "solids": _v_solids,
}


def generate_math_grade2_pages(*, seed: int = 20261026) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pages = _pages_from_seed(seed)
    validate_edition(pages)
    answers = build_answer_key(pages)
    if len(answers) != PAGE_COUNT or any(not item["lines"] for item in answers):
        raise ValueError("Answer key does not cover every page")
    meta = {
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "page_count": PAGE_COUNT,
        "title": BOOKLET_TITLE,
        "answers": answers,
    }
    return pages, meta
