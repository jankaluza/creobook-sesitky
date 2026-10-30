#!/usr/bin/env python3
"""Build the CreoBook kids planner A5 pages PDF and imposed A4 booklet."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

MM_TO_PT = 72.0 / 25.4
A5_W_PT = 148.0 * MM_TO_PT
A5_H_PT = 210.0 * MM_TO_PT
A4_LAND_W_PT = 297.0 * MM_TO_PT
A4_LAND_H_PT = 210.0 * MM_TO_PT
TOL_PT = 2.0  # allow small MediaBox rounding

EXPECTED_A5_PAGES = 24
EXPECTED_BOOKLET_PAGES = 12


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def booklet_spreads(page_count: int = 24) -> list[tuple[int, int]]:
    """Return (left, right) pairs in print order for a 24-page booklet."""
    if page_count % 4 != 0:
        raise ValueError("page_count must be a multiple of 4")
    spreads: list[tuple[int, int]] = []
    sheets = page_count // 4
    for sheet in range(sheets):
        left_front = page_count - 2 * sheet
        right_front = 2 * sheet + 1
        left_back = 2 * sheet + 2
        right_back = page_count - 2 * sheet - 1
        spreads.append((left_front, right_front))
        spreads.append((left_back, right_back))
    return spreads


def require_pypdf():
    try:
        from pypdf import PageObject, PdfReader, PdfWriter, Transformation
    except ImportError as exc:
        print(
            "Missing dependency: pypdf\n"
            "Install with:  pip install pypdf\n"
            "           or:  uv pip install pypdf",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    return PageObject, PdfReader, PdfWriter, Transformation


def compile_typst(root: Path, source: Path, output: Path) -> None:
    """Compile Typst via CLI if available, else via the Python typst package."""
    output.parent.mkdir(parents=True, exist_ok=True)
    typst_bin = shutil.which("typst")
    if typst_bin:
        cmd = [
            typst_bin,
            "compile",
            "--root",
            str(root),
            str(source),
            str(output),
        ]
        print(f"Compiling with Typst CLI: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print("Typst compilation failed.", file=sys.stderr)
            raise SystemExit(exc.returncode) from exc
        return

    try:
        import typst
    except ImportError as exc:
        print(
            "Typst is not available.\n"
            "Install the Typst CLI from https://typst.app/docs/installation/\n"
            "  or install the Python package:  pip install typst\n"
            "                              or:  uv pip install typst",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    print(f"Compiling with Python typst package: {source} → {output}")
    try:
        typst.compile(str(source), output=str(output), root=str(root))
    except Exception as exc:  # noqa: BLE001 — surface Typst errors clearly
        print(f"Typst compilation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def verify_pdf(
    path: Path,
    *,
    expected_pages: int,
    expected_w: float,
    expected_h: float,
    label: str,
) -> None:
    _, PdfReader, _, _ = require_pypdf()
    reader = PdfReader(str(path))
    n = len(reader.pages)
    if n != expected_pages:
        print(
            f"{label}: expected {expected_pages} pages, found {n}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    page = reader.pages[0]
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)
    if abs(w - expected_w) > TOL_PT or abs(h - expected_h) > TOL_PT:
        print(
            f"{label}: unexpected page size "
            f"{w:.1f}×{h:.1f} pt "
            f"(expected ≈ {expected_w:.1f}×{expected_h:.1f} pt)",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(f"OK  {label}: {n} pages, {w:.1f}×{h:.1f} pt")


def impose_booklet(a5_pdf: Path, booklet_pdf: Path) -> list[tuple[int, int]]:
    PageObject, PdfReader, PdfWriter, Transformation = require_pypdf()
    reader = PdfReader(str(a5_pdf))
    pages = list(reader.pages)
    if len(pages) != EXPECTED_A5_PAGES:
        print(
            f"Cannot impose: need {EXPECTED_A5_PAGES} A5 pages, got {len(pages)}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    spreads = booklet_spreads(EXPECTED_A5_PAGES)
    sheet_w = A4_LAND_W_PT
    sheet_h = A4_LAND_H_PT
    half_w = sheet_w / 2.0
    writer = PdfWriter()

    for left_idx, right_idx in spreads:
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)

        def place(src_index: int, x_offset: float) -> None:
            src = pages[src_index - 1]
            src_w = float(src.mediabox.width)
            src_h = float(src.mediabox.height)
            scale = min(half_w / src_w, sheet_h / src_h)
            tx = x_offset + (half_w - src_w * scale) / 2.0
            ty = (sheet_h - src_h * scale) / 2.0
            sheet.merge_transformed_page(
                src,
                Transformation().scale(scale, scale).translate(tx, ty),
                over=True,
            )

        place(left_idx, 0.0)
        place(right_idx, half_w)
        writer.add_page(sheet)

    booklet_pdf.parent.mkdir(parents=True, exist_ok=True)
    with booklet_pdf.open("wb") as fh:
        writer.write(fh)
    return spreads


def print_pairing(spreads: list[tuple[int, int]]) -> None:
    print("\nBooklet page pairing (left + right on each A4 landscape side):")
    print(f"{'Sheet':<8}{'Side':<8}{'Left':>6}{'Right':>8}")
    for i, (left, right) in enumerate(spreads):
        sheet = i // 2 + 1
        side = "Front" if i % 2 == 0 else "Back"
        print(f"{sheet:<8}{side:<8}{left:>6}{right:>8}")
    print()


def main() -> int:
    root = project_root()
    source = root / "src" / "main.typ"
    out_dir = root / "output"
    a5_pdf = out_dir / "creobook-kids-planner-a5.pdf"
    booklet_pdf = out_dir / "creobook-kids-planner-booklet-a4.pdf"

    if not source.is_file():
        print(f"Missing Typst source: {source}", file=sys.stderr)
        return 1

    print(f"Project root: {root}")
    compile_typst(root, source, a5_pdf)
    verify_pdf(
        a5_pdf,
        expected_pages=EXPECTED_A5_PAGES,
        expected_w=A5_W_PT,
        expected_h=A5_H_PT,
        label="A5 pages PDF",
    )

    spreads = impose_booklet(a5_pdf, booklet_pdf)
    verify_pdf(
        booklet_pdf,
        expected_pages=EXPECTED_BOOKLET_PAGES,
        expected_w=A4_LAND_W_PT,
        expected_h=A4_LAND_H_PT,
        label="A4 booklet PDF",
    )
    print_pairing(spreads)

    print("Generated files:")
    print(f"  {a5_pdf.relative_to(root)}")
    print(f"  {booklet_pdf.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
