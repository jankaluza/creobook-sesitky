# CreoBook Templates

Generate printable **A5** notebook inserts and calendars for CreoBook, with optional **A4 landscape** booklet imposition for duplex printing.

Local-only pipeline: Python builds structured JSON → Typst renders vector A5 PDFs → Python imposes booklets. No Typst web app or remote services.

Output is **high-contrast black & white** (solid black rules/text) so thin lines and labels print reliably on typical laser printers.

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

Bundled fonts: **Inter** (primary, OFL) and DejaVu Sans (fallback) in `assets/fonts/`, with Czech glyph coverage.

Pinned Typst compiler: **0.13.2** (PyPI package `typst==0.13.2`).

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

Outputs land in `output/pages/` as `creobook-$name-a5.pdf` (Czech ASCII slugs):

| Page type | File | Subtitle |
| --- | --- | --- |
| blank | `creobook-prazdny-a5.pdf` | Prázdný |
| ruled | `creobook-linky-a5.pdf` | Linky |
| ruled --margin-line | `creobook-linky-odsazene-a5.pdf` | Linky odsazené |
| dotted | `creobook-tecky-a5.pdf` | Tečky |
| grid | `creobook-mrizka-a5.pdf` | Mřížka |
| checklist | `creobook-seznam-a5.pdf` | Seznam |
| cornell | `creobook-cornell-a5.pdf` | Cornell |
| calendar | `creobook-kalendar-a5.pdf` | Kalendář |

Imposed booklets use the same `creobook-$name-a5.pdf` basename in `output/booklet/`
(the suffix is A5 because that is the page size after folding). Repeating inserts
(linky, seznam, …) are generated as **20** sequential A5 pages so footers number
1–20 correctly.

Accent colour override (hex):

```bash
uv run creobook page ruled --accent "#444444"
```

## Quarterly planner

Modular one-quarter planner that fits under a single CreoBook elastic.

**Physical format** (be explicit when printing):

- 7 physical A4 sheets, duplex printed
- each printed A4 side holds two A5 pages → **14** A4 landscape PDF pages
- **28** logical A5 portrait pages in one nested booklet

```bash
uv run creobook planner quarter --year 2027 --quarter 1
```

Options: `--locale cs-CZ`, `--accent-color`, `--show-holidays` / `--no-show-holidays`,
`--fold-guide` / `--no-fold-guide`, `--output`.

Outputs:

- `output/pages/creobook-quarterly-planner-2027-q1-a5.pdf` — 28 sequential A5 pages
- `output/booklet/creobook-quarterly-planner-2027-q1-a4.pdf` — 14-side imposed booklet

Page structure:

1. Quarterly overview (goals, three mini calendars, milestones)
2–27. Thirteen weekly facing spreads (pairs 2–3 … 26–27)
28. Transfer to the next quarter (Q4 rolls to Q1 of the following year)

When a quarter intersects 14 ISO weeks, pages 2–3 are a special boundary spread
(opening partial week | closing partial week); the twelve complete weeks follow.

### Printing the quarterly planner

1. Open the booklet PDF.
2. Print on **A4**, landscape, **duplex**, flip on the **short edge**, **100% / actual size**
   (do not use “fit to printable area”).
3. Keep the seven sheets in order, nest them, fold on the centre line, and place
   under one CreoBook elastic.
4. At quarter end, archive the booklet and replace it with the next quarter.

## Game booklets

Deterministic pencil-and-paper games live under `src/creobook/games/` with Typst layouts in `templates/games/`. Packs are YAML in `config/games/packs/`.

```bash
# CreoBook Hlavolamy (16 A5 pages → 4 A4 sheets)
uv run creobook games generate \
  --pack hlavolamy \
  --output output/booklet/creobook-20260918-hlavolamy.pdf \
  --sheets 4 \
  --difficulty mixed \
  --seed 20260918 \
  --answers

# CreoBook Hry pro dva
uv run creobook games generate \
  --pack pro-dva \
  --output output/booklet/creobook-20260918-hry-pro-dva.pdf \
  --sheets 4 \
  --seed 20260918 \
  --no-answers

# Sudoku-only booklet (6 A4 sheets = 24 A5 pages, pages filled with puzzles)
uv run creobook games generate \
  --pack sudoku \
  --output output/booklet/creobook-20260918-sudoku.pdf \
  --sheets 6 \
  --seed 20260918 \
  --answers

# Single games (dev / testing)
uv run creobook games sudoku --difficulty easy --seed 42
uv run creobook games maze --difficulty medium --seed 42
uv run creobook games word-search --theme zvířata --seed 42
```

Or: `make` / `make games` — writes dated packs to `output/booklet/creobook-<YYYYMMDD>-<pack>.pdf`
using today’s date as both the filename infix and the default `--seed` (override with `DATE=` / `SEED=`).

### Printing game booklets

1. Open the A4 landscape PDF (e.g. `output/booklet/creobook-20260918-hlavolamy.pdf`).
2. Print on **A4**, **100% scale** (no fit-to-page).
3. **Duplex**, flip on the **short edge**.
4. Fold each sheet in half and nest into a booklet.

Logical pages are always a multiple of four (`sheets × 4`). Imposition stays a separate step from puzzle generation.

### Seeds

The same `--seed` always yields the same puzzles (per page slot). Change the seed for a new edition.

### Adding a game type

1. Implement a `GameGenerator` subclass in `src/creobook/games/`, decorate with `@register`, emit `PuzzleBase` + `answer`.
2. Import the module from `creobook.games` so it registers.
3. Add a Typst renderer branch in `templates/games/pages.typ`.
4. Reference the new `kind` from a pack YAML page slot.

### Adding Czech word lists

Add `config/games/words/<theme>.yaml`:

```yaml
words:
  - KOČKA
  - PES
```

Use uppercase; Czech diacritics are supported via Inter.

## Booklet imposition

Imposition is a separate step. Templates never contain booklet ordering logic.

```bash
uv run creobook booklet output/pages/creobook-kalendar-a5.pdf
```

Behaviour:

- Input: sequential A5 PDF
- Output: A4 landscape (`297 × 210 mm`), two A5 pages per side; file basename keeps `-a5` (folded page size)
- Blank pages are added until the count is divisible by four
- **Repeating inserts** (ruled, checklist, …) should be rendered with `--count 20` (5 sheets × 4) so page numbers run 1–20
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
# Multi-page contact-sheet style preview
uv run creobook preview output/pages/creobook-kalendar-a5.pdf --dpi 72

# One website PNG per booklet (also: make previews)
uv run creobook web-preview output/pages/creobook-linky-a5.pdf
# → output/preview/creobook-linky-a5.png
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

## just / make

```bash
just install
just test
just samples          # sample PDFs for year 2026
just calendar 2027
just booklet output/pages/creobook-kalendar-a5.pdf
```

Or with Make (regenerates all A5 pages, notebook booklets, and dated game packs):

```bash
make                  # YEAR=2026, DATE=$(date +%Y%m%d) by default
make games            # hlavolamy + pro-dva + sudoku → output/booklet/
make DATE=20260101    # pin edition date/seed
make YEAR=2027
make previews
make clean
```

## Tests

```bash
uv run pytest -q
```

Coverage includes PDF page counts, A5/A4 MediaBox sizes, month presence, leap years, ISO weeks around New Year, booklet ordering, Czech holidays, and MediaBox containment checks.

## Licence

Project code is MIT. DejaVu fonts retain their upstream licence (`assets/fonts/LICENSE-DejaVu.txt`).
