#import "base.typ": *

#let count = int(data.at("page_count", default: 1))
#let title = data.at("title", default: none)
#let subtitle = data.at("subtitle", default: none)

#show: creobook-page.with(title: title, subtitle: subtitle)

#for page-i in range(count) {
  if page-i > 0 { pagebreak() }
  // Empty writing surface — header/footer come from page setup
  v(1fr)
}
