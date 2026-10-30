#import "../base.typ": *
#import "math_grade1.typ": icon-row, shape-draw
#import "math_grade2.typ": coin, dot-field, solid-draw

#let num-size = 15.5pt
#let task-size = 12pt

#let abox(w: 15mm, h: 8mm) = box(
  width: w,
  height: h,
  stroke: 0.7pt + ink,
  outset: 0pt,
)

#let wordline(w: 40mm) = box(
  width: w,
  height: 7mm,
  stroke: (bottom: 0.7pt + ink),
)

#let op-t(op) = text(size: num-size, op)

#let block-head(b) = {
  text(size: task-size)[#text(weight: "bold", b.letter) #h(1.4mm) #b.title]
  v(0.7mm)
}

#let item-grid(items, cols, draw) = {
  grid(
    columns: (1fr,) * cols,
    column-gutter: 3.2mm,
    row-gutter: 2.2mm,
    ..items.map(it => block(width: 100%, breakable: false, draw(it))),
  )
}

#let clock-draw(hour-deg, minute-deg, r: 8.6mm, hands: true) = {
  box(width: 2.2 * r, height: 2.2 * r)[
    #place(center + horizon)[#circle(radius: r, stroke: 0.8pt + ink)]
    #for h in range(12) {
      let ang = h * 30deg - 90deg
      let num-r = r - 2.05mm
      place(center + horizon, dx: calc.cos(ang) * num-r, dy: calc.sin(ang) * num-r)[
        #text(size: if r < 11mm { 6.5pt } else { 8pt }, str(if h == 0 { 12 } else { h }))
      ]
    }
    #if hands {
      place(center + horizon)[#line(length: r * 0.46, angle: hour-deg * 1deg, stroke: 1.35pt + ink)]
      place(center + horizon)[#line(length: r * 0.72, angle: minute-deg * 1deg, stroke: 0.75pt + ink)]
      place(center + horizon)[#circle(radius: 0.55mm, fill: ink)]
    }
  ]
}

#let sym-draw(id) = box(baseline: 0.35em)[
  #if id == "circle" {
    circle(radius: 1.7mm, stroke: 0.8pt + ink)
  } else {
    square(size: 3.3mm, stroke: 0.8pt + ink)
  }
]

#let sym-row(ids, op) = {
  for (i, id) in ids.enumerate() {
    sym-draw(id)
    if i + 1 < ids.len() {
      h(0.7mm)
      text(size: num-size, op)
      h(0.7mm)
    }
  }
}

#let coin-row(values) = {
  for v in values {
    coin(v)
    h(0.7mm)
  }
}

#let stacks(heights) = {
  let s = 4.4mm
  let maxh = calc.max(..heights)
  let n = heights.len()
  box(width: n * (s + 0.8mm), height: maxh * s + 1.6mm)[
    #for (i, h) in heights.enumerate() {
      let x = i * (s + 0.8mm)
      for k in range(h) {
        place(dx: x, dy: (maxh - 1 - k) * s)[
          #rect(width: s, height: s, stroke: 0.7pt + ink)
        ]
      }
    }
  ]
}

#let plan-grid(rows, fill: false) = {
  let cols = rows.at(0).len()
  let cells = ()
  for row in rows {
    for v in row {
      cells.push(v)
    }
  }
  grid(
    columns: (7.2mm,) * cols,
    rows: (7.2mm,) * rows.len(),
    gutter: 0pt,
    ..cells.map(v => box(width: 7.2mm, height: 7.2mm, stroke: 0.7pt + ink)[
      #align(center + horizon)[
        #if fill { abox(w: 6mm, h: 6mm) } else { text(size: 12pt, str(v)) }
      ]
    ]),
  )
}

#let arrow-right() = box(height: 3.2mm, width: 10mm)[
  #place(dy: 1.3mm)[#line(length: 8mm, stroke: 0.8pt + ink)]
  #place(dx: 6.6mm, dy: 0.35mm)[
    #polygon(fill: ink, (0mm, 0mm), (2.4mm, 1.2mm), (0mm, 2.4mm))
  ]
]

#let seg-card(it) = {
  let cell = 5.4mm
  let cols = it.cols
  let rows = it.rows
  let w = (cols - 1) * cell
  let h = (rows - 1) * cell
  let ox = 1.2mm
  let oy = 1.2mm
  box(width: w + 3mm, height: h + 3mm)[
    #for r in range(rows) {
      for c in range(cols) {
        place(dx: ox + c * cell, dy: oy + r * cell)[
          #circle(radius: 0.55mm, fill: ink)
        ]
      }
    }
    #let pts = it.points
    #for i in range(pts.len() - 1) {
      let p = pts.at(i)
      let q = pts.at(i + 1)
      let x0 = p.at(0)
      let y0 = p.at(1)
      let x1 = q.at(0)
      let y1 = q.at(1)
      if y0 == y1 {
        let x = calc.min(x0, x1)
        place(dx: ox + x * cell, dy: oy + y0 * cell - 0.45pt)[
          #line(length: calc.abs(x1 - x0) * cell, stroke: 1.15pt + ink)
        ]
      } else {
        let y = calc.min(y0, y1)
        place(dx: ox + x0 * cell - 0.45pt, dy: oy + y * cell)[
          #line(length: calc.abs(y1 - y0) * cell, angle: 90deg, stroke: 1.15pt + ink)
        ]
      }
    }
  ]
}

#let word-to-num(it) = grid(
  columns: (auto, 16mm),
  column-gutter: 1.6mm,
  align: horizon,
  text(size: num-size)[#it.prompt #h(1mm) #text(size: num-size, "=")],
  abox(),
)

#let num-to-word(it) = grid(
  columns: (auto, 1fr),
  column-gutter: 1.6mm,
  align: horizon,
  text(size: num-size)[#it.prompt #h(1mm) #text(size: num-size, "=")],
  wordline(w: 100%),
)

#let render-wordnum(b) = {
  let chunks = ()
  let pending = ()
  for it in b.items {
    if it.mode == "to_num" and it.prompt.len() > 10 {
      if pending.len() > 0 {
        chunks.push(pending)
        pending = ()
      }
      chunks.push((it,))
    } else {
      pending.push(it)
    }
  }
  if pending.len() > 0 {
    chunks.push(pending)
  }
  stack(
    dir: ttb,
    spacing: 2.2mm,
    ..chunks.map(group => {
      let head = group.at(0)
      if group.len() == 1 and head.mode == "to_num" and head.prompt.len() > 10 {
        word-to-num(head)
      } else {
        item-grid(group, 2, it => {
          if it.mode == "to_num" { word-to-num(it) } else { num-to-word(it) }
        })
      }
    }),
  )
}

#let render-place(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #text(size: num-size, it.shown)
    #h(1mm)
    #abox()
    #if it.suffix != "" {
      h(1mm)
      text(size: num-size, it.suffix)
    }
  ]
})

#let render-seq(b) = {
  for it in b.items {
    block(breakable: false, below: 1.4mm)[
      #if it.style == "line" {
        box(width: 100%, height: 3.2mm)[
          #place(dy: 1.4mm)[#line(length: 100%, stroke: 0.7pt + ink)]
        ]
      }
      #grid(
        columns: (1fr,) * it.cells.len(),
        align: center + horizon,
        ..it.cells.map(cell => {
          if cell == "" { abox(w: 11mm, h: 7.2mm) } else { text(size: num-size, cell) }
        }),
      )
    ]
  }
}

#let render-compare(b) = {
  item-grid(b.items, b.at("cols", default: 3), it => {
    box[
      #text(size: num-size, str(it.a))
      #h(1mm)
      #abox(w: 8mm, h: 8mm)
      #h(1mm)
      #text(size: num-size, str(it.b))
    ]
  })
  if b.at("order", default: none) != none {
    v(1.2mm)
    let nums = b.order.numbers.map(n => str(n)).join("   ")
    text(size: num-size, nums)
    h(2mm)
    text(size: task-size, "od nejmenšího")
    h(1.5mm)
    for _ in range(4) {
      abox(w: 11mm, h: 7.2mm)
      h(1mm)
    }
  }
}

#let render-complement(b) = item-grid(b.items, b.at("cols", default: 3), it => {
  box[
    #text(size: num-size, str(it.a))
    #h(0.8mm)
    #text(size: num-size, "+")
    #h(0.8mm)
    #abox()
    #h(0.8mm)
    #text(size: num-size, "=")
    #h(0.8mm)
    #text(size: num-size, str(it.target))
  ]
})

#let render-calc(b) = item-grid(b.items, b.at("cols", default: 3), it => {
  box[
    #text(size: num-size, str(it.a))
    #h(0.7mm)
    #op-t(it.op)
    #h(0.7mm)
    #text(size: num-size, str(it.b))
    #h(0.8mm)
    #text(size: num-size, "=")
    #h(0.7mm)
    #abox()
  ]
})

#let render-decomp(b) = {
  if b.at("model_text", default: "") != "" {
    text(size: task-size, b.model_text)
    v(1mm)
  }
  for it in b.items {
    block(breakable: false, below: 1.5mm)[
      #text(size: num-size, str(it.a))
      #h(0.6mm)
      #op-t(it.op)
      #h(0.6mm)
      #text(size: num-size, str(it.b))
      #h(0.7mm)
      #text(size: num-size, "=")
      #h(0.6mm)
      #text(size: num-size, str(it.a))
      #h(0.6mm)
      #op-t(it.op)
      #h(0.5mm)
      #abox(w: 9mm, h: 7.4mm)
      #h(0.5mm)
      #op-t(it.op)
      #h(0.5mm)
      #abox(w: 9mm, h: 7.4mm)
      #h(0.6mm)
      #text(size: num-size, "=")
      #h(0.5mm)
      #abox()
    ]
  }
}

#let render-pairs(b) = {
  grid(
    columns: (1fr, 1fr),
    column-gutter: 8mm,
    [
      #for left in b.left [
        #text(size: num-size, left)
        #v(1.3mm)
      ]
    ],
    [
      #for right in b.right [
        #text(size: num-size, right)
        #v(1.3mm)
      ]
    ],
  )
}

#let render-sign(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #text(size: num-size, str(it.a))
    #h(0.8mm)
    #abox(w: 8mm, h: 8mm)
    #h(0.8mm)
    #text(size: num-size, str(it.b))
    #h(0.8mm)
    #text(size: num-size, "=")
    #h(0.8mm)
    #text(size: num-size, str(it.result))
  ]
})

#let render-missing(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #if it.form == "add_left" or it.form == "sub_left" {
      abox()
    } else {
      text(size: num-size, str(it.a))
    }
    #h(0.7mm)
    #if it.form == "add_left" or it.form == "add_right" {
      text(size: num-size, "+")
    } else {
      op-t("−")
    }
    #h(0.7mm)
    #if it.form == "add_right" or it.form == "sub_right" {
      abox()
    } else {
      text(size: num-size, str(it.b))
    }
    #h(0.7mm)
    #text(size: num-size, "=")
    #h(0.7mm)
    #text(size: num-size, str(it.c))
  ]
})

#let render-choice(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #text(size: num-size, it.prompt)
    #h(1.2mm)
    #for opt in it.options {
      box(stroke: 0.7pt + ink, radius: 3mm, inset: (x: 1.1mm, y: 0.3mm))[
        #text(size: 13pt, str(opt))
      ]
      h(1mm)
    }
  ]
})

#let render-compare-expr(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #text(size: num-size, str(it.a))
    #h(0.5mm)
    #op-t(it.op)
    #h(0.5mm)
    #text(size: num-size, str(it.b))
    #h(0.7mm)
    #abox(w: 8mm, h: 8mm)
    #h(0.7mm)
    #text(size: num-size, str(it.c))
    #h(0.5mm)
    #op-t(it.op2)
    #h(0.5mm)
    #text(size: num-size, str(it.d))
  ]
})

#let render-brackets(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #text(size: num-size, str(it.a))
    #h(0.5mm)
    #if it.form == "add_sum" {
      text(size: num-size, "+")
    } else {
      op-t("−")
    }
    #h(0.4mm)
    #text(size: num-size, "(")
    #text(size: num-size, str(it.b))
    #h(0.4mm)
    #if it.form == "sub_diff" {
      op-t("−")
    } else {
      text(size: num-size, "+")
    }
    #h(0.4mm)
    #text(size: num-size, str(it.c))
    #text(size: num-size, ")")
    #h(0.5mm)
    #text(size: num-size, "=")
    #h(0.5mm)
    #abox()
  ]
})

#let render-fix(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #text(size: num-size, str(it.a))
    #h(0.5mm)
    #op-t(it.op)
    #h(0.5mm)
    #text(size: num-size, str(it.b))
    #h(0.5mm)
    #text(size: num-size, "=")
    #h(0.5mm)
    #text(size: num-size, str(it.shown))
    #h(1.2mm)
    #abox()
  ]
})

#let render-pyramid(b) = {
  grid(
    columns: (1fr, 1fr),
    column-gutter: 4mm,
    ..b.items.map(it => align(center)[
      #abox(w: 11mm, h: 7mm)
      #v(1mm)
      #abox(w: 11mm, h: 7mm)
      #h(3mm)
      #abox(w: 11mm, h: 7mm)
      #v(1mm)
      #text(size: num-size, str(it.bottom.at(0)))
      #h(3.5mm)
      #text(size: num-size, str(it.bottom.at(1)))
      #h(3.5mm)
      #text(size: num-size, str(it.bottom.at(2)))
    ]),
  )
}

#let render-chain(b) = {
  for it in b.items {
    block(breakable: false, below: 1.6mm)[
      #text(size: num-size, str(it.start))
      #for step in it.steps {
        h(1mm)
        text(size: num-size, step.op)
        h(0.4mm)
        text(size: num-size, str(step.n))
        h(0.8mm)
        arrow-right()
        h(0.6mm)
        abox(w: 12mm, h: 7.4mm)
      }
    ]
  }
}

#let render-symbols(b) = {
  for m in b.models {
    block(breakable: false, below: 0.8mm)[
      #sym-row(m.ids, m.op)
      #h(1mm)
      #text(size: num-size, "=")
      #h(1mm)
      #text(size: num-size, str(m.result))
      #h(2mm)
      #text(size: task-size)[#m.name = #str(m.value)]
    ]
  }
  v(0.6mm)
  for it in b.items {
    block(breakable: false, below: 1.1mm)[
      #sym-row(it.ids, it.op)
      #h(1mm)
      #text(size: num-size, "=")
      #h(1mm)
      #abox()
    ]
  }
}

#let render-web(b) = {
  for it in b.items {
    block(breakable: false, below: 1.2mm)[
      #text(size: num-size, str(b.start))
      #h(1mm)
      #arrow-right()
      #h(0.8mm)
      #text(size: num-size, it.op)
      #h(0.4mm)
      #text(size: num-size, str(it.n))
      #h(1mm)
      #arrow-right()
      #h(0.8mm)
      #abox()
    ]
  }
}

#let group-pics(groups, each, icon, size: 3.1mm) = {
  for _ in range(groups) {
    box(stroke: 0.6pt + ink, inset: 0.4mm)[#icon-row(icon, each, size: size, gap: 0.35mm)]
    h(0.7mm)
  }
}

#let render-groups(b) = {
  text(size: task-size, b.model_text)
  v(0.6mm)
  group-pics(b.model.groups, b.model.each, b.model.icon)
  v(1.2mm)
  for it in b.items {
    block(breakable: false, below: 1.2mm)[
      #group-pics(it.groups, it.each, it.icon)
      #h(1.5mm)
      #abox()
    ]
  }
}

#let render-rewrite(b) = item-grid(b.items, b.at("cols", default: 1), it => {
  let adds = ()
  for _ in range(it.groups) { adds.push(str(it.each)) }
  grid(
    columns: (1fr, 13mm),
    column-gutter: 1.2mm,
    align: horizon,
    text(size: 14pt)[#adds.join(" + ") = #str(it.groups) · #str(it.each) =],
    abox(w: 12mm, h: 7.2mm),
  )
})

#let render-array(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #grid(
      columns: (2.6mm,) * it.cols,
      rows: (2.6mm,) * it.rows,
      gutter: 0.7mm,
      ..range(it.rows * it.cols).map(_ => circle(radius: 1.05mm, stroke: 0.6pt + ink)),
    )
    #h(1.5mm)
    #abox(w: 12mm, h: 7.2mm)
  ]
})

#let render-pic-pairs(b) = {
  for (i, left) in b.left.enumerate() {
    block(below: 1.5mm, breakable: false)[
      #grid(
        columns: (1fr, 22mm),
        column-gutter: 3mm,
        align: horizon,
        block(width: 100%)[#group-pics(left.groups, left.each, left.icon, size: 2mm)],
        text(size: num-size, b.right.at(i)),
      )
    ]
  }
}

#let render-factor(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  box[
    #text(size: num-size, str(it.a))
    #h(0.6mm)
    #text(size: num-size, "·")
    #h(0.6mm)
    #abox()
    #h(0.6mm)
    #text(size: num-size, "=")
    #h(0.6mm)
    #text(size: num-size, str(it.product))
  ]
})

#let render-parity(b) = item-grid(b.items, b.at("cols", default: 3), it => {
  box[
    #text(size: num-size, str(it.n))
    #h(1.2mm)
    #box(stroke: 0.7pt + ink, radius: 2.5mm, inset: (x: 1mm, y: 0.3mm))[#text(size: 12pt, "sudé")]
    #h(0.8mm)
    #box(stroke: 0.7pt + ink, radius: 2.5mm, inset: (x: 1mm, y: 0.3mm))[#text(size: 12pt, "liché")]
  ]
})

#let render-table(b) = {
  let cols = b.cols
  let rows = b.rows
  let head = (10mm,) + (12mm,) * cols.len()
  let cells = ()
  cells.push(box(width: 10mm, height: 8mm)[#align(center + horizon)[#text(size: 12pt, "·")]])
  for c in cols {
    cells.push(box(width: 12mm, height: 8mm)[#align(center + horizon)[#text(size: 13pt, weight: "bold", str(c))]])
  }
  for (r-i, r) in rows.enumerate() {
    cells.push(box(width: 10mm, height: 8mm)[#align(center + horizon)[#text(size: 13pt, weight: "bold", str(r))]])
    for (c-i, c) in cols.enumerate() {
      let blank = b.items.any(it => it.r == r-i and it.c == c-i)
      cells.push(box(width: 12mm, height: 8mm, stroke: 0.6pt + ink)[
        #align(center + horizon)[
          #if blank { abox(w: 9mm, h: 6.2mm) } else { text(size: 12pt, str(r * c)) }
        ]
      ])
    }
  }
  grid(columns: head, gutter: 0pt, ..cells)
}

#let render-dots(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  block(breakable: false)[
    #dot-field(it.count)
    #v(0.4mm)
    #text(size: task-size, it.prompt)
    #h(1mm)
    #abox(w: 12mm, h: 7.2mm)
  ]
})

#let render-family(b) = {
  for it in b.items {
    block(breakable: false, below: 1.5mm)[
      #stack(
        dir: ltr,
        spacing: 1.6mm,
        text(size: 14pt)[#str(it.a) · #str(it.b) = #str(it.product)],
        text(size: 14pt)[#str(it.product) : #str(it.b) =],
        abox(w: 10mm, h: 6.8mm),
        text(size: 14pt)[#str(it.product) :],
        abox(w: 10mm, h: 6.8mm),
        text(size: 14pt, "= " + str(it.b)),
      )
    ]
  }
}

#let render-clocks(b) = {
  item-grid(b.items, b.at("cols", default: 4), it => align(center)[
    #clock-draw(it.hour_deg, it.minute_deg, r: 10mm)
    #v(0.4mm)
    #abox(w: 14mm, h: 6.6mm)
  ])
  let shifts = b.at("shifts", default: ())
  if shifts.len() > 0 {
    v(1.2mm)
    item-grid(shifts, 2, it => box[
      #text(size: task-size, it.prompt)
      #h(1mm)
      #abox(w: 16mm, h: 7.2mm)
    ])
  }
}

#let render-clock-match(b) = {
  grid(
    columns: (1.4fr, 0.6fr),
    column-gutter: 3mm,
    item-grid(b.items, 3, it => align(center)[
      #text(size: 12pt, weight: "bold", it.label)
      #v(0.3mm)
      #clock-draw(it.hour_deg, it.minute_deg, r: 9.4mm)
    ]),
    [
      #for opt in b.options {
        text(size: num-size, opt)
        v(2.4mm)
      }
    ],
  )
}

#let render-clock-blank(b) = item-grid(b.items, b.at("cols", default: 2), it => align(center)[
  #text(size: num-size, it.prompt)
  #v(0.4mm)
  #clock-draw(0, 0, r: 12mm, hands: false)
])

#let render-time-words(b) = item-grid(b.items, b.at("cols", default: 2), it => {
  if it.mode == "to_digital" {
    box[#text(size: task-size, it.prompt) #h(1mm) #text(size: num-size, "=") #h(1mm) #abox(w: 16mm)]
  } else {
    box[#text(size: num-size, it.prompt) #h(1mm) #text(size: num-size, "=") #h(1mm) #wordline(w: 36mm)]
  }
})

#let render-time-shift(b) = item-grid(b.items, b.at("cols", default: 2), it => box[
  #text(size: task-size, it.prompt)
  #h(1mm)
  #abox(w: 16mm, h: 7.2mm)
])

#let render-coins(b) = {
  item-grid(b.items, b.at("cols", default: 2), it => align(left)[
    #coin-row(it.coins)
    #v(0.5mm)
    #abox(w: 14mm, h: 7.2mm)
    #h(0.6mm)
    #text(size: 12pt, "Kč")
  ])
  let enough = b.at("enough", default: ())
  if enough.len() > 0 {
    v(1mm)
    item-grid(enough, 2, it => box[
      #text(size: task-size)[#str(it.price) Kč, máš #str(it.have) Kč]
      #h(1mm)
      #box(stroke: 0.7pt + ink, radius: 2.5mm, inset: (x: 1mm, y: 0.2mm))[#text(size: 12pt, "ano")]
      #h(0.7mm)
      #box(stroke: 0.7pt + ink, radius: 2.5mm, inset: (x: 1mm, y: 0.2mm))[#text(size: 12pt, "ne")]
    ])
  }
}

#let render-coin-gap(b) = {
  for it in b.items {
    block(breakable: false, below: 1.4mm)[
      #coin-row(it.have)
      #h(1.5mm)
      #text(size: task-size)[nabídka ]
      #text(size: task-size, it.offer.map(v => str(v)).join(", "))
      #h(1mm)
      #text(size: task-size)[do #str(it.target) Kč]
      #h(1mm)
      #abox(w: 12mm, h: 7.2mm)
    ]
  }
}

#let render-coin-pair(b) = {
  for it in b.items {
    block(breakable: false, below: 1.3mm)[
      #coin-row(it.a)
      #h(2mm)
      #text(size: 12pt, "a")
      #h(2mm)
      #coin-row(it.b)
      #h(1.5mm)
      #abox(w: 14mm, h: 7.2mm)
      #text(size: 12pt, " Kč")
    ]
  }
}

#let render-enough(b) = item-grid(b.items, b.at("cols", default: 2), it => box[
  #text(size: task-size)[#str(it.price) Kč, máš #str(it.have) Kč]
  #h(1mm)
  #box(stroke: 0.7pt + ink, radius: 2.5mm, inset: (x: 1mm, y: 0.2mm))[#text(size: 12pt, "ano")]
  #h(0.7mm)
  #box(stroke: 0.7pt + ink, radius: 2.5mm, inset: (x: 1mm, y: 0.2mm))[#text(size: 12pt, "ne")]
])

#let render-shop(b) = {
  let goods = b.at("goods", default: ())
  if goods.len() > 0 {
    grid(
      columns: (1fr, 1fr),
      column-gutter: 4mm,
      row-gutter: 0.8mm,
      ..goods.map(g => text(size: task-size)[#g.name #h(2mm) #str(g.price) Kč]),
    )
    v(1mm)
  }
  for it in b.items {
    block(breakable: false, below: 1.1mm)[
      #text(size: task-size, it.prompt)
      #h(1.2mm)
      #if it.at("box", default: "num") == "word" {
        wordline(w: 32mm)
      } else {
        abox(w: 16mm, h: 7.2mm)
      }
    ]
  }
}

#let render-shapes(b) = item-grid(b.items, 4, it => align(center)[
  #shape-draw(it.id)
  #v(0.5mm)
  #for opt in it.options {
    text(size: 12pt, opt)
    linebreak()
  }
])

#let render-solids(b) = item-grid(b.items, 4, it => align(center)[
  #if it.id == "sphere" or it.id == "cylinder" {
    solid-draw(it.id)
  } else {
    shape-draw(it.id)
  }
  #v(0.4mm)
  #for opt in it.options {
    text(size: 12pt, opt)
    linebreak()
  }
])

#let render-count-shapes(b) = {
  block[
    #for id in b.shapes {
      box(inset: (x: 0.4mm))[#scale(x: 62%, y: 62%, reflow: true)[#shape-draw(id)]]
    }
  ]
  v(0.6mm)
  item-grid(b.items, 2, it => box[
    #text(size: task-size)[Kolik je #it.label?]
    #h(1mm)
    #abox(w: 12mm, h: 7.2mm)
  ])
}

#let render-segments(b) = {
  let cards = item-grid(b.items, b.at("cols", default: 3), it => box[
    #text(size: 12pt, weight: "bold", it.label)
    #h(1mm)
    #seg-card(it)
    #h(1mm)
    #abox(w: 10mm, h: 7mm)
  ])
  if b.at("plan", default: none) != none {
    grid(
      columns: (1fr, 1fr),
      column-gutter: 3mm,
      cards,
      [
        #plan-grid(b.plan.rows)
        #h(2mm)
        #text(size: task-size, "kostek")
        #h(1mm)
        #abox(w: 12mm, h: 7.2mm)
        #linebreak()
        #arrow-right()
      ],
    )
  } else {
    cards
  }
}

#let render-seg-compare(b) = item-grid(b.items, 2, it => box[
  #text(size: num-size, it.a)
  #h(1mm)
  #abox(w: 8mm, h: 8mm)
  #h(1mm)
  #text(size: num-size, it.b)
])

#let render-path(b) = {
  let it = b.items.at(0)
  let cell = 6mm
  let cols = it.cols
  let rows = it.rows
  box(width: (cols - 1) * cell + 4mm, height: (rows - 1) * cell + 4mm)[
    #for r in range(rows) {
      for c in range(cols) {
        place(dx: 2mm + c * cell, dy: 2mm + r * cell)[
          #circle(radius: 0.6mm, fill: ink)
        ]
      }
    }
    #place(dx: 3.4mm, dy: 2mm + (rows - 1) * cell - 3.4mm)[#text(size: 9pt, weight: "bold", "A")]
  ]
}

#let render-columns(b) = item-grid(b.items, b.at("cols", default: 4), it => align(center)[
  #stacks(it.heights)
  #v(0.5mm)
  #abox(w: 11mm, h: 7mm)
])

#let render-plan(b) = item-grid(b.items, b.at("cols", default: 2), it => box[
  #plan-grid(it.rows)
  #h(1.5mm)
  #abox(w: 12mm, h: 7.2mm)
  #linebreak()
  #arrow-right()
  #h(1mm)
  #text(size: 10pt, "doprava")
])

#let render-plan-fill(b) = {
  let it = b.items.at(0)
  stacks(it.heights)
  h(3mm)
  plan-grid((it.heights.map(_ => 0),), fill: true)
  h(2mm)
  arrow-right()
  h(1mm)
  text(size: 10pt, "doprava")
}

#let render-plan-match(b) = {
  let it = b.items.at(0)
  stacks(it.heights)
  h(3mm)
  text(size: 12pt, weight: "bold", "A")
  h(1mm)
  plan-grid((it.plans.at(0),))
  h(3mm)
  text(size: 12pt, weight: "bold", "B")
  h(1mm)
  plan-grid((it.plans.at(1),))
  h(2mm)
  arrow-right()
}

#let render-story(b) = {
  let story-card(it) = block(breakable: false, below: 0.8mm)[
    #text(size: task-size, it.prompt)
    #v(0.2mm)
    #box(width: 100%, height: 4.2mm, stroke: (bottom: 0.45pt + ink))
    #v(0.2mm)
    #text(size: task-size, "Odpověď:")
    #h(1mm)
    #abox(w: 16mm, h: 7mm)
  ]
  if b.items.len() == 2 {
    grid(
      columns: (1fr, 1fr),
      column-gutter: 3mm,
      story-card(b.items.at(0)),
      story-card(b.items.at(1)),
    )
  } else {
    for it in b.items {
      story-card(it)
    }
  }
  if b.at("hl", default: none) != none {
    text(size: num-size, "1 hl")
    h(1mm)
    text(size: num-size, "=")
    h(1mm)
    abox(w: 16mm)
    h(1mm)
    text(size: task-size, "l")
  }
}

#let render-kind(b) = {
  let k = b.kind
  if k == "wordnum" { render-wordnum(b) }
  else if k == "place" { render-place(b) }
  else if k == "seq" { render-seq(b) }
  else if k == "compare" { render-compare(b) }
  else if k == "complement" { render-complement(b) }
  else if k == "calc" { render-calc(b) }
  else if k == "decomp" { render-decomp(b) }
  else if k == "pairs" { render-pairs(b) }
  else if k == "sign" { render-sign(b) }
  else if k == "missing" { render-missing(b) }
  else if k == "choice" { render-choice(b) }
  else if k == "compare_expr" { render-compare-expr(b) }
  else if k == "brackets" { render-brackets(b) }
  else if k == "fix" { render-fix(b) }
  else if k == "pyramid" { render-pyramid(b) }
  else if k == "chain" { render-chain(b) }
  else if k == "symbols" { render-symbols(b) }
  else if k == "web" { render-web(b) }
  else if k == "groups" { render-groups(b) }
  else if k == "rewrite" { render-rewrite(b) }
  else if k == "array" { render-array(b) }
  else if k == "pic_pairs" { render-pic-pairs(b) }
  else if k == "factor" { render-factor(b) }
  else if k == "parity" { render-parity(b) }
  else if k == "table" { render-table(b) }
  else if k == "dots" { render-dots(b) }
  else if k == "family" { render-family(b) }
  else if k == "clocks" { render-clocks(b) }
  else if k == "clock_match" { render-clock-match(b) }
  else if k == "clock_blank" { render-clock-blank(b) }
  else if k == "time_words" { render-time-words(b) }
  else if k == "time_shift" { render-time-shift(b) }
  else if k == "coins" { render-coins(b) }
  else if k == "coin_gap" { render-coin-gap(b) }
  else if k == "coin_pair" { render-coin-pair(b) }
  else if k == "enough" { render-enough(b) }
  else if k == "shop" { render-shop(b) }
  else if k == "shapes" { render-shapes(b) }
  else if k == "solids" { render-solids(b) }
  else if k == "count_shapes" { render-count-shapes(b) }
  else if k == "segments" { render-segments(b) }
  else if k == "seg_compare" { render-seg-compare(b) }
  else if k == "path" { render-path(b) }
  else if k == "columns" { render-columns(b) }
  else if k == "plan" { render-plan(b) }
  else if k == "plan_fill" { render-plan-fill(b) }
  else if k == "plan_match" { render-plan-match(b) }
  else if k == "story" { render-story(b) }
  else { text(fill: rgb("#b00020"), "CHYBÍ " + k) }
}

#let render-math-set(page) = {
  let d = page.data
  set par(leading: 0.42em, spacing: 0.5em)
  set block(spacing: 0.55em)
  if d.show_name {
    text(size: 14pt, weight: "bold", d.booklet_title)
    linebreak()
    text(size: task-size, d.subtitle)
    v(0.5mm)
    text(size: task-size)[Jméno:]
    h(1.5mm)
    box(width: 55mm, stroke: (bottom: 0.6pt + ink), inset: (y: 1.1mm))[]
    v(0.8mm)
  }
  text(size: 13pt, weight: "bold", d.heading)
  v(0.4mm)
  if d.note != "" {
    block(below: 0.8mm)[#text(size: task-size, d.note)]
  }
  for b in d.blocks {
    block(above: 0.7mm, below: 0.2mm, breakable: true)[
      #block-head(b)
      #render-kind(b)
    ]
  }
}

#let render-math-set-answers(page) = {
  let d = page.data
  text(size: 14pt, weight: "bold", page.title)
  v(0.5mm)
  text(size: 9.5pt, page.instructions)
  v(0.4mm)
  text(size: 8.5pt)[Vydání: #d.edition_date · část #str(d.part)/#str(d.parts)]
  v(0.6mm)
  line(length: 100%, stroke: 0.6pt + ink)
  v(0.6mm)
  for item in d.items {
    block(below: 1.5mm, breakable: false)[
      #text(size: 11pt, weight: "bold")[Strana #str(item.page) — #item.heading]
      #v(0.35mm)
      #for line in item.lines {
        text(size: 8pt)[• #line]
        linebreak()
      }
    ]
  }
}
