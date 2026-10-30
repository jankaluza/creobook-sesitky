"""Tests for Matematika – 2. třída booklet."""

from __future__ import annotations

import shutil
import struct
import subprocess
import zlib
from pathlib import Path

from creobook.games.math_grade2 import (
    BOOKLET_TITLE,
    CHALLENGE_FACTORS,
    COIN_VALUES,
    CORE_FACTORS,
    HEADINGS,
    PAGE_COUNT,
    PAGE_TOPICS,
    generate_math_grade2_pages,
)
from creobook.games.math_grade2_booklet import (
    EXPECTED_SPREADS,
    build_math_grade2_booklet_pages,
    compile_math_grade2_booklet,
)
from creobook.imposition import booklet_spreads
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
    extract_page_text,
)


def _sec(page: dict, sid: str) -> dict:
    return next(s for s in page["data"]["sections"] if s["id"] == sid)


def _eval(a: int, op: str, b: int) -> int:
    if op == "+":
        return a + b
    if op in ("-", "−"):
        return a - b
    if op == "·":
        assert b != 0 or a == 0
        return a * b
    if op == ":":
        assert b != 0 and a % b == 0
        return a // b
    raise AssertionError(op)


def _cross_add(a: int, b: int) -> bool:
    return a < 10 and b < 10 and a + b >= 11


def _cross_sub(a: int, b: int) -> bool:
    return a <= 20 and (b > a % 10 or (a % 10 == 0 and b > 0))


def test_structure_and_spreads():
    pages, meta = build_math_grade2_booklet_pages(seed=20261026)
    assert len(pages) == PAGE_COUNT == 20
    assert len(PAGE_TOPICS) == 20
    assert booklet_spreads(PAGE_COUNT) == EXPECTED_SPREADS == [
        (20, 1),
        (2, 19),
        (18, 3),
        (4, 17),
        (16, 5),
        (6, 15),
        (14, 7),
        (8, 13),
        (12, 9),
        (10, 11),
    ]
    assert all(p["kind"] == "math_grade2" for p in pages)
    assert [p["data"]["topic"] for p in pages] == list(PAGE_TOPICS)
    assert [p["data"]["heading"] for p in pages] == [HEADINGS[t - 1] for t in PAGE_TOPICS]
    assert pages[0]["data"] != pages[1]["data"]
    assert pages[0]["data"]["show_name_field"] is True
    assert pages[0]["data"]["booklet_title"] == BOOKLET_TITLE
    assert sum(1 for p in pages if p["data"].get("show_name_field")) == 1
    assert [item["heading"] for item in meta["answers"]] == [HEADINGS[t - 1] for t in PAGE_TOPICS]
    assert "Matýsek" not in str(pages) and "Matysek" not in str(pages)


def test_deterministic():
    a, ma = generate_math_grade2_pages(seed=42)
    b, mb = generate_math_grade2_pages(seed=42)
    c, _ = generate_math_grade2_pages(seed=43)
    assert a == b
    assert ma["answers"] == mb["answers"]
    assert a[0]["data"] != c[0]["data"]


def test_answers_follow_the_operands():
    for seed in (1, 7, 42, 20261026, 20270101):
        pages, meta = generate_math_grade2_pages(seed=seed)
        assert len(pages) == 20
        checkers = {
            1: _check_page1,
            2: _check_page2,
            3: _check_page3,
            4: _check_page4,
            5: _check_page5,
            6: _check_page6,
            7: _check_page7,
            8: _check_page8,
        }
        for page in pages:
            checkers[page["data"]["topic"]](page)
        key = "\n".join(line for item in meta["answers"] for line in item["lines"])
        word = _sec(pages[0], "word20")["item"]
        assert f"{word['answer']} {word['unit']}" in key
        assert "5 cm" in key
        assert "malá ručička" in key or "malá mezi" in key


def _check_page1(page: dict) -> None:
    comp = _sec(page, "complements")
    assert len(comp["items"]) == 4
    for it in comp["items"]:
        assert it["answer"] == 10 - it["a"]
    decomp = _sec(page, "decompose")
    ex = decomp["example"]
    assert ex["bridge"] == 10 - ex["a"]
    assert ex["rest"] == ex["b"] - ex["bridge"] >= 1
    assert ex["answer"] == ex["a"] + ex["b"] == 10 + ex["rest"]
    assert len(decomp["items"]) == 2
    for it in decomp["items"]:
        assert it["bridge"] == 10 - it["a"] and it["rest"] >= 1
        assert it["answer"] == it["a"] + it["b"]
    mixed = _sec(page, "mixed20")["items"]
    assert len(mixed) == 8
    assert sum(1 for it in mixed if it["op"] == "+") == 4
    assert sum(1 for it in mixed if it["op"] == "−") == 4
    for it in mixed:
        assert it["answer"] == _eval(it["a"], it["op"], it["b"])
        assert 0 <= it["answer"] <= 20
        if it["op"] == "+":
            assert _cross_add(it["a"], it["b"])
        else:
            assert _cross_sub(it["a"], it["b"])
    assert len(_sec(page, "missing20")["items"]) == 4
    for it in _sec(page, "missing20")["items"]:
        _check_missing(it, hi=20)
    word = _sec(page, "word20")["item"]
    if word["kind"] == "total":
        assert word["answer"] == word["a"] + word["b"]
    else:
        assert word["kind"] == "left"
        assert word["answer"] == word["a"] - word["b"]


def _check_missing(it: dict, *, hi: int) -> None:
    if it["form"] == "x+b":
        assert it["answer"] + it["b"] == it["total"]
    elif it["form"] == "a+x":
        assert it["a"] + it["answer"] == it["total"]
    elif it["form"] == "a-x":
        assert it["a"] - it["answer"] == it["result"]
    elif it["form"] == "x-b":
        assert it["answer"] - it["b"] == it["result"]
    else:
        raise AssertionError(it["form"])
    assert 0 <= it["answer"] <= hi


def _check_page2(page: dict) -> None:
    kinds = [it["kind"] for it in _sec(page, "place_value")["items"]]
    assert kinds == ["split_ones", "split_tens", "words", "hundred"]
    for it in _sec(page, "place_value")["items"]:
        if it["kind"] == "split_ones":
            assert it["answer"] == it["n"] - it["tens"] and it["n"] % 10 != 0
        elif it["kind"] == "split_tens":
            assert it["answer"] + it["ones"] == it["n"]
        elif it["kind"] == "words":
            assert it["ones_count"] == 0
            assert it["answer"] == it["tens_count"] * 10
        else:
            assert it["answer"] == 10 and it["tens_count"] == 10
            assert "n" not in it
    blob = str(_sec(page, "place_value"))
    assert "dvojcifern" not in blob
    seqs = _sec(page, "sequences")["sequences"]
    assert len(seqs) == 2
    for seq in seqs:
        holes = {item["index"]: item["value"] for item in seq["answers"]}
        values = [holes.get(i, v) for i, v in enumerate(seq["values"])]
        step = seq["step"]
        assert values == list(range(values[0], values[0] + step * len(values), step))
        if step == 1:
            assert any(v % 10 == 0 for v in values[1:-1])
        else:
            assert 100 in values
    symbols = {it["answer"] for it in _sec(page, "compare")["items"]}
    assert symbols == {"<", ">", "="}
    assert len(_sec(page, "compare")["items"]) == 6
    for it in _sec(page, "compare")["items"]:
        if it["a"] < it["b"]:
            assert it["answer"] == "<"
        elif it["a"] > it["b"]:
            assert it["answer"] == ">"
        else:
            assert it["answer"] == "="
    order = _sec(page, "order")
    assert order["answer"] == sorted(order["numbers"])
    assert len(set(order["numbers"])) == 5 and 100 in order["numbers"]
    line = _sec(page, "number_line")
    assert line["end"] == line["start"] + 10
    assert all(line["start"] < n < line["end"] for n in line["missing"])
    rnd = _sec(page, "round")
    for it in [rnd["example"], *rnd["items"]]:
        units = it["n"] % 10
        expect = it["n"] - units if units < 5 else it["n"] - units + 10
        assert it["answer"] == expect
    directions = {it["n"] % 10 < 5 for it in rnd["items"]}
    assert directions == {True, False}


def _check_page3(page: dict) -> None:
    calc = _sec(page, "calc100")
    ex = calc["example"]
    assert ex["answer"] == ex["a"] + ex["b"] == ex["ten"] + ex["rest"]
    assert ex["bridge"] + ex["rest"] == ex["b"] and ex["rest"] >= 1
    labels = [block["label"] for block in calc["blocks"]]
    assert labels == [
        "Celé desítky",
        "Bez přechodu",
        "S přechodem",
        "Číslo a desítky",
        "Dvě dvojciferná",
    ]
    assert sum(len(block["items"]) for block in calc["blocks"]) == 12
    for block in calc["blocks"]:
        for it in block["items"]:
            assert it["answer"] == _eval(it["a"], it["op"], it["b"])
            assert 0 <= it["answer"] <= 100
    assert len(_sec(page, "missing100")["items"]) == 4
    for it in _sec(page, "missing100")["items"]:
        _check_missing(it, hi=100)
    fixes = _sec(page, "fix_error")["items"]
    assert len(fixes) == 2
    for it in fixes:
        assert it["answer"] == _eval(it["a"], it["op"], it["b"])
        assert it["shown"] != it["answer"]
        assert abs(it["shown"] - it["answer"]) == 10


def _has(page: dict, sid: str) -> bool:
    return any(sec["id"] == sid for sec in page["data"]["sections"])


def _check_page4(page: dict) -> None:
    if _has(page, "stories"):
        items = _sec(page, "stories")["items"]
        assert [it["kind"] for it in items] == ["total", "left", "more", "less"]
        for it in items:
            assert "krát" not in it["text"]
            assert it["answer"] == _eval(it["a"], "+" if it["kind"] in {"total", "more"} else "−", it["b"])
            assert 0 <= it["answer"] <= 100
    if _has(page, "challenge_story"):
        for sec in page["data"]["sections"]:
            if sec["id"] != "challenge_story":
                continue
            extra = sec["item"]
            assert extra["sum"] == extra["a"] + extra["b"]
            assert extra["pay"] == 50
            assert extra["change"] == 50 - extra["sum"] >= 1


def _check_page5(page: dict) -> None:
    if _has(page, "groups"):
        groups = _sec(page, "groups")["items"]
        assert len(groups) == 2
        for it in groups:
            assert it["answer"] == it["groups"] * it["each"]
            assert it["groups"] in (3, 4) and 2 <= it["each"] <= 4
    if _has(page, "array"):
        array = _sec(page, "array")
        assert array["answer_total"] == array["answer_rows"] * array["answer_cols"] <= 15
    if _has(page, "facts"):
        facts = _sec(page, "facts")["items"]
        assert 10 <= len(facts) <= 12
        assert any(it["b"] == 0 for it in facts) and any(it["b"] == 1 for it in facts)
        for it in facts:
            assert it["a"] in CORE_FACTORS and 0 <= it["b"] <= 10
            assert it["answer"] == it["a"] * it["b"]
            assert it["op"] == "·"
    for sec in page["data"]["sections"]:
        if sec["id"] == "mult_seq":
            for seq in sec["sequences"]:
                assert seq["step"] in (2, 5, 10)
        if sec["id"] == "word_mul":
            word = sec["item"]
            assert word["answer"] == word["groups"] * word["each"]


def _check_page6(page: dict) -> None:
    if _has(page, "share"):
        share = _sec(page, "share")
        assert share["total"] == share["parts"] * share["answer"]
        assert share["parts"] in (2, 3, 4)
    if _has(page, "make_groups"):
        groups = _sec(page, "make_groups")
        assert groups["total"] == groups["size"] * groups["answer"]
    if _has(page, "div_facts"):
        divs = _sec(page, "div_facts")["items"]
        assert len(divs) == 8
        assert sum(1 for it in divs if it["b"] == 1) == 1
        for it in divs:
            assert it["op"] == ":" and it["b"] in (1, 2, 3, 4, 5, 10)
            assert it["answer"] == _eval(it["a"], ":", it["b"])
    if _has(page, "families"):
        families = _sec(page, "families")["items"]
        assert len(families) == 2
        assert families[0]["rows"][0]["hide"] is None
        for fam in families:
            seen = {(row["x"], row["op"], row["y"], row["z"]) for row in fam["rows"]}
            assert len(seen) == 4
            for row in fam["rows"]:
                assert row["z"] == _eval(row["x"], row["op"], row["y"])
    for sec in page["data"]["sections"]:
        if sec["id"] == "word_times":
            word = sec["item"]
            assert "krát méně" in word["text"]
            assert "o několik" not in word["text"]
            assert word["answer"] * word["b"] == word["a"]
        if sec["id"] == "challenge_mul":
            challenge = sec["items"]
            assert len(challenge) == 4
            assert sum(1 for it in challenge if it["op"] == ":") == 1
            for it in challenge:
                assert it["answer"] == _eval(it["a"], it["op"], it["b"])
                if it["op"] == "·":
                    assert it["a"] in CHALLENGE_FACTORS or it["b"] in CHALLENGE_FACTORS
                else:
                    assert it["b"] in CHALLENGE_FACTORS


def _check_page7(page: dict) -> None:
    prices = _sec(page, "prices")
    assert prices["total"] == sum(it["price"] * it["count"] for it in prices["bought"])
    assert prices["change"] == prices["pay"] - prices["total"]
    assert prices["change"] >= 0 and prices["total"] <= 100
    coins = _sec(page, "coins")
    assert all(c in COIN_VALUES for c in coins["coins"])
    assert coins["answer"] == sum(coins["coins"]) <= 100
    clock_sec = _sec(page, "clocks")
    assert clock_sec["hour_hand"] < clock_sec["minute_hand"]
    clocks = clock_sec["items"]
    assert sorted(it["minute"] for it in clocks) == [0, 30]
    assert clocks[0]["hour"] != clocks[1]["hour"]
    for it in clocks:
        assert it["minute_deg"] == it["minute_cw"] - 90
        assert it["hour_deg"] == it["hour_cw"] - 90
        if it["minute"] == 30:
            assert it["hour"] * 30 < it["hour_cw"] < it["hour"] * 30 + 30
            assert it["minute_cw"] == 180
        else:
            assert it["hour_cw"] == it["hour"] * 30 and it["minute_cw"] == 0
    duration = _sec(page, "duration")
    start_h = int(duration["start"].split(":")[0])
    end_h = int(duration["end"].split(":")[0])
    assert duration["answer"] == end_h - start_h
    table = _sec(page, "table")
    values = [row["value"] for row in table["rows"]]
    assert table["total"] == sum(values) <= 100
    assert table["most_value"] == max(values)
    assert sum(1 for v in values if v == table["most_value"]) == 1


def _check_page8(page: dict) -> None:
    if _has(page, "shapes2d"):
        shapes = {it["id"] for it in _sec(page, "shapes2d")["items"]}
        assert shapes == {"square", "rectangle", "triangle", "circle"}
    if _has(page, "lines"):
        lines = _sec(page, "lines")["items"]
        assert {it["kind"] for it in lines} == {"segment", "line", "polyline"}
        assert next(it["letter"] for it in lines if it["kind"] == "line") == "p"
    if _has(page, "measure"):
        measure = _sec(page, "measure")
        assert "100 %" in measure["note"]
        lengths = sorted(it["length_mm"] for it in measure["items"])
        assert lengths == [40, 70]
        for it in measure["items"]:
            assert it["answer_cm"] == it["length_mm"] / 10
    for sec in page["data"]["sections"]:
        if sec["id"] == "draw":
            assert sec["length_cm"] == 5 and "5 cm" in sec["condition"]
    if _has(page, "units"):
        units = {(it["left"], it["answer"], it["right"]) for it in _sec(page, "units")["items"]}
        assert units == {("m", 100, "cm"), ("dm", 10, "cm")}
    if _has(page, "solids"):
        solids = {it["id"] for it in _sec(page, "solids")["items"]}
        assert solids == {"cube", "cuboid", "sphere", "cylinder"}


def test_pdf_outputs_order_and_segment_length(tmp_path: Path):
    pages_pdf = tmp_path / "math2-a5.pdf"
    booklet_pdf = tmp_path / "math2-a4.pdf"
    answers_pdf = tmp_path / "math2-odpovedi.pdf"
    compile_math_grade2_booklet(
        seed=20261026,
        pages_output=pages_pdf,
        output=booklet_pdf,
        answers_output=answers_pdf,
        json_output=tmp_path / "math2.json",
    )
    assert check_page_count(pages_pdf, 20).ok
    assert check_a5_pages(pages_pdf).ok
    assert check_content_within_media_box(pages_pdf).ok
    assert check_page_count(booklet_pdf, 10).ok
    assert check_a4_landscape_sheets(booklet_pdf).ok

    texts = extract_page_text(pages_pdf)
    assert len(texts) == 20
    assert "Matematika – 2. třída" in texts[0]
    assert "Jméno" in texts[0]
    assert all(heading in texts[i] for i, heading in enumerate(HEADINGS[t - 1] for t in PAGE_TOPICS))
    assert all("Jméno:" not in text for text in texts[1:])
    joined = "\n".join(texts)
    assert "·" in joined and ":" in joined and "−" in joined
    assert "100 %" in texts[17] and "100 %" in texts[18]
    assert "Výzva navíc" in texts[8] and "Výzva navíc" in texts[14]
    assert any(ch in joined for ch in "áčďéěíňóřšťúůýž")
    assert "Matýsek" not in joined

    sheets = extract_page_text(booklet_pdf)
    assert len(sheets) == 10
    markers = _page_markers(20261026)
    for sheet, (left, right) in zip(sheets, EXPECTED_SPREADS, strict=True):
        left_at = sheet.find(markers[left - 1])
        right_at = sheet.find(markers[right - 1])
        assert left_at >= 0 and right_at >= 0
        assert left_at < right_at

    answers = "\n".join(extract_page_text(answers_pdf))
    for heading in HEADINGS:
        assert heading in answers
    assert "5 cm" in answers and "100 %" in answers

    for page, dest in ((18, "a5-18"), (19, "a5-19")):
        lengths = _rendered_segment_lengths(pages_pdf, tmp_path / dest, page=page)
        assert lengths == [40.0, 70.0]
    left = _rendered_segment_lengths(
        booklet_pdf, tmp_path / "a4-left", page=3, left_half=True
    )
    right = _rendered_segment_lengths(
        booklet_pdf, tmp_path / "a4-right", page=2, right_half=True
    )
    assert left == [40.0, 70.0]
    assert right == [40.0, 70.0]


def _page_markers(seed: int) -> list[str]:
    """A snippet that the imposed sheet must contain for that A5 page."""
    pages, _ = generate_math_grade2_pages(seed=seed)
    grouped: list[list[str]] = []
    for page in pages:
        found: list[str] = []

        def walk(obj: object) -> None:
            if isinstance(obj, str) and len(obj) > 20:
                found.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        walk(page["data"]["sections"])
        grouped.append(list(dict.fromkeys(found)))
    counts: dict[str, int] = {}
    for group in grouped:
        for text in group:
            counts[text] = counts.get(text, 0) + 1
    markers: list[str] = []
    for page, group in zip(pages, grouped, strict=True):
        unique = [text for text in group if counts[text] == 1]
        if unique:
            # Keep the prefix: extracted PDF text wraps longer sentences.
            markers.append(unique[0][:22])
            continue
        by_id = {sec["id"]: sec for sec in page["data"]["sections"]}
        if "calc100" in by_id:
            ex = by_id["calc100"]["example"]
            markers.append(f"{ex['a']}+{ex['b']}={ex['a']}+{ex['bridge']}")
        elif "facts" in by_id:
            first, second = by_id["facts"]["items"][:2]
            markers.append(f"{first['a']}·{first['b']} = {second['a']}·{second['b']}")
        elif "measure" in by_id:
            markers.append("Tiskněte ve skutečné velikosti")
        else:
            raise AssertionError(page["data"]["page"])
    return markers


def _rendered_segment_lengths(
    pdf: Path,
    dest: Path,
    *,
    page: int,
    left_half: bool = False,
    right_half: bool = False,
) -> list[float]:
    pdftoppm = shutil.which("pdftoppm")
    assert pdftoppm, "pdftoppm is required to measure printed segments"
    dest.mkdir()
    subprocess.run(
        [pdftoppm, "-png", "-r", "200", "-f", str(page), "-l", str(page), str(pdf), str(dest / "p")],
        check=True,
    )
    png = next(dest.glob("p*.png"))
    width, _height, bpp, rows = _read_png(png)
    x_min = width // 2 if right_half else 0
    x_max = width // 2 if left_half else width
    dpi = 200
    px = dpi / 25.4

    def dark(x: int, y: int) -> bool:
        if x < x_min or y < 0 or x >= x_max or y >= len(rows):
            return False
        pixel = rows[y][x * bpp : (x + 1) * bpp]
        return sum(pixel[:3]) / 3 < 120

    found: list[float] = []
    for y, row_index in enumerate(range(len(rows))):
        del row_index
        run = 0
        start = 0
        spans: list[tuple[int, int]] = []
        for x in range(x_min, x_max):
            if dark(x, y):
                if run == 0:
                    start = x
                run += 1
            else:
                if 35 * px <= run <= 75 * px:
                    spans.append((start, start + run - 1))
                run = 0
        if 35 * px <= run <= 75 * px:
            spans.append((start, start + run - 1))
        for left, right in spans:
            c1 = _tick_center(dark, left, y, px)
            c2 = _tick_center(dark, right, y, px)
            if c1 is None or c2 is None:
                continue
            length = round((c2 - c1) / px, 2)
            if not any(abs(length - prev) < 0.8 for prev in found):
                found.append(length)
    return sorted(round(v) for v in found)


def _tick_center(dark, around: int, y: int, px: float) -> float | None:
    xs: list[int] = []
    reach = int(2.2 * px)
    need = int(1.2 * px)
    for x in range(around - 4, around + 5):
        above = sum(1 for dy in range(1, reach) if dark(x, y - dy))
        below = sum(1 for dy in range(1, reach) if dark(x, y + dy))
        if above >= need and below >= need:
            xs.append(x)
    if not xs:
        return None
    return sum(xs) / len(xs)


def _read_png(path: Path) -> tuple[int, int, int, list[bytearray]]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = color = 0
    idat = b""
    while pos < len(data):
        size = struct.unpack(">I", data[pos : pos + 4])[0]
        kind = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + size]
        pos += 12 + size
        if kind == b"IHDR":
            width, height, _bit, color = struct.unpack(">IIBB", chunk[:10])
        elif kind == b"IDAT":
            idat += chunk
        elif kind == b"IEND":
            break
    raw = zlib.decompress(idat)
    bpp = {2: 3, 6: 4}.get(color, 1)
    stride = width * bpp
    rows: list[bytearray] = []
    cursor = 0
    prev = bytearray(stride)

    def paeth(a: int, b: int, c: int) -> int:
        estimate = a + b - c
        pa, pb, pc = abs(estimate - a), abs(estimate - b), abs(estimate - c)
        if pa <= pb and pa <= pc:
            return a
        return b if pb <= pc else c

    for _y in range(height):
        filt = raw[cursor]
        cursor += 1
        row = bytearray(raw[cursor : cursor + stride])
        cursor += stride
        if filt == 1:
            for x in range(stride):
                row[x] = (row[x] + (row[x - bpp] if x >= bpp else 0)) & 255
        elif filt == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 255
        elif filt == 3:
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + ((left + prev[x]) // 2)) & 255
        elif filt == 4:
            for x in range(stride):
                a = row[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + paeth(a, b, c)) & 255
        elif filt != 0:
            raise AssertionError(f"unsupported PNG filter {filt}")
        prev = row
        rows.append(row)
    return width, height, bpp, rows
