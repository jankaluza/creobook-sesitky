#import "theme.typ": *
#import "content.typ": all-pages
#import "components.typ": page-number

#set document(
  title: "CreoBook — Můj plán (dětský plánovač)",
  author: "CreoBook",
)

#set page(
  width: page-w,
  height: page-h,
  margin: (
    inside: margin-inside,
    outside: margin-outside,
    top: margin-top,
    bottom: margin-bottom,
  ),
  fill: color-white,
)

#set text(
  font: font-family,
  size: size-body,
  fill: color-ink,
  lang: "cs",
)

#set par(leading: 0.5em)

#for (i, page-fn) in all-pages.enumerate() {
  if i > 0 {
    pagebreak()
  }
  // Keep each logical page on a single A5 sheet
  block(width: 100%, breakable: false, {
    page-fn()
  })
  page-number(i + 1, total: all-pages.len())
}
