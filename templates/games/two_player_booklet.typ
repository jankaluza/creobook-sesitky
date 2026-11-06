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
  block(width: 100%, breakable: false, above: 6.5mm)[
    #text(size: 11pt, weight: "bold", heading)
    #v(1.6mm)
    #set text(size: 9.2pt)
    #set par(leading: 0.72em, spacing: 1.05em)
    #set enum(tight: false, spacing: 0.95em)
    #body
  ]
}

#let render-rules(page) = {
  title-line(page.title, size: 14pt)
  v(2.5mm)
  text(size: 9.5pt, fill: quiet, style: "italic", "Čtyři hry. Stačí tužka a spoluhráč.")
  rule-block(
    "Piškvorky",
    [Hráči střídavě kreslí křížky a kolečka do prázdných políček. Vyhrává ten, kdo jako první vytvoří pět svých značek vedle sebe – vodorovně, svisle nebo šikmo.],
  )
  rule-block(
    "Lodě",
    [
      Každý hráč si tajně rozmístí svou flotilu: 1× loď o 4 políčkách, 2× o 3 políčkách, 3× o 2 políčkách a 4× o 1 políčku. Lodě mohou být jen vodorovně nebo svisle a nesmějí se dotýkat ani rohy.

      Hráči se střídají ve střelbě na souřadnice soupeře. Zásah označte křížkem, vodu tečkou. Své pokusy zaznamenávejte do mřížky „Moje střely“. Loď je potopená, když jsou zasažena všechna její políčka. Vyhrává ten, kdo jako první potopí celou soupeřovu flotilu.

      #text(weight: "bold")[Jak připravit přepážku]
      #v(1.4mm)
      + *Povytáhněte listy.* Otevřete sešitek na stránkách s Loděmi. Zbývající vnitřní listy povytáhněte z~pruženky tak, aby pod ní zůstalo jen několik centimetrů papíru.
      + *Vytvořte stříšku.* Povytáhnuté listy zvedněte a přehněte tak, aby mezi hráči vznikla přepážka.
      + *Zajistěte přepážku.* Volný konec přehnutých listů zasuňte pod jejich část, kterou stále drží pruženka.

      #v(0.6mm)
      Hotovo! Přepážka drží na místě a hráči si navzájem nevidí do hry.
    ],
  )
  rule-block(
    "Čtverečky",
    [Hráči střídavě spojují dvě sousední tečky vodorovnou nebo svislou čarou. Kdo uzavře čtverec, napíše do něj svou značku, získá bod a hraje znovu. Vyhrává hráč s největším počtem čtverců.],
  )
  rule-block(
    "Město, jméno, zvíře, věc",
    [
      Zvolte písmeno a každý vyplňte svůj řádek: město, jméno, zvíře a věc. Jakmile jeden hráč dopíše, řekne STOP. Oba přestanou psát a porovnají odpovědi.

      Za platnou odpověď, kterou soupeř nemá, získáte 10 bodů. Za stejnou odpověď 5 bodů, za prázdnou nebo neplatnou 0 bodů. Vyhrává hráč s nejvíce body po dohodnutém počtu kol.
    ],
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

// Upright labels for normal booklet reading; rotated labels for sitting at the
// short edge. Tops of secondary labels point outward toward each short edge:
// +90° on the left half, −90° on the right.
#let coord-plain(label, width, height) = {
  box(width: width, height: height)[
    #align(center + horizon)[
      #text(size: 6.5pt, label)
    ]
  ]
}

#let coord-turned(label, turn, width, height) = {
  box(width: width, height: height)[
    #align(center + horizon)[
      #rotate(turn, origin: center)[
        #text(size: 6.5pt, label)
      ]
    ]
  ]
}

// spine-right: true when the fold is on the right of this A5 (left half of A4).
// Upright title + numbers sit toward the top / spine; rotated title + numbers
// sit toward the outer short edge, same reading direction as the turned letters.
#let ship-board(name, spec, turn: 90deg, spine-right: true) = {
  let n = spec.size
  let cell = spec.cell_mm * 1mm
  let lab = spec.label_mm * 1mm
  let cap = spec.caption_mm * 1mm
  let letters = spec.columns
  let grid-cells = ()
  for _ in range(n) {
    for _ in range(n) {
      grid-cells.push([])
    }
  }
  let top = stack(dir: ltr, ..letters.map(letter => coord-plain(letter, cell, lab)))
  // On the right A4 half, secondary labels read from the outer short edge, so
  // reverse their sequence to match that viewing direction (primaries stay A–J / 1–10).
  let bottom-letters = if spine-right { letters } else { letters.rev() }
  let bottom = stack(dir: ltr, ..bottom-letters.map(letter => coord-turned(letter, turn, cell, lab)))
  let upright-nums = stack(
    dir: ttb,
    ..range(n).map(index => coord-plain(str(index + 1), lab, cell)),
  )
  let turned-indexes = if spine-right { range(n) } else { range(n).rev() }
  let turned-nums = stack(
    dir: ttb,
    ..turned-indexes.map(index => coord-turned(str(index + 1), turn, lab, cell)),
  )
  // Lay the caption out on a wide one-line box, then rotate it into the outer
  // strip. The strip itself is only a few millimetres wide and would wrap.
  let turned-title = box(width: cap, height: n * cell)[
    #place(center + horizon)[
      #rotate(turn, origin: center)[
        #box(width: n * cell, height: cap)[
          #align(center + horizon)[
            #text(size: 8pt, weight: "bold")[#name]
          ]
        ]
      ]
    ]
  ]
  let board = table(
    columns: n * (cell,),
    rows: n * (cell,),
    inset: 0pt,
    align: center + horizon,
    stroke: 0.28mm + gray,
    ..grid-cells,
  )
  let upright-title = block(width: 100%)[
    #align(center, text(size: 8pt, weight: "bold", name))
  ]
  block(breakable: false)[
    #upright-title
    #v(0.5mm)
    #if spine-right {
      // Outer edge on the left: rotated title, then turned numbers.
      grid(
        columns: (cap, lab, n * cell, lab),
        rows: (lab, n * cell, lab),
        column-gutter: 0pt,
        row-gutter: 0pt,
        [], [], top, [],
        turned-title, turned-nums, board, upright-nums,
        [], [], bottom, [],
      )
    } else {
      // Outer edge on the right: turned numbers, then rotated title.
      grid(
        columns: (lab, n * cell, lab, cap),
        rows: (lab, n * cell, lab),
        column-gutter: 0pt,
        row-gutter: 0pt,
        [], top, [], [],
        upright-nums, board, turned-nums, turned-title,
        [], bottom, [], [],
      )
    }
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
  // Derive rotation from the physical A4 half (sheet_hand), not a shared angle.
  // Outward toward the short-edge player: left +90°, right −90°.
  let hand = page.at("sheet_hand")
  let turn = if hand == "right" { -90deg } else { 90deg }
  let spine-right = hand == "left"
  let outer = if spine-right { left + horizon } else { right + horizon }
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
  align(center, ship-board("Moje lodě", spec, turn: turn, spine-right: spine-right))
  v(spec.space_mm * 1mm)
  align(center, ship-board("Moje střely", spec, turn: turn, spine-right: spine-right))
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
