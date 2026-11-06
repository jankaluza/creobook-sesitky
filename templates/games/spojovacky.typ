// Connect-the-dots booklet. Dots and numbers are placed from saved geometry.
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

#let render-dots(page, connect) = {
  place(top + center, dy: 0.5mm)[
    #text(size: 9pt, weight: "bold", page.heading)
  ]
  place(bottom + center, dy: 0mm)[
    #text(size: 7.5pt, fill: quiet, page.caption)
  ]
  let pts = page.dots
  if connect {
    for index in range(pts.len()) {
      let a = pts.at(index)
      let b = pts.at(calc.rem(index + 1, pts.len()))
      place(
        top + left,
        dx: a.x * 1mm,
        dy: a.y * 1mm,
        line(
          end: ((b.x - a.x) * 1mm, (b.y - a.y) * 1mm),
          stroke: 0.35mm + black,
        ),
      )
    }
  }
  for dot in pts {
    if dot.n == 0 {
      place(
        top + left,
        dx: (dot.x - 1.7) * 1mm,
        dy: (dot.y - 1.7) * 1mm,
      )[
        #circle(radius: 1.7mm, stroke: 0.25mm + black, fill: none)
      ]
    }
    place(
      top + left,
      dx: (dot.x - 0.6) * 1mm,
      dy: (dot.y - 0.6) * 1mm,
    )[
      #circle(radius: 0.6mm, fill: black, stroke: none)
    ]
    place(
      top + left,
      dx: (dot.lx - dot.lw / 2) * 1mm,
      dy: (dot.ly - dot.lh / 2) * 1mm,
    )[
      #box(width: dot.lw * 1mm, height: dot.lh * 1mm)[
        #align(center + horizon)[
          #text(size: page.font_pt * 1pt)[#str(dot.n)]
        ]
      ]
    ]
  }
}

#for (index, page) in data.pages.enumerate() {
  if index > 0 { pagebreak() }
  if page.kind == "cover" { render-cover(page) }
  else if page.kind == "puzzle" { render-dots(page, false) }
  else if page.kind == "answer" { render-dots(page, true) }
}
