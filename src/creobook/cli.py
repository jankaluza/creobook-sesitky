"""CreoBook CLI — page rendering, calendar generation, booklet imposition."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

import typer

from creobook import __version__
from creobook.calendar import build_calendar_data
from creobook.compiler import compile_calendar, compile_page, compile_planner
from creobook.imposition import BOOKLET_A5_PAGES, impose_booklet
from creobook.names import a5_filename, booklet_filename_from_pages_path
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
games_app = typer.Typer(help="Generate pencil-and-paper game booklets and puzzles.")
app.add_typer(games_app, name="games")
planner_app = typer.Typer(help="Generate modular quarterly planner booklets.")
app.add_typer(planner_app, name="planner")


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
    out = output or (_pages_dir() / a5_filename("blank"))
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
    out = output or (_pages_dir() / a5_filename("ruled", margin_line=margin_line))
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
    out = output or (_pages_dir() / a5_filename("dotted"))
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
    out = output or (_pages_dir() / a5_filename("grid"))
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
    out = output or (_pages_dir() / a5_filename("checklist"))
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
    out = output or (_pages_dir() / a5_filename("cornell"))
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
    out = output or (_pages_dir() / a5_filename("calendar"))
    data = build_calendar_data(year, accent=accent)
    compile_calendar(year, out, accent=accent, calendar_data=data)
    typer.echo(f"Wrote {out} ({len(data['months'])} months)")


@planner_app.command("quarter")
def planner_quarter_cmd(
    year: int = typer.Option(..., "--year", "-y", help="Calendar year"),
    quarter: int = typer.Option(
        ..., "--quarter", "-q", help="Quarter number (1–4)"
    ),
    locale: str = typer.Option("cs-CZ", "--locale", help="Locale (cs-CZ)"),
    accent_color: Optional[str] = typer.Option(
        None, "--accent-color", help="Accent colour hex"
    ),
    show_holidays: bool = typer.Option(
        True, "--show-holidays/--no-show-holidays", help="Mark Czech public holidays"
    ),
    fold_guide: bool = typer.Option(
        True, "--fold-guide/--no-fold-guide", help="Centre fold marks on booklet"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional A5 pages PDF path (booklet uses default booklet path)",
    ),
) -> None:
    """
    Generate a 28-page A5 quarterly planner and impose it as a 7-sheet booklet.

    Physical format: 7 duplex A4 sheets → 14 A4 landscape PDF pages → 28 A5 pages.
    """
    from creobook.planner import (
        PLANNER_A4_SIDES,
        PLANNER_A5_PAGES,
        PLANNER_PHYSICAL_SHEETS,
        PlannerError,
        build_planner_data,
        planner_a5_filename,
        planner_booklet_filename,
        validate_quarter,
    )

    try:
        validate_quarter(quarter)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    try:
        data = build_planner_data(
            year,
            quarter,
            locale=locale,
            accent=accent_color,
            show_holidays=show_holidays,
        )
    except (PlannerError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    pages_out = output or (_pages_dir() / planner_a5_filename(year, quarter))
    compile_planner(
        year,
        quarter,
        pages_out,
        accent=accent_color,
        locale=locale,
        show_holidays=show_holidays,
        planner_data=data,
    )
    typer.echo(
        f"Wrote {pages_out} ({PLANNER_A5_PAGES} A5 pages · "
        f"{data['week_count']} ISO weeks · "
        f"{'boundary' if data['boundary_mode'] else 'standard'} mode)"
    )

    booklet_out = _booklet_dir() / planner_booklet_filename(year, quarter)
    impose_booklet(pages_out, booklet_out, fold_guide=fold_guide)
    typer.echo(
        f"Wrote {booklet_out} ({PLANNER_A4_SIDES} A4 sides · "
        f"{PLANNER_PHYSICAL_SHEETS} physical duplex sheets)"
    )
    typer.echo(
        "Print duplex, flip on the short edge, 100% scale (A4 landscape booklet)."
    )


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
    out = output or (_booklet_dir() / booklet_filename_from_pages_path(input_pdf))
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
    pages: int = typer.Option(
        BOOKLET_A5_PAGES,
        "--pages",
        "-n",
        help="A5 page count for repeating notebook inserts (default: 20)",
    ),
) -> None:
    """Render all page types plus calendar; optionally impose booklets."""
    theme = load_theme().with_accent(accent)
    pages_dir = _pages_dir()
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
        margin_line = bool(kwargs.get("margin_line"))
        out = pages_dir / a5_filename(page_type, margin_line=margin_line)
        compile_page(page_type, out, accent=accent, page_count=pages, **kwargs)
        outputs.append(out)
        typer.echo(f"Wrote {out}")

    cal_out = pages_dir / a5_filename("calendar")
    compile_calendar(year, cal_out, accent=accent)
    outputs.append(cal_out)
    typer.echo(f"Wrote {cal_out}")

    if booklet:
        bdir = _booklet_dir()
        for pdf in outputs:
            bout = bdir / booklet_filename_from_pages_path(pdf)
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


@app.command("web-preview")
def web_preview_cmd(
    pdf: Path = typer.Argument(..., help="A5 PDF to sample for a website PNG"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output PNG path (default: output/preview/<stem>.png)"
    ),
    dpi: int = typer.Option(144, "--dpi", help="PNG resolution"),
    page: int = typer.Option(1, "--page", "-p", help="1-based page to export"),
) -> None:
    """Export a single PNG of one page for website product imagery."""
    if shutil.which("pdftoppm") is None:
        typer.echo(
            "pdftoppm not found. Install Poppler (e.g. poppler-utils) for previews.",
            err=True,
        )
        raise typer.Exit(code=1)
    if not pdf.exists():
        raise typer.BadParameter(f"PDF not found: {pdf}")

    out = output or (project_root() / "output" / "preview" / f"{pdf.stem}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    # pdftoppm appends .png to the prefix when using -singlefile
    prefix = out.with_suffix("")
    subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            str(dpi),
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            str(pdf),
            str(prefix),
        ],
        check=True,
    )
    if not out.exists():
        raise typer.Exit(code=1)
    typer.echo(f"Wrote {out}")


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


@games_app.command("generate")
def games_generate(
    pack: str = typer.Option(..., "--pack", "-p", help="Pack id: hlavolamy | pro-dva"),
    output: Path = typer.Option(
        ..., "--output", "-o", help="Output A4 booklet PDF (or A5 if --pages-only)"
    ),
    sheets: Optional[int] = typer.Option(None, "--sheets", help="Physical A4 sheets"),
    difficulty: Optional[str] = typer.Option(
        None, "--difficulty", help="easy|medium|hard|mixed"
    ),
    seed: Optional[int] = typer.Option(None, "--seed"),
    answers: bool = typer.Option(
        True, "--answers/--no-answers", help="Include answer pages where configured"
    ),
    pages_only: bool = typer.Option(
        False, "--pages-only", help="Write sequential A5 PDF only (no imposition)"
    ),
    accent: Optional[str] = typer.Option(None, "--accent"),
) -> None:
    """Generate a full game booklet pack and impose to A4 landscape."""
    from creobook.games.booklet import compile_games_booklet
    from creobook.games.models import BookletBuildOptions, Difficulty

    diff = Difficulty(difficulty) if difficulty else None
    opts = BookletBuildOptions(
        pack_id=pack,
        sheets=sheets,
        difficulty=diff,
        seed=seed,
        answers=answers,
        accent=accent,
    )
    if pages_only:
        pages_out = output
        booklet_out = None
        impose = False
    else:
        # Write A5 pages alongside, impose to --output
        pages_out = output.with_name(output.stem + "-pages.pdf")
        if output.suffix.lower() != ".pdf":
            pages_out = Path(str(output) + "-pages.pdf")
        booklet_out = output
        impose = True
    result = compile_games_booklet(
        opts,
        pages_out,
        impose=impose,
        booklet_output=booklet_out,
    )
    for label, path in result.items():
        typer.echo(f"Wrote {label}: {path}")
    if impose:
        typer.echo("Print duplex, flip on the short edge, 100% scale (A4 landscape).")


def _game_single(
    kind: str,
    difficulty: str,
    seed: int,
    output: Optional[Path],
    theme: Optional[str] = None,
    accent: Optional[str] = None,
) -> None:
    from creobook.games.booklet import compile_single_game
    from creobook.games.models import Difficulty

    out = output or (_pages_dir() / f"game-{kind}.pdf")
    compile_single_game(
        kind,
        out,
        seed=seed,
        difficulty=Difficulty(difficulty),
        theme_name=theme,
        accent=accent,
    )
    typer.echo(f"Wrote {out}")


@games_app.command("sudoku")
def games_sudoku(
    difficulty: str = typer.Option("easy", "--difficulty"),
    seed: int = typer.Option(42, "--seed"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a single Sudoku page."""
    _game_single("sudoku", difficulty, seed, output)


@games_app.command("maze")
def games_maze(
    difficulty: str = typer.Option("medium", "--difficulty"),
    seed: int = typer.Option(42, "--seed"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a single maze page."""
    _game_single("maze", difficulty, seed, output)


@games_app.command("word-search")
def games_word_search(
    theme: str = typer.Option("zvířata", "--theme"),
    difficulty: str = typer.Option("easy", "--difficulty"),
    seed: int = typer.Option(42, "--seed"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate a single Czech word-search page."""
    _game_single("word_search", difficulty, seed, output, theme=theme)


@games_app.command("nonogram")
def games_nonogram(
    difficulty: str = typer.Option("easy", "--difficulty"),
    seed: int = typer.Option(42, "--seed"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    _game_single("nonogram", difficulty, seed, output)


@games_app.command("connect-dots")
def games_connect_dots(
    difficulty: str = typer.Option("easy", "--difficulty"),
    seed: int = typer.Option(42, "--seed"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    _game_single("connect_dots", difficulty, seed, output)


@games_app.command("spot-difference")
def games_spot_difference(
    difficulty: str = typer.Option("easy", "--difficulty"),
    seed: int = typer.Option(42, "--seed"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    _game_single("spot_difference", difficulty, seed, output)


@games_app.command("cipher")
def games_cipher(
    difficulty: str = typer.Option("easy", "--difficulty"),
    seed: int = typer.Option(42, "--seed"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    _game_single("cipher", difficulty, seed, output)


if __name__ == "__main__":
    app()
