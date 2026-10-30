"""Three Grade-2 Czech maths booklets: numbers, times tables, everyday maths.

Tasks are original. The thematic mix follows the Grade-2 outline at
https://www.umimematiku.cz/matematika-detail-2-trida (numbers to 100,
crossing a ten, multiplication and division, time, money, shapes).
Nothing is copied from that site.

The same seed always rebuilds the same prompts and answers. Answers are
computed from the operands that are printed.
"""

from __future__ import annotations

from random import Random
from typing import Any

from creobook.games.base import make_rng

GENERATOR_VERSION = "1.0.0"
PAGE_COUNT = 8
DEFAULT_SEED = 20261026

MINUS = "−"
MUL = "·"
DIV = ":"

CORE = (2, 3, 4, 5, 10)
CHALLENGE = (6, 7, 8, 9)
COINS = (1, 2, 5, 10, 20, 50)
ICONS = ("apple", "star", "ball", "block", "flower", "leaf")

_ONES = ("nula", "jedna", "dva", "tři", "čtyři", "pět", "šest", "sedm", "osm", "devět")
_TEENS = (
    "deset",
    "jedenáct",
    "dvanáct",
    "třináct",
    "čtrnáct",
    "patnáct",
    "šestnáct",
    "sedmnáct",
    "osmnáct",
    "devatenáct",
)
_TENS = (
    "",
    "",
    "dvacet",
    "třicet",
    "čtyřicet",
    "padesát",
    "šedesát",
    "sedmdesát",
    "osmdesát",
    "devadesát",
)
_HOUR_ACC = {
    1: "jednu",
    2: "dvě",
    3: "tři",
    4: "čtyři",
    5: "pět",
    6: "šest",
    7: "sedm",
    8: "osm",
    9: "devět",
    10: "deset",
    11: "jedenáct",
    12: "dvanáct",
}
_HOUR_GEN = {
    1: "jedné",
    2: "druhé",
    3: "třetí",
    4: "čtvrté",
    5: "páté",
    6: "šesté",
    7: "sedmé",
    8: "osmé",
    9: "deváté",
    10: "desáté",
    11: "jedenácté",
    12: "dvanácté",
}
_HOUR_CARD = {
    1: "jedna hodina",
    2: "dvě hodiny",
    3: "tři hodiny",
    4: "čtyři hodiny",
    5: "pět hodin",
    6: "šest hodin",
    7: "sedm hodin",
    8: "osm hodin",
    9: "devět hodin",
    10: "deset hodin",
    11: "jedenáct hodin",
    12: "dvanáct hodin",
}

SETS: dict[str, dict[str, Any]] = {
    "cisla": {
        "title": "Čísla do 100",
        "subtitle": "Sčítání a odčítání · 2. třída",
        "slug": "cisla-do-100",
        "item_min": 150,
        "item_max": 190,
    },
    "nasobilka": {
        "title": "Násobilka",
        "subtitle": "Násobení a dělení · 2. třída",
        "slug": "nasobilka",
        "item_min": 150,
        "item_max": 190,
    },
    "kolem": {
        "title": "Matematika kolem nás",
        "subtitle": "Čas, peníze a tvary · 2. třída",
        "slug": "matematika-kolem-nas",
        "item_min": 90,
        "item_max": 120,
    },
}


def words(n: int) -> str:
    if n == 100:
        return "sto"
    if n < 10:
        return _ONES[n]
    if n < 20:
        return _TEENS[n - 10]
    tens, ones = divmod(n, 10)
    if ones == 0:
        return _TENS[tens]
    return f"{_TENS[tens]} {_ONES[ones]}"


def digital(hour: int, minute: int) -> str:
    return f"{hour}:{minute:02d}"


def next_hour(hour: int) -> int:
    return 1 if hour == 12 else hour + 1


def time_phrase(hour: int, minute: int) -> str:
    nxt = next_hour(hour)
    if minute == 0:
        return _HOUR_CARD[hour]
    if minute == 15:
        return f"čtvrt na {_HOUR_ACC[nxt]}"
    if minute == 30:
        return f"půl {_HOUR_GEN[nxt]}"
    if minute == 45:
        return f"tři čtvrtě na {_HOUR_ACC[nxt]}"
    raise ValueError(f"unsupported minute {minute}")


def clock_degrees(hour: int, minute: int) -> tuple[float, float]:
    minute_cw = minute * 6
    hour_cw = (hour % 12) * 30 + minute * 0.5
    return hour_cw - 90, minute_cw - 90


def hand_sentence(hour: int, minute: int) -> str:
    nxt = next_hour(hour)
    if minute == 0:
        return f"malá ručička na {hour}, velká na 12"
    if minute == 15:
        return f"malá ručička mezi {hour} a {nxt}, blíž k {hour}, velká na 3"
    if minute == 30:
        return f"malá ručička mezi {hour} a {nxt}, velká na 6"
    if minute == 45:
        return f"malá ručička mezi {hour} a {nxt}, blíž k {nxt}, velká na 9"
    raise ValueError(minute)


def result(a: int, op: str, b: int) -> int:
    if op == "+":
        value = a + b
    elif op == MINUS:
        value = a - b
    elif op == MUL:
        value = a * b
    elif op == DIV:
        if b == 0 or a % b != 0:
            raise ValueError(f"illegal division {a}:{b}")
        value = a // b
    else:
        raise ValueError(op)
    for n in (a, b, value):
        if not isinstance(n, int) or isinstance(n, bool) or n < 0 or n > 100:
            raise ValueError(f"out of range {a} {op} {b} = {value}")
    return value


def _band(item: Any) -> int:
    if isinstance(item, int):
        return item
    if len(item) >= 3 and isinstance(item[1], str):
        return max(item[0], item[2])
    return int(item[0])


def take(rng: Random, pool: list[Any], n: int, used: set[Any]) -> list[Any]:
    fresh = [p for p in pool if p not in used]
    if len(fresh) < n:
        raise ValueError(f"need {n}, pool has {len(fresh)}")
    rng.shuffle(fresh)
    picked = fresh[:n]
    picked.sort(key=_band)
    used.update(picked)
    return picked


def take_ops(
    rng: Random,
    used: set[Any],
    add_pool: list[tuple[int, str, int]],
    sub_pool: list[tuple[int, str, int]],
    n: int,
    rule: str,
) -> list[dict[str, Any]]:
    n_sub = n // 2
    n_add = n - n_sub
    adds = take(rng, add_pool, n_add, used)
    subs = take(rng, sub_pool, n_sub, used)
    mixed: list[tuple[int, str, int]] = []
    for i in range(max(len(adds), len(subs))):
        if i < len(adds):
            mixed.append(adds[i])
        if i < len(subs):
            mixed.append(subs[i])
    return [as_calc(p, rule) for p in mixed]


def as_calc(triple: tuple[int, str, int], rule: str) -> dict[str, Any]:
    a, op, b = triple
    return {"a": a, "op": op, "b": b, "answer": result(a, op, b), "rule": rule}


def blk(kind: str, title: str, items: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"kind": kind, "title": title, "items": items}
    data.update(extra)
    data["count"] = int(extra["count"]) if "count" in extra else len(items)
    return data


def note(text: str) -> dict[str, Any]:
    return {"kind": "note", "title": "", "text": text, "items": [], "count": 0}


def eq(a: int, op: str, b: int, answer: int | None = None) -> str:
    value = result(a, op, b) if answer is None else answer
    return f"{a} {op} {b} = {value}"


def _pools() -> dict[str, list[Any]]:
    cross20_add = [(a, "+", b) for a in range(2, 10) for b in range(2, 10) if 11 <= a + b <= 18]
    cross20_sub = [
        (a, MINUS, b) for a in range(11, 19) for b in range(2, 10) if b > a % 10 and a % 10 != 0
    ]
    tens_add, tens_sub, addtens_add, addtens_sub = [], [], [], []
    for a in range(10, 100, 10):
        for b in range(10, 100, 10):
            if a + b <= 100:
                tens_add.append((a, "+", b))
            if 0 < b < a:
                tens_sub.append((a, MINUS, b))
    for a in range(11, 100):
        if a % 10 == 0:
            continue
        for b in range(10, 100, 10):
            if a + b <= 100:
                addtens_add.append((a, "+", b))
            if a - b >= 0:
                addtens_sub.append((a, MINUS, b))
    nc1_add, nc1_sub, nc2_add, nc2_sub = [], [], [], []
    c1_add, c1_sub, c2_add, c2_sub = [], [], [], []
    for a in range(10, 100):
        for b in range(1, 10):
            if (a % 10) + b <= 9 and a + b <= 100:
                nc1_add.append((a, "+", b))
            if (a % 10) >= b:
                nc1_sub.append((a, MINUS, b))
            if a % 10 != 0 and (a % 10) + b >= 10 and a + b <= 100:
                c1_add.append((a, "+", b))
            if b > a % 10 and a - b >= 0:
                c1_sub.append((a, MINUS, b))
    for a in range(12, 90):
        if a % 10 == 0:
            continue
        for b in range(11, 90):
            if b % 10 == 0:
                continue
            if (a % 10) + (b % 10) <= 9 and a + b <= 100:
                nc2_add.append((a, "+", b))
            if a > b and (a % 10) >= (b % 10):
                nc2_sub.append((a, MINUS, b))
            if (a % 10) + (b % 10) >= 10 and a + b <= 100:
                c2_add.append((a, "+", b))
    for a in range(21, 100):
        for b in range(12, a):
            if (a % 10) < (b % 10):
                c2_sub.append((a, MINUS, b))
    mul = {
        f: [(f, MUL, k) for k in range(1, 11)]
        for f in (2, 3, 4, 5, 6, 7, 8, 9, 10)
    }
    div = {
        d: [(d * q, DIV, d) for q in range(1, 11) if d * q <= 100]
        for d in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    }
    zeros = [(f, MUL, 0) for f in CORE] + [(0, MUL, f) for f in CORE]
    ones = [(f, MUL, 1) for f in CORE] + [(1, MUL, f) for f in CORE]
    tens_mul = [(10, MUL, k) for k in range(2, 10)]
    return {
        "cross20_add": cross20_add,
        "cross20_sub": cross20_sub,
        "tens_add": tens_add,
        "tens_sub": tens_sub,
        "addtens_add": addtens_add,
        "addtens_sub": addtens_sub,
        "nc1_add": nc1_add,
        "nc1_sub": nc1_sub,
        "nc2_add": nc2_add,
        "nc2_sub": nc2_sub,
        "c1_add": c1_add,
        "c1_sub": c1_sub,
        "c2_add": c2_add,
        "c2_sub": c2_sub,
        "mul": mul,
        "div": div,
        "zeros": zeros,
        "ones": ones,
        "tens_mul": tens_mul,
    }


def _split_add(a: int, b: int) -> tuple[int, int, int]:
    bridge = 10 - (a % 10)
    rest = b - bridge
    if not (1 <= bridge <= 9 and rest >= 1 and (a + bridge) % 10 == 0):
        raise ValueError(f"bad add split {a}+{b}")
    return bridge, rest, a + b


def _split_sub(a: int, b: int) -> tuple[int, int, int]:
    bridge = a % 10
    rest = b - bridge
    if not (bridge >= 1 and rest >= 1 and (a - bridge) % 10 == 0):
        raise ValueError(f"bad sub split {a}-{b}")
    return bridge, rest, a - b


def _splittable(triple: tuple[int, str, int]) -> bool:
    a, op, b = triple
    if op == "+":
        bridge = 10 - (a % 10)
        return 1 <= bridge <= 9 and b - bridge >= 1
    return a % 10 >= 1 and b - a % 10 >= 1


def _decomp(triple: tuple[int, str, int]) -> dict[str, Any]:
    a, op, b = triple
    if op == "+":
        bridge, rest, answer = _split_add(a, b)
    else:
        bridge, rest, answer = _split_sub(a, b)
    return {
        "a": a,
        "op": op,
        "b": b,
        "bridge": bridge,
        "rest": rest,
        "answer": answer,
    }


def _choice(rng: Random, item: dict[str, Any]) -> dict[str, Any]:
    ans = item["answer"]
    cands = []
    for delta in (1, -1, 2, -2, 10, -10):
        value = ans + delta
        if 0 <= value <= 100 and value != ans:
            cands.append(value)
    rng.shuffle(cands)
    opts = [ans, cands[0], cands[1]]
    if len(set(opts)) != 3:
        raise ValueError(opts)
    rng.shuffle(opts)
    return {
        "prompt": f"{item['a']} {item['op']} {item['b']}",
        "options": opts,
        "answer": ans,
        "a": item["a"],
        "op": item["op"],
        "b": item["b"],
    }


def _pair_blk(rng: Random, title: str, calcs: list[dict[str, Any]]) -> dict[str, Any]:
    packed = _text_pairs(rng, calcs)
    return blk(
        "pairs",
        title,
        packed["items"],
        left=packed["left"],
        right=packed["right"],
        links=packed["links"],
    )


def _text_pairs(rng: Random, items: list[dict[str, Any]]) -> dict[str, Any]:
    answers = [str(it["answer"]) for it in items]
    if len(set(answers)) != len(answers):
        raise ValueError("pair answers must be unique")
    left = [f"{it['a']} {it['op']} {it['b']}" for it in items]
    order = list(range(len(left)))
    rng.shuffle(order)
    guard = 0
    while order == list(range(len(left))) and guard < 8:
        rng.shuffle(order)
        guard += 1
    right = [answers[i] for i in order]
    links = [order.index(i) for i in range(len(order))]
    return {
        "left": left,
        "right": right,
        "links": links,
        "items": [{"answer": answers[i]} for i in range(len(left))],
    }


def _take_unique_calcs(
    rng: Random,
    pool: list[tuple[int, str, int]],
    n: int,
    used: set[Any],
    rule: str,
) -> list[dict[str, Any]]:
    fresh = [p for p in pool if p not in used]
    rng.shuffle(fresh)
    picked: list[tuple[int, str, int]] = []
    seen: set[int] = set()
    for triple in fresh:
        ans = result(*triple)
        if ans in seen:
            continue
        picked.append(triple)
        seen.add(ans)
        if len(picked) == n:
            break
    if len(picked) != n:
        raise ValueError("not enough unique answers")
    picked.sort(key=_band)
    used.update(picked)
    return [as_calc(p, rule) for p in picked]


def _missing(triple: tuple[int, str, int], form: str) -> dict[str, Any]:
    a, op, b = triple
    c = result(a, op, b)
    if form in ("add_left", "add_right") and op != "+":
        raise ValueError(form)
    if form in ("sub_left", "sub_right") and op != MINUS:
        raise ValueError(form)
    if form == "add_left":
        answer = a
    elif form == "add_right":
        answer = b
    elif form == "sub_left":
        answer = a
    elif form == "sub_right":
        answer = b
    else:
        raise ValueError(form)
    return {"form": form, "a": a, "b": b, "c": c, "op": op, "answer": answer}


def _fix(rng: Random, item: dict[str, Any]) -> dict[str, Any]:
    ans = item["answer"]
    deltas = [1, -1, 10, -10, 2, -2]
    rng.shuffle(deltas)
    shown = None
    for delta in deltas:
        cand = ans + delta
        if 0 <= cand <= 100 and cand != ans:
            shown = cand
            break
    if shown is None:
        raise ValueError("no wrong result")
    return {**item, "shown": shown, "answer": ans}


def _seq(start: int, step: int, length: int = 6) -> dict[str, Any]:
    vals = [start + i * step for i in range(length)]
    if any(v < 0 or v > 100 for v in vals):
        raise ValueError(vals)
    cells = [("" if i in (2, 4) else str(v)) for i, v in enumerate(vals)]
    return {"style": "row", "cells": cells, "answers": [vals[2], vals[4]]}


def _line(start: int) -> dict[str, Any]:
    vals = [start + i * 10 for i in range(6)]
    if vals[-1] > 100:
        raise ValueError(vals)
    cells = [("" if i in (2, 4) else str(v)) for i, v in enumerate(vals)]
    return {"style": "line", "cells": cells, "answers": [vals[2], vals[4]]}


def _pyramid(rng: Random, lo: int, hi: int) -> dict[str, Any]:
    for _ in range(200):
        bottom = [rng.randint(lo, hi) for _ in range(3)]
        mid = [bottom[0] + bottom[1], bottom[1] + bottom[2]]
        top = mid[0] + mid[1]
        if top <= 100:
            return {"bottom": bottom, "mid": mid, "top": top}
    raise RuntimeError("pyramid")


def _chain(rng: Random, start: int, steps_n: int = 3) -> dict[str, Any]:
    cur = start
    steps = []
    for _ in range(steps_n):
        can_add = cur <= 90
        can_sub = cur >= 8
        if can_add and (not can_sub or rng.random() < 0.65):
            n = rng.randint(2, min(15, 100 - cur))
            cur += n
            op = "+"
        else:
            n = rng.randint(2, min(12, cur))
            cur -= n
            op = MINUS
        steps.append({"op": op, "n": n, "answer": cur})
    return {"start": start, "steps": steps}


def _symbols(rng: Random) -> dict[str, Any]:
    circle = rng.randint(2, 8)
    square = rng.randint(2, 8)
    while square == circle:
        square = rng.randint(2, 8)
    values = {"circle": circle, "square": square}
    questions = [
        {"ids": ["circle", "square"], "op": "+", "answer": circle + square},
        {"ids": ["square", "square", "circle"], "op": "+", "answer": square + square + circle},
        {"ids": ["circle", "circle", "circle"], "op": "+", "answer": circle * 3},
    ]
    return {
        "values": values,
        "models": [
            {"ids": ["circle", "circle"], "op": "+", "result": circle * 2, "name": "kruh", "value": circle},
            {"ids": ["square", "square"], "op": "+", "result": square * 2, "name": "čtverec", "value": square},
        ],
        "items": questions,
    }


def _expr_sides(limit: int = 70) -> list[tuple[int, str, int, int]]:
    rows = []
    for a in range(0, limit):
        for b in range(1, 16):
            if a + b <= 100:
                rows.append((a, "+", b, a + b))
            if a >= b:
                rows.append((a, MINUS, b, a - b))
    return rows


def _compare_exprs(rng: Random, n: int) -> list[dict[str, Any]]:
    rows = _expr_sides()
    by_val: dict[int, list[tuple[int, str, int, int]]] = {}
    for row in rows:
        by_val.setdefault(row[3], []).append(row)
    equals = [v for v, group in by_val.items() if len(group) >= 2]
    rng.shuffle(equals)
    items: list[dict[str, Any]] = []
    used_pairs: set[tuple[Any, Any]] = set()

    def add(left: tuple[int, str, int, int], right: tuple[int, str, int, int]) -> bool:
        key = (left[:3], right[:3])
        if key in used_pairs or left[:3] == right[:3]:
            return False
        symbol = "<" if left[3] < right[3] else (">" if left[3] > right[3] else "=")
        items.append(
            {
                "a": left[0],
                "op": left[1],
                "b": left[2],
                "c": right[0],
                "op2": right[1],
                "d": right[2],
                "left": left[3],
                "right": right[3],
                "answer": symbol,
            }
        )
        used_pairs.add(key)
        return True

    sample = rows[:]
    rng.shuffle(sample)
    sample = sample[:120]
    for symbol in ("<", ">", "="):
        found = False
        for left in sample:
            for right in sample:
                got = "<" if left[3] < right[3] else (">" if left[3] > right[3] else "=")
                if got == symbol and add(left, right):
                    found = True
                    break
            if found:
                break
        if not found:
            raise ValueError(f"missing compare {symbol}")
    guard = 0
    while len(items) < n and guard < 800:
        guard += 1
        add(rng.choice(rows), rng.choice(rows))
    if len(items) < n:
        raise ValueError("compare exprs")
    symbols = {it["answer"] for it in items}
    if symbols != {"<", ">", "="}:
        raise ValueError(f"compare symbols {symbols}")
    return items[:n]


def _brackets(rng: Random, n: int) -> list[dict[str, Any]]:
    pool: list[dict[str, Any]] = []
    for b in range(1, 21):
        for c in range(1, 16):
            inner = b + c
            if inner > 60:
                continue
            for a in (inner, inner + 4, inner + 9, min(100, inner + 15)):
                if inner <= a <= 100:
                    pool.append(
                        {"form": "sub_sum", "a": a, "b": b, "c": c, "answer": a - inner}
                    )
            if b > c:
                diff = b - c
                for a in (diff, diff + 6, diff + 12):
                    if 0 <= a - diff <= 100 and a <= 100:
                        pool.append(
                            {
                                "form": "sub_diff",
                                "a": a,
                                "b": b,
                                "c": c,
                                "answer": a - diff,
                            }
                        )
            total = b + c
            for a in (3, 8, 12, 20):
                if a + total <= 100:
                    pool.append(
                        {"form": "add_sum", "a": a, "b": b, "c": c, "answer": a + total}
                    )
    rng.shuffle(pool)
    picked: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    forms: set[str] = set()
    for item in pool:
        key = (item["form"], item["a"], item["b"], item["c"])
        if key in seen:
            continue
        seen.add(key)
        picked.append(item)
        forms.add(item["form"])
        if len(picked) == n and forms == {"sub_sum", "add_sum", "sub_diff"}:
            break
    if len(picked) < n or forms != {"sub_sum", "add_sum", "sub_diff"}:
        raise ValueError("brackets")
    return picked[:n]


def _page(
    *,
    seed: int,
    index: int,
    heading: str,
    blocks: list[dict[str, Any]],
    title: str,
    subtitle: str,
    show_name: bool,
    note_text: str = "",
) -> dict[str, Any]:
    letters = "ABCDEFGH"
    li = 0
    for block in blocks:
        if block["kind"] == "note":
            block["letter"] = ""
            continue
        block["letter"] = letters[li]
        li += 1
    return {
        "kind": "math_set",
        "title": heading,
        "instructions": "",
        "difficulty": "easy",
        "seed": seed + index,
        "data": {
            "booklet_title": title,
            "subtitle": subtitle,
            "heading": heading,
            "show_name": show_name,
            "note": note_text,
            "page_no": index,
            "blocks": blocks,
        },
        "answer": {},
    }


def _compares(rng: Random, n: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    x = rng.randint(12, 80)
    items.append({"a": x, "b": x, "answer": "="})
    seen.add((x, x))
    lo, hi = rng.sample(range(0, 101), 2)
    items.append({"a": min(lo, hi), "b": max(lo, hi), "answer": "<"})
    items.append({"a": max(lo, hi), "b": min(lo, hi), "answer": ">"})
    seen.add((min(lo, hi), max(lo, hi)))
    seen.add((max(lo, hi), min(lo, hi)))
    while len(items) < n:
        a = rng.randint(0, 100)
        b = rng.randint(0, 100)
        if a == b or (a, b) in seen:
            continue
        seen.add((a, b))
        items.append({"a": a, "b": b, "answer": "<" if a < b else ">"})
    items.sort(key=lambda it: max(it["a"], it["b"]))
    symbols = {it["answer"] for it in items}
    if symbols != {"<", ">", "="}:
        raise ValueError(symbols)
    nums = [rng.randint(0, 100) for _ in range(4)]
    while len(set(nums)) < 4:
        nums = [rng.randint(0, 100) for _ in range(4)]
    order = {"numbers": nums, "answer": sorted(nums)}
    if nums == order["answer"]:
        nums = list(reversed(order["answer"]))
        order["numbers"] = nums
    return items, order


def _words_and_place(rng: Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    small = rng.choice([4, 6, 8, 9])
    teen = rng.choice([11, 13, 14, 17, 19])
    round_ten = rng.choice([20, 40, 50, 80])
    mixed = rng.sample([28, 35, 42, 56, 63, 74, 81, 97], 3)
    hundred = 100
    to_num = [small, teen, mixed[0]]
    to_words = [round_ten, mixed[1], hundred]
    word_items = [
        {"mode": "to_num", "prompt": words(n), "answer": str(n)} for n in to_num
    ] + [{"mode": "to_words", "prompt": str(n), "answer": words(n)} for n in to_words]
    place_nums = [round_ten, mixed[2], *rng.sample([23, 37, 48, 61, 79, 85, 92], 4)]
    place_nums = place_nums[:6]
    place = []
    for i, n in enumerate(sorted(place_nums)):
        tens, ones = divmod(n, 10)
        if i % 2 == 0:
            place.append({"shown": f"{n} = {tens * 10} +", "suffix": "", "answer": str(ones)})
        else:
            place.append({"shown": f"{n} =", "suffix": f"+ {ones}", "answer": str(tens * 10)})
    return word_items, place


def _signs(rng: Random, pool: list[tuple[int, str, int]], n: int, used: set[Any]) -> list[dict[str, Any]]:
    fresh = []
    for a, op, b in pool:
        if b == 0 or (a, op, b) in used:
            continue
        res = result(a, op, b)
        try:
            other = result(a, MINUS if op == "+" else "+", b)
        except ValueError:
            other = None
        if other == res:
            continue
        fresh.append((a, b, res, op))
    rng.shuffle(fresh)
    picked = fresh[:n]
    if len(picked) < n:
        raise ValueError("signs")
    items = []
    for a, b, res, op in sorted(picked, key=lambda row: row[0]):
        used.add((a, op, b))
        items.append({"a": a, "b": b, "result": res, "answer": "+" if op == "+" else MINUS})
    return items


def _build_cisla(rng: Random, seed: int, pools: dict[str, list[Any]]) -> list[dict[str, Any]]:
    spec = SETS["cisla"]
    title, subtitle = spec["title"], spec["subtitle"]
    used: set[Any] = set()
    pages = []

    word_items, place = _words_and_place(rng)
    sequences = [
        _seq(rng.randint(12, 40), 1),
        _seq(rng.choice([10, 20, 30, 40]), 10),
    ]
    line = _line(rng.choice([10, 20, 30, 40, 50]))
    comps, order = _compares(rng, 6)
    pages.append(
        _page(
            seed=seed,
            index=1,
            heading="Poznáváme čísla",
            title=title,
            subtitle=subtitle,
            show_name=True,
            blocks=[
                blk("wordnum", "Napiš číslo, nebo ho zapiš slovy.", word_items, cols=2),
                blk("place", "Doplň desítky a jednotky.", place, cols=2),
                blk(
                    "seq",
                    "Doplň chybějící čísla. Na ose jsou stejné mezery.",
                    sequences + [line],
                ),
                blk(
                    "compare",
                    "Doplň <, > nebo =. Čtveřici seřaď od nejmenšího.",
                    comps,
                    order=order,
                    count=len(comps) + 1,
                    cols=3,
                ),
            ],
        )
    )

    used.add((8, "+", 5))
    used.add((13, MINUS, 5))
    decomps = [_decomp(p) for p in take(rng, pools["cross20_add"], 2, used)]
    decomps += [_decomp(p) for p in take(rng, pools["cross20_sub"], 1, used)]
    comps10 = []
    for n in take(rng, list(range(1, 10)), 8, used):
        comps10.append({"a": n, "target": 10, "answer": 10 - n})
    calcs = take_ops(rng, used, pools["cross20_add"], pools["cross20_sub"], 12, "cross20")
    pair_calcs = _take_unique_calcs(rng, pools["cross20_add"] + pools["cross20_sub"], 4, used, "cross20")
    pages.append(
        _page(
            seed=seed,
            index=2,
            heading="Přes desítku do 20",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("complement", "Doplň do deseti.", comps10, cols=2),
                blk(
                    "decomp",
                    "Doplň mezikroky i výsledek.",
                    decomps,
                    model_text="Vzor: 8 + 5 = 8 + 2 + 3 = 13.    13 − 5 = 13 − 3 − 2 = 8.",
                ),
                blk("calc", "Spočítej.", calcs, cols=3),
                _pair_blk(rng, "Spoj příklad s výsledkem.", pair_calcs),
            ],
        )
    )

    tens = take_ops(rng, used, pools["tens_add"], pools["tens_sub"], 8, "tens")
    addtens = take_ops(rng, used, pools["addtens_add"], pools["addtens_sub"], 8, "addtens")
    to100 = []
    for n in take(rng, [10, 20, 25, 30, 40, 45, 50, 55, 60, 70, 75, 80, 90], 6, used):
        to100.append({"a": n, "target": 100, "answer": 100 - n})
    signs = _signs(rng, pools["tens_add"] + pools["tens_sub"] + pools["addtens_add"] + pools["addtens_sub"], 6, used)
    pages.append(
        _page(
            seed=seed,
            index=3,
            heading="Počítáme s desítkami",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Spočítej násobky deseti.", tens, cols=2),
                blk("calc", "Přičítej a odčítej desítky.", addtens, cols=2),
                blk("complement", "Doplň do 100.", to100, cols=2),
                blk("sign", "Doplň + nebo −. Platí jen jedno znaménko.", signs, cols=2),
            ],
        )
    )

    one = take_ops(rng, used, pools["nc1_add"], pools["nc1_sub"], 12, "nocross1")
    two = take_ops(rng, used, pools["nc2_add"], pools["nc2_sub"], 6, "nocross2")
    miss_pool = take(rng, pools["nc1_add"], 2, used) + take(rng, pools["nc1_sub"], 2, used)
    forms = ["add_right", "add_left", "sub_right", "sub_left"]
    missing = [_missing(p, forms[i]) for i, p in enumerate(miss_pool)]
    choice_src = take_ops(rng, used, pools["nc1_add"], pools["nc2_sub"], 4, "nocross")
    pages.append(
        _page(
            seed=seed,
            index=4,
            heading="Bez přechodu přes desítku",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Spočítej. Desítky se nemění.", one, cols=3),
                blk("calc", "Spočítej bez výměny desítky.", two, cols=2),
                blk("missing", "Doplň chybějící číslo.", missing, cols=2),
                blk(
                    "choice",
                    "Zakroužkuj správný výsledek.",
                    [_choice(rng, it) for it in choice_src],
                    cols=2,
                ),
            ],
        )
    )

    c_one = take_ops(rng, used, pools["c1_add"], pools["c1_sub"], 12, "cross1")
    c_two = take_ops(rng, used, pools["c2_add"], pools["c2_sub"], 6, "cross2")
    d_add = [_decomp(p) for p in take(rng, [p for p in pools["c1_add"] if _splittable(p)], 2, used)]
    d_sub = [_decomp(p) for p in take(rng, [p for p in pools["c1_sub"] if _splittable(p)], 2, used)]
    model = d_add[0]
    model_sub = d_sub[0]
    practice = d_add[1:] + d_sub[1:]
    extra = take_ops(rng, used, pools["c1_add"], pools["c2_sub"], 4, "cross")
    pages.append(
        _page(
            seed=seed,
            index=5,
            heading="S přechodem přes desítku",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Spočítej s přechodem.", c_one, cols=3),
                blk("calc", "Spočítej dvojciferná čísla.", c_two, cols=2),
                blk(
                    "decomp",
                    "Doplň mezikroky i výsledek.",
                    practice,
                    model_text=(
                        f"Vzor: {model['a']} + {model['b']} = {model['a']} + {model['bridge']} + "
                        f"{model['rest']} = {model['answer']}.    "
                        f"{model_sub['a']} − {model_sub['b']} = {model_sub['a']} − {model_sub['bridge']} − "
                        f"{model_sub['rest']} = {model_sub['answer']}."
                    ),
                ),
                blk("calc", "Ještě spočítej.", extra, cols=2),
            ],
        )
    )

    miss_adds = take(rng, pools["c1_add"] + pools["nc1_add"], 2, used) + take(rng, pools["nc2_add"], 2, used)
    miss_subs = take(rng, pools["c1_sub"] + pools["nc1_sub"], 2, used) + take(rng, pools["c2_sub"], 2, used)
    missing6 = [_missing(p, "add_left" if i % 2 == 0 else "add_right") for i, p in enumerate(miss_adds)]
    missing6 += [_missing(p, "sub_left" if i % 2 == 0 else "sub_right") for i, p in enumerate(miss_subs)]
    fix_src = take_ops(rng, used, pools["nc2_add"], pools["c1_sub"], 4, "any")
    pages.append(
        _page(
            seed=seed,
            index=6,
            heading="Porovnej a doplň",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("compare_expr", "Doplň <, > nebo =.", _compare_exprs(rng, 8), cols=2),
                blk("missing", "Doplň sčítanec, menšenec, nebo menšitel.", missing6, cols=2),
                blk("brackets", "Spočítej. Nejdřív závorku.", _brackets(rng, 4), cols=2),
                blk(
                    "fix",
                    "Oprav výsledek. Čísla vlevo nech.",
                    [_fix(rng, it) for it in fix_src],
                    cols=2,
                ),
            ],
        )
    )

    sym = _symbols(rng)
    web_start = rng.randint(18, 55)
    web_items = []
    web_ops = [("+", rng.randint(3, 12)), ("+", rng.randint(13, 20)), (MINUS, rng.randint(3, 12))]
    for op, n in web_ops:
        ans = web_start + n if op == "+" else web_start - n
        if not 0 <= ans <= 100:
            raise ValueError("web")
        web_items.append({"op": op, "n": n, "answer": ans})
    pages.append(
        _page(
            seed=seed,
            index=7,
            heading="Početní hlavolamy",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk(
                    "pyramid",
                    "Horní políčko je součet dvou políček přímo pod ním.",
                    [_pyramid(rng, 2, 9), _pyramid(rng, 8, 20)],
                ),
                blk(
                    "chain",
                    "Počítej zleva doprava. Doplň každé políčko.",
                    [_chain(rng, rng.randint(8, 20)), _chain(rng, rng.randint(25, 45)), _chain(rng, rng.randint(30, 60))],
                ),
                blk(
                    "symbols",
                    "Stejný tvar znamená stejné číslo.",
                    sym["items"],
                    models=sym["models"],
                    values=sym["values"],
                ),
                blk(
                    "web",
                    "Šipka vede od čísla k políčku. Doplň výsledek.",
                    web_items,
                    start=web_start,
                ),
            ],
        )
    )

    mixed = (
        take_ops(rng, used, pools["nc1_add"], pools["nc1_sub"], 4, "nocross1")
        + take_ops(rng, used, pools["c1_add"], pools["c1_sub"], 4, "cross1")
        + take_ops(rng, used, pools["addtens_add"], pools["tens_sub"], 4, "any")
    )
    mixed_choice = take_ops(rng, used, pools["c2_add"], pools["nc2_sub"], 4, "any")
    a = rng.randint(12, 40)
    b = rng.randint(5, 18)
    c = rng.randint(20, 55)
    d = rng.randint(5, min(15, c - 1))
    e = rng.randint(10, 40)
    f = rng.randint(5, 16)
    stories = [
        {
            "prompt": f"Na polici je {a} knih. Přibude {b} knih. Kolik je jich teď?",
            "answer": str(a + b),
            "value": a + b,
        },
        {
            "prompt": f"V misce je {c} jahod. Sníme {d} jahod. Kolik zbude?",
            "answer": str(c - d),
            "value": c - d,
        },
        {
            "prompt": f"Petr má {e} korálků. Lenka má o {f} více. Kolik má Lenka?",
            "answer": str(e + f),
            "value": e + f,
        },
    ]
    pages.append(
        _page(
            seed=seed,
            index=8,
            heading="Smíšený trénink",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Spočítej.", mixed, cols=2),
                blk(
                    "choice",
                    "Zakroužkuj správný výsledek.",
                    [_choice(rng, it) for it in mixed_choice],
                    cols=2,
                ),
                blk("story", "Vypočítej a napiš odpověď.", stories),
                blk(
                    "chain",
                    "Počítej zleva doprava.",
                    [_chain(rng, rng.randint(15, 40), 3)],
                ),
            ],
        )
    )
    return pages


def _mul_items(triples: list[tuple[int, str, int]], rule: str) -> list[dict[str, Any]]:
    return [as_calc(p, rule) for p in triples]


def _mul_seq(factor: int) -> dict[str, Any]:
    vals = [factor * i for i in range(1, 7)]
    cells = [("" if i in (2, 4) else str(v)) for i, v in enumerate(vals)]
    return {"style": "row", "cells": cells, "answers": [vals[2], vals[4]], "factor": factor}


def _parity(rng: Random, n: int) -> list[dict[str, Any]]:
    evens = [i for i in range(0, 101, 2)]
    odds = [i for i in range(1, 100, 2)]
    rng.shuffle(evens)
    rng.shuffle(odds)
    nums = evens[: n // 2] + odds[: n - n // 2]
    rng.shuffle(nums)
    nums.sort()
    return [{"n": v, "answer": "sudé" if v % 2 == 0 else "liché"} for v in nums]


def _table(rows: list[int], cols: list[int], blanks: list[tuple[int, int]]) -> dict[str, Any]:
    items = []
    for r, c in blanks:
        items.append({"row": rows[r], "col": cols[c], "answer": rows[r] * cols[c], "r": r, "c": c})
    return {"rows": rows, "cols": cols, "items": items}


def _family(triple: tuple[int, str, int]) -> dict[str, Any]:
    a, _op, b = triple
    prod = a * b
    return {
        "a": a,
        "b": b,
        "product": prod,
        "answer_div": b and prod // b,
        "answer_div2": a,
    }


def _story_groups(g: int, e: int) -> dict[str, Any]:
    return {
        "prompt": f"Skupin je {g}. V každé je {e} tužek. Kolik je tužek?",
        "answer": str(g * e),
        "value": g * e,
        "kind_story": "groups",
    }


def _story_share(n: int, d: int) -> dict[str, Any]:
    return {
        "prompt": (
            f"Bonbonů je {n}. Dětí je {d}. Každé dítě dostane stejně. "
            "Kolik dostane jedno dítě?"
        ),
        "answer": str(n // d),
        "value": n // d,
        "kind_story": "share",
    }


def _story_times(rng: Random) -> dict[str, Any]:
    a = rng.randint(5, 10)
    k = rng.choice([2, 3, 4, 5])
    while a * k > 100 or a * k == a + k:
        a = rng.randint(5, 8)
        k = rng.choice([3, 4, 5])
    if rng.random() < 0.5:
        return {
            "prompt": (
                f"V košíku je {a} rohlíků. V pytli je jich {k}krát více. Kolik je v pytli?"
            ),
            "answer": str(a * k),
            "value": a * k,
            "kind_story": "times_more",
        }
    big = a * k
    return {
        "prompt": (
            f"V pytli je {big} rohlíků. V košíku je jich {k}krát méně. Kolik je v košíku?"
        ),
        "answer": str(a),
        "value": a,
        "kind_story": "times_less",
    }


def _build_nasobilka(rng: Random, seed: int, pools: dict[str, list[Any]]) -> list[dict[str, Any]]:
    spec = SETS["nasobilka"]
    title, subtitle = spec["title"], spec["subtitle"]
    used: set[Any] = set()
    pages = []

    model = {"groups": 4, "each": 3, "icon": "apple"}
    used.add((4, MUL, 3))
    practice = []
    options = [(2, 5), (3, 4), (5, 2), (2, 6), (3, 5), (4, 4), (5, 3), (2, 4)]
    rng.shuffle(options)
    for g, e in options:
        if (g, MUL, e) in used:
            continue
        practice.append({"groups": g, "each": e, "icon": ICONS[len(practice) % len(ICONS)], "answer": g * e})
        used.add((g, MUL, e))
        if len(practice) == 2:
            break
    rewrites = []
    for g, _op, e in take(rng, [(g, MUL, e) for g in (2, 3) for e in range(2, 8)], 6, used):
        rewrites.append({"groups": g, "each": e, "answer": g * e})
    arrays = []
    for rows, _op, cols in take(rng, [(r, MUL, c) for r in (2, 3, 4) for c in (2, 3, 4, 5)], 2, used):
        arrays.append({"rows": rows, "cols": cols, "answer": rows * cols})
    pic = []
    for g, _op, e in take(rng, [(5, MUL, e) for e in range(2, 8)], 4, used):
        pic.append(
            {
                "groups": g,
                "each": e,
                "icon": ICONS[g % len(ICONS)],
                "expr": f"{g} {MUL} {e}",
                "answer": f"{g} {MUL} {e}",
            }
        )
    exprs = [it["expr"] for it in pic]
    order = list(range(4))
    rng.shuffle(order)
    if order == [0, 1, 2, 3]:
        order = [1, 0, 3, 2]
    pages.append(
        _page(
            seed=seed,
            index=1,
            heading="Stejné skupiny",
            title=title,
            subtitle=subtitle,
            show_name=True,
            blocks=[
                blk(
                    "groups",
                    "Kolik je předmětů?",
                    practice,
                    model=model,
                    model_text="4 skupiny po 3: 3 + 3 + 3 + 3 = 4 · 3 = 12.",
                ),
                blk("rewrite", "Přepiš sčítání na násobení a doplň výsledek.", rewrites, cols=2),
                blk("array", "Kolik je puntíků?", arrays, cols=2),
                blk(
                    "pic_pairs",
                    "Spoj obrázek s výpočtem.",
                    pic,
                    left=[{"groups": it["groups"], "each": it["each"], "icon": it["icon"]} for it in pic],
                    right=[exprs[i] for i in order],
                    links=[order.index(i) for i in range(4)],
                ),
            ],
        )
    )

    used = set()
    facts23 = _mul_items(take(rng, pools["mul"][2], 5, used) + take(rng, pools["mul"][3], 5, used), "mul23")
    facts23.sort(key=lambda it: (it["a"], it["b"]))
    seqs = [_mul_seq(2), _mul_seq(3)]
    missing_src = take(rng, pools["mul"][2] + pools["mul"][3], 4, used)
    missing = [
        {"a": a, "b": b, "answer": b, "product": a * b, "form": "right"}
        for a, _op, b in missing_src
    ]
    pair_src = _take_unique_calcs(rng, pools["mul"][2] + pools["mul"][3], 4, used, "mul23")
    pages.append(
        _page(
            seed=seed,
            index=2,
            heading="Násobíme dvěma a třemi",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Spočítej.", facts23, cols=3),
                blk("seq", "Doplň řadu násobků.", seqs),
                blk("factor", "Doplň chybějící činitel.", missing, cols=2),
                _pair_blk(rng, "Spoj příklad s výsledkem.", pair_src),
                blk("parity", "Zakroužkuj, zda je číslo sudé, nebo liché.", _parity(rng, 6), cols=3),
            ],
        )
    )

    used = set()
    facts45 = _mul_items(take(rng, pools["mul"][4], 5, used) + take(rng, pools["mul"][5], 5, used), "mul45")
    facts45.sort(key=lambda it: (it["a"], it["b"]))
    ch_src = take(rng, pools["mul"][4] + pools["mul"][5], 2, used)
    miss45 = [
        {"a": a, "b": b, "answer": b, "product": a * b, "form": "right"}
        for a, _op, b in take(rng, pools["mul"][4] + pools["mul"][5], 2, used)
    ]
    cmp_src = _take_unique_calcs(rng, pools["mul"][4] + pools["mul"][5], 4, used, "mul45")
    cmp_items = []
    for i in range(0, 4, 2):
        left, right = cmp_src[i], cmp_src[i + 1]
        symbol = "<" if left["answer"] < right["answer"] else (">" if left["answer"] > right["answer"] else "=")
        cmp_items.append(
            {
                "a": left["a"],
                "op": MUL,
                "b": left["b"],
                "c": right["a"],
                "op2": MUL,
                "d": right["b"],
                "left": left["answer"],
                "right": right["answer"],
                "answer": symbol,
            }
        )
    g, e = 5, 4
    pages.append(
        _page(
            seed=seed,
            index=3,
            heading="Násobíme čtyřmi a pěti",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Spočítej.", facts45, cols=3),
                blk("choice", "Zakroužkuj správný výsledek.", [_choice(rng, as_calc(p, "mul45")) for p in ch_src], cols=2),
                blk("factor", "Doplň chybějící činitel.", miss45, cols=2),
                blk("compare_expr", "Porovnej součiny.", cmp_items, cols=2),
                blk("story", "Vypočítej.", [_story_groups(g, e)]),
            ],
        )
    )

    used = set()
    special = _mul_items(
        take(rng, pools["zeros"], 2, used) + take(rng, pools["ones"], 4, used) + take(rng, pools["tens_mul"], 6, used),
        "mul01",
    )
    mix_pool = pools["mul"][2] + pools["mul"][3] + pools["mul"][4] + pools["mul"][5] + pools["mul"][10]
    mixed = _mul_items(take(rng, mix_pool, 9, used), "mulmix")
    table = _table([2, 4, 5], [3, 5, 10], [(0, 1), (1, 0), (1, 2), (2, 1)])
    fix_src = _mul_items(take(rng, mix_pool, 4, used), "mulmix")
    pages.append(
        _page(
            seed=seed,
            index=4,
            heading="Nula, jedna, deset a smíšený trénink",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Násobení nulou, jedničkou a deseti.", special, cols=2),
                blk("calc", "Smíchej násobilky 2, 3, 4, 5 a 10.", mixed, cols=3),
                blk(
                    "table",
                    "Doplň tabulku. V záhlaví jsou činitele.",
                    table["items"],
                    rows=table["rows"],
                    cols=table["cols"],
                ),
                blk("fix", "Oprav výsledek. Činitele nech.", [_fix(rng, it) for it in fix_src], cols=2),
            ],
        )
    )

    used = set()
    visuals = [
        {
            "count": 12,
            "by": 3,
            "mode": "share",
            "answer": 4,
            "prompt": "Mezi 3 děti. Kolik dostane jedno?",
        },
        {
            "count": 12,
            "by": 3,
            "mode": "groups",
            "answer": 4,
            "prompt": "Do sáčků po 3. Kolik bude sáčků?",
        },
        {
            "count": 10,
            "by": 2,
            "mode": "share",
            "answer": 5,
            "prompt": "Mezi 2 děti. Kolik dostane jedno?",
        },
        {
            "count": 15,
            "by": 5,
            "mode": "groups",
            "answer": 3,
            "prompt": "Do misek po 5. Kolik bude misek?",
        },
    ]
    div_facts = _mul_items(
        take(rng, pools["div"][2] + pools["div"][3] + pools["div"][4] + pools["div"][5] + pools["div"][10], 10, used),
        "divcore",
    )
    pages.append(
        _page(
            seed=seed,
            index=5,
            heading="Rozdělujeme stejným dílem",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("dots", "Rozděl. Mezi děti, nebo do skupin dané velikosti.", visuals, cols=2),
                blk("calc", "Děl. Vychází to beze zbytku.", div_facts, cols=2),
                blk("story", "Vypočítej.", [_story_share(20, 5)]),
            ],
        )
    )

    used = set()
    fam_src = take(rng, [p for p in mix_pool if p[2] >= 2], 4, used)
    families = [_family(p) for p in fam_src]
    both = _mul_items(take(rng, mix_pool, 6, used), "mulmix") + _mul_items(
        take(rng, pools["div"][2] + pools["div"][3] + pools["div"][4] + pools["div"][5] + pools["div"][10], 3, used),
        "divcore",
    )
    pages.append(
        _page(
            seed=seed,
            index=6,
            heading="Násobení a dělení patří k sobě",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("family", "Doplň. V trojici jsou stále stejná čísla.", families),
                blk("calc", "Násob i děl.", both, cols=3),
                _same_result_blk(
                    rng,
                    mix_pool
                    + pools["div"][2]
                    + pools["div"][3]
                    + pools["div"][4]
                    + pools["div"][5]
                    + pools["div"][10],
                    used,
                    4,
                ),
            ],
        )
    )

    used = set()
    challenge_blocks = []
    for factor, name in ((6, "šesti"), (7, "sedmi"), (8, "osmi"), (9, "devíti")):
        muls = _mul_items(take(rng, pools["mul"][factor], 4, used), "challenge")
        divs = _mul_items(take(rng, pools["div"][factor], 2, used), "challenge")
        challenge_blocks.append(blk("calc", f"Násobilka {name}.", muls + divs, cols=3))
    pages.append(
        _page(
            seed=seed,
            index=7,
            heading="Výzva navíc: násobilky 6–9",
            title=title,
            subtitle=subtitle,
            show_name=False,
            note_text="Tuto stránku si nech, až budete násobilky 6–9 probírat.",
            blocks=challenge_blocks,
        )
    )

    used = set()
    final = _mul_items(take(rng, mix_pool, 6, used), "mulmix") + _mul_items(
        take(rng, pools["div"][2] + pools["div"][3] + pools["div"][5] + pools["div"][10], 3, used),
        "divcore",
    )
    logic = _table([2, 3, 5], [2, 4, 5], [(0, 2), (1, 0), (2, 1), (2, 2)])
    pages.append(
        _page(
            seed=seed,
            index=8,
            heading="Násobilka v příbězích a příkladech",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("calc", "Spočítej spoje z násobilek 2, 3, 4, 5 a 10.", final, cols=3),
                blk(
                    "story",
                    "3krát více znamená násobení. O 3 více by znamenalo přičtení.",
                    [_story_groups(3, 6), _story_share(15, 3), _story_times(rng)],
                ),
                blk(
                    "table",
                    "Doplň tabulku.",
                    logic["items"],
                    rows=logic["rows"],
                    cols=logic["cols"],
                ),
            ],
        )
    )
    return pages


def _same_result_blk(
    rng: Random,
    pool: list[tuple[int, str, int]],
    used: set[Any],
    n: int,
) -> dict[str, Any]:
    grouped: dict[int, list[tuple[int, str, int]]] = {}
    for triple in pool:
        if triple in used:
            continue
        grouped.setdefault(result(*triple), []).append(triple)
    options = [group for group in grouped.values() if len(group) >= 2]
    rng.shuffle(options)
    pairs: list[tuple[str, str, int]] = []
    for group in options:
        rng.shuffle(group)
        first, second = group[0], group[1]
        if first in used or second in used:
            continue
        left = f"{first[0]} {first[1]} {first[2]}"
        right = f"{second[0]} {second[1]} {second[2]}"
        if left == right:
            continue
        value = result(*first)
        if any(value == seen for _l, _r, seen in pairs):
            continue
        used.add(first)
        used.add(second)
        pairs.append((left, right, value))
        if len(pairs) == n:
            break
    if len(pairs) < n:
        raise ValueError(f"same-result pairs: {len(pairs)}")
    order = list(range(n))
    rng.shuffle(order)
    if order == list(range(n)):
        order = list(reversed(order))
    right_col = [pairs[i][1] for i in order]
    links = [order.index(i) for i in range(n)]
    items = [{"answer": pairs[i][1], "value": pairs[i][2]} for i in range(n)]
    return blk(
        "pairs",
        "Spoj příklady se stejným výsledkem.",
        items,
        left=[p[0] for p in pairs],
        right=right_col,
        links=links,
    )


def _clock(hour: int, minute: int, **extra: Any) -> dict[str, Any]:
    hour_deg, minute_deg = clock_degrees(hour, minute)
    data = {
        "hour": hour,
        "minute": minute,
        "hour_deg": hour_deg,
        "minute_deg": minute_deg,
        "digital": digital(hour, minute),
        "phrase": time_phrase(hour, minute),
        "answer": digital(hour, minute),
    }
    data.update(extra)
    return data


def _shift(hour: int, minute: int, delta: int, label: str) -> dict[str, Any]:
    total = hour * 60 + minute + delta
    nh, nm = divmod(total, 60)
    if nh < 1 or nh > 11:
        raise ValueError("shift leaves the morning")
    return {
        "prompt": f"{digital(hour, minute)} dopoledne, {label}",
        "answer": digital(nh, nm),
        "hour": hour,
        "minute": minute,
        "delta": delta,
    }


def _build_kolem(rng: Random, seed: int) -> list[dict[str, Any]]:
    spec = SETS["kolem"]
    title, subtitle = spec["title"], spec["subtitle"]
    used_times: set[tuple[int, int]] = set()
    used_coins: set[tuple[int, ...]] = set()
    used_plans: set[tuple[int, ...]] = set()
    used_segs: set[tuple[Any, ...]] = set()
    pages = []

    def take_time(cands: list[tuple[int, int]], n: int) -> list[tuple[int, int]]:
        fresh = [c for c in cands if c not in used_times]
        rng.shuffle(fresh)
        if len(fresh) < n:
            raise ValueError("times")
        picked = fresh[:n]
        used_times.update(picked)
        return picked

    whole = take_time([(h, 0) for h in range(1, 13)], 4)
    half = take_time([(h, 30) for h in range(1, 13)], 4)
    match = take_time([(h, 0) for h in range(1, 13)] + [(h, 30) for h in range(1, 13)], 3)
    draw = take_time([(h, 0) for h in range(1, 13)] + [(h, 30) for h in range(1, 13)], 2)
    match_clocks = [_clock(h, m, label="ABC"[i]) for i, (h, m) in enumerate(match)]
    options = [c["digital"] for c in match_clocks]
    opt_order = list(range(3))
    rng.shuffle(opt_order)
    pages.append(
        _page(
            seed=seed,
            index=1,
            heading="Kolik je hodin?",
            title=title,
            subtitle=subtitle,
            show_name=True,
            blocks=[
                blk("clocks", "Napiš čas čísly. Celé hodiny.", [_clock(h, m) for h, m in whole], cols=4),
                blk("clocks", "Napiš čas čísly. Půlhodiny.", [_clock(h, m) for h, m in half], cols=4),
                blk(
                    "clock_match",
                    "Spoj ciferník s časem.",
                    match_clocks,
                    options=[options[i] for i in opt_order],
                    links=[opt_order.index(i) for i in range(3)],
                ),
                blk(
                    "clock_blank",
                    "Nakresli ručičky. Malá je kratší.",
                    [
                        {
                            "prompt": digital(h, m),
                            "answer": hand_sentence(h, m),
                            "hour": h,
                            "minute": m,
                        }
                        for h, m in draw
                    ],
                    cols=2,
                ),
            ],
        )
    )

    quarter_cands = []
    for h in range(1, 12):
        for m in (0, 15, 30, 45):
            quarter_cands.append((h, m))
    shown = take_time(quarter_cands, 4)
    # Force a spread of minutes when the random pick collapsed.
    minutes = {m for _h, m in shown}
    if len(minutes) < 4:
        shown = []
        used_times_backup = set(used_times)
        for m in (0, 15, 30, 45):
            cands = [(h, m) for h in range(1, 12) if (h, m) not in used_times]
            rng.shuffle(cands)
            shown.append(cands[0])
            used_times.add(cands[0])
        for old in list(used_times_backup):
            pass
    phrase_pool = []
    for h, m in ((7, 15), (7, 30), (7, 45), (12, 15), (12, 30), (2, 15), (5, 45), (9, 30), (3, 15), (11, 45)):
        if (h, m) not in used_times:
            phrase_pool.append((h, m))
    rng.shuffle(phrase_pool)
    phrases = []
    for i, (h, m) in enumerate(phrase_pool[:4]):
        used_times.add((h, m))
        if i % 2 == 0:
            phrases.append({"mode": "to_digital", "prompt": time_phrase(h, m), "answer": digital(h, m), "hour": h, "minute": m})
        else:
            phrases.append({"mode": "to_words", "prompt": digital(h, m), "answer": time_phrase(h, m), "hour": h, "minute": m})
    def pick_shift(delta: int, label: str, *, prefer_fresh: bool = True) -> dict[str, Any]:
        cands = []
        for h in range(1, 12):
            for m in (0, 15, 30, 45):
                total = h * 60 + m + delta
                nh, _nm = divmod(total, 60)
                if 1 <= nh <= 11 and (not prefer_fresh or (h, m) not in used_times):
                    cands.append((h, m))
        if not cands:
            return pick_shift(delta, label, prefer_fresh=False)
        rng.shuffle(cands)
        h, m = cands[0]
        used_times.add((h, m))
        return _shift(h, m, delta, label)

    shifts = [
        pick_shift(60, "za hodinu bude"),
        pick_shift(30, "za půl hodiny bude"),
        pick_shift(-60, "před hodinou bylo"),
        pick_shift(-30, "před půlhodinou bylo"),
    ]
    pages.append(
        _page(
            seed=seed,
            index=2,
            heading="Čtvrt, půl, tři čtvrtě",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk(
                    "clocks",
                    "Napiš čas čísly.",
                    [_clock(h, m) for h, m in shown],
                    cols=4,
                ),
                blk("time_words", "Spoj slovní čas s čísly, nebo naopak.", phrases, cols=2),
                blk("time_shift", "Dopoledne. Napiš čas čísly.", shifts, cols=2),
            ],
        )
    )

    def coin_group(k: int, limit: int = 80) -> list[int]:
        for _ in range(80):
            coins = [rng.choice(COINS) for _ in range(k)]
            sig = tuple(sorted(coins))
            if sum(coins) <= limit and sig not in used_coins:
                used_coins.add(sig)
                return coins
        raise ValueError("coins")

    groups = [coin_group(k) for k in (2, 3, 3, 4)]
    gaps = []
    offers_base = [1, 2, 5, 10, 20, 50]
    for _ in range(2):
        have = coin_group(2, 40)
        need = rng.choice([c for c in COINS if sum(have) + c <= 80])
        wrong = [c for c in offers_base if c != need]
        rng.shuffle(wrong)
        offer = wrong[:3] + [need]
        rng.shuffle(offer)
        gaps.append({"have": have, "target": sum(have) + need, "offer": offer, "answer": need})
    catalog = [
        (20, (10, 10), (20,)),
        (15, (10, 5), (5, 5, 5)),
        (30, (20, 10), (10, 10, 10)),
        (12, (10, 2), (5, 5, 2)),
        (25, (20, 5), (10, 10, 5)),
        (8, (5, 2, 1), (2, 2, 2, 2)),
        (40, (20, 20), (10, 10, 10, 10)),
        (11, (10, 1), (5, 5, 1)),
    ]
    rng.shuffle(catalog)
    pairs = []
    for total, left, right in catalog:
        if tuple(sorted(left)) in used_coins or tuple(sorted(right)) in used_coins:
            continue
        used_coins.add(tuple(sorted(left)))
        used_coins.add(tuple(sorted(right)))
        pairs.append({"a": list(left), "b": list(right), "answer": total})
        if len(pairs) == 2:
            break
    enough = []
    for price, have, ans in ((18, 20, "ano"), (36, 20, "ne"), (42, 50, "ano"), (64, 50, "ne")):
        enough.append({"price": price, "have": have, "answer": ans})
    pages.append(
        _page(
            seed=seed,
            index=3,
            heading="Poznáváme peníze",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("coins", "Kolik korun je na hromádce?", [{"coins": c, "answer": sum(c)} for c in groups], cols=2),
                blk("coin_gap", "Doplň jednu minci z nabídky.", gaps),
                blk("coin_pair", "Obě skupinky mají stejnou hodnotu. Kolik to je?", pairs),
                blk("enough", "Stačí peníze? Zakroužkuj ano, nebo ne.", enough, cols=2),
            ],
        )
    )

    goods = _shop_goods(rng)
    questions = _shop_questions(goods)
    pages.append(
        _page(
            seed=seed,
            index=4,
            heading="Malý obchod",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk(
                    "shop",
                    "Ceny platí jen pro toto cvičení. Spočítej nákup.",
                    questions[:4],
                    goods=goods,
                ),
                blk("shop", "Kolik korun se vrátí?", questions[4:7]),
                blk("shop", "Porovnej nákupy.", questions[7:10]),
                blk("shop", "Ještě odpověz.", questions[10:]),
            ],
        )
    )

    shape_names = {
        "circle": "kruh",
        "square": "čtverec",
        "rectangle": "obdélník",
        "triangle": "trojúhelník",
    }
    solid_names = {
        "cube": "krychle",
        "cuboid": "kvádr",
        "sphere": "koule",
        "cylinder": "válec",
    }
    shape_items = []
    for sid, name in shape_names.items():
        opts = [name] + [n for n in shape_names.values() if n != name][:2]
        rng.shuffle(opts)
        shape_items.append({"id": sid, "options": opts, "answer": name})
    solid_items = []
    for sid, name in solid_names.items():
        opts = [name] + [n for n in solid_names.values() if n != name][:2]
        rng.shuffle(opts)
        solid_items.append({"id": sid, "options": opts, "answer": name})
    picture = ["triangle", "circle", "square", "triangle", "rectangle", "circle", "circle", "square"]
    counts = {k: picture.count(k) for k in ("triangle", "circle", "square", "rectangle")}
    labels = {
        "triangle": "trojúhelníků",
        "circle": "kruhů",
        "square": "čtverců",
        "rectangle": "obdélníků",
    }
    count_items = [{"ask": k, "label": labels[k], "answer": counts[k]} for k in labels]
    pages.append(
        _page(
            seed=seed,
            index=5,
            heading="Tvary a tělesa",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk("shapes", "Zakroužkuj název rovinného útvaru.", shape_items, cols=4),
                blk("solids", "Zakroužkuj název tělesa.", solid_items, cols=4),
                blk(
                    "count_shapes",
                    "Počítej jen samostatně nakreslené tvary, ne větší složené obrázky.",
                    count_items,
                    shapes=picture,
                ),
            ],
        )
    )

    segs = []
    labels_s = list("ABCDEFGHI")
    straight = [
        ((0, 1), (4, 1)),
        ((0, 0), (2, 0)),
        ((1, 0), (1, 2)),
        ((3, 0), (3, 2)),
        ((0, 2), (3, 2)),
        ((2, 0), (2, 1)),
        ((0, 1), (1, 1)),
    ]
    polys = [((0, 2), (3, 2), (3, 0)), ((1, 0), (1, 2), (4, 2))]
    for (p0, p1) in straight:
        length = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
        segs.append(
            {
                "label": labels_s[len(segs)],
                "cols": 5,
                "rows": 3,
                "points": [list(p0), list(p1)],
                "answer": length,
            }
        )
        used_segs.add((tuple(p0), tuple(p1)))
    for pts in polys:
        length = 0
        for a, b in zip(pts, pts[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                raise ValueError("diagonal")
            length += abs(b[0] - a[0]) + abs(b[1] - a[1])
        segs.append(
            {
                "label": labels_s[len(segs)],
                "cols": 5,
                "rows": 3,
                "points": [list(p) for p in pts],
                "answer": length,
            }
        )
    comp = [
        {"a": segs[0]["label"], "b": segs[2]["label"], "la": segs[0]["answer"], "lb": segs[2]["answer"]},
        {"a": segs[4]["label"], "b": segs[5]["label"], "la": segs[4]["answer"], "lb": segs[5]["answer"]},
    ]
    for item in comp:
        item["answer"] = "<" if item["la"] < item["lb"] else (">" if item["la"] > item["lb"] else "=")
    pages.append(
        _page(
            seed=seed,
            index=6,
            heading="Délky na mřížce",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk(
                    "segments",
                    "Jedna hrana čtverečku je 1. Počítej hrany, ne tečky. Jen rovné úseky.",
                    segs,
                    cols=3,
                ),
                blk("seg_compare", "Porovnej délky úseček.", comp, cols=2),
                blk(
                    "path",
                    "Dokresli cestu z 5 hran. Začni u A. Jen vodorovně a svisle.",
                    [
                        {
                            "cols": 5,
                            "rows": 4,
                            "length": 5,
                            "answer": "libovolná cesta z 5 hran od A, jen vodorovně a svisle",
                        }
                    ],
                ),
            ],
        )
    )

    columns = []
    totals = set()
    guard = 0
    while len(columns) < 4 and guard < 80:
        guard += 1
        heights = [rng.randint(1, 4) for _ in range(3)]
        if sum(heights) in totals or heights in columns:
            continue
        columns.append(heights)
        totals.add(sum(heights))
    columns.sort(key=sum)
    plans = []
    while len(plans) < 2:
        grid = [[rng.randint(0, 4) for _ in range(3)] for _ in range(2)]
        sig = tuple(v for row in grid for v in row)
        if sig in used_plans or sum(sig) == 0:
            continue
        used_plans.add(sig)
        plans.append({"rows": grid, "answer": sum(sig)})
    fill_h = [2, 1, 3]
    match_h = [1, 4, 2]
    match_alt = [2, 4, 1]
    plans_m = [match_h, match_alt]
    rng.shuffle(plans_m)
    match_letter = "A" if plans_m[0] == match_h else "B"
    pages.append(
        _page(
            seed=seed,
            index=7,
            heading="Stavby z kostek",
            title=title,
            subtitle=subtitle,
            show_name=False,
            note_text=(
                "Sloupce jsou plné, bez děr a převisů. Číslo je počet kostek. "
                "Šipka znamená zleva doprava. 0 je prázdné místo."
            ),
            blocks=[
                blk(
                    "columns",
                    "Kolik je kostek? Pohled zepředu.",
                    [{"heights": h, "answer": sum(h)} for h in columns],
                    cols=4,
                ),
                blk("plan", "Kolik je kostek v plánu?", plans, cols=2),
                blk(
                    "plan_fill",
                    "Zapiš výšky sloupců do plánu.",
                    [{"heights": fill_h, "answer": fill_h}],
                ),
                blk(
                    "plan_match",
                    "Zakroužkuj plán, který patří ke stavbě.",
                    [{"heights": match_h, "plans": plans_m, "answer": match_letter}],
                ),
            ],
        )
    )

    p8_clocks = take_time([(h, m) for h in range(1, 12) for m in (15, 45)], 2)
    p8_shifts = [
        pick_shift(60, "za hodinu bude"),
        pick_shift(-30, "před půlhodinou bylo"),
    ]
    p8_coins = [coin_group(3, 70), coin_group(2, 60)]
    seg = {
        "label": "M",
        "cols": 5,
        "rows": 3,
        "points": [[0, 0], [0, 2], [3, 2]],
        "answer": 5,
    }
    used_segs.add(((0, 0), (0, 2), (3, 2)))
    grid = [[rng.randint(1, 3) for _ in range(2)] for _ in range(2)]
    sig = tuple(v for row in grid for v in row)
    while sig in used_plans:
        grid = [[rng.randint(1, 3) for _ in range(2)] for _ in range(2)]
        sig = tuple(v for row in grid for v in row)
    used_plans.add(sig)
    ticket = rng.randint(12, 24)
    ice = rng.randint(8, 18)
    stories = [
        {
            "prompt": f"Jízdenka stojí {ticket} Kč a zmrzlina {ice} Kč. Kolik stojí dohromady?",
            "answer": str(ticket + ice),
            "value": ticket + ice,
        },
        {
            "prompt": f"Zmrzlina stojí {ice} Kč. Zaplatíš 50 Kč. Kolik korun se vrátí?",
            "answer": str(50 - ice),
            "value": 50 - ice,
        },
    ]
    pages.append(
        _page(
            seed=seed,
            index=8,
            heading="Praktická matematická výzva",
            title=title,
            subtitle=subtitle,
            show_name=False,
            blocks=[
                blk(
                    "clocks",
                    "Napiš čas čísly. U posunu počítej dopoledne.",
                    [_clock(h, m) for h, m in p8_clocks],
                    shifts=p8_shifts,
                    count=len(p8_clocks) + len(p8_shifts),
                    cols=2,
                ),
                blk(
                    "coins",
                    "Kolik je korun? U otázky zakroužkuj, zda částka stačí.",
                    [{"coins": c, "answer": sum(c)} for c in p8_coins],
                    enough=[{"price": 15, "have": 50, "answer": "ano"}, {"price": 28, "have": 20, "answer": "ne"}],
                    count=len(p8_coins) + 2,
                    cols=2,
                ),
                blk(
                    "segments",
                    "Jedna hrana je 1. U plánu sečti kostky ve sloupcích.",
                    [seg],
                    plan={"rows": grid, "answer": sum(sig)},
                    count=2,
                ),
                blk(
                    "story",
                    "Vypočítej. Pomůcka: 1 hl = 100 l.",
                    stories,
                    hl={"prompt": "1 hl =", "answer": "100", "unit": "l"},
                    count=len(stories) + 1,
                ),
            ],
        )
    )
    return pages


def _shop_goods(rng: Random) -> list[dict[str, Any]]:
    for _ in range(40):
        goods = [
            {"name": "sešit", "price": rng.randint(18, 32)},
            {"name": "tužky", "price": rng.randint(10, 16)},
            {"name": "guma", "price": rng.randint(5, 9)},
            {"name": "pravítko", "price": rng.randint(12, 20)},
        ]
        prices = [g["price"] for g in goods]
        if len(set(prices)) < 4:
            continue
        by = {g["name"]: g["price"] for g in goods}
        if by["sešit"] + by["tužky"] != by["pravítko"] + by["guma"]:
            return goods
    raise ValueError("shop prices")


def _shop_questions(goods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by = {g["name"]: g["price"] for g in goods}
    a_sum = by["sešit"] + by["tužky"]
    b_sum = by["pravítko"] + by["guma"]
    dearer = "A" if a_sum > b_sum else "B"
    dearest = max(goods, key=lambda g: g["price"])["name"]
    questions = [
        {"prompt": "Kolik stojí sešit a guma?", "answer": str(by["sešit"] + by["guma"])},
        {"prompt": "Kolik stojí dvě gumy?", "answer": str(2 * by["guma"])},
        {"prompt": "Kolik stojí dvoje tužky?", "answer": str(2 * by["tužky"])},
        {"prompt": "Kolik stojí guma, tužky a pravítko?", "answer": str(by["guma"] + by["tužky"] + by["pravítko"])},
        {"prompt": "Zaplatíš za gumu 50 Kč. Kolik se vrátí?", "answer": str(50 - by["guma"])},
        {"prompt": "Zaplatíš za sešit 100 Kč. Kolik se vrátí?", "answer": str(100 - by["sešit"])},
        {
            "prompt": "Zaplatíš za sešit a pravítko 100 Kč. Kolik se vrátí?",
            "answer": str(100 - by["sešit"] - by["pravítko"]),
        },
        {
            "prompt": "Který nákup je dražší? A sešit a tužky, B pravítko a guma.",
            "answer": dearer,
            "box": "word",
        },
        {"prompt": "O kolik korun je dražší nákup z minulé úlohy?", "answer": str(abs(a_sum - b_sum))},
        {"prompt": "Stačí 50 Kč na tužky a gumu? Napiš ano, nebo ne.", "answer": "ano", "box": "word"},
        {"prompt": "Které zboží je nejdražší? Napiš název.", "answer": dearest, "box": "word"},
        {"prompt": "Kolik stojí pravítko a tužky?", "answer": str(by["pravítko"] + by["tužky"])},
    ]
    for q in questions:
        if q["answer"].lstrip("-").isdigit() and int(q["answer"]) < 0:
            raise ValueError(q)
    return questions


def _answer_line(block: dict[str, Any]) -> str:
    kind = block["kind"]
    bits: list[str] = []
    if kind == "wordnum":
        bits = [f"{it['prompt']} = {it['answer']}" for it in block["items"]]
    elif kind == "place":
        bits = [f"{it['shown']} {it['answer']} {it['suffix']}".strip() for it in block["items"]]
    elif kind == "seq":
        for it in block["items"]:
            vals = []
            ai = 0
            for cell in it["cells"]:
                if cell == "":
                    vals.append(str(it["answers"][ai]))
                    ai += 1
                else:
                    vals.append(cell)
            bits.append(", ".join(vals))
    elif kind == "compare":
        bits = [f"{it['a']} {it['answer']} {it['b']}" for it in block["items"]]
        if block.get("order"):
            bits.append("seřaď " + ", ".join(str(n) for n in block["order"]["answer"]))
    elif kind == "complement":
        bits = [f"{it['a']} + {it['answer']} = {it['target']}" for it in block["items"]]
    elif kind == "decomp":
        for it in block["items"]:
            sign = "+" if it["op"] == "+" else "−"
            bits.append(
                f"{it['a']} {sign} {it['b']} = {it['a']} {sign} {it['bridge']} {sign} {it['rest']} = {it['answer']}"
            )
    elif kind == "calc":
        bits = [eq(it["a"], it["op"], it["b"]) for it in block["items"]]
    elif kind == "pairs":
        for i, left in enumerate(block["left"]):
            bits.append(f"{left} → {block['right'][block['links'][i]]}")
    elif kind == "pic_pairs":
        for i, left in enumerate(block["left"]):
            bits.append(f"{left['groups']} skupin po {left['each']} → {block['right'][block['links'][i]]}")
    elif kind == "sign":
        bits = [f"{it['a']} {it['answer']} {it['b']} = {it['result']}" for it in block["items"]]
    elif kind == "missing":
        for it in block["items"]:
            if it["form"] == "add_left":
                bits.append(f"{it['answer']} + {it['b']} = {it['c']}")
            elif it["form"] == "add_right":
                bits.append(f"{it['a']} + {it['answer']} = {it['c']}")
            elif it["form"] == "sub_left":
                bits.append(f"{it['answer']} − {it['b']} = {it['c']}")
            else:
                bits.append(f"{it['a']} − {it['answer']} = {it['c']}")
    elif kind == "choice":
        bits = [f"{it['prompt']} = {it['answer']}" for it in block["items"]]
    elif kind == "compare_expr":
        bits = [
            f"{it['a']} {it['op']} {it['b']} {it['answer']} {it['c']} {it['op2']} {it['d']}"
            for it in block["items"]
        ]
    elif kind == "brackets":
        for it in block["items"]:
            if it["form"] == "sub_sum":
                bits.append(f"{it['a']} − ({it['b']} + {it['c']}) = {it['answer']}")
            elif it["form"] == "add_sum":
                bits.append(f"{it['a']} + ({it['b']} + {it['c']}) = {it['answer']}")
            else:
                bits.append(f"{it['a']} − ({it['b']} − {it['c']}) = {it['answer']}")
    elif kind == "fix":
        bits = [f"{it['a']} {it['op']} {it['b']} = {it['answer']} (ne {it['shown']})" for it in block["items"]]
    elif kind == "pyramid":
        for it in block["items"]:
            bits.append(
                f"{it['bottom'][0]}, {it['bottom'][1]}, {it['bottom'][2]} → "
                f"{it['mid'][0]}, {it['mid'][1]} → {it['top']}"
            )
    elif kind == "chain":
        for it in block["items"]:
            path = [str(it["start"])] + [str(step["answer"]) for step in it["steps"]]
            bits.append(" → ".join(path))
    elif kind == "symbols":
        names = {"circle": "kruh", "square": "čtverec"}
        for it in block["items"]:
            left = f" {it['op']} ".join(names[i] for i in it["ids"])
            bits.append(f"{left} = {it['answer']}")
    elif kind == "web":
        bits = [f"{block['start']} {it['op']} {it['n']} = {it['answer']}" for it in block["items"]]
    elif kind == "groups":
        bits = [f"{it['groups']} skupin po {it['each']} = {it['answer']}" for it in block["items"]]
    elif kind == "rewrite":
        for it in block["items"]:
            adds = " + ".join([str(it["each"])] * it["groups"])
            bits.append(f"{adds} = {it['groups']} · {it['each']} = {it['answer']}")
    elif kind == "array":
        bits = [f"{it['rows']} řádků po {it['cols']} = {it['answer']}" for it in block["items"]]
    elif kind == "factor":
        bits = [f"{it['a']} · □ = {it['product']} → {it['answer']}" for it in block["items"]]
    elif kind == "parity":
        bits = [f"{it['n']} {it['answer']}" for it in block["items"]]
    elif kind == "table":
        bits = [f"{it['row']} · {it['col']} = {it['answer']}" for it in block["items"]]
    elif kind == "dots":
        bits = [f"{it['prompt']} → {it['answer']}" for it in block["items"]]
    elif kind == "family":
        for it in block["items"]:
            bits.append(
                f"{it['a']} · {it['b']} = {it['product']}; "
                f"{it['product']} : {it['b']} = {it['a']}; "
                f"{it['product']} : □ = {it['b']} → {it['a']}"
            )
    elif kind == "clocks":
        bits = [it["digital"] for it in block["items"]]
        bits += [f"{it['prompt']} → {it['answer']}" for it in block.get("shifts") or []]
    elif kind == "clock_match":
        bits = [f"{it['label']} = {it['digital']}" for it in block["items"]]
    elif kind == "clock_blank":
        bits = [f"{it['prompt']}: {it['answer']}" for it in block["items"]]
    elif kind == "time_words":
        bits = [f"{it['prompt']} = {it['answer']}" for it in block["items"]]
    elif kind == "time_shift":
        bits = [f"{it['prompt']} → {it['answer']}" for it in block["items"]]
    elif kind == "coins":
        bits = [" + ".join(str(c) for c in it["coins"]) + f" = {it['answer']} Kč" for it in block["items"]]
        bits += [f"{it['price']} Kč z {it['have']} Kč: {it['answer']}" for it in block.get("enough") or []]
    elif kind == "coin_gap":
        bits = [f"doplň {it['answer']} Kč k {sum(it['have'])} Kč = {it['target']} Kč" for it in block["items"]]
    elif kind == "coin_pair":
        bits = [f"{it['answer']} Kč" for it in block["items"]]
    elif kind == "enough":
        bits = [f"{it['price']} Kč z {it['have']} Kč: {it['answer']}" for it in block["items"]]
    elif kind == "shop":
        bits = [f"{g['name']} {g['price']} Kč" for g in block.get("goods") or []]
        bits += [f"{it['prompt']} → {it['answer']}" for it in block["items"]]
    elif kind in ("shapes", "solids"):
        bits = [f"{it['id']} = {it['answer']}" for it in block["items"]]
    elif kind == "count_shapes":
        bits = [f"{it['label']}: {it['answer']}" for it in block["items"]]
    elif kind == "segments":
        bits = [f"{it['label']} = {it['answer']}" for it in block["items"]]
        if block.get("plan"):
            bits.append(f"plán {block['plan']['answer']} kostek")
    elif kind == "seg_compare":
        bits = [f"{it['a']} {it['answer']} {it['b']}" for it in block["items"]]
    elif kind == "path":
        bits = [it["answer"] for it in block["items"]]
    elif kind == "columns":
        bits = [" + ".join(str(h) for h in it["heights"]) + f" = {it['answer']}" for it in block["items"]]
    elif kind == "plan":
        bits = [f"{it['answer']} kostek" for it in block["items"]]
    elif kind == "plan_fill":
        bits = [", ".join(str(h) for h in it["answer"]) for it in block["items"]]
    elif kind == "plan_match":
        bits = [it["answer"] for it in block["items"]]
    elif kind == "story":
        bits = [f"{it['prompt']} → {it['answer']}" for it in block["items"]]
        if block.get("hl"):
            bits.append(f"1 hl = {block['hl']['answer']} l")
    elif kind == "hl":
        bits = [f"1 hl = {it['answer']} l" for it in block["items"]]
    else:
        raise ValueError(f"no answer formatter for {kind}")
    return f"{block['letter']}  {block['title']}  " + "; ".join(bits)


def _answers_for(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for page in pages:
        lines = []
        for block in page["data"]["blocks"]:
            if block["kind"] == "note" or block["count"] == 0:
                continue
            lines.append(_answer_line(block))
        rows.append(
            {
                "page": page["data"]["page_no"],
                "heading": page["data"]["heading"],
                "lines": lines,
            }
        )
    return rows


def _item_count(page: dict[str, Any]) -> int:
    return sum(int(b["count"]) for b in page["data"]["blocks"])


def _check_rule(item: dict[str, Any]) -> None:
    if "a" not in item or "op" not in item or "b" not in item:
        return
    a, op, b = item["a"], item["op"], item["b"]
    ans = result(a, op, b)
    if "answer" in item and item.get("rule"):
        if item["answer"] != ans:
            raise ValueError(item)
    rule = item.get("rule", "")
    if rule == "cross20":
        if op == "+":
            assert a < 10 and b < 10 and a + b >= 11
        else:
            assert b > a % 10
        assert ans <= 20
    elif rule == "tens":
        assert a % 10 == 0 and b % 10 == 0 and b != 0
    elif rule == "addtens":
        assert b % 10 == 0 and b != 0 and a % 10 != 0
    elif rule in ("nocross1", "nocross2", "nocross"):
        if op == "+":
            assert (a % 10) + (b % 10) <= 9
        elif op == MINUS:
            assert (a % 10) >= (b % 10)
    elif rule == "cross1":
        assert 0 < b < 10 and a >= 10
        if op == "+":
            assert (a % 10) + b >= 10
        else:
            assert b > a % 10
    elif rule == "cross2":
        assert a >= 10 and b >= 10
        if op == "+":
            assert (a % 10) + (b % 10) >= 10
        else:
            assert (a % 10) < (b % 10)
    elif rule == "mul23":
        assert op == MUL and a in (2, 3) and 1 <= b <= 10
    elif rule == "mul45":
        assert op == MUL and a in (4, 5) and 1 <= b <= 10
    elif rule == "mul01":
        assert op == MUL and 0 <= b <= 10 and a in (0, 1, 2, 3, 4, 5, 10)
        assert 0 in (a, b) or 1 in (a, b) or 10 in (a, b)
    elif rule == "mulmix":
        assert op == MUL and a in CORE and 0 <= b <= 10
    elif rule == "divcore":
        assert op == DIV and b in (1, 2, 3, 4, 5, 10) and a // b <= 10
    elif rule == "challenge":
        if op == MUL:
            assert a in CHALLENGE and 0 <= b <= 10
        else:
            assert op == DIV and b in CHALLENGE and a // b <= 10
    elif rule in ("any", "core", "cross", ""):
        return
    else:
        raise ValueError(f"unknown rule {rule}")


def _validate(set_id: str, pages: list[dict[str, Any]]) -> None:
    spec = SETS[set_id]
    if len(pages) != PAGE_COUNT:
        raise ValueError(f"{set_id} has {len(pages)} pages")
    if pages[0]["data"]["show_name"] is not True:
        raise ValueError("name line missing")
    if any(p["data"]["show_name"] for p in pages[1:]):
        raise ValueError("name line repeated")
    total = 0
    counts = []
    for page in pages:
        n = _item_count(page)
        counts.append(n)
        total += n
        exercise = [b for b in page["data"]["blocks"] if b["kind"] != "note"]
        if not 3 <= len(exercise) <= 6:
            raise ValueError(f"{page['data']['heading']} has {len(exercise)} blocks")
        for block in page["data"]["blocks"]:
            if block["kind"] == "note":
                continue
            if not block["letter"] or not block["title"]:
                raise ValueError("block label")
            extra = 0
            extra += len(block.get("shifts") or [])
            extra += len(block.get("enough") or [])
            extra += 1 if block.get("plan") else 0
            extra += 1 if block.get("hl") else 0
            extra += 1 if block.get("order") else 0
            if block["count"] != len(block.get("items") or []) + extra:
                raise ValueError(f"{block['title']} count {block['count']}")
            _validate_block(set_id, page["data"]["page_no"], block)
    lo, hi = spec["item_min"], spec["item_max"]
    if not lo <= total <= hi:
        raise ValueError(f"{set_id} has {total} items, pages {counts}, expected {lo}–{hi}")
    if set_id == "nasobilka":
        note_text = pages[6]["data"]["note"]
        if note_text != "Tuto stránku si nech, až budete násobilky 6–9 probírat.":
            raise ValueError(note_text)
        for page in pages:
            if page["data"]["page_no"] == 7:
                continue
            for block in page["data"]["blocks"]:
                for item in block.get("items", []):
                    if item.get("rule") == "challenge":
                        raise ValueError("challenge fact leaked")
                    for key in ("a", "b"):
                        if item.get("op") in (MUL, DIV) and item.get(key) in CHALLENGE and key == "a" and item["op"] == MUL:
                            raise ValueError(item)
                        if item.get("op") == DIV and item.get("b") in CHALLENGE:
                            raise ValueError(item)
    _self_check_language()


def _validate_block(set_id: str, page_no: int, block: dict[str, Any]) -> None:
    kind = block["kind"]
    for item in block.get("items", []):
        _check_rule(item)
        if kind == "choice":
            opts = item["options"]
            if len(set(opts)) != 3 or opts.count(item["answer"]) != 1:
                raise ValueError(item)
            if result(item["a"], item["op"], item["b"]) != item["answer"]:
                raise ValueError(item)
        if kind == "sign":
            plus = item["a"] + item["b"]
            minus = item["a"] - item["b"]
            if item["answer"] == "+":
                assert plus == item["result"] and minus != item["result"]
            elif item["answer"] == MINUS:
                assert minus == item["result"] and plus != item["result"]
            else:
                raise ValueError(item)
        if kind == "pyramid":
            b0, b1, b2 = item["bottom"]
            assert item["mid"] == [b0 + b1, b1 + b2]
            assert item["top"] == item["mid"][0] + item["mid"][1]
            assert item["top"] <= 100
        if kind == "chain":
            cur = item["start"]
            for step in item["steps"]:
                cur = result(cur, step["op"], step["n"])
                assert cur == step["answer"]
        if kind == "web":
            assert result(block["start"], item["op"], item["n"]) == item["answer"]
        if kind == "decomp":
            if item["op"] == "+":
                bridge, rest, ans = _split_add(item["a"], item["b"])
            else:
                bridge, rest, ans = _split_sub(item["a"], item["b"])
            assert (bridge, rest, ans) == (item["bridge"], item["rest"], item["answer"])
        if kind == "symbols":
            values = block["values"]
            got = values[item["ids"][0]]
            for other in item["ids"][1:]:
                got = result(got, item["op"], values[other]) if False else got
            expect = sum(values[i] for i in item["ids"]) if item["op"] == "+" else None
            assert expect == item["answer"]
        if kind == "clocks" or kind == "clock_match":
            _check_clock(item)
            for shift in block.get("shifts") or []:
                total = shift["hour"] * 60 + shift["minute"] + shift["delta"]
                nh, nm = divmod(total, 60)
                assert digital(nh, nm) == shift["answer"]
                assert 1 <= nh <= 11
        if kind == "coins":
            for extra_item in block.get("enough") or []:
                assert (extra_item["have"] >= extra_item["price"]) == (extra_item["answer"] == "ano")
        if kind == "segments" and block.get("plan"):
            plan = block["plan"]
            assert sum(v for row in plan["rows"] for v in row) == plan["answer"]
        if kind == "story" and block.get("hl"):
            assert block["hl"]["answer"] == "100"
        if kind == "clock_blank":
            assert item["answer"] == hand_sentence(item["hour"], item["minute"])
        if kind == "time_words":
            if item["mode"] == "to_digital":
                assert item["prompt"] == time_phrase(item["hour"], item["minute"])
                assert item["answer"] == digital(item["hour"], item["minute"])
            else:
                assert item["answer"] == time_phrase(item["hour"], item["minute"])
        if kind == "coins":
            assert all(c in COINS for c in item["coins"])
            assert sum(item["coins"]) == item["answer"] <= 100
        if kind == "coin_gap":
            assert all(c in COINS for c in item["have"] + item["offer"])
            assert item["answer"] in item["offer"]
            assert sum(1 for c in item["offer"] if c == item["target"] - sum(item["have"])) == 1
        if kind == "coin_pair":
            assert sorted(item["a"]) != sorted(item["b"])
            assert sum(item["a"]) == sum(item["b"]) == item["answer"]
        if kind == "enough":
            assert (item["have"] >= item["price"]) == (item["answer"] == "ano")
        if kind == "segments":
            pts = item["points"]
            length = 0
            for p, q in zip(pts, pts[1:]):
                if p[0] != q[0] and p[1] != q[1]:
                    raise ValueError("diagonal segment")
                length += abs(q[0] - p[0]) + abs(q[1] - p[1])
            assert length == item["answer"]
        if kind == "columns":
            assert all(h >= 1 for h in item["heights"])
            assert sum(item["heights"]) == item["answer"]
        if kind == "plan":
            assert sum(v for row in item["rows"] for v in row) == item["answer"]
        if kind == "plan_match":
            assert item["plans"][0 if item["answer"] == "A" else 1] == item["heights"]
            assert item["plans"][0] != item["plans"][1]
            assert sum(item["plans"][0]) == sum(item["plans"][1])
        if kind == "family":
            assert item["a"] * item["b"] == item["product"]
            assert item["product"] // item["b"] == item["a"]
            assert item["b"] != 0
        if kind == "factor":
            assert item["a"] * item["answer"] == item["product"]
            assert item["a"] != 0
        if kind == "parity":
            assert (item["n"] % 2 == 0) == (item["answer"] == "sudé")
            assert 0 <= item["n"] <= 100
        if kind in ("groups", "rewrite", "array"):
            if kind == "array":
                assert item["rows"] * item["cols"] == item["answer"]
            else:
                assert item["groups"] * item["each"] == item["answer"]
        if kind == "dots":
            assert item["count"] % item["by"] == 0
            if item["mode"] == "share":
                assert item["answer"] == item["count"] // item["by"]
            else:
                assert item["answer"] == item["count"] // item["by"]
        if kind == "shop":
            pass
        if kind == "story":
            assert str(item["answer"])
            if "value" in item:
                assert 0 <= item["value"] <= 100
        if kind == "fix":
            assert item["shown"] != item["answer"]
            assert result(item["a"], item["op"], item["b"]) == item["answer"]
        if kind == "missing":
            if item["form"] == "add_left":
                assert item["answer"] + item["b"] == item["c"]
            elif item["form"] == "add_right":
                assert item["a"] + item["answer"] == item["c"]
            elif item["form"] == "sub_left":
                assert item["answer"] - item["b"] == item["c"]
            else:
                assert item["a"] - item["answer"] == item["c"]
        if kind == "compare":
            assert item["answer"] == ("<" if item["a"] < item["b"] else ">" if item["a"] > item["b"] else "=")
        if kind == "compare_expr":
            left = result(item["a"], item["op"], item["b"])
            right = result(item["c"], item["op2"], item["d"])
            assert item["answer"] == ("<" if left < right else ">" if left > right else "=")
        if kind == "brackets":
            if item["form"] == "sub_sum":
                assert item["a"] - (item["b"] + item["c"]) == item["answer"]
            elif item["form"] == "add_sum":
                assert item["a"] + (item["b"] + item["c"]) == item["answer"]
            else:
                assert item["a"] - (item["b"] - item["c"]) == item["answer"]
            assert 0 <= item["answer"] <= 100
        if kind == "wordnum":
            if item["mode"] == "to_num":
                assert words(int(item["answer"])) == item["prompt"]
            else:
                assert words(int(item["prompt"])) == item["answer"]
        if kind == "place":
            assert item["answer"].isdigit()
        if kind == "pairs":
            for i, _left in enumerate(block["left"]):
                assert block["right"][block["links"][i]] == block["items"][i]["answer"]
            if len(block["links"]) != len(set(block["links"])):
                raise ValueError("pair links")
            if block["title"].startswith("Spoj příklady"):
                values = [it["value"] for it in block["items"]]
                if len(values) != len(set(values)):
                    raise ValueError("ambiguous same-result pairs")
        if kind == "pic_pairs":
            for i, _left in enumerate(block["left"]):
                assert block["right"][block["links"][i]] == block["items"][i]["answer"]
        if kind == "hl":
            assert item["answer"] == "100"
        if kind == "table":
            assert item["row"] * item["col"] == item["answer"]
    if kind == "pairs":
        if len(block["links"]) != len(set(block["links"])):
            raise ValueError("pair links")
    if kind == "shop":
        for q in block["items"]:
            if q["answer"].isdigit() and int(q["answer"]) < 0:
                raise ValueError(q)
    if set_id == "kolem" and page_no == 8 and kind == "clocks":
        return


def _check_clock(item: dict[str, Any]) -> None:
    hour, minute = item["hour"], item["minute"]
    hour_deg, minute_deg = clock_degrees(hour, minute)
    assert item["hour_deg"] == hour_deg
    assert item["minute_deg"] == minute_deg
    hour_cw = (hour % 12) * 30 + minute * 0.5
    this_h = (hour % 12) * 30
    next_h = this_h + 30
    if minute == 0:
        assert hour_cw == this_h
    elif minute == 30:
        assert this_h < hour_cw < next_h
        assert abs(hour_cw - (this_h + 15)) < 1e-9
    elif minute == 15:
        assert this_h < hour_cw < this_h + 15
    elif minute == 45:
        assert this_h + 15 < hour_cw < next_h
    else:
        raise ValueError(minute)
    minute_cw = minute * 6
    assert minute_cw in (0, 90, 180, 270)


def _self_check_language() -> None:
    assert words(68) == "šedesát osm"
    assert words(74) == "sedmdesát čtyři"
    assert words(21) == "dvacet jedna"
    assert words(11) == "jedenáct"
    assert words(40) == "čtyřicet"
    assert words(100) == "sto"
    assert time_phrase(7, 15) == "čtvrt na osm"
    assert time_phrase(7, 30) == "půl osmé"
    assert time_phrase(7, 45) == "tři čtvrtě na osm"
    assert time_phrase(12, 15) == "čtvrt na jednu"
    assert time_phrase(12, 30) == "půl jedné"
    assert time_phrase(1, 30) == "půl druhé"
    assert time_phrase(2, 15) == "čtvrt na tři"
    assert digital(7, 15) == "7:15"
    hour_cw = (8 % 12) * 30 + 15
    assert 8 * 30 < hour_cw < 9 * 30


def _types(pages: list[dict[str, Any]]) -> list[str]:
    found = []
    for page in pages:
        for block in page["data"]["blocks"]:
            if block["kind"] == "note":
                continue
            label = block["title"]
            if label not in found:
                found.append(label)
    return found


def generate_math_set(set_id: str, *, seed: int = DEFAULT_SEED) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if set_id not in SETS:
        raise ValueError(f"unknown set {set_id}")
    rng = make_rng(seed)
    pools = _pools()
    if set_id == "cisla":
        pages = _build_cisla(rng, seed, pools)
    elif set_id == "nasobilka":
        pages = _build_nasobilka(rng, seed, pools)
    else:
        pages = _build_kolem(rng, seed)
    _validate(set_id, pages)
    spec = SETS[set_id]
    counts = [_item_count(p) for p in pages]
    meta = {
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "set_id": set_id,
        "title": spec["title"],
        "subtitle": spec["subtitle"],
        "slug": spec["slug"],
        "page_count": PAGE_COUNT,
        "item_count": sum(counts),
        "page_counts": counts,
        "types": _types(pages),
        "answers": _answers_for(pages),
    }
    return pages, meta
