# Connect-the-dots booklets (spojovačky)

CreoBook connect-the-dots booklets use the same Typst pages and booklet imposition as the other game booklets. OpenAI draws a filled silhouette only. The program extracts the outline, places every number from 0 to the chosen maximum, and checks that the labels do not overlap. The image model never draws the numbers.

Image generation is paid. Nothing in the test suite calls the API. A normal command does not call it either, until you pass `--generate`.

## Install

From the repository root:

```bash
uv sync
```

Set the key in the environment. Do not commit it:

```bash
export OPENAI_API_KEY="..."
```

## How a puzzle is built

1. A local list picks an original subject for the theme (animals, dinosaurs, vehicles, space, fairy tales, sea creatures, nature, everyday objects). Unknown themes use the theme words as the subject.
2. The image model returns one filled black shape on white, with no text and no dots.
3. The largest dark shape is traced, smoothed, and simplified to a single outer contour.
4. Dots are spaced along that contour. Corners and narrow features get more dots than long gentle stretches.
5. Each number is tried in several positions around its dot. If any number would overlap, sit on a dot, or leave the page, that silhouette is rejected.
6. The answer page draws the same dots joined in order and prints the object name. It is not a second AI image.

A rejected silhouette is kept on disk. Fix it with `--regenerate-puzzle N`. The generator does not keep buying new images on its own.

## Commands

Plan the subjects only. This does not call OpenAI:

```bash
uv run creobook game spojovacky \
  --theme "Animals" \
  --title "Spojovačky – Zvířátka" \
  --puzzles 16 \
  --max-number 50 \
  --format A5 \
  --output output/spojovacky/zviratka \
  --dry-run
```

Draw the silhouettes and bind the booklet:

```bash
uv run creobook game spojovacky \
  --config output/spojovacky/zviratka/config.json \
  --generate
```

Difficulty presets, when you do not pass `--max-number`:

| Difficulty | Numbers |
| --- | --- |
| easy | 0–30 |
| medium | 0–50 |
| hard | 0–100 |

Mix several difficulties. The counts must add up to the booklet, and this example is 16 puzzles:

```bash
uv run creobook game spojovacky \
  --theme "Dinosaurs" \
  --title "Spojovačky – Dinosauři" \
  --mix 30:4,50:8,75:4 \
  --output output/spojovacky/dinosauri \
  --generate \
  --max-new 16
```

Rebuild the PDFs from saved geometry, with no API calls:

```bash
uv run creobook game spojovacky \
  --config output/spojovacky/zviratka/config.json \
  --pdf-only
```

Redraw one puzzle (1-based index in the plan):

```bash
uv run creobook game spojovacky \
  --config output/spojovacky/zviratka/config.json \
  --regenerate-puzzle 5
```

`--force-regenerate` redraws every silhouette and requires `--generate`. `--no-answers` leaves the solutions out. Numbering always starts at 0. The puzzle page says „Co se skrývá mezi tečkami?“ and does not name the object. Dot 0 has a small ring. Completed solutions are written to `*-reseni.pdf` and are not part of the folded booklet.

## Cache

Each puzzle lives in `puzzles/NN-name/`:

- `prompt.txt` — the silhouette prompt
- `original.png` — the image returned by the API
- `dots.json` — numbers, dot coordinates, and label positions
- `puzzle.svg` — the puzzle, with no connecting lines
- `answer.svg` — the same dots joined in order
- `meta.json` — model, prompt, and usage

A finished puzzle is reused while the prompt, maximum number, and page format stay the same. Deleting `dots.json` and keeping `original.png` rebuilds the geometry locally.

`review.html` shows each puzzle SVG, its number range, and the answer name.

## Printing

A5 booklets impose onto A4 landscape:

1. Open `*-tisk.pdf`.
2. Print at 100% scale.
3. Duplex, flip on the short edge.
4. Fold each sheet in half and nest them.

A6 booklets impose onto A5 landscape. The page count is padded to a multiple of four so the folded booklet closes.
