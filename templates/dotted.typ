#import "base.typ": *
#import "components.typ": dot-grid

#let count = int(data.at("page_count", default: 1))
#let spacing = data.at("spacing_mm", default: theme.defaults.dotted_spacing_mm)
#let title = data.at("title", default: none)

#show: creobook-page.with(title: title)

#for page-i in range(count) {
  if page-i > 0 { pagebreak() }
  dot-grid(spacing)
}
