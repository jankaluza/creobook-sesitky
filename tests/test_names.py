"""Tests for Czech page filenames and subtitles."""

from __future__ import annotations

from creobook.names import (
    PAGE_NAMES,
    a5_filename,
    booklet_filename,
    booklet_filename_from_pages_path,
    get_page_name,
)


def test_a5_filenames():
    assert a5_filename("ruled") == "creobook-linky-a5.pdf"
    assert a5_filename("ruled", margin_line=True) == "creobook-linky-odsazene-a5.pdf"
    assert a5_filename("dotted") == "creobook-tecky-a5.pdf"
    assert a5_filename("grid") == "creobook-mrizka-a5.pdf"
    assert a5_filename("checklist") == "creobook-seznam-a5.pdf"
    assert a5_filename("cornell") == "creobook-cornell-a5.pdf"
    assert a5_filename("blank") == "creobook-prazdny-a5.pdf"
    assert a5_filename("calendar") == "creobook-kalendar-a5.pdf"


def test_czech_subtitles_with_diacritics():
    assert get_page_name("ruled").subtitle == "Linky"
    assert get_page_name("ruled", margin_line=True).subtitle == "Linky odsazené"
    assert get_page_name("grid").subtitle == "Mřížka"
    assert get_page_name("dotted").subtitle == "Tečky"
    assert get_page_name("blank").subtitle == "Prázdný"
    assert get_page_name("calendar").subtitle == "Kalendář"
    assert get_page_name("checklist").subtitle == "Seznam"


def test_booklet_keeps_a5_suffix():
    assert booklet_filename("ruled") == "creobook-linky-a5.pdf"
    assert (
        booklet_filename_from_pages_path("output/pages/creobook-linky-a5.pdf")
        == "creobook-linky-a5.pdf"
    )


def test_all_slugs_ascii():
    for name in PAGE_NAMES.values():
        assert name.slug.isascii()
        assert " " not in name.slug
