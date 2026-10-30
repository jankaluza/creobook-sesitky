"""Tests for Matematika – 1. třída booklet."""

from __future__ import annotations

from creobook.games.math_grade1 import (
    PAGE_COUNT,
    TOPIC_COUNT,
    VARIANTS_PER_TOPIC,
    generate_math_grade1_pages,
)
from creobook.games.math_grade1_booklet import (
    EXPECTED_SPREADS,
    build_math_grade1_booklet_pages,
    compile_math_grade1_booklet,
)
from creobook.imposition import booklet_spreads
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
    extract_page_text,
)


def test_structure_and_validation():
    pages, meta = build_math_grade1_booklet_pages(seed=20270101)
    assert len(pages) == PAGE_COUNT == 32
    assert pages[0]["kind"] == "math_grade1"
    assert pages[0]["data"]["show_name_field"] is True
    assert pages[0]["data"]["heading"] == "Počítáme a poznáváme čísla"
    assert pages[0]["data"]["topic"] == 1
    assert pages[3]["data"]["topic"] == 1
    assert pages[4]["data"]["topic"] == 2
    assert pages[31]["data"]["heading"] == "Tvary, prostor a vzory"
    assert pages[31]["data"]["topic"] == 8
    assert booklet_spreads(PAGE_COUNT) == EXPECTED_SPREADS
    assert len(EXPECTED_SPREADS) == 16  # 16 A4 sides → 8 sheets
    assert len(meta["answers"]) == 32
    assert meta["topic_count"] == TOPIC_COUNT
    assert meta["variants_per_topic"] == VARIANTS_PER_TOPIC
    # Name field only on first page
    assert sum(1 for p in pages if p["data"].get("show_name_field")) == 1
    # No cover / solutions kinds inside the child booklet
    assert all(p["kind"] == "math_grade1" for p in pages)


def test_deterministic():
    a, _ = generate_math_grade1_pages(seed=42)
    b, _ = generate_math_grade1_pages(seed=42)
    c, _ = generate_math_grade1_pages(seed=43)
    assert a[2]["data"] == b[2]["data"]
    assert a[2]["data"] != c[2]["data"]


def test_no_cross_ten_in_core_page6():
    pages, _ = generate_math_grade1_pages(seed=20270101)
    topic6_pages = [p for p in pages if p["data"]["topic"] == 6]
    assert len(topic6_pages) == VARIANTS_PER_TOPIC
    p6 = topic6_pages[0]["data"]
    core = next(s for s in p6["sections"] if s["id"] == "calc20")
    for it in core["items"]:
        if it["op"] == "+" and it["a"] >= 10:
            assert (it["a"] % 10) + it["b"] <= 10
        if it["op"] == "-" and it["a"] % 10:
            assert it["b"] <= it["a"] % 10
    challenge = next(s for s in p6["sections"] if s["id"] == "challenge")
    assert len(challenge["items"]) == 4


def test_pdf_outputs(tmp_path):
    pages_pdf = tmp_path / "math-a5.pdf"
    booklet_pdf = tmp_path / "math-a4.pdf"
    answers_pdf = tmp_path / "math-ans.pdf"
    json_path = tmp_path / "math.json"
    compile_math_grade1_booklet(
        seed=20270101,
        pages_output=pages_pdf,
        output=booklet_pdf,
        answers_output=answers_pdf,
        json_output=json_path,
    )
    assert check_page_count(pages_pdf, 32).ok
    assert check_a5_pages(pages_pdf).ok
    assert check_content_within_media_box(pages_pdf).ok
    assert check_page_count(booklet_pdf, 16).ok  # 16 A4 sides = 8 sheets
    assert check_a4_landscape_sheets(booklet_pdf).ok
    assert answers_pdf.exists()
    assert check_page_count(answers_pdf, 4).ok

    texts = extract_page_text(pages_pdf)
    assert "Matematika" in texts[0]
    assert "1. třída" in texts[0] or "1. trida" in texts[0].lower()
    assert "Jméno" in texts[0] or "Jmeno" in texts[0]
    assert "Počítáme" in texts[0] or "Pocitame" in texts[0]
    # Topic 6 first appears on page 21 (index 20)
    topic6_idx = next(i for i, p in enumerate(texts) if "Výzva" in p or "Vyzva" in p)
    assert "Výzva navíc" in texts[topic6_idx] or "Vyzva" in texts[topic6_idx]
    joined = "\n".join(texts)
    assert any(ch in joined for ch in "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ")

    ans_text = "\n".join(extract_page_text(answers_pdf))
    assert "Řešení" in ans_text or "Reseni" in ans_text
