#import "../base.typ": *
#import "common.typ": game-header, difficulty-label

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
  game-header(
    page.title,
    difficulty: difficulty-label(page.difficulty),
    instructions: if show-answer { "Řešení — vyznačená cesta" } else { page.instructions },
  )
  let rows = page.data.rows
  let cols = page.data.cols
  let cell = calc.min(12mm, 110mm / cols)
  let path = if show-answer { page.answer.path } else { () }
  let path-set = path.map(p => str(p.at(0)) + "," + str(p.at(1)))
  align(center)[
    #box(width: cols * cell, height: rows * cell)[
      #for e in page.data.edges {
        let x0 = e.x0 * cell
        let y0 = e.y0 * cell
        let x1 = e.x1 * cell
        let y1 = e.y1 * cell
        if e.y0 == e.y1 {
          place(dx: x0, dy: y0)[#line(length: cell, stroke: mm(theme.lines.rule_width_mm) + ink)]
        } else {
          place(dx: x0, dy: y0)[#line(angle: 90deg, length: cell, stroke: mm(theme.lines.rule_width_mm) + ink)]
        }
      }
      #for p in path {
        place(dx: p.at(1) * cell + cell * 0.35, dy: p.at(0) * cell + cell * 0.35)[
          #circle(radius: cell * 0.12, fill: ink)
        ]
      }
      #place(dx: 1mm, dy: 1mm)[#text(size: 6pt, weight: "bold", "START")]
      #place(dx: (cols - 1) * cell + 0.5mm, dy: (rows - 1) * cell + cell - 3.5mm)[
        #text(size: 6pt, weight: "bold", "CÍL")
      ]
    ]
  ]
}

#let render-word-search(page, show-answer: false) = {
  game-header(
    page.title,
    difficulty: difficulty-label(page.difficulty),
    instructions: if show-answer { "Řešení — pozice slov" } else { page.instructions },
  )
  let grid = page.data.grid
  let n = page.data.size
  let cell = calc.min(7mm, 105mm / n)
  align(center)[
    #table(
      columns: n * (cell,),
      rows: n * (cell,),
      stroke: mm(theme.lines.rule_width_mm) * 0.8 + ink,
      align: center + horizon,
      ..grid.flatten().map(ch => text(size: cell * 0.4, weight: "medium", ch)),
    )
  ]
  v(3mm)
  text(size: 8pt, weight: "bold", "Slova:")
  v(1mm)
  text(size: 8pt, page.data.words.join(" · "))
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

#let render-page(page) = {
  let k = page.kind
  if k == "cover" { render-cover(page) }
  else if k == "back" { render-back(page) }
  else if k == "instructions" { render-instructions(page) }
  else if k == "rules" { render-rules(page) }
  else if k == "sudoku" { render-sudoku(page) }
  else if k == "maze" { render-maze(page) }
  else if k == "word_search" { render-word-search(page) }
  else if k == "nonogram" { render-nonogram(page) }
  else if k == "connect_dots" { render-connect-dots(page) }
  else if k == "spot_difference" { render-spot(page) }
  else if k == "cipher" { render-cipher(page) }
  else if k == "two_player" { render-two-player(page) }
  else if k == "bonus" { render-sudoku(page) }
  else if k == "solutions" { render-solutions(page) }
  else if k == "free_grid" { render-free-grid(page) }
  else if k == "score_table" { render-score(page) }
  else { text("Unknown page: " + k) }
}
