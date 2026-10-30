# CreoBook templates — regenerate A5 pages, booklets, and web previews.
#
# Usage:
#   make              # pages + booklets + dated game packs + next 4 quarterly planners
#   make all          # same
#   make YEAR=2027    # calendar year override
#   make DATE=20260101  # pin game edition date/seed + planner anchor
#   make previews     # website PNG previews (needs Poppler)
#   make clean

YEAR  ?= 2026
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
GAME_HLAVOLAMY   := $(BOOKLET_DIR)/creobook-$(DATE)-hlavolamy.pdf
GAME_PRO_DVA     := $(BOOKLET_DIR)/creobook-$(DATE)-hry-pro-dva.pdf
GAME_SUDOKU      := $(BOOKLET_DIR)/creobook-$(DATE)-sudoku.pdf
GAME_OSMISMERKY  := $(BOOKLET_DIR)/creobook-$(DATE)-osmismerky.pdf
GAME_BLUDISTE    := $(BOOKLET_DIR)/creobook-$(DATE)-bludiste.pdf
GAME_KRIZOVKY    := $(BOOKLET_DIR)/creobook-$(DATE)-krizovky.pdf
GAME_MATEMATIKA  := $(BOOKLET_DIR)/creobook-$(DATE)-matematika-1trida.pdf
GAME_MATEMATIKA2 := $(BOOKLET_DIR)/creobook-$(DATE)-matematika-2trida.pdf
GAME_CISLA       := $(BOOKLET_DIR)/creobook-$(DATE)-cisla-do-100.pdf
GAME_NASOBILKA   := $(BOOKLET_DIR)/creobook-$(DATE)-nasobilka.pdf
GAME_KOLEM       := $(BOOKLET_DIR)/creobook-$(DATE)-matematika-kolem-nas.pdf
GAME_BOOKLETS    := $(GAME_HLAVOLAMY) $(GAME_PRO_DVA) $(GAME_SUDOKU) $(GAME_OSMISMERKY) $(GAME_BLUDISTE) $(GAME_KRIZOVKY) $(GAME_MATEMATIKA) $(GAME_MATEMATIKA2) $(GAME_CISLA) $(GAME_NASOBILKA) $(GAME_KOLEM)

GAME_PREVIEWS := \
	$(PREVIEW_DIR)/creobook-$(DATE)-hlavolamy.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-hry-pro-dva.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-sudoku.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-osmismerky.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-bludiste.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-krizovky.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-matematika-1trida.png \
	$(PREVIEW_DIR)/creobook-$(DATE)-matematika-2trida.png

.PHONY: all pages booklets games planner previews install test clean versions help

all: pages booklets games planner
	@echo "Done: pages, notebook booklets, game booklets, and planners (YEAR=$(YEAR) DATE=$(DATE) SEED=$(SEED))"

help:
	@echo "Targets:"
	@echo "  make / make all   A5 pages + notebook booklets + dated game packs + next 4 planners"
	@echo "  make pages        A5 notebook PDFs only"
	@echo "  make booklets     Imposed notebook booklet PDFs (A5 after folding)"
	@echo "  make games        Game packs → output/booklet/creobook-\$$DATE-<pack>.pdf"
	@echo "  make planner      Next 4 quarters from DATE (rolls across year boundary)"
	@echo "  make previews     One website PNG per booklet"
	@echo "  make install|test|clean|versions"
	@echo "Variables: YEAR=$(YEAR) DATE=$(DATE) SEED=$(SEED) DPI=$(DPI) PAGES=$(PAGES)"

install:
	uv sync --all-extras

pages: $(PAGE_PDFS)

booklets: $(BOOKLET_PDFS)

# Always regenerate today's edition (seed = DATE unless overridden)
games: | $(BOOKLET_DIR)
	$(CREOBOOK) games generate --pack hlavolamy --output $(GAME_HLAVOLAMY) --sheets 4 --seed $(SEED) --answers
	$(CREOBOOK) games generate --pack pro-dva --output $(GAME_PRO_DVA) --sheets 4 --seed $(SEED) --no-answers
	$(CREOBOOK) games generate --pack sudoku --output $(GAME_SUDOKU) --sheets 6 --seed $(SEED) --answers
	$(CREOBOOK) game word-search --language cs --easy 6 --medium 6 --hard 6 --seed $(SEED) --output $(GAME_OSMISMERKY)
	$(CREOBOOK) game maze --easy 6 --medium 6 --hard 6 --seed $(SEED) --output $(GAME_BLUDISTE)
	$(CREOBOOK) game crossword --obtiznost mixed --seed $(SEED) --output $(GAME_KRIZOVKY)
	$(CREOBOOK) game math-grade1 --seed $(SEED) --output $(GAME_MATEMATIKA)
	$(CREOBOOK) game math-grade2 --seed $(SEED) --output $(GAME_MATEMATIKA2)
	$(CREOBOOK) game math-set cisla --seed $(SEED) --output $(GAME_CISLA)
	$(CREOBOOK) game math-set nasobilka --seed $(SEED) --output $(GAME_NASOBILKA)
	$(CREOBOOK) game math-set kolem --seed $(SEED) --output $(GAME_KOLEM)
	@echo "Game booklets (DATE=$(DATE) SEED=$(SEED)): $(GAME_BOOKLETS)"

# 7 duplex A4 sheets → 14 A4 sides → 28 A5 pages — next 4 quarters from DATE
planner: | $(PAGES_DIR) $(BOOKLET_DIR)
	$(CREOBOOK) planner upcoming --count 4 --from $(DATE)
	@echo "Wrote next 4 quarterly planners (from DATE=$(DATE))"

# --- A5 pages -----------------------------------------------------------------

# Rebuild when theme or page templates change (Make has no other prerequisites)
PAGE_DEPS := config/theme.toml templates/base.typ templates/components.typ \
	templates/blank.typ templates/ruled.typ templates/dotted.typ templates/grid.typ \
	templates/checklist.typ templates/cornell.typ templates/calendar.typ

$(PAGES_DIR)/creobook-prazdny-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
	$(CREOBOOK) page blank -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-linky-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
	$(CREOBOOK) page ruled --spacing 8 -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-linky-odsazene-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
	$(CREOBOOK) page ruled --spacing 8 --margin-line -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-tecky-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
	$(CREOBOOK) page dotted --spacing 5 -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-mrizka-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
	$(CREOBOOK) page grid --spacing 5 -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-seznam-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
	$(CREOBOOK) page checklist -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-cornell-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
	$(CREOBOOK) page cornell -n $(PAGES) -o $@

$(PAGES_DIR)/creobook-kalendar-a5.pdf: $(PAGE_DEPS) | $(PAGES_DIR)
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
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-osmismerky-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-osmismerky.png --dpi $(DPI)
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-bludiste-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-bludiste.png --dpi $(DPI)
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-krizovky-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-krizovky.png --dpi $(DPI)
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-matematika-1trida-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-matematika-1trida.png --dpi $(DPI)
	$(CREOBOOK) web-preview $(BOOKLET_DIR)/creobook-$(DATE)-matematika-2trida-pages.pdf \
		-o $(PREVIEW_DIR)/creobook-$(DATE)-matematika-2trida.png --dpi $(DPI)
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
