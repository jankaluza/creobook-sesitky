"""Generic A4-landscape booklet imposition for sequential A5 PDFs."""

from __future__ import annotations

import tempfile
from pathlib import Path

import typst
from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from creobook.theme import Theme, load_theme

MM_TO_PT = 72.0 / 25.4

# Default notebook insert booklet: 5 physical A4 sheets → 20 A5 pages after folding.
BOOKLET_SHEETS = 5
BOOKLET_A5_PAGES = BOOKLET_SHEETS * 4


def mm_to_pt(mm: float) -> float:
    return mm * MM_TO_PT


def pad_page_count(n: int) -> int:
    """Return n rounded up to the next multiple of 4 (minimum 4 if n > 0)."""
    if n <= 0:
        return 0
    remainder = n % 4
    if remainder == 0:
        return n
    return n + (4 - remainder)


def booklet_spreads(page_count: int) -> list[tuple[int | None, int | None]]:
    """
    Compute booklet page pairs for a sequential page count.

    Returns a list of (left, right) pairs in print order (front, back, ...),
    using 1-based page indices. ``None`` marks a blank pad page.

    For 12 logical pages the order is:
      (12, 1), (2, 11), (10, 3), (4, 9), (8, 5), (6, 7)
    """
    n = pad_page_count(page_count)
    if n == 0:
        return []

    spreads: list[tuple[int | None, int | None]] = []
    sheets = n // 4
    for sheet in range(sheets):
        left_front = n - 2 * sheet
        right_front = 2 * sheet + 1
        left_back = 2 * sheet + 2
        right_back = n - 2 * sheet - 1

        def idx(i: int) -> int | None:
            return i if i <= page_count else None

        spreads.append((idx(left_front), idx(right_front)))
        spreads.append((idx(left_back), idx(right_back)))
    return spreads


def _fold_guide_overlay(
    theme: Theme,
    width_mm: float | None = None,
    height_mm: float | None = None,
) -> PageObject:
    """Build a vector landscape page with a subtle centre fold guide via Typst."""
    w = theme.booklet.sheet_width_mm if width_mm is None else width_mm
    h = theme.booklet.sheet_height_mm if height_mm is None else height_mm
    stroke = theme.lines.fold_guide_width_mm
    color = theme.colors.fold_guide
    source = f"""
#set page(width: {w}mm, height: {h}mm, margin: 0mm)
#place(top + center, dy: 8mm)[
  #line(angle: 90deg, length: 8mm, stroke: {stroke}mm + rgb("{color}"))
]
#place(bottom + center, dy: -8mm)[
  #line(angle: 90deg, length: 8mm, stroke: {stroke}mm + rgb("{color}"))
]
"""
    with tempfile.TemporaryDirectory(prefix="creobook-fold-") as tmp:
        typ_path = Path(tmp) / "fold.typ"
        pdf_path = Path(tmp) / "fold.pdf"
        typ_path.write_text(source, encoding="utf-8")
        typst.compile(str(typ_path), output=str(pdf_path), root=str(tmp))
        return PdfReader(str(pdf_path)).pages[0]


def impose_booklet(
    input_pdf: Path | str,
    output_pdf: Path | str,
    *,
    theme: Theme | None = None,
    fold_guide: bool | None = None,
    sheet_width_mm: float | None = None,
    sheet_height_mm: float | None = None,
) -> Path:
    """
    Impose a sequential A5 PDF onto A4 landscape sheets in booklet order.

    Preserves vector content by embedding source pages (pypdf page merge).
    Adds blank pages until the count is divisible by 4.

    For repeating notebook inserts, render ``BOOKLET_A5_PAGES`` (20) sequential
    A5 pages with correct page numbers, then impose — do not rely on duplicating
    a single page.
    """
    theme = theme or load_theme()
    input_path = Path(input_pdf)
    output_path = Path(output_pdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(input_path))
    pages = list(reader.pages)
    page_count = len(pages)
    spreads = booklet_spreads(page_count)

    width_mm = theme.booklet.sheet_width_mm if sheet_width_mm is None else sheet_width_mm
    height_mm = theme.booklet.sheet_height_mm if sheet_height_mm is None else sheet_height_mm
    sheet_w = mm_to_pt(width_mm)
    sheet_h = mm_to_pt(height_mm)
    half_w = sheet_w / 2.0

    show_guide = theme.booklet.fold_guide if fold_guide is None else fold_guide
    guide_page = _fold_guide_overlay(theme, width_mm, height_mm) if show_guide else None

    writer = PdfWriter()

    for left_idx, right_idx in spreads:
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)

        def place(src_index: int | None, x_offset: float) -> None:
            if src_index is None:
                return
            src = pages[src_index - 1]
            src_w = float(src.mediabox.width)
            src_h = float(src.mediabox.height)
            scale_x = half_w / src_w
            scale_y = sheet_h / src_h
            scale = min(scale_x, scale_y)
            tx = x_offset + (half_w - src_w * scale) / 2.0
            ty = (sheet_h - src_h * scale) / 2.0
            sheet.merge_transformed_page(
                src,
                Transformation().scale(scale, scale).translate(tx, ty),
                over=True,
            )

        place(left_idx, 0.0)
        place(right_idx, half_w)

        if guide_page is not None:
            sheet.merge_page(guide_page, over=True)

        writer.add_page(sheet)

    with output_path.open("wb") as fh:
        writer.write(fh)
    return output_path
