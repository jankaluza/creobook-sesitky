"""Číslování herních sešitků pro nahrání na e-shop."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "publish_herni",
    ROOT / "scripts" / "publish_herni.py",
)
assert spec and spec.loader
publish_herni = importlib.util.module_from_spec(spec)
sys.modules["publish_herni"] = publish_herni
spec.loader.exec_module(publish_herni)


def test_booklet_number_matches_the_product_name():
    assert publish_herni.booklet_number(2) == "č. 2"
    assert publish_herni.product_name("Sudoku", 2) == "Sudoku č. 2"
    assert publish_herni.product_name("Osmisměrky", 2).endswith(publish_herni.booklet_number(2))
    assert publish_herni.product_name("Bludiště", 2).endswith(publish_herni.booklet_number(2))


def test_plan_edition_increments_when_the_seed_is_new():
    products = [
        {"id": 205, "name": "Sudoku č. 1", "slug": "sudoku-c-1", "date_created": "2026-09-01T08:00:00"},
        {"id": 301, "name": "Sudoku č. 3", "slug": "sudoku-c-3", "sku": "sudoku-c-20261001"},
        {"id": 208, "name": "Osmisměrky č. 1", "slug": "osmismerky-c-1"},
        {"id": 230, "name": "Bludiště č. 1", "slug": "bludiste-c-1"},
        {"id": 13, "name": "CreoBook A5", "slug": "creobook-a5"},
    ]
    sudoku = publish_herni.plan_edition(products, publish_herni.SERIES[0], 20261030)
    words = publish_herni.plan_edition(products, publish_herni.SERIES[1], 20261030)
    maze = publish_herni.plan_edition(products, publish_herni.SERIES[2], 20261030)
    assert (sudoku.number, sudoku.source_id, sudoku.update_id) == (4, 301, None)
    assert words.number == 2 and words.update_id is None
    assert maze.number == 2 and maze.update_id is None


def test_plan_edition_updates_the_product_with_the_same_seed():
    products = [
        {"id": 205, "name": "Sudoku č. 1", "slug": "sudoku-c-1"},
        {
            "id": 410,
            "name": "Sudoku č. 2",
            "slug": "sudoku-c-2",
            "sku": "sudoku-c-20261030",
            "meta_data": [{"key": "_creobook_seed", "value": "20261030"}],
        },
    ]
    edition = publish_herni.plan_edition(products, publish_herni.SERIES[0], 20261030)
    assert (edition.number, edition.update_id, edition.source_name) == (2, 410, "Sudoku č. 2")


def test_plan_edition_updates_the_latest_product_from_the_same_day():
    products = [
        {"id": 205, "name": "Sudoku č. 1", "slug": "sudoku-c-1", "date_created": "2026-09-01T08:00:00"},
        {
            "id": 410,
            "name": "Sudoku č. 2",
            "slug": "sudoku-c-2",
            "date_created": "2026-10-30T06:05:00",
        },
    ]
    edition = publish_herni.plan_edition(products, publish_herni.SERIES[0], 20261030)
    assert edition.update_id == 410
    assert edition.number == 2


def test_edition_number_accepts_slug_when_the_title_has_no_number():
    assert publish_herni.edition_number("Sudoku", "sudoku-c-2", "Sudoku", "sudoku-c") == 2
    assert publish_herni.edition_number("Seznam", "seznam", "Sudoku", "sudoku-c") is None


def test_middle_page_is_the_center_of_the_booklet():
    assert publish_herni.middle_page_number(24) == 12
    assert publish_herni.middle_page_number(1) == 1
    with pytest.raises(ValueError):
        publish_herni.middle_page_number(0)


def test_payload_uses_the_new_preview_and_keeps_the_description():
    edition = publish_herni.Edition(
        series=publish_herni.SERIES[0],
        number=2,
        source_id=205,
        source_name="Sudoku č. 1",
    )
    source = {
        "description": "<p>Od pohodového luštění</p>",
        "short_description": "<p>57 sudoku</p>",
        "regular_price": "0",
        "images": [{"id": 207, "src": "https://example.test/hard9.png"}],
        "categories": [{"id": 23}, {"id": 19}, {"id": 24}],
        "meta_data": [
            {"key": "_downloadable_files", "value": [{"file": "https://example.test/old.pdf"}]},
            {"id": 88, "key": "_creobook_seed", "value": "20261001"},
            {"id": 44, "key": "_somdn_included", "value": "yes"},
        ],
    }
    payload = publish_herni.product_payload(
        source,
        edition,
        "https://example.test/sudoku-c-2.pdf",
        501,
        20261030,
    )
    assert payload["name"] == "Sudoku č. 2"
    assert payload["slug"] == "sudoku-c-2"
    assert payload["sku"] == "sudoku-c-20261030"
    assert payload["description"] == source["description"]
    assert payload["short_description"] == source["short_description"]
    assert payload["images"] == [{"id": 501}]
    assert payload["categories"] == [{"id": 23}, {"id": 19}, {"id": 24}]
    assert payload["regular_price"] == "0"
    assert payload["downloadable"] is True
    assert payload["downloads"] == [
        {"name": "Sudoku č. 2.pdf", "file": "https://example.test/sudoku-c-2.pdf"}
    ]
    assert payload["meta_data"] == [
        {"id": 44, "key": "_somdn_included", "value": "yes"},
        {"id": 88, "key": "_creobook_seed", "value": "20261030"},
    ]
