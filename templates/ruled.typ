#import "base.typ": *
#import "components.typ": ruled-lines

#let count = int(data.at("page_count", default: 1))
#let spacing = data.at("spacing_mm", default: theme.defaults.ruled_spacing_mm)
#let margin-line = data.at("margin_line", default: false)
#let title = data.at("title", default: none)

#show: creobook-page.with(title: title)

#for page-i in range(count) {
  if page-i > 0 { pagebreak() }
  ruled-lines(spacing, margin-line: margin-line)
}
