"""Tests for booklet imposition ordering and padding."""

from __future__ import annotations

from creobook.imposition import booklet_spreads, pad_page_count


def test_pad_page_count():
    assert pad_page_count(0) == 0
    assert pad_page_count(1) == 4
    assert pad_page_count(4) == 4
    assert pad_page_count(5) == 8
    assert pad_page_count(12) == 12
    assert pad_page_count(13) == 16


def test_booklet_order_twelve_pages():
    """Canonical 12-page booklet spread order."""
    spreads = booklet_spreads(12)
    assert spreads == [
        (12, 1),
        (2, 11),
        (10, 3),
        (4, 9),
        (8, 5),
        (6, 7),
    ]


def test_booklet_order_generic_eight():
    spreads = booklet_spreads(8)
    assert spreads == [
        (8, 1),
        (2, 7),
        (6, 3),
        (4, 5),
    ]


def test_booklet_pads_with_none():
    spreads = booklet_spreads(5)
    # page_count=5, n=8 → pages 6–8 are blanks (None)
    assert spreads == [
        (None, 1),  # 8 blank, 1
        (2, None),  # 2, 7 blank
        (None, 3),  # 6 blank, 3
        (4, 5),  # 4, 5 (both real)
    ]
