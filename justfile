# Pin Typst compiler via the `typst` Python package (see pyproject.toml).
TYPST_VERSION := "0.13.2"

# Default calendar year for sample builds
YEAR := "2026"

root := justfile_directory()

# Install dependencies and the package in editable mode
install:
    uv sync --all-extras

# Run the full test suite
test:
    uv run pytest -q

# Render a ruled A5 page
ruled spacing="7":
    uv run creobook page ruled --spacing {{spacing}}

# Render a dotted A5 page
dotted spacing="5":
    uv run creobook page dotted --spacing {{spacing}}

# Render the Czech monthly calendar for YEAR
calendar year=YEAR:
    uv run creobook calendar --year {{year}}

# Impose an A5 PDF as an A4 landscape booklet
booklet input:
    uv run creobook booklet {{input}}

# Build all page types + calendar (+ booklets)
build-all year=YEAR:
    uv run creobook build-all --year {{year}}

# Low-res PNG previews (requires Poppler pdftoppm)
preview pdf:
    uv run creobook preview {{pdf}}

# Generate sample PDFs for visual inspection
samples year=YEAR: install
    uv run creobook page ruled --spacing 7 -o output/pages/ruled.pdf
    uv run creobook page ruled --spacing 7 --margin-line -o output/pages/ruled-margin.pdf
    uv run creobook page dotted --spacing 5 -o output/pages/dotted.pdf
    uv run creobook page grid --spacing 5 -o output/pages/grid.pdf
    uv run creobook page blank -o output/pages/blank.pdf
    uv run creobook page checklist -o output/pages/checklist.pdf
    uv run creobook page cornell -o output/pages/cornell.pdf
    uv run creobook calendar --year {{year}} -o output/pages/calendar-{{year}}.pdf
    uv run creobook booklet output/pages/calendar-{{year}}.pdf -o output/booklet/calendar-{{year}}-booklet.pdf
    uv run creobook booklet output/pages/ruled.pdf -o output/booklet/ruled-booklet.pdf
    -uv run creobook preview output/pages/calendar-{{year}}.pdf --dpi 72

# Show pinned versions
versions:
    uv run creobook version
    @echo "just TYPST_VERSION={{TYPST_VERSION}}"

# Clean generated outputs
clean:
    rm -rf output/pages/*.pdf output/booklet/*.pdf output/preview
