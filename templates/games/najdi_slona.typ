// Najdi slona! The header and the solution circles are drawn here, not by the image model.
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
    #image(page.elephant, height: 28mm, fit: "contain")
    #v(4mm)
    #text(size: 20pt, weight: "bold", page.title)
    #v(3mm)
    #text(size: 11pt, fill: quiet, page.subtitle)
  ]
  place(bottom + center, dy: -1mm)[
    #text(size: 8pt, fill: quiet, page.footer)
  ]
}

#let render-puzzle(page) = {
  place(top + left)[
    #text(size: 13pt, weight: "bold")[Najdi slona!]
  ]
  place(top + right)[
    #image(page.elephant, height: 12mm, fit: "contain")
  ]
  place(top + left, dx: page.image_x_mm * 1mm, dy: page.image_y_mm * 1mm)[
    #image(page.image, width: page.image_w_mm * 1mm, height: page.image_h_mm * 1mm)
  ]
}

#let render-solution(page) = {
  place(top + left)[
    #text(size: 12pt, weight: "bold")[Řešení]
  ]
  for thumb in page.thumbs {
    place(top + left, dx: thumb.caption_x_mm * 1mm, dy: thumb.caption_y_mm * 1mm)[
      #text(size: 8pt, thumb.caption)
    ]
    place(top + left, dx: thumb.image_x_mm * 1mm, dy: thumb.image_y_mm * 1mm)[
      #image(thumb.image, width: thumb.image_w_mm * 1mm, height: thumb.image_h_mm * 1mm)
    ]
    place(
      top + left,
      dx: (thumb.cx_mm - thumb.r_mm) * 1mm,
      dy: (thumb.cy_mm - thumb.r_mm) * 1mm,
    )[
      #circle(radius: thumb.r_mm * 1mm, stroke: 0.6pt + black)
    ]
    let inner = thumb.r_mm - 0.5
    if inner > 0.4 {
      place(
        top + left,
        dx: (thumb.cx_mm - inner) * 1mm,
        dy: (thumb.cy_mm - inner) * 1mm,
      )[
        #circle(radius: inner * 1mm, stroke: 0.45pt + black)
      ]
    }
  }
}

#for (index, page) in data.pages.enumerate() {
  if index > 0 { pagebreak() }
  if page.kind == "cover" { render-cover(page) }
  else if page.kind == "puzzle" { render-puzzle(page) }
  else if page.kind == "solution" { render-solution(page) }
}
