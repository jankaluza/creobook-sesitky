# CreoBook templates — regenerate A5 pages, booklets, and web previews.
#
# Usage:
#   make              # pages + booklets + dated game packs
#   make all          # same
#   make YEAR=2027    # calendar year override
#   make DATE=20260101  # pin game edition date/seed
#   make previews     # website PNG previews (needs Poppler)
#   make clean

YEAR  ?= 2026
QUARTER ?= 1
DPI   ?= 144
# Game edition date (YYYYMMDD) — used as filename infix and default seed
DATE  ?= $(shell date +%Y%m%d)
SEED  ?= $(DATE)
# Repeating notebook inserts: 5 A4 sheets → 20 A5 pages after folding
PAGES ?= 20

UV       := uv run
CREOBOOK := $(UV) creobook

PAGES_DIR   := output/pages
BOOKLET_DIR := output/booklet
PREVIEW_DIR := output/preview

# Czech ASCII slugs: creobook-$name-a5.pdf (pages and booklets share the basename;
# booklets live in BOOKLET_DIR — suffix is A5 because that is the folded page size)
PAGE_PDFS := \
	$(PAGES_DIR)/creobook-prazdny-a5.pdf \
	$(PAGES_DIR)/creobook-linky-a5.pdf \
	$(PAGES_DIR)/creobook-linky-odsazene-a5.pdf \
	$(PAGES_DIR)/creobook-tecky-a5.pdf \
	$(PAGES_DIR)/creobook-mrizka-a5.pdf \
	$(PAGES_DIR)/creobook-seznam-a5.pdf \
	$(PAGES_DIR)/creobook-cornell-a5.pdf \
	$(PAGES_DIR)/creobook-kalendar-a5.pdf

BOOKLET_PDFS := $(patsubst $(PAGES_DIR)/%,$(BOOKLET_DIR)/%,$(PAGE_PDFS))

# One website PNG per booklet (sampled from the sequential A5 pages PDF)
WEB_PREVIEWS := $(patsubst $(PAGES_DIR)/%.pdf,$(PREVIEW_DIR)/%.png,$(PAGE_PDFS))

# Dated game packs: creobook-<DATE>-<pack>.pdf in output/booklet/
GAME_HLAVOLAMY := $(BOOKLET_DIR)/creobook-$(DATE)-hlavolamy.pdf
GAME_PRO_DVA   := $(BOOKLET_DIR)/creobook-$(DATE)-hry-pro-dva.pdf
GAME_SUDOKU    := $(BOOKLET_DIR)/creobook-$(DATE)-sudoku.pdf
GAME_BOOKLETS  := $(GAME_HLAVOLAMY) $(GAME_PRO_DVA) $(GAME_SUDOKU)

GAME_PREVIEWS := \
	$(PREVIEW_DIR)/creobook-$(DATE)-hlavolamy.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-hry-pro-dva.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-sudoku.png

.PHONY: all pages booklets games planner previews install test clean versions help

all: pages booklets games
	@echo "Done: pages, notebook booklets, and game booklets (YEAR=$(YEAR) DATE=$(DATE) SEED=$(SEED))"

help:
	@echo "Targets:"
	@echo "  make / make all   A5 pages + notebook booklets + dated game packs"
	@echo "  make pages        A5 notebook PDFs only"
	@echo "  make booklets     Imposed notebook booklet PDFs (A5 after folding)"
	@echo "  make games        Game packs → output/booklet/creobook-\$$DATE-<pack>.pdf"
	@echo "  make planner      Quarterly planner (YEAR + QUARTER)"
	@echo "  make previews     One website PNG per booklet"
	@echo "  make install|test|clean|versions"
	@echo "Variables: YEAR=$(YEAR) QUARTER=$(QUARTER) DATE=$(DATE) SEED=$(SEED) DPI=$(DPI) PAGES=$(PAGES)"

install:
	uv sync --all-extras

pages: $(PAGE_PDFS)

booklets: $(BOOKLET_PDFS)

# Always regenerate today's edition (seed = DATE unless overridden)
games: | $(BOOKLET_DIR)
	$(CREOBOOK) games generate --pack hlavolamy --output $(GAME_HLAVOLAMY) --sheets 4 --seed $(SEED) --answers
	$(CREOBOOK) games generate --pack pro-dva --output $(GAME_PRO_DVA) --sheets 4 --seed $(SEED) --no-answers
	$(CREOBOOK) games generate --pack sudoku --output $(GAME_SUDOKU) --sheets 6 --seed $(SEED) --answers
	@echo "Game booklets (DATE=$(DATE) SEED=$(SEED)): $(GAME_BOOKLETS)"

# 7 duplex A4 sheets → 14 A4 sides → 28 A5 pages
planner: | $(PAGES_DIR) $(BOOKLET_DIR)
	$(CREOBOOK) planner quarter --year $(YEAR) --quarter $(QUARTER)

# --- A5 pages -----------------------------------------------------------------

$(PAGES_DIR)/creobook-prazdny-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) page blank -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-linky-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) page ruled --spacing 7 -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-linky-odsazene-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) page ruled --spacing 7 --margin-line -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-tecky-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) page dotted --spacing 5 -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-mrizka-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) page grid --spacing 5 -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-seznam-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) page checklist -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-cornell-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) page cornell -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-kalendar-a5.pdf: | $(PAGES_DIR)
	$(CREOBOOK) calendar --year $(YEAR) -o $@

# --- Booklets (same -a5 basename; folded pages are A5) ------------------------

$(BOOKLET_DIR)/creobook-%-a5.pdf: $(PAGES_DIR)/creobook-%-a5.pdf | $(BOOKLET_DIR)
	$(CREOBOOK) booklet $< -o $@

# --- Website previews (one PNG per booklet; needs pdftoppm) -------------------

previews: $(WEB_PREVIEWS) games
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-hlavolamy-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-hlavolamy.png --dpi $(DPI)
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-hry-pro-dva-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-hry-pro-dva.png --dpi $(DPI)
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-sudoku-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-sudoku.png --dpi $(DPI)
	@echo "Wrote website previews under $(PREVIEW_DIR)/"

$(PREVIEW_DIR)/creobook-%-a5.png: $(PAGES_DIR)/creobook-%-a5.pdf | $(PREVIEW_DIR)
	$(CREOBOOK) web-preview $< -o $@ --dpi $(DPI)

# --- Utilities ----------------------------------------------------------------

$(PAGES_DIR) $(BOOKLET_DIR) $(PREVIEW_DIR):
	mkdir -p $@

test:
	$(UV) pytest -q

versions:
	$(CREOBOOK) version

clean:
	rm -f $(PAGES_DIR)/*.pdf $(BOOKLET_DIR)/*.pdf
	rm -rf $(PREVIEW_DIR)
