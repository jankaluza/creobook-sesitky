"""PDF validation helpers for CreoBook outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from creobook.imposition import mm_to_pt
from creobook.theme import Theme, load_theme

# Tolerance for floating-point media box comparisons (points ≈ 0.1 mm)
SIZE_TOLERANCE_PT = 0.3


@dataclass
class ValidationResult:
    ok: bool
    messages: list[str]

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise AssertionError("; ".join(self.messages))


def _approx_equal(a: float, b: float, tol: float = SIZE_TOLERANCE_PT) -> bool:
    return abs(a - b) <= tol


def check_page_count(pdf: Path | str, expected: int) -> ValidationResult:
    reader = PdfReader(str(pdf))
    actual = len(reader.pages)
    if actual == expected:
        return ValidationResult(True, [f"page count OK: {actual}"])
    return ValidationResult(False, [f"page count {actual} != expected {expected}"])


def check_media_box(
    pdf: Path | str,
    width_mm: float,
    height_mm: float,
    *,
    theme: Theme | None = None,
) -> ValidationResult:
    """Verify every page MediaBox matches expected millimetre dimensions."""
    expected_w = mm_to_pt(width_mm)
    expected_h = mm_to_pt(height_mm)
    reader = PdfReader(str(pdf))
    messages: list[str] = []
    ok = True
    for i, page in enumerate(reader.pages, start=1):
        box = page.mediabox
        w = float(box.width)
        h = float(box.height)
        if not (_approx_equal(w, expected_w) and _approx_equal(h, expected_h)):
            ok = False
            messages.append(
                f"page {i}: MediaBox {w:.2f}×{h:.2f} pt "
                f"!= {expected_w:.2f}×{expected_h:.2f} pt "
                f"({width_mm}×{height_mm} mm)"
            )
    if ok:
        messages.append(
            f"MediaBox OK: {width_mm}×{height_mm} mm on {len(reader.pages)} page(s)"
        )
    return ValidationResult(ok, messages)


def check_a5_pages(pdf: Path | str, theme: Theme | None = None) -> ValidationResult:
    theme = theme or load_theme()
    return check_media_box(pdf, theme.page.width_mm, theme.page.height_mm, theme=theme)


def check_a4_landscape_sheets(
    pdf: Path | str, theme: Theme | None = None
) -> ValidationResult:
    theme = theme or load_theme()
    return check_media_box(
        pdf,
        theme.booklet.sheet_width_mm,
        theme.booklet.sheet_height_mm,
        theme=theme,
    )


def check_content_within_media_box(pdf: Path | str) -> ValidationResult:
    """
    Ensure CropBox / BleedBox / TrimBox do not extend beyond MediaBox.

    Typst content is clipped to the page; this catches mis-set boxes.
    """
    reader = PdfReader(str(pdf))
    messages: list[str] = []
    ok = True
    for i, page in enumerate(reader.pages, start=1):
        media = page.mediabox
        for name, box in (
            ("CropBox", page.cropbox),
            ("BleedBox", getattr(page, "bleedbox", None)),
            ("TrimBox", getattr(page, "trimbox", None)),
        ):
            if box is None:
                continue
            try:
                if (
                    float(box.left) < float(media.left) - SIZE_TOLERANCE_PT
                    or float(box.bottom) < float(media.bottom) - SIZE_TOLERANCE_PT
                    or float(box.right) > float(media.right) + SIZE_TOLERANCE_PT
                    or float(box.top) > float(media.top) + SIZE_TOLERANCE_PT
                ):
                    ok = False
                    messages.append(f"page {i}: {name} extends beyond MediaBox")
            except Exception as exc:  # noqa: BLE001
                messages.append(f"page {i}: could not compare {name}: {exc}")
    if ok:
        messages.append("content boxes within MediaBox")
    return ValidationResult(ok, messages)


def extract_page_text(pdf: Path | str) -> list[str]:
    reader = PdfReader(str(pdf))
    return [(page.extract_text() or "") for page in reader.pages]


def check_calendar_months_present(pdf: Path | str, year: int) -> ValidationResult:
    from creobook.calendar import MONTH_NAMES_CS

    texts = extract_page_text(pdf)
    messages: list[str] = []
    ok = True
    if len(texts) != 12:
        ok = False
        messages.append(f"expected 12 calendar pages, found {len(texts)}")

    # Match longest names first so "červen" does not steal "červenec"
    sorted_names = sorted(MONTH_NAMES_CS, key=len, reverse=True)
    claimed = [False] * len(texts)
    found_counts = {name: 0 for name in MONTH_NAMES_CS}

    for name in sorted_names:
        for i, text in enumerate(texts):
            if claimed[i]:
                continue
            if name in text:
                found_counts[name] += 1
                claimed[i] = True
                break

    for name in MONTH_NAMES_CS:
        count = found_counts[name]
        if count != 1:
            ok = False
            messages.append(f"month '{name}' found {count} time(s), expected 1")

    joined = "\n".join(texts)
    if str(year) not in joined:
        ok = False
        messages.append(f"year {year} not found in PDF text")
    if ok:
        messages.append(f"all 12 months present exactly once for {year}")
    return ValidationResult(ok, messages)
