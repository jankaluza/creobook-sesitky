# Najdi slona!

Seek-and-find coloring booklets. Each page is a busy black-and-white scene. The child looks for one small elephant, then colors the picture.

The elephant is drawn once. The same picture is placed in the page header and composited into every scene. Scene prompts tell the image model not to draw an elephant. The program inserts the saved elephant afterwards, so the reference and the hidden animal match.

Image generation is paid. Tests do not call the API. A normal command does not call it either, until you pass `--generate`.

## Install

From the repository root:

```bash
uv sync
```

Set the key in the environment. Do not commit it and do not paste it into the command line:

```bash
export OPENAI_API_KEY="..."
```

The image models are `gpt-image-2.5-flare` (default) and `gpt-image-2.5-sunburst`. Quality is `low`, `medium`, or `high`. Scene size is a portrait size the coloring booklets already use: `1024x1536` or `2160x3840`. The text plan uses `gpt-6-astra`.

## How a page is built

1. The text model writes `plan.json`: one distinct location per page, in the language of the booklet title. Any theme works. The plan is not a fixed list of circus or factory rooms.
2. The image model draws one elephant. A few themes add a simple accessory (circus bow tie, factory overalls, pirate hat, space helmet, knight helmet). Other themes get a plain elephant.
3. Exterior white is removed with a flood fill. White regions inside the outline stay white, so the elephant can still be colored.
4. Each scene is drawn as black-and-white line art, with an explicit instruction not to include elephants.
5. The scene is thresholded. The program looks for a white gap inside the drawing, big enough for the elephant and next to the surrounding objects, and places it there. Different pages use different gaps. Scene lines are cleared only where the elephant covers them. A position set with `--move-elephant` stays put.
6. The header “Najdi slona!” and the solution circles are drawn by Typst from the saved placement. They are not part of the generated image.

The same elephant file is reused on every page. `--regenerate-elephant` draws a new character and rebuilds the composites from the saved scenes.

Difficulty is the elephant’s width as a fraction of the scene:

| Difficulty | Width |
| --- | --- |
| easy | about 11% |
| medium | about 8.5% |
| hard | about 6% |

The elephant stands in open space inside the scene. It is not dropped on a fixed coordinate. Each page hides a different piece of that elephant: the whole body, the head, an ear, the legs, or the trunk side, sometimes mirrored. The small picture in the header is the same piece. The cover still shows the whole elephant.

Mix page sizes in one booklet. Easy pages use a larger elephant and a more open scene. Hard pages use a smaller elephant and a wide, distant view packed with more people and more objects:

```bash
uv run creobook game najdi-slona \
  --theme "Circus" \
  --title "Najdi slona – Cirkus" \
  --mix easy:4,medium:4,hard:4 \
  --format A5 \
  --output output/najdi-slona/cirkus \
  --generate \
  --max-new 16
```

Solution thumbnails then show snadné, střední, or těžší next to the page number.

Automatic checks cover page size, a white background, leftover gray, a clipped elephant, and the solution circle. They cannot tell whether the model drew an extra elephant, or whether the hiding place is a fair puzzle for ages 6–8. Use `review.html` before printing.

## Commands

Plan the scenes. This calls the text model once if `plan.json` is missing, and it never calls the image API:

```bash
uv run creobook game najdi-slona \
  --theme "Circus" \
  --title "Najdi slona – Cirkus" \
  --pages 12 \
  --difficulty medium \
  --format A5 \
  --output output/najdi-slona/cirkus \
  --dry-run
```

Draw the elephant and the scenes, then bind the booklet. Twelve scenes plus the elephant are 13 images, under the default `--max-new` of 16:

```bash
uv run creobook game najdi-slona \
  --config output/najdi-slona/cirkus/config.json \
  --generate
```

Example themes: circus, factory, amusement park, medieval castle, jungle, pirate harbor, space station, airport, train station, farm, toy factory, Christmas village, dinosaur park, magical school, underwater city. Any other theme is planned the same way.

Rebuild the PDFs from saved pictures, with no API calls:

```bash
uv run creobook game najdi-slona \
  --config output/najdi-slona/cirkus/config.json \
  --pdf-only
```

Redraw one scene (1-based index in the plan):

```bash
uv run creobook game najdi-slona \
  --config output/najdi-slona/cirkus/config.json \
  --regenerate-scene 5
```

Move the elephant and rebuild. This does not call the API. Coordinates are fractions of the picture, from the top left:

```bash
uv run creobook game najdi-slona \
  --config output/najdi-slona/cirkus/config.json \
  --move-elephant 5 \
  --position 0.65,0.72
```

`--force-regenerate` redraws the elephant and every scene, and it requires `--generate`. `--no-solutions` leaves the solution pages out. The default booklet includes them. Puzzle pages do not print the scene title and do not mark the elephant.

If a run stops after some images exist, run the same command again. Saved originals are processed locally. Only missing originals are bought, and only with `--generate`.

## Cache

- `plan.json` — scene list
- `config.json` — theme, model, quality, size, difficulty
- `elephant/original.png` — the image returned by the API
- `elephant/asset.png` — the elephant with a transparent exterior
- `elephant/prompt.txt` and `elephant/meta.json`
- `scenes/NN-name/original.png` — the scene before the elephant is added
- `scenes/NN-name/processed.png` — thresholded line art
- `scenes/NN-name/composed.png` — the puzzle
- `scenes/NN-name/solution.png` — the same puzzle with a double circle
- `scenes/NN-name/placement.json` — center, scale, rotation, and bounding box
- `review.html` — contact sheet, coordinates, and warnings

Changing a placement reuses `processed.png` and `asset.png`. Deleting `composed.png` rebuilds it locally when `original.png` is still there.

## Printing

The reading PDF is one page per sheet, in order: cover, puzzles, then solution thumbnails. Blank pages are added only so the sheet count is a multiple of four.

A5 booklets impose onto A4 landscape (`*-tisk.pdf`):

1. Print at 100% scale.
2. Duplex, flip on the short edge.
3. Fold each sheet in half and nest them.

A6 booklets impose onto A5 landscape the same way.
