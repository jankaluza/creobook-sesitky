// CreoBook base page setup — all dimensions from theme JSON (millimetres).
// Templates must not hard-code colours, fonts, margins, or line widths.

#let data = json("data.json")
#let theme = data.theme

#let mm(v) = v * 1mm

#let page-width = mm(theme.page.width_mm)
#let page-height = mm(theme.page.height_mm)

#let ink = rgb(theme.colors.ink)
#let muted = rgb(theme.colors.muted)
#let light = rgb(theme.colors.light)
#let rule-color = rgb(theme.colors.rule)
#let accent = rgb(theme.colors.accent)
#let weekend-color = rgb(theme.colors.weekend)
#let holiday-color = rgb(theme.colors.holiday)
#let adjacent-color = rgb(theme.colors.adjacent)
#let header-color = rgb(theme.colors.header)

#let page-header(title: none, subtitle: none) = context {
  let label = if title != none { title } else { theme.brand.name }
  block(width: 100%)[
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(size: 7.5pt, fill: header-color, tracking: 0.08em, upper(label)),
      if subtitle != none {
        text(size: 7pt, fill: light, subtitle)
      } else {
        text(size: 7pt, fill: light, theme.brand.tagline)
      },
    )
    #v(1.5mm)
    #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + rule-color)
  ]
}

#let page-footer(page-label: none) = context {
  block(width: 100%)[
    #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + rule-color)
    #v(1.2mm)
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(size: 6.5pt, fill: light, theme.brand.name),
      text(
        size: 6.5pt,
        fill: light,
        if page-label != none { page-label } else { counter(page).display() },
      ),
    )
  ]
}

#let creobook-page(
  body,
  title: none,
  subtitle: none,
  show-header: true,
  show-footer: true,
) = {
  set page(
    width: page-width,
    height: page-height,
    fill: rgb(theme.colors.background),
    margin: (
      inside: mm(theme.margins.inner_mm),
      outside: mm(theme.margins.outer_mm),
      top: mm(theme.margins.top_mm),
      bottom: mm(theme.margins.bottom_mm),
    ),
    header: if show-header {
      page-header(title: title, subtitle: subtitle)
    } else { none },
    footer: if show-footer { page-footer() } else { none },
    header-ascent: 3mm,
    footer-descent: 2mm,
  )
  set text(
    font: theme.fonts.family,
    size: 9pt,
    fill: ink,
    lang: "cs",
  )
  set par(leading: 0.65em)
  body
}
