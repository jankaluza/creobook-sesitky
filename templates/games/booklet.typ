#import "../base.typ": *
#import "pages.typ": render-page

#let pages = data.pages

#show: creobook-page.with(show-header: false, show-footer: true)

#for (i, page) in pages.enumerate() {
  if i > 0 { pagebreak() }
  render-page(page)
}
