"""Tests for the three 8-page Grade-2 maths booklets."""

from __future__ import annotations

from pathlib import Path

import pytest

from creobook.games.math_sets import (
    COINS,
    PAGE_COUNT,
    SETS,
    generate_math_set,
    time_phrase,
)
from creobook.games.math_sets_booklet import (
    EXPECTED_SPREADS,
    compile_math_set_booklet,
)
from creobook.imposition import booklet_spreads
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_page_count,
    extract_page_text,
)

SEED = 20261026
CHALLENGE_NOTE = "Tuto stránku si nech, až budete násobilky 6–9 probírat."


def _blocks(pages, index):
    return pages[index]["data"]["blocks"]


def _items(pages, index, kind):
    out = []
    for block in _blocks(pages, index):
        if block["kind"] == kind:
            out.extend(block["items"])
    return out


@pytest.mark.parametrize("set_id", ["cisla", "nasobilka", "kolem"])
def test_eight_pages_and_deterministic(set_id):
    pages, meta = generate_math_set(set_id, seed=SEED)
    again, meta2 = generate_math_set(set_id, seed=SEED)
    assert len(pages) == PAGE_COUNT == 8
    assert meta["item_count"] == meta2["item_count"]
    assert meta["answers"] == meta2["answers"]
    assert pages[0]["data"]["show_name"] is True
    assert all(page["data"]["show_name"] is False for page in pages[1:])
    assert all(page["kind"] == "math_set" for page in pages)
    assert booklet_spreads(8) == EXPECTED_SPREADS
    low, high = SETS[set_id]["item_min"], SETS[set_id]["item_max"]
    assert low <= meta["item_count"] <= high
    assert sum(meta["page_counts"]) == meta["item_count"]
    letters = []
    for page in pages:
        for block in page["data"]["blocks"]:
            letters.append(block["letter"])
            assert 3 <= len(page["data"]["blocks"]) <= 6
    assert letters


@pytest.mark.parametrize("seed", [1, 7, 42, 99])
def test_other_seeds_validate(seed):
    for set_id in ("cisla", "nasobilka", "kolem"):
        pages, meta = generate_math_set(set_id, seed=seed)
        assert len(pages) == 8
        low, high = SETS[set_id]["item_min"], SETS[set_id]["item_max"]
        assert low <= meta["item_count"] <= high


def test_cisla_rules():
    pages, _meta = generate_math_set("cisla", seed=SEED)
    assert pages[0]["data"]["heading"] == "Poznáváme čísla"
    for item in _items(pages, 3, "calc"):
        a, b, op = item["a"], item["b"], item["op"]
        if op == "+":
            assert a % 10 + b % 10 <= 9
        else:
            assert a % 10 >= b % 10
        assert 0 <= item["answer"] <= 100
    crossed = False
    for item in _items(pages, 4, "calc"):
        a, b, op = item["a"], item["b"], item["op"]
        assert 0 <= item["answer"] <= 100
        if op == "+" and a % 10 + b % 10 >= 10:
            crossed = True
        if op == "−" and b > a % 10:
            crossed = True
    assert crossed
    for block in _blocks(pages, 5):
        if block["kind"] == "fix":
            assert "Oprav výsledek" in block["title"]


def test_nasobilka_core_and_challenge():
    pages, _meta = generate_math_set("nasobilka", seed=SEED)
    assert pages[6]["data"]["note"] == CHALLENGE_NOTE
    for index, page in enumerate(pages):
        for block in page["data"]["blocks"]:
            if block["kind"] not in {"calc", "factor", "family"}:
                continue
            for item in block["items"]:
                if "a" not in item:
                    continue
                op = item.get("op")
                if index == 6 and op == "·":
                    assert item["a"] in {6, 7, 8, 9}
                if index != 6 and op == "·":
                    assert item["a"] not in {6, 7, 8, 9}
                if op == ":":
                    assert item["b"] != 0
                    assert item["a"] % item["b"] == 0
                    if index == 6:
                        assert item["b"] in {6, 7, 8, 9}
                    else:
                        assert item["b"] not in {6, 7, 8, 9}


def test_kolem_language_coins_and_clocks():
    pages, _meta = generate_math_set("kolem", seed=SEED)
    assert time_phrase(7, 15) == "čtvrt na osm"
    assert time_phrase(7, 30) == "půl osmé"
    assert time_phrase(7, 45) == "tři čtvrtě na osm"
    assert time_phrase(12, 15) == "čtvrt na jednu"
    for block in _blocks(pages, 1):
        if block["kind"] != "time_words":
            continue
        for item in block["items"]:
            phrase = time_phrase(item["hour"], item["minute"])
            assert phrase in {item["prompt"], item["answer"]}
    for page in pages:
        for block in page["data"]["blocks"]:
            if block["kind"] in {"coins", "coin_gap", "coin_pair"}:
                for item in block["items"]:
                    values = item.get("coins") or item.get("have") or []
                    if "a" in item and "b" in item:
                        values = list(item["a"]) + list(item["b"])
                    for value in values:
                        assert value in COINS
    clocks = _items(pages, 0, "clocks")
    assert clocks
    half = next(item for item in clocks if item["minute"] == 30)
    assert 0 < (half["hour_deg"] - ((half["hour"] % 12) * 30 - 90)) < 30


def test_pdf_page_counts_and_imposition(tmp_path: Path):
    markers = {
        "cisla": ["Smíšený trénink", "Poznáváme čísla", "Přes desítku", "Početní hlavolamy"],
        "nasobilka": ["Násobilka v příbězích", "Stejné skupiny", "Násobíme dvěma", "Výzva navíc"],
        "kolem": ["Praktická", "Kolik je hodin", "Čtvrt, půl", "Stavby z kostek"],
    }
    for set_id, marks in markers.items():
        result = compile_math_set_booklet(
            set_id,
            seed=SEED,
            output=tmp_path / f"{set_id}.pdf",
            pages_output=tmp_path / f"{set_id}-a5.pdf",
            answers_output=tmp_path / f"{set_id}-odpovedi.pdf",
            json_output=tmp_path / f"{set_id}.json",
        )
        pages_pdf = result["pages"]
        booklet = result["booklet"]
        answers = result["answers"]
        assert check_page_count(pages_pdf, 8).ok
        assert check_a5_pages(pages_pdf).ok
        assert check_page_count(booklet, 4).ok
        assert check_a4_landscape_sheets(booklet).ok
        texts = extract_page_text(pages_pdf)
        assert "Jméno:" in texts[0]
        assert all("Jméno:" not in text for text in texts[1:])
        assert "Čísla" in texts[0] or "Násobilka" in texts[0] or "Matematika" in texts[0]
        sheet = extract_page_text(booklet)
        assert marks[0] in sheet[0] and marks[1] in sheet[0]
        assert sheet[0].find(marks[0]) < sheet[0].find(marks[1])
        assert marks[2] in sheet[1] and marks[3] in sheet[1]
        assert sheet[1].find(marks[2]) < sheet[1].find(marks[3])
        key = "\n".join(extract_page_text(answers))
        assert "Řešení" in key
        assert "čtyři" in key or "čtvrt" in key or "·" in key
