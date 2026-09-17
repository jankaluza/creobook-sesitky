"""CreoBook CLI — page rendering, calendar generation, booklet imposition."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

import typer

from creobook import __version__
from creobook.calendar import build_calendar_data
from creobook.compiler import compile_calendar, compile_page
from creobook.imposition import impose_booklet
from creobook.theme import (
    default_booklet_dir,
    default_pages_dir,
    load_theme,
    project_root,
)

app = typer.Typer(
    name="creobook",
    help="Generate printable CreoBook A5 notebook inserts and A4 booklet PDFs.",
    no_args_is_help=True,
)
page_app = typer.Typer(help="Render a single page type to an A5 PDF.")
app.add_typer(page_app, name="page")


def _pages_dir() -> Path:
    path = default_pages_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _booklet_dir() -> Path:
    path = default_booklet_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


@app.callback()
def main_callback() -> None:
    """CreoBook templates CLI."""


@app.command("version")
def version_cmd() -> None:
    """Show package and pinned Typst versions."""
    from creobook.compiler import PINNED_TYPST_VERSION

    typer.echo(f"creobook-templates {__version__}")
    typer.echo(f"typst (pinned) {PINNED_TYPST_VERSION}")


@page_app.command("blank")
def page_blank(
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    count: int = typer.Option(1, "--count", "-n", help="Number of pages"),
    accent: Optional[str] = typer.Option(None, "--accent", help="Accent colour hex"),
) -> None:
    """Blank page with subtle header and footer."""
    out = output or (_pages_dir() / "blank.pdf")
    compile_page("blank", out, accent=accent, page_count=count)
    typer.echo(f"Wrote {out}")


@page_app.command("ruled")
def page_ruled(
    spacing: Optional[float] = typer.Option(None, "--spacing", help="Line spacing in mm"),
    margin_line: bool = typer.Option(
        False, "--margin-line", help="Add vertical margin line"
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    count: int = typer.Option(1, "--count", "-n"),
    accent: Optional[str] = typer.Option(None, "--accent"),
) -> None:
    """Ruled page with configurable spacing (optionally with vertical margin)."""
    out = output or (
        _pages_dir() / ("ruled-margin.pdf" if margin_line else "ruled.pdf")
    )
    compile_page(
        "ruled",
        out,
        accent=accent,
        spacing_mm=spacing,
        margin_line=margin_line,
        page_count=count,
    )
    typer.echo(f"Wrote {out}")


@page_app.command("dotted")
def page_dotted(
    spacing: Optional[float] = typer.Option(None, "--spacing", help="Dot spacing in mm"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    count: int = typer.Option(1, "--count", "-n"),
    accent: Optional[str] = typer.Option(None, "--accent"),
) -> None:
    """Dot-grid page with configurable spacing."""
    out = output or (_pages_dir() / "dotted.pdf")
    compile_page(
        "dotted", out, accent=accent, spacing_mm=spacing, page_count=count
    )
    typer.echo(f"Wrote {out}")


@page_app.command("grid")
def page_grid(
    spacing: Optional[float] = typer.Option(
        None, "--spacing", help="Grid spacing in mm"
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    count: int = typer.Option(1, "--count", "-n"),
    accent: Optional[str] = typer.Option(None, "--accent"),
) -> None:
    """Square-grid page with configurable spacing."""
    out = output or (_pages_dir() / "grid.pdf")
    compile_page("grid", out, accent=accent, spacing_mm=spacing, page_count=count)
    typer.echo(f"Wrote {out}")


@page_app.command("checklist")
def page_checklist(
    rows: Optional[int] = typer.Option(None, "--rows", help="Number of checklist rows"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    count: int = typer.Option(1, "--count", "-n"),
    accent: Optional[str] = typer.Option(None, "--accent"),
) -> None:
    """Checklist page."""
    out = output or (_pages_dir() / "checklist.pdf")
    compile_page("checklist", out, accent=accent, rows=rows, page_count=count)
    typer.echo(f"Wrote {out}")


@page_app.command("cornell")
def page_cornell(
    spacing: Optional[float] = typer.Option(None, "--spacing", help="Note line spacing mm"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    count: int = typer.Option(1, "--count", "-n"),
    accent: Optional[str] = typer.Option(None, "--accent"),
) -> None:
    """Cornell notes page."""
    out = output or (_pages_dir() / "cornell.pdf")
    compile_page(
        "cornell", out, accent=accent, spacing_mm=spacing, page_count=count
    )
    typer.echo(f"Wrote {out}")


@app.command("calendar")
def calendar_cmd(
    year: int = typer.Option(..., "--year", "-y", help="Calendar year"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    accent: Optional[str] = typer.Option(None, "--accent"),
) -> None:
    """Generate a twelve-page A5 monthly calendar (Czech locale)."""
    out = output or (_pages_dir() / f"calendar-{year}.pdf")
    data = build_calendar_data(year, accent=accent)
    compile_calendar(year, out, accent=accent, calendar_data=data)
    typer.echo(f"Wrote {out} ({len(data['months'])} months)")


@app.command("booklet")
def booklet_cmd(
    input_pdf: Path = typer.Argument(..., help="Sequential A5 PDF to impose"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    fold_guide: bool = typer.Option(
        True, "--fold-guide/--no-fold-guide", help="Centre fold marks"
    ),
) -> None:
    """Impose sequential A5 pages onto A4 landscape booklet sheets."""
    if not input_pdf.exists():
        raise typer.BadParameter(f"Input PDF not found: {input_pdf}")
    out = output or (_booklet_dir() / f"{input_pdf.stem}-booklet.pdf")
    impose_booklet(input_pdf, out, fold_guide=fold_guide)
    typer.echo(f"Wrote {out}")
    typer.echo(
        "Print duplex, flip on the short edge (A4 landscape booklet)."
    )


@app.command("build-all")
def build_all(
    year: int = typer.Option(2026, "--year", "-y"),
    accent: Optional[str] = typer.Option(None, "--accent"),
    booklet: bool = typer.Option(True, "--booklet/--no-booklet"),
) -> None:
    """Render all page types plus calendar; optionally impose booklets."""
    theme = load_theme().with_accent(accent)
    pages = _pages_dir()
    outputs: list[Path] = []

    for page_type, kwargs in [
        ("blank", {}),
        ("ruled", {"spacing_mm": theme.defaults.ruled_spacing_mm}),
        ("ruled", {"spacing_mm": theme.defaults.ruled_spacing_mm, "margin_line": True}),
        ("dotted", {"spacing_mm": theme.defaults.dotted_spacing_mm}),
        ("grid", {"spacing_mm": theme.defaults.grid_spacing_mm}),
        ("checklist", {}),
        ("cornell", {}),
    ]:
        suffix = "-margin" if kwargs.get("margin_line") else ""
        out = pages / f"{page_type}{suffix}.pdf"
        compile_page(page_type, out, accent=accent, **kwargs)
        outputs.append(out)
        typer.echo(f"Wrote {out}")

    cal_out = pages / f"calendar-{year}.pdf"
    compile_calendar(year, cal_out, accent=accent)
    outputs.append(cal_out)
    typer.echo(f"Wrote {cal_out}")

    if booklet:
        bdir = _booklet_dir()
        for pdf in outputs:
            bout = bdir / f"{pdf.stem}-booklet.pdf"
            impose_booklet(pdf, bout)
            typer.echo(f"Wrote {bout}")


@app.command("preview")
def preview_cmd(
    pdf: Path = typer.Argument(..., help="PDF to preview as PNG"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    dpi: int = typer.Option(72, "--dpi", help="Preview resolution"),
    contact_sheet: bool = typer.Option(
        True, "--contact-sheet/--no-contact-sheet", help="Build contact sheet"
    ),
) -> None:
    """Render low-resolution PNG previews with Poppler (pdftoppm) when available."""
    if shutil.which("pdftoppm") is None:
        typer.echo(
            "pdftoppm not found. Install Poppler (e.g. poppler-utils) for previews.",
            err=True,
        )
        raise typer.Exit(code=1)

    out_dir = output_dir or (project_root() / "output" / "preview" / pdf.stem)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "page"
    subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            str(dpi),
            str(pdf),
            str(prefix),
        ],
        check=True,
    )
    typer.echo(f"Wrote PNG previews under {out_dir}")

    if contact_sheet:
        _make_contact_sheet(out_dir, out_dir / "contact-sheet.png")


def _make_contact_sheet(preview_dir: Path, output: Path, cols: int = 4) -> None:
    """Assemble a simple contact sheet with ImageMagick or PIL if available."""
    pages = sorted(preview_dir.glob("page*.png"))
    if not pages:
        return

    if shutil.which("montage"):
        subprocess.run(
            [
                "montage",
                *[str(p) for p in pages],
                "-geometry",
                "200x280+8+8",
                "-tile",
                f"{cols}x",
                "-background",
                "#f0f0f0",
                str(output),
            ],
            check=False,
        )
        if output.exists():
            typer.echo(f"Wrote contact sheet {output}")
            return

    # Fallback: try Pillow if installed (optional)
    try:
        from PIL import Image
    except ImportError:
        typer.echo("Contact sheet skipped (install ImageMagick or Pillow).")
        return

    images = [Image.open(p) for p in pages]
    thumb_w, thumb_h = 200, 280
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (thumb_w + 8) + 8, rows * (thumb_h + 8) + 8), "#f0f0f0")
    for idx, img in enumerate(images):
        thumb = img.copy()
        thumb.thumbnail((thumb_w, thumb_h))
        r, c = divmod(idx, cols)
        # divmod gives (quotient, remainder) = (row-ish wrong)
        row, col = idx // cols, idx % cols
        x = 8 + col * (thumb_w + 8)
        y = 8 + row * (thumb_h + 8)
        sheet.paste(thumb, (x, y))
    sheet.save(output)
    typer.echo(f"Wrote contact sheet {output}")


if __name__ == "__main__":
    app()
