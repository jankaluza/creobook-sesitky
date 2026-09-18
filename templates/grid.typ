#import "base.typ": *
#import "components.typ": square-grid

#let count = int(data.at("page_count", default: 1))
#let spacing = data.at("spacing_mm", default: theme.defaults.grid_spacing_mm)
#let title = data.at("title", default: none)
#let subtitle = data.at("subtitle", default: none)

#show: creobook-page.with(title: title, subtitle: subtitle)

#for page-i in range(count) {
  if page-i > 0 { pagebreak() }
  square-grid(spacing)
}
