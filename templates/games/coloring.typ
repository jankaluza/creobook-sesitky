// Coloring booklet. Illustrations are already print-ready PNGs.
#import "../base.typ": data, theme, ink

#let quiet = rgb("#555555")

#set page(
  width: data.page_width_mm * 1mm,
  height: data.page_height_mm * 1mm,
  fill: white,
  margin: (
    inside: data.margin_inside_mm * 1mm,
    outside: data.margin_outside_mm * 1mm,
    top: data.margin_top_mm * 1mm,
    bottom: data.margin_bottom_mm * 1mm,
  ),
  header: none,
  footer: context align(center, text(size: 6.5pt, fill: quiet, counter(page).display())),
  footer-descent: 2.2mm,
)
#set text(font: theme.fonts.family, size: 9pt, fill: ink, lang: "cs", hyphenate: false)

#let render-cover(page) = {
  align(center + horizon)[
    #text(size: 22pt, weight: "bold", page.title)
    #v(4mm)
    #text(size: 11pt, fill: quiet, page.subtitle)
  ]
  place(bottom + center, dy: -1mm)[
    #text(size: 8pt, fill: quiet, page.footer)
  ]
}

#let render-illustration(page) = {
  align(center + horizon)[
    #image(page.image, width: 100%, height: 100%, fit: "contain")
  ]
}

#for (index, page) in data.pages.enumerate() {
  if index > 0 { pagebreak() }
  if page.kind == "cover" { render-cover(page) }
  else if page.kind == "illustration" { render-illustration(page) }
}
