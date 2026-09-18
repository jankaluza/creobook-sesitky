#import "base.typ": *
#import "components.typ": checklist-rows

#let count = int(data.at("page_count", default: 1))
#let rows = int(data.at("rows", default: theme.defaults.checklist_rows))
#let title = data.at("title", default: none)
#let subtitle = data.at("subtitle", default: none)

#show: creobook-page.with(title: title, subtitle: subtitle)

#for page-i in range(count) {
  if page-i > 0 { pagebreak() }
  checklist-rows(rows)
}
