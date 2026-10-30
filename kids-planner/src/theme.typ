// CreoBook kids planner — colors, type, spacing, and sizes.
// Edit this file to restyle the booklet without changing page content.

#let page-w = 148mm
#let page-h = 210mm

// Binding-aware margins (Typst mirrors inside/outside per page side)
#let margin-inside = 14mm
#let margin-outside = 10mm
#let margin-top = 10mm
#let margin-bottom = 12mm

#let color-ink = rgb("#1a4a5c")        // dark petrol — headings
#let color-accent = rgb("#d4783a")     // muted orange — highlights
#let color-panel = rgb("#e5f3f5")      // pale turquoise — soft panels
#let color-line = rgb("#b8b8b8")       // light grey — writing lines
#let color-border = rgb("#9aa8ad")     // soft border
#let color-muted = rgb("#5a6e76")      // secondary text
#let color-white = rgb("#ffffff")
#let color-soft = rgb("#f7fafb")

// Readable open-source stack with Czech diacritics
#let font-family = ("Montserrat", "Noto Sans", "DejaVu Sans", "Liberation Sans")

#let size-title = 20pt
#let size-heading = 13pt
#let size-body = 10.5pt
#let size-small = 9pt
#let size-tiny = 8pt

#let stroke-thin = 0.4pt + color-line
#let stroke-mid = 0.55pt + color-border
#let stroke-accent = 0.7pt + color-accent
#let stroke-ink = 0.6pt + color-ink

#let checkbox-size = 4.2mm
#let circle-check-size = 3.8mm
#let field-gap = 2.2mm
#let panel-radius = 3mm
#let line-spacing = 7mm

#let content-w = page-w - margin-inside - margin-outside
#let content-h = page-h - margin-top - margin-bottom
