# Coloring booklets (omalovánky)

CreoBook coloring booklets use the same Typst page renderer and booklet imposition as the other game booklets. OpenAI draws the line art. The PDF step only places those PNGs.

Image generation is paid. Nothing in the test suite calls the API. A normal command does not call it either, until you pass `--generate`.

## Install

From the repository root:

```bash
uv sync
```

That installs Pillow and the official OpenAI SDK together with the rest of CreoBook.

Set the key in the environment. Do not commit it and do not put it in the repository:

```bash
export OPENAI_API_KEY="..."
```

## Models

Image models:

- `gpt-image-2.5-flare` (default) — everyday generation
- `gpt-image-2.5-sunburst` — higher quality

Quality is `low`, `medium` (default), or `high`. Illustrations are portrait PNGs. The default size is `1024x1536`. `2160x3840` is the other accepted portrait size.

The illustration plan uses a text model, default `gpt-6-astra` (`--text-model`).

## Commands

Plan only. This may call the text model once if `plan.json` does not exist yet. It does not generate images:

```bash
uv run creobook game coloring \
  --theme "Forest animals" \
  --title "Lesní kamarádi" \
  --age-group 6-8 \
  --illustrations 16 \
  --format A5 \
  --output output/coloring/lesni-kamaradi \
  --dry-run
```

Edit `output/coloring/lesni-kamaradi/plan.json` if you want different scenes. Then generate the missing images and build the PDFs:

```bash
uv run creobook game coloring \
  --config output/coloring/lesni-kamaradi/config.json \
  --generate
```

The command prints how many images are cached, how many would be new, the model, and the quality. If `config/coloring/pricing.json` has a numeric per-image price, it also prints an estimate. Copy `config/coloring/pricing.example.json` to `config/coloring/pricing.json` and fill in prices you trust. Prices are not hardcoded. When the API returns usage, those token counts are stored in each illustration's `meta.json` and printed. That usage is not converted into money unless the pricing file says so.

`--max-new` defaults to 16. If more new images are required, the command stops before any image request.

Rebuild the PDFs from cached PNGs, with no API calls:

```bash
uv run creobook game coloring \
  --config output/coloring/lesni-kamaradi/config.json \
  --pdf-only
```

Regenerate one illustration (1-based index in the plan):

```bash
uv run creobook game coloring \
  --config output/coloring/lesni-kamaradi/config.json \
  --regenerate-image 5
```

`--force-regenerate` redraws every illustration and requires `--generate`.

The cover plus the illustrations always fill a whole signature (a multiple of four pages). If `--illustrations` would leave a short last sheet, the planner asks for a few more drawings instead of inserting blank pages. Sixteen illustrations become nineteen, so the booklet has twenty pages.

`--single-sided` still leaves the back of each drawing blank so markers do not bleed through. Those blank pages follow the booklet's physical reverses.

## Cache

Each illustration lives in `illustrations/NN-id/`:

- `prompt.txt` — the exact image prompt
- `original.png` — the PNG returned by the API
- `print.png` — the processed line art used in the PDF
- `thumb.png` — small preview
- `meta.json` — model, size, quality, timestamp, usage, and quality warnings

Files are written atomically. If a run stops after `original.png` and before `print.png`, the next run processes the original locally and does not call the image API again. A finished illustration is reused while the prompt, model, quality, and size stay the same.

`review.html` is a contact sheet: number, title, thumbnail, status, and warnings. Warnings do not delete the image. Look at the sheet, then regenerate the ones you do not want.

Quality checks look at dimensions, white background, dark-pixel share, large solid black areas, leftover gray, blank pages, and very dense drawings.

## Copyright

The planner is told to invent original scenes. Before any image call, titles and descriptions are scanned for obvious franchise, character, and brand names. A hit blocks `--generate` until you edit `plan.json`. The scan is a precaution, not a legal clearance. The generator does not download reference images.

## Printing

A5 booklets impose onto A4 landscape, the same fold as Sudoku and the other game booklets:

1. Open `*-tisk.pdf`.
2. Print at 100% scale.
3. Duplex, flip on the short edge.
4. Fold each sheet in half and nest them.

A6 booklets are 105 × 148 mm. Their print PDF is A5 landscape (two A6 pages per side). Print that on A5 paper, duplex, flip on the short edge, and fold in half.

Reading-order PDFs are `*-a5.pdf` or `*-a6.pdf` in the same folder.

## Friday shop run

`scripts/publish_herni.py` publishes one new coloring theme each Friday, after Sudoku, Osmisměrky, and Bludiště. It walks the fixed theme list and skips any theme whose product is already on the shop. The description, categories, and price are copied from [Omalovánky – Lesní kamarádi](https://www.creobook.cz/produkt/omalovanky-lesni-kamaradi/). The product image is the middle page of the reading-order PDF. The download is the imposed print PDF.

The run needs `OPENAI_API_KEY` in `/etc/creobook/herni.env` (Ansible vault `openai_api_key`, or the `OPENAI_API_KEY` GitHub secret). Without the key the three game booklets still publish and the coloring booklet is skipped. `--dry-run` only prints the next missing theme. It does not call the image API.
