// Hry pro dva — A5 vector pages. Sizes come from the Python layout check.
#import "../base.typ": data, theme, ink

#let layout = data.layout
#let gray = rgb("#6e6e6e")
#let line-gray = rgb("#8a8a8a")
#let quiet = rgb("#555555")

#set page(
  width: layout.page_width_mm * 1mm,
  height: layout.page_height_mm * 1mm,
  fill: white,
  margin: (
    inside: layout.margin_inside_mm * 1mm,
    outside: layout.margin_outside_mm * 1mm,
    top: layout.margin_top_mm * 1mm,
    bottom: layout.margin_bottom_mm * 1mm,
  ),
  header: none,
  footer: context align(center, text(size: 6.5pt, fill: quiet, counter(page).display())),
  footer-descent: 2.4mm,
)
#set text(font: theme.fonts.family, size: 9pt, fill: ink, lang: "cs", hyphenate: false)
#set par(leading: 0.45em, spacing: 0pt)
#set block(spacing: 0pt)

#let title-line(label, size: 10pt) = {
  text(size: size, weight: "bold", label)
}

#let writing-line(width) = box(
  width: width,
  height: 0.35mm,
  baseline: 0.2mm,
  fill: quiet,
)

#let render-cover(page) = {
  align(center + horizon)[
    #block(width: 36mm, height: 22mm)[
      #for i in range(5) {
        place(dx: i * 9mm, dy: 0mm)[
          #line(angle: 90deg, length: 22mm, stroke: 0.2mm + rgb("#c4c4c4"))
        ]
        place(dx: 0mm, dy: i * 5.5mm)[
          #line(length: 36mm, stroke: 0.2mm + rgb("#c4c4c4"))
        ]
      }
      #place(dx: 12mm, dy: 6mm)[
        #box(width: 8mm, height: 8mm)[
          #place(center + horizon)[#rotate(45deg)[#rect(width: 8mm, height: 0.45mm, fill: ink)]]
          #place(center + horizon)[#rotate(-45deg)[#rect(width: 8mm, height: 0.45mm, fill: ink)]]
        ]
      ]
      #place(dx: 24mm, dy: 6mm)[
        #circle(radius: 3.2mm, stroke: 0.4mm + ink)
      ]
    ]
    #v(7mm)
    #text(size: 26pt, weight: "bold", tracking: 0.08em, page.title)
    #v(4mm)
    #text(size: 11pt, fill: quiet, page.subtitle)
    #v(8mm)
    #grid(
      columns: 4 * (5mm,),
      rows: (5mm,),
      gutter: 1.6mm,
      align: center + horizon,
      circle(radius: 0.7mm, fill: rgb("#444444")),
      circle(radius: 0.7mm, fill: rgb("#444444")),
      circle(radius: 0.7mm, fill: rgb("#444444")),
      circle(radius: 0.7mm, fill: rgb("#444444")),
    )
  ]
  place(bottom + center, dy: -1mm)[
    #text(size: 8pt, fill: quiet, page.footer)
  ]
}

#let rule-block(heading, body) = {
  block(width: 100%, breakable: false, above: 3.2mm)[
    #text(size: 10pt, weight: "bold", heading)
    #v(0.8mm)
    #text(size: 8pt, body)
  ]
}

#let render-rules(page) = {
  title-line(page.title, size: 12pt)
  v(1mm)
  text(size: 8pt, fill: quiet, "Čtyři hry. Stačí tužka a spoluhráč.")
  rule-block(
    "Piškvorky",
    [Hráči střídavě zapisují křížky a kolečka. Vyhrává ten, kdo jako první vytvoří pět svých značek v řadě vodorovně, svisle nebo diagonálně.],
  )
  rule-block(
    "Lodě",
    [Každý hráč má vlastní stránku. Do mřížky Moje lodě tajně rozmístěte flotilu: 1× loď o 4 polích, 2× o 3, 3× o 2 a 4× o 1 poli. Lodě leží vodorovně nebo svisle. Nesmějí se překrývat ani dotýkat, a to ani rohy. Střídáte se po jednom výstřelu. Zásah označte X, vodu tečkou. Střely pište do mřížky Moje střely. Vyhrává hráč, který potopí všechny lodě soupeře.],
  )
  rule-block(
    "Čtverečky",
    [Hráči střídavě spojují dvě sousední tečky vodorovnou nebo svislou čarou. Kdo dokončí čtverec, označí ho svou iniciálou, získá bod a hraje znovu. Vyhrává hráč s největším počtem čtverců.],
  )
  rule-block(
    "Město, jméno, zvíře, věc",
    [Každý hráč vyplňuje vlastní tabulku. Zvolte písmeno a doplňte město, jméno, zvíře a věc, která na něj začíná. 10 bodů za platnou odpověď, kterou soupeř nemá. 5 bodů za stejnou platnou odpověď. 0 bodů za prázdnou nebo neplatnou. Dvě sousední stránky tvoří jednu partii.],
  )
}

#let render-piskvorky(page) = {
  let spec = layout.piskvorky
  let cell = spec.cell_mm * 1mm
  let cols = spec.cols
  let rows = spec.rows
  block(height: spec.title_mm * 1mm)[
    #align(center, title-line(page.title))
  ]
  v(spec.space_mm * 1mm)
  align(center)[
    #box(width: cols * cell, height: rows * cell)[
      #for r in range(rows + 1) {
        place(dx: 0mm, dy: r * cell)[
          #line(length: cols * cell, stroke: 0.22mm + line-gray)
        ]
      }
      #for c in range(cols + 1) {
        place(dx: c * cell, dy: 0mm)[
          #line(angle: 90deg, length: rows * cell, stroke: 0.22mm + line-gray)
        ]
      }
    ]
  ]
  v(spec.space_mm * 1mm)
  block(height: spec.names_mm * 1mm)[
    #align(center + horizon)[
      #text(size: 8pt, fill: quiet)[×]
      #h(1.4mm)
      #writing-line(32mm)
      #h(4mm)
      #text(size: 8pt, fill: quiet)[○]
      #h(1.4mm)
      #writing-line(32mm)
      #h(4mm)
      #writing-line(14mm)
      #h(1.4mm)
      #text(size: 8pt, fill: quiet)[:]
      #h(1.4mm)
      #writing-line(14mm)
    ]
  ]
}

#let ship-board(name, spec) = {
  let n = spec.size
  let cell = spec.cell_mm * 1mm
  let lab = spec.label_mm * 1mm
  let letters = spec.columns
  let cells = ()
  cells.push([])
  for letter in letters {
    cells.push(text(size: 6.5pt, letter))
  }
  for (index, _) in spec.rows.enumerate() {
    cells.push(text(size: 6.5pt, str(index + 1)))
    for _ in range(n) {
      cells.push([])
    }
  }
  block(breakable: false)[
    #text(size: 8pt, weight: "bold", name)
    #v(0.6mm)
    #table(
      columns: (lab,) + (n * (cell,)),
      rows: (lab,) + (n * (cell,)),
      inset: 0pt,
      align: center + horizon,
      stroke: (x, y) => if x == 0 or y == 0 { none } else { 0.28mm + gray },
      ..cells,
    )
  ]
}

#let ship-sample(length, cell) = {
  stack(
    dir: ttb,
    spacing: -0.35mm,
    ..range(length).map(_ => box(
      width: cell,
      height: cell,
      stroke: 0.35mm + ink,
    )),
  )
}

// Count plus one drawn ship, on the outer edge so the grids stay clear.
#let fleet-edge(spec) = {
  let cell = spec.sample_mm * 1mm
  stack(
    dir: ttb,
    spacing: 3.4mm,
    text(size: 6.5pt, weight: "bold", tracking: 0.08em, "TVARY"),
    ..spec.fleet.map(group => grid(
      columns: (5.5mm, cell),
      column-gutter: 1.1mm,
      align: (right + horizon, left + horizon),
      text(size: 7pt, weight: "bold", str(group.count) + "×"),
      ship-sample(group.length, cell),
    )),
  )
}

#let render-lode(page) = {
  let spec = layout.lode
  let outer = if calc.odd(page.number) { right + horizon } else { left + horizon }
  place(outer, fleet-edge(spec))
  block(height: spec.title_mm * 1mm)[
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      title-line(page.title),
      text(size: 8pt, page.heading),
    )
  ]
  v(spec.space_mm * 1mm)
  align(center, ship-board("Moje lodě", spec))
  v(spec.space_mm * 1mm)
  align(center, ship-board("Moje střely", spec))
}

#let render-ctverecky(page) = {
  let spec = layout.ctverecky
  let gap = spec.gap_mm * 1mm
  let radius = spec.dot_radius_mm * 1mm
  let cols = spec.cols
  let rows = spec.rows
  block(height: spec.title_mm * 1mm)[
    #align(center, title-line(page.title))
  ]
  v(spec.space_mm * 1mm)
  align(center)[
    #box(
      width: (cols - 1) * gap + 2 * radius,
      height: (rows - 1) * gap + 2 * radius,
    )[
      #for r in range(rows) {
        for c in range(cols) {
          place(dx: radius + c * gap - radius, dy: radius + r * gap - radius)[
            #circle(radius: radius, fill: rgb("#3a3a3a"))
          ]
        }
      }
    ]
  ]
  v(spec.score_gap_mm * 1mm)
  block(height: spec.score_mm * 1mm)[
    #align(center)[
      #text(size: 8pt)[Hráč 1]
      #h(1.6mm)
      #writing-line(38mm)
      #h(5mm)
      #text(size: 8pt)[Skóre]
      #h(1.6mm)
      #writing-line(16mm)
      #v(2.2mm)
      #text(size: 8pt)[Hráč 2]
      #h(1.6mm)
      #writing-line(38mm)
      #h(5mm)
      #text(size: 8pt)[Skóre]
      #h(1.6mm)
      #writing-line(16mm)
    ]
  ]
}

#let render-mesto(page) = {
  let spec = layout.mesto
  let columns = spec.columns
  let rounds = spec.rows
  block(height: spec.title_mm * 1mm)[
    #align(center, title-line(page.title, size: 9pt))
  ]
  block(height: spec.name_mm * 1mm)[
    #grid(
      columns: (1fr, 1.4fr),
      align: (left + horizon, left + horizon),
      text(size: 8pt, page.heading),
      [
        #text(size: 8pt)[Jméno]
        #h(1.6mm)
        #writing-line(42mm)
      ],
    )
  ]
  v(spec.space_mm * 1mm)
  let cells = ()
  for column in columns {
    cells.push(table.cell(align: center + horizon)[
      #text(size: 6.5pt, weight: "bold", column.title)
    ])
  }
  for _ in range(rounds) {
    for _ in columns {
      cells.push([])
    }
  }
  cells.push(table.cell(colspan: 5, align: right + horizon)[
    #text(size: 7.5pt, weight: "bold", "Součet")
  ])
  cells.push([])
  table(
    columns: columns.map(column => column.width_mm * 1mm),
    rows: (spec.header_mm * 1mm,)
      + (rounds * (spec.row_mm * 1mm,))
      + (spec.total_mm * 1mm,),
    inset: (x: 1.1mm, y: 0pt),
    align: left + horizon,
    stroke: 0.22mm + line-gray,
    ..cells,
  )
}

#let render-page(page) = {
  let kind = page.kind
  if kind == "cover" { render-cover(page) }
  else if kind == "rules" { render-rules(page) }
  else if kind == "piskvorky" { render-piskvorky(page) }
  else if kind == "lode" { render-lode(page) }
  else if kind == "ctverecky" { render-ctverecky(page) }
  else if kind == "mesto" { render-mesto(page) }
}

#for (index, page) in data.pages.enumerate() {
  if index > 0 { pagebreak() }
  render-page(page)
}
