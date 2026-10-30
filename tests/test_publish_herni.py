"""Číslování herních sešitků pro nahrání na e-shop."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "publish_herni",
    ROOT / "scripts" / "publish_herni.py",
)
assert spec and spec.loader
publish_herni = importlib.util.module_from_spec(spec)
sys.modules["publish_herni"] = publish_herni
spec.loader.exec_module(publish_herni)


def test_next_edition_increments_the_highest_number():
    products = [
        {"id": 205, "name": "Sudoku č. 1", "slug": "sudoku-c-1"},
        {"id": 301, "name": "Sudoku č. 3", "slug": "sudoku-c-3"},
        {"id": 208, "name": "Osmisměrky č. 1", "slug": "osmismerky-c-1"},
        {"id": 230, "name": "Bludiště č. 1", "slug": "bludiste-c-1"},
        {"id": 13, "name": "CreoBook A5", "slug": "creobook-a5"},
    ]
    sudoku = publish_herni.next_edition(products, publish_herni.SERIES[0])
    words = publish_herni.next_edition(products, publish_herni.SERIES[1])
    maze = publish_herni.next_edition(products, publish_herni.SERIES[2])
    assert (sudoku.number, sudoku.source_id, sudoku.source_name) == (4, 301, "Sudoku č. 3")
    assert words.number == 2
    assert maze.number == 2


def test_edition_number_accepts_slug_when_the_title_has_no_number():
    assert publish_herni.edition_number("Sudoku", "sudoku-c-2", "Sudoku", "sudoku-c") == 2
    assert publish_herni.edition_number("Seznam", "seznam", "Sudoku", "sudoku-c") is None


def test_payload_reuses_description_image_and_categories():
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
            {"key": "_somdn_included", "value": "yes"},
        ],
    }
    payload = publish_herni.product_payload(source, edition, "https://example.test/sudoku-c-2.pdf")
    assert payload["name"] == "Sudoku č. 2"
    assert payload["slug"] == "sudoku-c-2"
    assert payload["description"] == source["description"]
    assert payload["short_description"] == source["short_description"]
    assert payload["images"] == [{"id": 207}]
    assert payload["categories"] == [{"id": 23}, {"id": 19}, {"id": 24}]
    assert payload["regular_price"] == "0"
    assert payload["downloadable"] is True
    assert payload["downloads"] == [
        {"name": "Sudoku č. 2.pdf", "file": "https://example.test/sudoku-c-2.pdf"}
    ]
    assert payload["meta_data"] == [{"key": "_somdn_included", "value": "yes"}]
