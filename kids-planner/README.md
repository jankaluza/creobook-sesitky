# CreoBook kids planner — „MŮJ PLÁN“

Český prázdný plánovač pro děti (cca 7–11 let) do modulárního zápisníku
**CreoBook**. Děti a rodiče si sami dopisují rozvrh, rutiny a úkoly — nic není
předvyplněné.

## What it generates

```bash
python scripts/build.py
```

creates:

| File | Description |
|------|-------------|
| `output/creobook-kids-planner-a5.pdf` | 24 A5 portrait pages in reading order |
| `output/creobook-kids-planner-booklet-a4.pdf` | 12 A4 landscape sides, already imposed for duplex folding |

Physical result: **6 A4 sheets**, duplex, short-edge flip → one nested 24-page A5 booklet.

## Requirements

- **Typst** — either the [Typst CLI](https://typst.app/docs/installation/) **or** the Python package `typst`
- **Python 3.10+**
- **pypdf** — for booklet imposition and PDF checks

### Install Typst CLI (optional if using the Python package)

```bash
# macOS (Homebrew)
brew install typst

# or download a release from https://github.com/typst/typst/releases
```

### Install Python dependencies

```bash
pip install typst pypdf
# or
uv pip install typst pypdf
```

The build script prefers the `typst` CLI when it is on `PATH`; otherwise it uses the
Python `typst` package.

## Build

From this project directory:

```bash
python scripts/build.py
```

The script will:

1. Compile `src/main.typ` to the A5 PDF  
2. Verify **24** A5 pages and dimensions  
3. Impose the A4 landscape booklet  
4. Verify **12** A4 pages and dimensions  
5. Print the sheet pairing table to the terminal  

## A5 vs A4 PDF

- **A5 PDF** — for proofreading on screen, or if you impose yourself.  
- **A4 booklet PDF** — ready to print. Each landscape page already holds two A5
  pages in booklet order. **Do not** enable printer “booklet” mode.

## Editing the design

| File | Role |
|------|------|
| `src/theme.typ` | Colours, fonts, sizes, margins, stroke weights |
| `src/components.typ` | Reusable UI: titles, checkboxes, timetable, day panels, … |
| `src/content.typ` | Page wording and page order (blank templates only) |
| `src/main.typ` | Document setup and page loop |

### Colours and typography

Open `src/theme.typ`. Useful knobs:

- `color-ink`, `color-accent`, `color-panel`, `color-line`
- `font-family` (defaults to Montserrat / Noto Sans / DejaVu — Czech-capable)
- `size-title`, `size-heading`, `size-body`
- `margin-inside` (14 mm), `margin-outside` (10 mm)

### Page content

Edit labels and instructions in `src/content.typ`. Routine pages (`page-morning`,
`page-after-school`, `page-bedtime`) share `page-routine` — reuse it for extra
custom routines if you add pages later (remember booklet length must stay a
multiple of 4).

Weekly plan pages (9–20) all call `page-weekly-plan()`.

## Printing

Settings for the **A4 booklet** PDF:

| Setting | Value |
|---------|--------|
| Paper size | A4 |
| Orientation | Landscape |
| Scale | Actual size / 100% |
| Duplex | On |
| Flip | **Short edge** |
| Printer booklet mode | **Off** (PDF is already imposed) |

After printing: keep sheets in order, nest them, fold once on the centre line,
place under a CreoBook elastic. No stapling required.

### Manual duplex

1. Print the front of all sheets.  
2. Reinsert the stack in the correct orientation for short-edge flip.  
3. Print the reverse sides.  
4. Test with **one sheet** before the full run.

## Page map

1. Obálka — MŮJ PLÁN  
2. Můj rozvrh  
3. Moje odpoledne  
4. Moje ráno  
5. Po škole  
6. Před spaním  
7. Moje školní taška  
8. Moje pravidelné úkoly  
9–20. Můj týden (×12)  
21. Důležitá data  
22. Můj projekt  
23. Ohlédnutí  
24. Poznámky a nápady  

## Licence note

This mini-project is part of CreoBook templates. Fonts are resolved from the
system (Montserrat, Noto Sans, DejaVu Sans, …).
