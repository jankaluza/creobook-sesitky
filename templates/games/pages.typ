#import "../base.typ": *
#import "common.typ": game-header, difficulty-label
#import "math_grade1.typ": render-math-grade1, render-math-grade1-answers
#import "math_grade2.typ": render-math-grade2, render-math-grade2-answers
#import "math_sets.typ": render-math-set, render-math-set-answers

#let render-cover(page) = {
  align(center + horizon)[
    #text(size: 28pt, weight: "bold", fill: ink, page.title)
    #v(6mm)
    #text(size: 12pt, fill: muted, page.instructions)
    #v(12mm)
    #line(length: 40%, stroke: mm(theme.lines.rule_width_mm) + ink)
    #v(8mm)
    #text(size: 9pt, fill: muted, "A5 · tisk jako A4 booklet · duplex · krátká hrana")
  ]
}

#let render-back(page) = {
  align(center + horizon)[
    #text(size: 18pt, weight: "bold", fill: ink, "CreoBook")
    #v(5mm)
    #block(width: 85%)[
      #set text(size: 9pt, fill: muted)
      #set align(center)
      #page.data.at("pack_description", default: page.instructions)
    ]
    #v(10mm)
    #text(size: 8pt, fill: muted, "creobook · tužka a papír")
  ]
}

#let render-instructions(page) = {
  game-header(page.title, instructions: page.instructions)
  text(size: 9pt, weight: "bold", "Obtížnost")
  v(2mm)
  for (label, desc) in (
    ("snadné", "kratší mřížky, více nápověd"),
    ("střední", "více směru / méně nápověd"),
    ("těžké", "větší mřížky, méně nápověd"),
  ) {
    block(below: 2mm)[
      #text(weight: "bold", label + ": ")
      #text(fill: muted, desc)
    ]
  }
  v(4mm)
  text(size: 9pt)[
    Piš tužkou. Řešení najdeš na konci sešitu. U her pro dva si pravidla
    přečtěte společně před první partií.
  ]
}

#let render-rules(page) = {
  game-header(page.title, instructions: page.instructions)
  let items = (
    ("Piškvorky", "5 v řadě na 15×15 mřížce."),
    ("Lodě", "Umístěte flotilu, střílejte na soupeřovu mřížku."),
    ("Čtverečky", "Uzavírejte čtverce spojením bodů."),
    ("Papírový fotbal", "Posouvejte míček po čarách do brány."),
    ("Šibenice", "Hádejte písmena českého slova."),
    ("Kategorie", "Doplňte slova na zvolené písmeno."),
  )
  for (t, d) in items {
    block(below: 2.5mm)[
      #text(weight: "bold", t)
      #text(fill: muted, " — " + d)
    ]
  }
}

#let sudoku-grid(grid, n, box, cell) = {
  table(
    columns: n * (cell,),
    rows: n * (cell,),
    stroke: (x, y) => {
      let thick = mm(theme.lines.margin_line_width_mm)
      let thin = mm(theme.lines.rule_width_mm)
      (
        top: if y == 0 or calc.rem(y, box.at(0)) == 0 { thick + ink } else { thin + ink },
        left: if x == 0 or calc.rem(x, box.at(1)) == 0 { thick + ink } else { thin + ink },
        right: if x == n - 1 { thick + ink } else { 0pt },
        bottom: if y == n - 1 { thick + ink } else { 0pt },
      )
    },
    align: center + horizon,
    inset: 0pt,
    ..grid.flatten().map(v => {
      if v == 0 { [] } else { text(size: cell * 0.42, weight: "bold", str(v)) }
    }),
  )
}

#let render-sudoku(page, show-answer: false) = {
  game-header(
    page.title,
    difficulty: difficulty-label(page.difficulty),
    instructions: if show-answer { "Řešení" } else { page.instructions },
  )
  let n = page.data.size
  let box = page.data.box
  let puzzles = page.data.at(
    "puzzles",
    default: ((id: 1, grid: page.data.grid),),
  )
  let answers = page.answer.at(
    "puzzles",
    default: ((id: 1, grid: page.answer.grid),),
  )
  let count = puzzles.len()
  let cols = page.data.at("cols", default: if count > 1 and n < 9 { 2 } else { 1 })

  // Cell size tuned for handwriting; fewer puzzles per page than dense packing
  let cell = if count == 1 {
    if n == 9 { 5.5mm } else if n == 6 { 7mm } else { 8mm }
  } else if n == 9 {
    // 2× stacked 9×9 — large enough to write in
    8.0mm
  } else if n == 6 {
    // 2×2 grid of 6×6
    8.5mm
  } else {
    // 2×3 grid of 4×4
    10.0mm
  }

  let cards = range(count).map(i => {
    let grid = if show-answer { answers.at(i).grid } else { puzzles.at(i).grid }
    block(width: 100%, breakable: false)[
      #if count > 1 {
        text(size: 7pt, weight: "bold", fill: muted)[š.#str(i + 1)]
        v(0.6mm)
      }
      #align(center)[#sudoku-grid(grid, n, box, cell)]
    ]
  })

  if cols == 1 {
    for (i, card) in cards.enumerate() {
      card
      if i + 1 < cards.len() { v(3mm) }
    }
  } else {
    grid(
      columns: (1fr, 1fr),
      column-gutter: 4mm,
      row-gutter: 3mm,
      ..cards,
    )
  }
}

#let render-maze(page, show-answer: false) = {
  // Keep one maze per A5 page — do not let markers/labels spill onto a blank page.
  block(width: 100%, breakable: false)[
    #let num = page.data.at("maze_number", default: none)
    #let marker = page.data.at("difficulty_marker", default: none)
    #let label-cs = page.data.at("difficulty_label_cs", default: difficulty-label(page.difficulty))
    #let header-right = if marker != none { label-cs + " · " + marker } else { difficulty-label(page.difficulty) }
    #let title = if num != none { "Bludiště " + str(num) } else { page.title }
    #game-header(
      title,
      difficulty: header-right,
      instructions: if show-answer { "Řešení — vyznačená cesta" } else { page.instructions },
    )
    #let rows = page.data.rows
    #let cols = page.data.cols
    #let wall-pt = page.data.at("wall_pt", default: 0.7) * 1pt
    // Content height ≈ 176mm; header+checkbox ≈ 28mm → grid ≤ ~145mm.
    // Keep START/CÍL labels inside the grid box so they never force a page break.
    #let max-w = 124mm
    #let max-h = 145mm
    #let cell = calc.min(max-w / cols, max-h / rows)
    #let path = if show-answer { page.answer.path } else { () }
    #let start = page.data.start
    #let goal = page.data.goal
    #let label-size = calc.min(5.5pt, cell * 0.28)
    #align(center)[
      #box(width: cols * cell, height: rows * cell, clip: true)[
        // Solution path under walls
        #if path.len() > 1 {
          for i in range(path.len() - 1) {
            let a = path.at(i)
            let b = path.at(i + 1)
            let x0 = a.at(1) * cell + cell / 2
            let y0 = a.at(0) * cell + cell / 2
            let x1 = b.at(1) * cell + cell / 2
            let y1 = b.at(0) * cell + cell / 2
            place(dx: calc.min(x0, x1), dy: calc.min(y0, y1))[
              #line(
                start: (0pt, 0pt),
                end: (calc.abs(x1 - x0), calc.abs(y1 - y0)),
                stroke: (paint: luma(55%), thickness: calc.max(1.1pt, cell * 0.18), cap: "round"),
              )
            ]
          }
        }
        #for e in page.data.edges {
          let x0 = e.x0 * cell
          let y0 = e.y0 * cell
          if e.y0 == e.y1 {
            place(dx: x0, dy: y0)[#line(length: cell, stroke: wall-pt + ink)]
          } else {
            place(dx: x0, dy: y0)[#line(angle: 90deg, length: cell, stroke: wall-pt + ink)]
          }
        }
        // START marker (outlined circle) + label inside cell
        #place(
          dx: start.at(1) * cell + cell * 0.22,
          dy: start.at(0) * cell + cell * 0.12,
        )[
          #circle(radius: cell * 0.18, stroke: wall-pt + ink, fill: none)
        ]
        #place(
          dx: start.at(1) * cell + cell * 0.05,
          dy: start.at(0) * cell + cell * 0.55,
        )[
          #text(size: label-size, weight: "bold", "START")
        ]
        // CÍL marker (filled square) + label inside cell
        #place(
          dx: goal.at(1) * cell + cell * 0.28,
          dy: goal.at(0) * cell + cell * 0.12,
        )[
          #rect(width: cell * 0.40, height: cell * 0.40, fill: ink, stroke: none)
        ]
        #place(
          dx: goal.at(1) * cell + cell * 0.08,
          dy: goal.at(0) * cell + cell * 0.58,
        )[
          #text(size: label-size, weight: "bold", "CÍL")
        ]
      ]
    ]
    #v(1.5mm)
    #box(width: 2.8mm, height: 2.8mm, stroke: mm(theme.lines.checkbox_stroke_mm) + ink)
    #h(1mm)
    #text(size: 6.5pt, fill: muted, "vyřešeno")
  ]
}

#let render-maze-cover(page) = {
  text(size: 26pt, weight: "bold", fill: ink, page.title)
  v(2mm)
  text(size: 11pt, fill: muted, page.data.at("pack_subtitle", default: ""))
  v(4mm)
  line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.2 + accent)
  v(3mm)
  text(size: 8.5pt, page.instructions)
  v(4mm)
  text(size: 9pt, weight: "bold", "Obtížnost")
  v(2mm)
  for item in page.data.at("legend", default: ()) {
    grid(
      columns: (22mm, 14mm, 1fr),
      column-gutter: 2mm,
      align: (left + horizon, left + horizon, left + horizon),
      text(size: 8pt, weight: "bold", item.label),
      text(size: 9pt, item.marker),
      text(size: 7.5pt, fill: muted, item.detail),
    )
    v(1.5mm)
  }
  v(6mm)
  text(size: 9pt, weight: "bold")[
    Vydání: #page.data.at("edition_date", default: "")
  ]
  v(1fr)
  align(center)[
    #text(size: 8pt, fill: muted, theme.brand.name + " · " + theme.brand.tagline)
    #v(1mm)
    #text(size: 7pt, fill: light, "A5 · 6 listů A4 booklet · duplex · krátká hrana")
  ]
}

#let render-maze-solutions(page) = {
  game-header(page.title, instructions: page.instructions)
  let items = page.data.at("items", default: ())
  if items.len() == 0 {
    text(size: 9pt, fill: muted, "Řešení nejsou zahrnuta.")
  } else {
    let n-items = items.len()
    let sol-cols = if n-items == 1 { 1 } else { 2 }
    let col-spec = if sol-cols == 1 { (1fr,) } else { (1fr, 1fr) }
    block(width: 100%, breakable: false)[
      #grid(
        columns: col-spec,
        column-gutter: 2.5mm,
        row-gutter: 2.8mm,
        ..items.map(item => {
          let rows = item.data.rows
          let cols = item.data.cols
          let max-w = if n-items <= 3 { 110mm } else { 58mm }
          let max-h = if n-items <= 3 { 52mm } else { 48mm }
          let cell = calc.min(max-w / cols, max-h / rows)
          let path = item.answer.path
          let start = item.data.start
          let goal = item.data.goal
          let wall-pt = 0.35pt
          block(width: 100%, breakable: false)[
            #text(size: 6.5pt, weight: "bold")[
              #str(item.puzzle_number). #item.data.difficulty_label_cs
              #h(1mm)
              #text(size: 5.5pt, fill: muted, item.data.difficulty_marker)
            ]
            #v(0.5mm)
            #align(center)[
              #box(width: cols * cell, height: rows * cell)[
                #if path.len() > 1 {
                  for i in range(path.len() - 1) {
                    let a = path.at(i)
                    let b = path.at(i + 1)
                    let x0 = a.at(1) * cell + cell / 2
                    let y0 = a.at(0) * cell + cell / 2
                    let x1 = b.at(1) * cell + cell / 2
                    let y1 = b.at(0) * cell + cell / 2
                    place(dx: calc.min(x0, x1), dy: calc.min(y0, y1))[
                      #line(
                        start: (0pt, 0pt),
                        end: (calc.abs(x1 - x0), calc.abs(y1 - y0)),
                        stroke: (paint: luma(50%), thickness: calc.max(0.7pt, cell * 0.22), cap: "round"),
                      )
                    ]
                  }
                }
                #for e in item.data.edges {
                  let x0 = e.x0 * cell
                  let y0 = e.y0 * cell
                  if e.y0 == e.y1 {
                    place(dx: x0, dy: y0)[#line(length: cell, stroke: wall-pt + ink)]
                  } else {
                    place(dx: x0, dy: y0)[#line(angle: 90deg, length: cell, stroke: wall-pt + ink)]
                  }
                }
                #place(dx: start.at(1)*cell+cell*0.3, dy: start.at(0)*cell+cell*0.3)[
                  #circle(radius: cell*0.18, stroke: 0.3pt+ink, fill: none)
                ]
                #place(dx: goal.at(1)*cell+cell*0.32, dy: goal.at(0)*cell+cell*0.32)[
                  #rect(width: cell*0.36, height: cell*0.36, fill: ink, stroke: none)
                ]
              ]
            ]
          ]
        }),
      )
    ]
  }
}

#let render-word-search(page, show-answer: false) = {
  let num = page.data.at("puzzle_number", default: none)
  let marker = page.data.at("difficulty_marker", default: none)
  let label-cs = page.data.at("difficulty_label_cs", default: difficulty-label(page.difficulty))
  let header-right = if marker != none {
    label-cs + " " + marker
  } else {
    difficulty-label(page.difficulty)
  }
  let title = if num != none {
    "Osmisměrka " + str(num) + " · " + page.title
  } else {
    page.title
  }
  game-header(
    title,
    difficulty: header-right,
    instructions: if show-answer { "Řešení — pozice slov" } else { page.instructions },
  )
  let letter-grid = page.data.grid
  let n = page.data.size
  // Fit square grid into available width; leave room for larger word list + footer
  let max-grid = if n <= 10 { 105mm } else if n <= 13 { 108mm } else { 114mm }
  let cell = calc.min(8.5mm, max-grid / n)
  let letter-size = calc.max(8pt, cell * 0.42)
  align(center)[
    #table(
      columns: n * (cell,),
      rows: n * (cell,),
      stroke: mm(theme.lines.rule_width_mm) * 0.75 + ink,
      align: center + horizon,
      inset: 0pt,
      ..letter-grid.flatten().map(ch => text(size: letter-size, weight: "medium", ch)),
    )
  ]
  v(2.5mm)
  let cols = int(page.data.at("list_columns", default: 2))
  let words = page.data.words
  text(size: 8pt, weight: "bold", "Slova k nalezení")
  h(2mm)
  box(width: 2.8mm, height: 2.8mm, stroke: mm(theme.lines.checkbox_stroke_mm) + ink)
  h(1mm)
  text(size: 7pt, fill: muted, "hotovo")
  v(1.4mm)
  let col-spec = if cols == 3 { (1fr, 1fr, 1fr) } else { (1fr, 1fr) }
  let word-size = if cols == 3 { 10pt } else { 11pt }
  grid(
    columns: col-spec,
    column-gutter: 2.5mm,
    row-gutter: 1.4mm,
    ..words.map(w => text(size: word-size, weight: "medium", w)),
  )
  if show-answer {
    v(2mm)
    for p in page.answer.placements {
      text(size: 7pt, fill: muted)[
        #p.word: ř#str(p.row + 1)/s#str(p.col + 1) · #p.direction
        #linebreak()
      ]
    }
  }
}

#let render-ws-cover(page) = {
  text(size: 26pt, weight: "bold", fill: ink, page.title)
  v(2mm)
  text(size: 11pt, fill: muted, page.data.at("pack_subtitle", default: page.instructions))
  v(4mm)
  line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.2 + accent)
  v(3mm)
  text(size: 8.5pt, page.instructions)
  v(4mm)
  text(size: 9pt, weight: "bold", "Obtížnost")
  v(2mm)
  for item in page.data.at("legend", default: ()) {
    grid(
      columns: (22mm, 14mm, 1fr),
      column-gutter: 2mm,
      align: (left + horizon, left + horizon, left + horizon),
      text(size: 8pt, weight: "bold", item.label),
      text(size: 9pt, item.marker),
      text(size: 7.5pt, fill: muted, item.detail),
    )
    v(1.5mm)
  }
  v(4mm)
  text(size: 8pt, fill: muted)[
    V mřížce bez diakritiky: židle → ZIDLE, kůň → KUN. Písmeno CH zabírá dvě políčka (C + H).
  ]
  v(6mm)
  text(size: 9pt, weight: "bold")[
    Vydání: #page.data.at("edition_date", default: "")
  ]
  v(1fr)
  align(center)[
    #text(size: 8pt, fill: muted, theme.brand.name + " · " + theme.brand.tagline)
    #v(1mm)
    #text(size: 7pt, fill: light, "A5 · 6 listů A4 booklet · duplex · krátká hrana")
  ]
}

#let render-ws-solutions(page) = {
  game-header(page.title, instructions: page.instructions)
  let items = page.data.at("items", default: ())
  if items.len() == 0 {
    text(size: 9pt, fill: muted, "Řešení nejsou zahrnuta.")
  } else {
    let n-items = items.len()
    // Prefer two columns so hard 16×16 miniatures stay on one page
    let sol-cols = if n-items == 1 { 1 } else { 2 }
    let col-spec = if sol-cols == 1 { (1fr,) } else { (1fr, 1fr) }
    block(width: 100%, breakable: false)[
      #grid(
        columns: col-spec,
        column-gutter: 2.5mm,
        row-gutter: 2.5mm,
        ..items.map(item => {
          let g = item.data.grid
          let n = g.len()
          let cell = if n >= 16 {
            if n-items <= 3 { 3.35mm } else { 3.1mm }
          } else if n >= 13 {
            if n-items <= 3 { 3.9mm } else { 3.5mm }
          } else {
            if n-items <= 4 { 4.5mm } else { 4.0mm }
          }
          let answer-cells = (:)
          for p in item.answer.placements {
            for cell-pos in p.at("cells", default: ()) {
              let key = str(cell-pos.at(0)) + "," + str(cell-pos.at(1))
              answer-cells.insert(key, true)
            }
          }
          block(width: 100%, breakable: false)[
            #text(size: 6.5pt, weight: "bold")[
              #str(item.puzzle_number). #item.data.theme_title
              #h(1mm)
              #text(size: 5.5pt, fill: muted, item.data.difficulty_label_cs)
            ]
            #v(0.5mm)
            #align(center)[
              #table(
                columns: n * (cell,),
                rows: n * (cell,),
                stroke: 0.12mm + ink,
                align: center + horizon,
                inset: 0pt,
                ..{
                  let cells = ()
                  for (r, row) in g.enumerate() {
                    for (c, ch) in row.enumerate() {
                      let key = str(r) + "," + str(c)
                      let hit = answer-cells.at(key, default: false)
                      cells.push(
                        box(
                          width: 100%,
                          height: 100%,
                          // High-contrast monochrome: answer cells = black fill + white letter
                          fill: if hit { ink } else { none },
                          stroke: none,
                          align(center + horizon)[
                            #text(
                              size: calc.max(3.8pt, cell * 0.52),
                              weight: if hit { "bold" } else { "regular" },
                              fill: if hit { rgb(theme.colors.background) } else { light },
                              ch,
                            )
                          ],
                        )
                      )
                    }
                  }
                  cells
                },
              )
            ]
          ]
        }),
      )
    ]
  }
}

#let render-nonogram(page, show-answer: false) = {
  game-header(
    page.title,
    difficulty: difficulty-label(page.difficulty),
    instructions: if show-answer { "Řešení" } else { page.instructions },
  )
  let n = page.data.size
  let cell = calc.min(6.5mm, 90mm / n)
  if show-answer {
    let grid = page.answer.grid
    align(center)[
      #table(
        columns: n * (cell,),
        rows: n * (cell,),
        stroke: mm(theme.lines.rule_width_mm) + ink,
        ..grid.flatten().map(v => {
          if v == 1 { rect(width: 100%, height: 100%, fill: ink, stroke: none) } else { [] }
        }),
      )
    ]
  } else {
    let rows = page.data.row_clues
    let cols = page.data.col_clues
    let clue-w = 18mm
    let clue-h = 14mm
    align(center)[
      #grid(
        columns: (clue-w, n * cell),
        rows: (clue-h, n * cell),
        [],
        {
          // column clues
          grid(
            columns: n * (cell,),
            rows: (clue-h,),
            stroke: none,
            align: center + bottom,
            ..cols.map(cl => text(size: 6pt, cl.map(str).join("\n"))),
          )
        },
        {
          grid(
            columns: (clue-w,),
            rows: n * (cell,),
            stroke: none,
            align: right + horizon,
            ..rows.map(cl => text(size: 6pt, cl.map(str).join(" "))),
          )
        },
        table(
          columns: n * (cell,),
          rows: n * (cell,),
          stroke: mm(theme.lines.rule_width_mm) + ink,
          ..(n * n * ([],)),
        ),
      )
    ]
  }
}

#let render-connect-dots(page, show-answer: false) = {
  game-header(
    page.title,
    difficulty: difficulty-label(page.difficulty),
    instructions: if show-answer { "Řešení — spojnice" } else { page.instructions },
  )
  let pts = page.data.points
  let side = 110mm
  align(center)[
    #box(width: side, height: side, stroke: mm(theme.lines.rule_width_mm) + ink)[
      #if show-answer {
        let coords = pts.map(p => (p.x * side, p.y * side))
        place(dx: 0mm, dy: 0mm)[
          #curve(
            ..coords.enumerate().map(((i, pt)) => {
              if i == 0 { curve.move(pt) } else { curve.line(pt) }
            }),
            stroke: mm(theme.lines.rule_width_mm) + ink,
            close: true,
          )
        ]
      }
      #for p in pts {
        place(dx: p.x * side - 1mm, dy: p.y * side - 1mm)[
          #circle(radius: 0.7mm, fill: ink)
        ]
        place(dx: p.x * side + 1mm, dy: p.y * side - 2mm)[
          #text(size: 5.5pt, str(p.n))
        ]
      }
    ]
  ]
}

#let draw-object(obj, scale: 110mm) = {
  let x = obj.x * scale
  let y = obj.y * scale
  let s = obj.at("s", default: 1.0)
  let mirror = obj.at("mirror", default: false)
  let mx = if mirror { -1 } else { 1 }
  if obj.type == "circle" or obj.type == "sun" {
    place(dx: x, dy: y)[#circle(radius: obj.at("r", default: 0.05) * scale * s, stroke: mm(0.3) + ink)]
  } else if obj.type == "cloud" {
    place(dx: x, dy: y)[
      #circle(radius: 3mm * s, stroke: mm(0.3) + ink)
      #place(dx: 3mm * s, dy: 0mm)[#circle(radius: 2.5mm * s, stroke: mm(0.3) + ink)]
      #place(dx: -3mm * s, dy: 0.5mm)[#circle(radius: 2.2mm * s, stroke: mm(0.3) + ink)]
    ]
  } else if obj.type == "house" {
    place(dx: x, dy: y)[
      #polygon(
        (-6mm * s * mx, 6mm * s),
        (-6mm * s * mx, 0mm),
        (0mm, -6mm * s),
        (6mm * s * mx, 0mm),
        (6mm * s * mx, 6mm * s),
        stroke: mm(0.3) + ink,
      )
    ]
  } else if obj.type == "tree" {
    place(dx: x, dy: y)[
      #polygon((0mm, -7mm * s), (-5mm * s, 2mm * s), (5mm * s, 2mm * s), stroke: mm(0.3) + ink)
      #place(dx: -1mm, dy: 2mm * s)[#rect(width: 2mm, height: 5mm * s, stroke: mm(0.3) + ink)]
    ]
  } else if obj.type == "star" {
    place(dx: x, dy: y)[#text(size: 10pt * s, "★")]
  } else if obj.type == "car" {
    place(dx: x, dy: y)[
      #rect(width: 12mm * s * mx, height: 5mm * s, stroke: mm(0.3) + ink)
      #place(dx: 1mm * s, dy: 5mm * s)[#circle(radius: 1.5mm * s, stroke: mm(0.3) + ink)]
      #place(dx: 8mm * s * mx, dy: 5mm * s)[#circle(radius: 1.5mm * s, stroke: mm(0.3) + ink)]
    ]
  } else if obj.type == "creature" {
    place(dx: x, dy: y)[
      #circle(radius: 4mm * s, stroke: mm(0.3) + ink)
      #place(dx: -1.5mm * s, dy: -1mm * s)[#circle(radius: 0.6mm * s, fill: ink)]
      #place(dx: 1.5mm * s, dy: -1mm * s)[#circle(radius: 0.6mm * s, fill: ink)]
    ]
  } else if obj.type == "flower" {
    place(dx: x, dy: y)[#text(size: 9pt * s, "❀")]
  } else if obj.type == "rect" {
    place(dx: x, dy: y)[
      #rect(width: obj.w * scale, height: obj.h * scale, stroke: mm(0.25) + ink)
    ]
  }
}

#let render-spot(page, show-answer: false) = {
  game-header(
    page.title,
    difficulty: difficulty-label(page.difficulty),
    instructions: if show-answer { "Řešení — zakroužkované rozdíly" } else { page.instructions },
  )
  let side = 55mm
  grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    {
      text(size: 7pt, weight: "bold", "A")
      v(1mm)
      box(width: side, height: side, stroke: mm(theme.lines.rule_width_mm) + ink, clip: true)[
        #for obj in page.data.left { draw-object(obj, scale: side) }
      ]
    },
    {
      text(size: 7pt, weight: "bold", "B")
      v(1mm)
      box(width: side, height: side, stroke: mm(theme.lines.rule_width_mm) + ink, clip: true)[
        #for obj in page.data.right { draw-object(obj, scale: side) }
        #if show-answer {
          for ch in page.answer.changes {
            place(dx: ch.x * side - 4mm, dy: ch.y * side - 4mm)[
              #circle(radius: 4.5mm, stroke: mm(0.45) + ink)
            ]
          }
        }
      ]
    },
  )
}

#let render-cipher(page, show-answer: false) = {
  game-header(
    page.title,
    difficulty: difficulty-label(page.difficulty),
    instructions: if show-answer { "Řešení" } else { page.instructions },
  )
  if show-answer {
    text(size: 14pt, weight: "bold", page.answer.plaintext)
  } else {
    text(size: 16pt, tracking: 0.12em, page.data.ciphertext)
    v(4mm)
    if page.data.mode == "symbols" {
      text(size: 8pt, weight: "bold", "Nápověda (symbol → písmeno):")
      v(1mm)
      for (k, v) in page.data.crib {
        text(size: 9pt)[#v = #k  ]
      }
    } else {
      text(size: 8pt, fill: muted, page.data.hint)
    }
    v(8mm)
    text(size: 8pt, "Řešení:")
    v(2mm)
    line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + ink)
    v(6mm)
    line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + ink)
  }
}

#let render-two-player(page) = {
  game-header(page.title, instructions: page.instructions)
  let variant = page.data.variant
  if variant == "piskvorky" {
    let n = page.data.grid
    let cell = 7mm
    align(center)[
      #table(
        columns: n * (cell,),
        rows: n * (cell,),
        stroke: mm(theme.lines.rule_width_mm) + ink,
        ..(n * n * ([],)),
      )
    ]
  } else if variant == "lode" {
    let n = 10
    let cell = 6mm
    grid(
      columns: (1fr, 1fr),
      column-gutter: 4mm,
      {
        text(size: 7pt, weight: "bold", "Flotila")
        v(1mm)
        table(columns: n * (cell,), rows: n * (cell,), stroke: mm(0.3) + ink, ..(100 * ([],)))
      },
      {
        text(size: 7pt, weight: "bold", "Střely")
        v(1mm)
        table(columns: n * (cell,), rows: n * (cell,), stroke: mm(0.3) + ink, ..(100 * ([],)))
      },
    )
  } else if variant == "ctverecky" {
    let n = page.data.dots
    let cell = 10mm
    align(center)[
      #box(width: (n - 1) * cell + 2mm, height: (n - 1) * cell + 2mm)[
        #for r in range(n) {
          for c in range(n) {
            place(dx: c * cell, dy: r * cell)[#circle(radius: 0.8mm, fill: ink)]
          }
        }
      ]
    ]
  } else if variant == "fotbal" {
    align(center)[
      #box(width: 110mm, height: 70mm, stroke: mm(0.4) + ink)[
        #place(dx: 55mm, dy: 0mm)[#line(angle: 90deg, length: 70mm, stroke: mm(0.3) + ink)]
        #place(dx: 0mm, dy: 20mm)[#rect(width: 8mm, height: 30mm, stroke: mm(0.3) + ink)]
        #place(dx: 102mm, dy: 20mm)[#rect(width: 8mm, height: 30mm, stroke: mm(0.3) + ink)]
        #place(dx: 53mm, dy: 33mm)[#circle(radius: 2mm, stroke: mm(0.35) + ink)]
      ]
    ]
  } else if variant == "sibenice" {
    align(center)[
      #box(width: 40mm, height: 50mm, stroke: mm(0.35) + ink)
      #v(4mm)
      #text(size: 8pt, "Slovo: _ _ _ _ _ _ _ _ _")
      #v(3mm)
      #text(size: 8pt, "Špatné tipy: ________________")
    ]
  } else if variant == "kategorie" {
    let cats = page.data.categories
    table(
      columns: (28mm, 1fr, 1fr),
      stroke: mm(theme.lines.rule_width_mm) + ink,
      inset: 2mm,
      text(weight: "bold", "Kategorie"), text(weight: "bold", "Hráč 1"), text(weight: "bold", "Hráč 2"),
      ..cats.map(c => (text(c), [], [])).flatten(),
    )
    v(3mm)
    text(size: 8pt, "Písmeno kola: ______")
  }
}

#let render-free-grid(page) = {
  game-header(page.title, instructions: page.instructions)
  let n = page.data.at("grid", default: 10)
  let cell = 9mm
  align(center)[
    #table(columns: n * (cell,), rows: n * (cell,), stroke: mm(0.3) + ink, ..(n * n * ([],)))
  ]
}

#let render-score(page) = {
  game-header(page.title, instructions: page.instructions)
  table(
    columns: (1fr, 20mm, 20mm, 20mm, 20mm),
    stroke: mm(theme.lines.rule_width_mm) + ink,
    inset: 2.5mm,
    text(weight: "bold", "Hra"), [*1*], [*2*], [*3*], [*Σ*],
    ..(8 * ([ ], [], [], [], [])).flatten(),
  )
}

#let render-solutions(page) = {
  game-header(page.title, instructions: page.instructions)
  let items = page.data.at("items", default: ())
  if items.len() == 0 {
    text(size: 9pt, fill: muted, "Žádná řešení na této straně.")
  } else {
    let sudoku-items = items.filter(it => it.kind == "sudoku")
    let other-items = items.filter(it => it.kind != "sudoku")

    if sudoku-items.len() > 0 {
      // Split bands keep item counts modest so grids stay readable
      let sol-cols = if sudoku-items.len() > 14 { 3 } else { 2 }
      let col-spec = if sol-cols == 3 { (1fr, 1fr, 1fr) } else { (1fr, 1fr) }
      grid(
        columns: col-spec,
        column-gutter: 3.5mm,
        row-gutter: 3mm,
        ..sudoku-items.map(item => {
          let g = item.answer.grid
          let n = g.len()
          let cell = if n == 9 { 2.8mm } else if n == 6 { 3.2mm } else { 4.0mm }
          block(width: 100%, breakable: false)[
            #text(size: 7pt, weight: "bold")[
              s.#str(item.page)#if item.at("sub", default: none) != none [·#str(item.sub)]
            ]
            #v(0.6mm)
            #table(
              columns: n * (cell,),
              rows: n * (cell,),
              stroke: 0.16mm + ink,
              align: center + horizon,
              inset: 0pt,
              ..g.flatten().map(v => text(size: calc.max(6pt, cell * 0.78), weight: "medium", str(v))),
            )
          ]
        }),
      )
      v(2mm)
    }

    for item in other-items {
      block(width: 100%, below: 2.5mm, breakable: false)[
        #text(size: 7.5pt, weight: "bold")[s.#str(item.page) · #item.title]
        #v(0.8mm)
        #if item.kind == "cipher" {
          text(size: 8pt, item.answer.plaintext)
        } else if item.kind == "word_search" {
          text(size: 6.5pt, item.answer.placements.map(p => p.word).join(", "))
        } else if item.kind == "nonogram" {
          let g = item.answer.grid
          let n = g.len()
          let cell = 2.2mm
          table(
            columns: n * (cell,),
            rows: n * (cell,),
            stroke: 0.15mm + ink,
            ..g.flatten().map(v => if v == 1 { rect(width: 100%, height: 100%, fill: ink, stroke: none) } else { [] }),
          )
        } else if item.kind == "maze" {
          text(size: 6.5pt, fill: muted, "Cesta má " + str(item.answer.path.len()) + " políček (START→CÍL).")
        } else if item.kind == "connect_dots" {
          text(size: 6.5pt, fill: muted, "Spoj body 1–" + str(item.data.count) + ".")
        } else if item.kind == "spot_difference" {
          text(size: 6.5pt, fill: muted)[
            Rozdíly: #item.answer.changes.map(c => c.type).join(", ")
          ]
        } else {
          text(size: 6.5pt, fill: muted, item.kind)
        }
      ]
    }
  }
}

#let crossword-grid(grid, tajenka-col, cell, show-letters: false) = {
  let rows = grid.len()
  let cols = grid.at(0).len()
  let thin = mm(theme.lines.rule_width_mm)
  let thick = mm(theme.lines.margin_line_width_mm)
  table(
    columns: cols * (cell,),
    rows: rows * (cell,),
    stroke: (x, y) => {
      let is-taj = x == tajenka-col
      let w = if is-taj { thick } else { thin }
      (
        top: w + ink,
        left: w + ink,
        right: if x == cols - 1 or x + 1 == tajenka-col or is-taj { thick + ink } else { 0pt },
        bottom: if y == rows - 1 { w + ink } else { 0pt },
      )
    },
    align: center + horizon,
    inset: 0pt,
    ..{
      let cells = ()
      for (r, row) in grid.enumerate() {
        for (c, ch) in row.enumerate() {
          let blocked = ch == "#"
          let is-taj = c == tajenka-col and not blocked
          let letter = if show-letters and not blocked and ch != "" { ch } else { "" }
          cells.push(
            box(
              width: 100%,
              height: 100%,
              fill: if blocked { ink } else { none },
              stroke: none,
              {
                if is-taj and not blocked {
                  place(top + left, dx: 0.3mm, dy: 0.3mm)[
                    #rect(
                      width: cell - 0.6mm,
                      height: cell - 0.6mm,
                      stroke: 0.35pt + ink,
                      fill: none,
                    )
                  ]
                }
                // Mark tajenka column only on full-size puzzle pages
                if r == 0 and is-taj and cell >= 5.5mm {
                  place(top + left, dx: 0.4mm, dy: 0.15mm)[
                    #text(size: calc.max(4pt, cell * 0.2), weight: "bold", "T")
                  ]
                }
                align(center + horizon)[
                  #text(
                    size: calc.max(7pt, cell * 0.42),
                    weight: "bold",
                    fill: if blocked { rgb(theme.colors.background) } else { ink },
                    letter,
                  )
                ]
              },
            )
          )
        }
      }
      cells
    },
  )
}

#let render-crossword(page, show-answer: false) = {
  let num = page.data.at("puzzle_number", default: none)
  let marker = page.data.at("difficulty_marker", default: none)
  let label-cs = page.data.at("difficulty_label_cs", default: difficulty-label(page.difficulty))
  let header-right = if marker != none { label-cs + " · " + marker } else { label-cs }
  let title = if num != none { "Křížovka " + str(num) } else { page.title }
  game-header(
    title,
    difficulty: header-right,
    instructions: if show-answer { "Řešení — vyplněná mřížka a tajenka" } else { page.instructions },
  )
  let grid-data = if show-answer { page.answer.grid } else { page.data.grid }
  let rows = page.data.rows
  let cols = page.data.cols
  let taj-col = page.data.tajenka_col
  let max-w = 124mm
  let max-h = if rows >= 11 { 88mm } else if rows >= 9 { 96mm } else { 105mm }
  // Generator keeps cols/rows within handwriting-friendly bounds (>= ~6 mm).
  let cell = calc.min(max-w / cols, max-h / rows, 9mm)
  align(center)[
    #crossword-grid(grid-data, taj-col, cell, show-letters: show-answer)
  ]
  v(2mm)
  text(size: 8pt, weight: "bold", "Nápovědy (vodorovně)")
  h(2mm)
  text(size: 7pt, fill: muted, page.data.at("ch_note", default: "CH = dvě políčka"))
  v(1.2mm)
  let clues = page.data.clues
  let clue-size = if clues.len() >= 11 { 8.5pt } else if clues.len() >= 9 { 9.5pt } else { 10.5pt }
  let mid = calc.ceil(clues.len() / 2)
  let left = clues.slice(0, mid)
  let right = clues.slice(mid)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    row-gutter: 0.8mm,
    {
      for item in left {
        block(below: 0.7mm)[
          #text(size: clue-size)[
            #text(weight: "bold", str(item.num) + ".")
            #h(0.8mm)
            #item.clue
            #text(size: clue-size - 1pt, fill: muted, " (" + str(item.length) + ")")
          ]
        ]
      }
    },
    {
      for item in right {
        block(below: 0.7mm)[
          #text(size: clue-size)[
            #text(weight: "bold", str(item.num) + ".")
            #h(0.8mm)
            #item.clue
            #text(size: clue-size - 1pt, fill: muted, " (" + str(item.length) + ")")
          ]
        ]
      }
    },
  )
  if show-answer {
    v(2mm)
    text(size: 9pt, weight: "bold")[
      Tajenka: #page.answer.tajenka
    ]
  }
}

#let render-cw-cover(page) = {
  text(size: 22pt, weight: "bold", fill: ink, page.title)
  v(2mm)
  text(size: 11pt, fill: muted, page.data.at("pack_subtitle", default: ""))
  v(4mm)
  line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.2 + accent)
  v(3mm)
  text(size: 8.5pt, page.instructions)
  v(4mm)
  text(size: 9pt, weight: "bold", "Obtížnost")
  v(2mm)
  for item in page.data.at("legend", default: ()) {
    grid(
      columns: (22mm, 14mm, 1fr),
      column-gutter: 2mm,
      align: (left + horizon, left + horizon, left + horizon),
      text(size: 8pt, weight: "bold", item.label),
      text(size: 9pt, item.marker),
      text(size: 7.5pt, fill: muted, item.detail),
    )
    v(1.5mm)
  }
  v(3mm)
  text(size: 8pt, fill: muted)[
    Tajenka se čte ve zvýrazněném sloupci shora dolů. Mezery v tajence se do mřížky
    nezapisují. Písmeno CH zabírá dvě políčka (C + H).
  ]
  v(4mm)
  text(size: 8pt, fill: muted, page.data.at("print_hint", default: ""))
  v(5mm)
  text(size: 9pt, weight: "bold")[
    Vydání: #page.data.at("edition_date", default: "")
  ]
  v(1fr)
  align(center)[
    #text(size: 8pt, fill: muted, theme.brand.name + " · " + theme.brand.tagline)
    #v(1mm)
    #text(size: 7pt, fill: light, "A5 · 6 listů A4 booklet · duplex · krátká hrana")
  ]
}

#let render-cw-solutions(page) = {
  game-header(page.title, instructions: page.instructions)
  let items = page.data.at("items", default: ())
  if items.len() == 0 {
    text(size: 9pt, fill: muted, "Řešení nejsou zahrnuta.")
  } else {
    let n-items = items.len()
    let sol-cols = if n-items <= 3 { 1 } else { 2 }
    let col-spec = if sol-cols == 1 { (1fr,) } else { (1fr, 1fr) }
    block(width: 100%, breakable: false)[
      #grid(
        columns: col-spec,
        column-gutter: 2.5mm,
        row-gutter: 2.2mm,
        ..items.map(item => {
          let g = item.answer.grid
          let rows = g.len()
          let cols = g.at(0).len()
          let taj = item.data.tajenka_col
          let max-w = if sol-cols == 1 { 110mm } else { 58mm }
          let max-h = if n-items <= 4 { 28mm } else if n-items <= 7 { 22mm } else { 18mm }
          let cell = calc.min(max-w / cols, max-h / rows, 4.2mm)
          block(width: 100%, breakable: false)[
            #text(size: 6.5pt, weight: "bold")[
              #str(item.puzzle_number).
              #item.data.difficulty_label_cs
              #h(1mm)
              #text(size: 5.5pt, fill: muted, item.data.difficulty_marker)
            ]
            #v(0.4mm)
            #align(center)[
              #crossword-grid(g, taj, cell, show-letters: true)
            ]
            #v(0.4mm)
            #text(size: 6pt, weight: "bold")[
              Tajenka: #item.answer.tajenka
            ]
          ]
        }),
      )
    ]
  }
}

#let render-page(page) = {
  let k = page.kind
  if k == "cover" { render-cover(page) }
  else if k == "ws_cover" { render-ws-cover(page) }
  else if k == "maze_cover" { render-maze-cover(page) }
  else if k == "cw_cover" { render-cw-cover(page) }
  else if k == "back" { render-back(page) }
  else if k == "instructions" { render-instructions(page) }
  else if k == "rules" { render-rules(page) }
  else if k == "sudoku" { render-sudoku(page) }
  else if k == "maze" { render-maze(page) }
  else if k == "word_search" { render-word-search(page) }
  else if k == "crossword" { render-crossword(page) }
  else if k == "math_grade1" { render-math-grade1(page) }
  else if k == "math_grade1_answers" { render-math-grade1-answers(page) }
  else if k == "math_grade2" { render-math-grade2(page) }
  else if k == "math_grade2_answers" { render-math-grade2-answers(page) }
  else if k == "math_set" { render-math-set(page) }
  else if k == "math_set_answers" { render-math-set-answers(page) }
  else if k == "nonogram" { render-nonogram(page) }
  else if k == "connect_dots" { render-connect-dots(page) }
  else if k == "spot_difference" { render-spot(page) }
  else if k == "cipher" { render-cipher(page) }
  else if k == "two_player" { render-two-player(page) }
  else if k == "bonus" { render-sudoku(page) }
  else if k == "solutions" { render-solutions(page) }
  else if k == "ws_solutions" { render-ws-solutions(page) }
  else if k == "maze_solutions" { render-maze-solutions(page) }
  else if k == "cw_solutions" { render-cw-solutions(page) }
  else if k == "free_grid" { render-free-grid(page) }
  else if k == "score_table" { render-score(page) }
  else { text("Unknown page: " + k) }
}
