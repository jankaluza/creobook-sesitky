# CreoBook Templates

Generate printable **A5** notebook inserts and calendars for CreoBook, with optional **A4 landscape** booklet imposition for duplex printing.

Local-only pipeline: Python builds structured JSON → Typst renders vector A5 PDFs → Python imposes booklets. No Typst web app or remote services.

## Stack

| Piece | Role |
| --- | --- |
| [Typst](https://typst.app) `0.13.2` (pinned via PyPI `typst`) | Document layout & PDF |
| Python ≥ 3.13 | Orchestration |
| [uv](https://github.com/astral-sh/uv) | Dependencies & venv |
| Typer | CLI |
| Pydantic | Theme / holiday validation |
| pypdf | Booklet imposition |
| pytest | Tests |
| Poppler (`pdftoppm`) | Optional PNG previews |

## Install

```bash
# Requires uv (https://docs.astral.sh/uv/)
uv sync --all-extras
```

Bundled font: **DejaVu Sans** (`assets/fonts/`) with Czech glyph coverage (Bitstream Vera / DejaVu licence in that folder).

## Generate pages

All lengths are configured in millimetres in `config/theme.toml` (margins, colours, fonts, line widths). Templates read theme tokens from JSON — do not hard-code them in individual `.typ` files.

```bash
# Ruled / dotted / grid / blank / checklist / Cornell
uv run creobook page ruled --spacing 7
uv run creobook page ruled --spacing 7 --margin-line
uv run creobook page dotted --spacing 5
uv run creobook page grid --spacing 5
uv run creobook page blank
uv run creobook page checklist
uv run creobook page cornell

# Twelve-month Czech calendar (Monday-first, ISO weeks, holidays)
uv run creobook calendar --year 2027

# Everything for a year (+ booklets)
uv run creobook build-all --year 2027
```

Outputs land in `output/pages/` by default.

Accent colour override (hex):

```bash
uv run creobook page ruled --accent "#444444"
```

## Booklet imposition

Imposition is a separate step. Templates never contain booklet ordering logic.

```bash
uv run creobook booklet output/pages/calendar-2027.pdf
```

Behaviour:

- Input: sequential A5 PDF
- Output: A4 landscape (`297 × 210 mm`), two A5 pages per side
- Blank pages are added until the count is divisible by four
- Vector content is preserved (page merge)
- Optional subtle centre fold guide (`--fold-guide` / `--no-fold-guide`)

### Printing

1. Print the booklet PDF on **A4**.
2. Use **duplex** (two-sided) mode.
3. Set flip / tumble to **short edge** (short-edge binding for landscape sheets).
4. Fold each sheet in half along the long centre line and nest into a booklet.

For twelve logical pages the sheet order is:

| Sheet side | Left | Right |
| --- | --- | --- |
| 1 front | 12 | 1 |
| 1 back | 2 | 11 |
| 2 front | 10 | 3 |
| 2 back | 4 | 9 |
| 3 front | 8 | 5 |
| 3 back | 6 | 7 |

## Previews

Requires Poppler (`pdftoppm`). Optional contact sheet via ImageMagick `montage` or Pillow.

```bash
uv run creobook preview output/pages/calendar-2027.pdf --dpi 72
```

## Configuration

- `config/theme.toml` — page size, mirrored margins (default inner 13 mm, outer 9 mm, top/bottom 11 mm), grayscale-friendly palette, accent, fonts, line widths
- `config/holidays-cz.yaml` — Czech public holidays (fixed dates + Easter-relative offsets)

Logical page size: **148 × 210 mm** (A5). Duplex uses Typst `inside` / `outside` margins so inner/outer edges mirror correctly.

## Architecture

1. Python generates structured JSON (`creobook.calendar`, `creobook.compiler`).
2. Typst loads JSON and renders logical A5 pages (`templates/`).
3. `creobook.imposition` places A5 pages onto A4 landscape sheets in booklet order.
4. Rendering and imposition work independently.

Pinned Typst version: see `PINNED_TYPST_VERSION` in `src/creobook/compiler.py` and the `typst==…` dependency in `pyproject.toml`.

## just recipes

```bash
just install
just test
just samples          # sample PDFs for year 2026
just calendar 2027
just booklet output/pages/calendar-2027.pdf
```

## Tests

```bash
uv run pytest -q
```

Coverage includes PDF page counts, A5/A4 MediaBox sizes, month presence, leap years, ISO weeks around New Year, booklet ordering, Czech holidays, and MediaBox containment checks.

## Licence

Project code is MIT. DejaVu fonts retain their upstream licence (`assets/fonts/LICENSE-DejaVu.txt`).
