// Matematika – 2. třída — A5 exercise pages.
#import "../base.typ": *
#import "math_grade1.typ": icon-row, shape-draw

#let num-size = 16pt
#let task-size = 12.5pt
#let title-size = 14pt

#let tight(body) = {
  set par(leading: 0.42em, spacing: 0.28em)
  set block(spacing: 0.32em)
  set text(hyphenate: false)
  body
}

#let abox(w: 11mm, h: 8.2mm) = box(
  width: w,
  height: h,
  baseline: 22%,
  stroke: 0.75pt + ink,
  radius: 0.45mm,
)

#let sec-title(t) = {
  v(0.7mm)
  text(size: 12pt, weight: "bold", t)
  v(0.3mm)
}

#let math2-header(d) = {
  if d.show_name_field {
    text(size: 13pt, weight: "bold", d.booklet_title)
    linebreak()
    text(size: 12.5pt, weight: "bold", d.heading)
    v(0.7mm)
    grid(
      columns: (auto, 1fr),
      column-gutter: 2mm,
      align: horizon,
      text(size: 12pt, "Jméno:"),
      box(width: 100%, height: 4.8mm, stroke: (bottom: 0.65pt + ink))[],
    )
  } else {
    text(size: title-size, weight: "bold", d.heading)
  }
  v(0.35mm)
}

#let calc-bit(a, op, b) = {
  text(size: num-size)[#str(a)]
  h(0.7mm)
  text(size: num-size, op)
  h(0.7mm)
  text(size: num-size)[#str(b)]
  h(0.8mm)
  text(size: num-size, "=")
  h(0.8mm)
  abox()
}

#let calc-grid(items, cols: 2) = {
  let n = calc.min(cols, items.len())
  grid(
    columns: (1fr,) * n,
    column-gutter: 2.2mm,
    row-gutter: 1.25mm,
    ..items.map(it => calc-bit(it.a, it.op, it.b)),
  )
}

#let missing-bit(it) = {
  let form = it.form
  let num(v) = text(size: num-size, str(v))
  let op(sign) = text(size: num-size, sign)
  let eq = text(size: num-size, "=")
  if form == "x+b" {
    abox(); h(0.7mm); op("+"); h(0.7mm); num(it.b); h(0.7mm); eq; h(0.7mm); num(it.total)
  } else if form == "a+x" {
    num(it.a); h(0.7mm); op("+"); h(0.7mm); abox(); h(0.7mm); eq; h(0.7mm); num(it.total)
  } else if form == "a-x" {
    num(it.a); h(0.7mm); op("−"); h(0.7mm); abox(); h(0.7mm); eq; h(0.7mm); num(it.result)
  } else {
    abox(); h(0.7mm); op("−"); h(0.7mm); num(it.b); h(0.7mm); eq; h(0.7mm); num(it.result)
  }
}

#let answer-line(label: "Odpověď:") = {
  text(size: 12pt, label)
  h(1.5mm)
  abox(w: 16mm, h: 8.5mm)
}

#let work-block(body) = {
  block(below: 1mm, breakable: false)[
    #text(size: task-size, body)
    #v(0.45mm)
    #grid(
      columns: (1fr, auto),
      column-gutter: 2.5mm,
      align: horizon,
      box(width: 100%, height: 7mm, stroke: (bottom: 0.65pt + ink))[],
      answer-line(),
    )
  ]
}

#let decomp-line(a, b, bridge, rest, total, filled: false) = {
  let slot(v) = {
    if filled {
      box(
        width: 8mm,
        height: 7.4mm,
        stroke: 0.65pt + ink,
        align(center + horizon)[#text(size: 13pt, weight: "bold", str(v))],
      )
    } else {
      abox(w: 9mm, h: 7.4mm)
    }
  }
  block(below: 0.7mm, breakable: false)[
    #grid(
      columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
      column-gutter: 0.7mm,
      align: horizon,
      text(size: 15pt, str(a)),
      text(size: 15pt, "+"),
      text(size: 15pt, str(b)),
      text(size: 15pt, "="),
      text(size: 15pt, str(a)),
      text(size: 15pt, "+"),
      slot(bridge),
      text(size: 15pt, "+"),
      slot(rest),
      text(size: 15pt, "="),
      slot(total),
      [], [], [], [], [], [],
      align(center, text(size: 7.5pt, "do 10")),
      [],
      align(center, text(size: 7.5pt, "zbytek")),
      [], [],
    )
  ]
}

#let seq-row(seq) = {
  block(below: 0.8mm, breakable: false)[
    #if "label" in seq.keys() {
      text(size: 11pt, weight: "bold", seq.label)
      h(1.6mm)
    }
    #for (i, v) in seq.values.enumerate() {
      if v == none {
        box(baseline: 22%)[#abox(w: 11mm, h: 8mm)]
      } else {
        text(size: 15pt, str(v))
      }
      if i + 1 < seq.values.len() {
        h(0.9mm)
        text(size: 11pt, "–")
        h(0.9mm)
      }
    }
  ]
}

#let dot(r: 1.35mm) = circle(radius: r, stroke: 0.65pt + ink)

#let dot-field(n) = {
  let cols = if n > 6 { calc.min(6, n) } else { n }
  grid(
    columns: cols,
    column-gutter: 1mm,
    row-gutter: 1mm,
    ..range(n).map(_ => dot()),
  )
}

#let child-icon() = {
  box(width: 7.2mm, height: 9.5mm)[
    #place(top + center)[#circle(radius: 1.55mm, stroke: 0.7pt + ink)]
    #place(center + horizon, dy: 0.8mm)[#line(length: 4.2mm, angle: 90deg, stroke: 0.7pt + ink)]
    #place(center + horizon, dy: 0.1mm)[#line(length: 5.2mm, stroke: 0.7pt + ink)]
    #place(center + bottom, dy: -0.1mm)[#line(length: 2.6mm, angle: 55deg, stroke: 0.65pt + ink)]
    #place(center + bottom, dy: -0.1mm)[#line(length: 2.6mm, angle: 125deg, stroke: 0.65pt + ink)]
  ]
}

#let coin(val) = {
  let big = val >= 10
  let d = if big { 10.5mm } else { 8.2mm }
  box(width: d, height: d)[
    #place(center + horizon)[#circle(radius: d / 2, stroke: 0.8pt + ink)]
    #if big {
      place(center + horizon)[#circle(radius: d / 2 - 0.9mm, stroke: 0.45pt + ink)]
    }
    #place(center + horizon)[
      #text(size: if big { 7pt } else { 6.5pt }, weight: "bold", str(val))
    ]
  ]
}

// Hour marks use the same angle convention as the hands: 0° is right, 90° is down.
#let clock-face(hour-deg, minute-deg, hour-ratio, minute-ratio) = {
  let r = 12.2mm
  box(width: 2.15 * r, height: 2.15 * r)[
    #place(center + horizon)[#circle(radius: r, stroke: 0.85pt + ink)]
    #for h in range(12) {
      let ang = h * 30deg - 90deg
      let num-r = r - 3.5mm
      place(center + horizon, dx: calc.cos(ang) * num-r, dy: calc.sin(ang) * num-r)[
        #text(size: 6.5pt, str(if h == 0 { 12 } else { h }))
      ]
      let tick-r = r - 0.9mm
      place(center + horizon, dx: calc.cos(ang) * tick-r, dy: calc.sin(ang) * tick-r)[
        #circle(radius: 0.38mm, fill: ink)
      ]
    }
    #place(center + horizon)[
      #line(length: r * hour-ratio, angle: hour-deg * 1deg, stroke: 1.45pt + ink)
    ]
    #place(center + horizon)[
      #line(length: r * minute-ratio, angle: minute-deg * 1deg, stroke: 0.8pt + ink)
    ]
    #place(center + horizon)[#circle(radius: 0.7mm, fill: ink)]
  ]
}

#let group-eq(groups, each) = {
  for i in range(groups) {
    text(size: 14pt, str(each))
    if i + 1 < groups {
      h(0.5mm)
      text(size: 14pt, "+")
      h(0.5mm)
    }
  }
  h(0.7mm)
  text(size: 14pt, "=")
  h(0.55mm)
  text(size: 14pt, str(groups))
  h(0.4mm)
  text(size: 14pt, "·")
  h(0.4mm)
  text(size: 14pt, str(each))
  h(0.55mm)
  text(size: 14pt, "=")
  h(0.45mm)
  abox()
}

#let solid-draw(id) = {
  if id == "sphere" {
    box(width: 14mm, height: 13mm)[
      #place(center + horizon)[#circle(radius: 5.2mm, stroke: 0.7pt + ink)]
      #place(center + horizon)[#ellipse(width: 10.4mm, height: 3.2mm, stroke: 0.6pt + ink)]
    ]
  } else if id == "cylinder" {
    box(width: 16mm, height: 15mm)[
      #place(dx: 2mm, dy: 0.4mm)[#ellipse(width: 12mm, height: 3.6mm, stroke: 0.7pt + ink)]
      #place(dx: 2mm, dy: 2.2mm)[#line(length: 9.5mm, angle: 90deg, stroke: 0.7pt + ink)]
      #place(dx: 14mm, dy: 2.2mm)[#line(length: 9.5mm, angle: 90deg, stroke: 0.7pt + ink)]
      #place(dx: 2mm, dy: 10mm)[#ellipse(width: 12mm, height: 3.6mm, stroke: 0.7pt + ink)]
    ]
  } else {
    shape-draw(id)
  }
}

// Length is the distance between the centres of the two endpoint ticks.
#let measured-segment(len-mm, left, right) = {
  let len = len-mm * 1mm
  let tick = 4.2mm
  block(below: 1.1mm, breakable: false)[
    #grid(
      columns: (auto, auto, auto, auto, auto),
      column-gutter: 1.4mm,
      align: horizon,
      text(size: 13pt, weight: "bold", left),
      box(width: len + 0.8mm, height: 5.6mm, clip: false)[
        #place(dx: 0pt, dy: 0.3mm)[#line(length: tick, angle: 90deg, stroke: 0.95pt + ink)]
        #place(dx: 0pt, dy: 2.4mm)[#line(length: len, stroke: 1.05pt + ink)]
        #place(dx: len, dy: 0.3mm)[#line(length: tick, angle: 90deg, stroke: 0.95pt + ink)]
      ],
      text(size: 13pt, weight: "bold", right),
      abox(w: 12mm, h: 8mm),
      text(size: 12pt, "cm"),
    )
  ]
}

#let line-kind(kind, letter: "p") = {
  if kind == "segment" {
    box(width: 36mm, height: 15mm, stroke: 0.65pt + ink)[
      #place(dx: 7mm, dy: 8mm)[#circle(radius: 0.75mm, fill: ink)]
      #place(dx: 7.7mm, dy: 8mm)[#line(length: 18mm, stroke: 0.9pt + ink)]
      #place(dx: 26.2mm, dy: 8mm)[#circle(radius: 0.75mm, fill: ink)]
      #place(dx: 5mm, dy: 1.4mm)[#text(size: 9pt, weight: "bold")[A]]
      #place(dx: 25mm, dy: 1.4mm)[#text(size: 9pt, weight: "bold")[B]]
    ]
  } else if kind == "line" {
    // The stroke crosses the inner frame and continues inside the outer box.
    box(width: 38mm, height: 15mm)[
      #place(dx: 4mm, dy: 0.8mm)[
        #rect(width: 30mm, height: 13.2mm, stroke: 0.65pt + ink)
      ]
      #place(dx: 0mm, dy: 7.4mm)[#line(length: 38mm, stroke: 0.95pt + ink)]
      #place(dx: 15mm, dy: 1.6mm)[#text(size: 11pt, style: "italic", letter)]
    ]
  } else {
    box(width: 36mm, height: 15mm, stroke: 0.65pt + ink)[
      #place(dx: 2mm, dy: 1.5mm)[
        #path(
          stroke: 0.9pt + ink,
          closed: false,
          (2mm, 10mm),
          (12mm, 2mm),
          (22mm, 9mm),
          (31mm, 3mm),
        )
      ]
      #place(dx: 3.2mm, dy: 10.7mm)[#circle(radius: 0.7mm, fill: ink)]
      #place(dx: 32.2mm, dy: 3.7mm)[#circle(radius: 0.7mm, fill: ink)]
    ]
  }
}

#let secs(d, id) = d.sections.filter(s => s.id == id)

#let render-m2-p1(page) = {
  let d = page.data
  math2-header(d)
  let s1 = d.sections.at(0)
  sec-title(s1.title)
  grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 1.2mm,
    ..s1.items.map(it => text(size: 14pt)[
      #str(it.a) + #abox(w: 8mm, h: 7.4mm) = 10
    ]),
  )

  let s2 = d.sections.at(1)
  sec-title(s2.title + "  —  " + s2.instruction)
  text(size: 10pt, weight: "bold", "Vzor")
  h(1.5mm)
  decomp-line(s2.example.a, s2.example.b, s2.example.bridge, s2.example.rest, s2.example.answer, filled: true)
  for it in s2.items {
    decomp-line(it.a, it.b, it.bridge, it.rest, it.answer, filled: false)
  }

  let s3 = d.sections.at(2)
  sec-title(s3.title)
  calc-grid(s3.items, cols: 2)

  let s4 = d.sections.at(3)
  sec-title(s4.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 2mm,
    row-gutter: 1.15mm,
    ..s4.items.map(missing-bit),
  )

  let s5 = d.sections.at(4)
  sec-title(s5.title)
  work-block(s5.item.text)
}

#let render-m2-p2(page) = {
  let d = page.data
  math2-header(d)
  let s1 = d.sections.at(0)
  sec-title(s1.title)
  let numeric = s1.items.filter(it => it.kind == "split_ones" or it.kind == "split_tens")
  let verbal = s1.items.filter(it => it.kind != "split_ones" and it.kind != "split_tens")
  grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    ..numeric.map(it => {
      if it.kind == "split_ones" {
        text(size: 15pt)[#str(it.n) = #str(it.tens) + #abox(w: 10mm, h: 8mm)]
      } else {
        text(size: 15pt)[#str(it.n) = #abox(w: 12mm, h: 8mm) + #str(it.ones)]
      }
    }),
  )
  v(0.8mm)
  for it in verbal {
    block(below: 0.7mm)[
      #if it.kind == "words" {
        text(size: 12.5pt)[#it.text #h(1mm) = #h(1mm)]
        abox(w: 12mm, h: 8mm)
      } else {
        text(size: 15pt)[100 = ]
        abox(w: 10mm, h: 8mm)
        h(1mm)
        text(size: 12.5pt)[desítek a 0 jednotek]
      }
    ]
  }

  let s2 = d.sections.at(1)
  sec-title(s2.title)
  for seq in s2.sequences { seq-row(seq) }

  let s3 = d.sections.at(2)
  sec-title(s3.title)
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.5mm,
    row-gutter: 1.15mm,
    ..s3.items.map(it => text(size: 15pt)[
      #str(it.a) #abox(w: 8mm, h: 7.6mm) #str(it.b)
    ]),
  )

  let s4 = d.sections.at(3)
  sec-title(s4.title)
  text(size: 13pt, s4.numbers.map(str).join("     "))
  v(0.7mm)
  for i in range(5) {
    abox(w: 12.5mm, h: 8mm)
    if i < 4 {
      h(0.8mm)
      text(size: 13pt, "<")
      h(0.8mm)
    }
  }

  let s5 = d.sections.at(4)
  sec-title(s5.title)
  let start = s5.start
  let count = s5.end - start + 1
  let cell = 10.4mm
  block(breakable: false)[
    #box(width: count * cell, height: 14mm)[
      #place(dx: cell / 2, dy: 1.5mm)[
        #line(length: (count - 1) * cell, stroke: 0.7pt + ink)
      ]
      #grid(
        columns: (cell,) * count,
        row-gutter: 0.5mm,
        ..range(count).map(_ => align(center)[
          #line(length: 3mm, angle: 90deg, stroke: 0.55pt + ink)
        ]),
        ..range(count).map(i => {
          let val = start + i
          align(center)[
            #if s5.missing.contains(val) {
              box(width: 8.4mm, height: 6.4mm, stroke: 0.6pt + ink)
            } else {
              text(size: 8pt, str(val))
            }
          ]
        }),
      )
    ]
  ]

  let s6 = d.sections.at(5)
  sec-title(s6.title)
  text(size: 12pt, s6.rule)
  h(1.5mm)
  text(size: 14pt)[Vzor: #str(s6.example.n) ≈ #str(s6.example.answer)]
  v(0.8mm)
  for it in s6.items {
    text(size: 15pt)[#str(it.n) ≈ ]
    abox(w: 12mm, h: 8mm)
    h(4mm)
  }
}

#let render-m2-p3(page) = {
  let d = page.data
  math2-header(d)
  let s1 = d.sections.at(0)
  sec-title(s1.title)
  let ex = s1.example
  text(size: 12pt, weight: "bold", "Vzor: ")
  text(size: 13pt)[#str(ex.a)]
  h(0.4mm)
  text(size: 13pt, "+")
  h(0.4mm)
  text(size: 13pt)[#str(ex.b)]
  h(0.45mm)
  text(size: 13pt, "=")
  h(0.45mm)
  text(size: 13pt)[#str(ex.a)]
  h(0.35mm)
  text(size: 13pt, "+")
  h(0.35mm)
  text(size: 13pt)[#str(ex.bridge)]
  h(0.35mm)
  text(size: 13pt, "+")
  h(0.35mm)
  text(size: 13pt)[#str(ex.rest)]
  h(0.45mm)
  text(size: 13pt, "=")
  h(0.45mm)
  text(size: 13pt)[#str(ex.ten)]
  h(0.35mm)
  text(size: 13pt, "+")
  h(0.35mm)
  text(size: 13pt)[#str(ex.rest)]
  h(0.45mm)
  text(size: 13pt, "=")
  h(0.45mm)
  text(size: 13pt, weight: "bold")[#str(ex.answer)]
  for block in s1.blocks {
    v(0.7mm)
    text(size: 11pt, weight: "bold", block.label)
    v(0.35mm)
    calc-grid(block.items, cols: block.items.len())
  }

  let s2 = d.sections.at(1)
  sec-title(s2.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 2mm,
    row-gutter: 1.2mm,
    ..s2.items.map(missing-bit),
  )

  let s3 = d.sections.at(2)
  sec-title(s3.title + "  —  " + s3.instruction)
  for it in s3.items {
    block(below: 1mm)[
      #text(size: 15pt)[#str(it.a) #it.op #str(it.b) = #str(it.shown)]
      #h(2mm)
      #text(size: 12pt)[správně:]
      #h(1mm)
      #abox(w: 12mm, h: 8mm)
    ]
  }
}

#let render-challenge-story(s2) = {
  v(1.2mm)
  block(width: 100%, stroke: 0.8pt + ink, inset: 2.2mm, radius: 0.8mm, breakable: false)[
    #text(size: 12pt, weight: "bold", s2.title)
    #h(2mm)
    #text(size: 11pt, s2.instruction)
    #v(0.8mm)
    #text(size: task-size, s2.item.text)
    #v(1.2mm)
    #box(width: 100%, height: 8mm, stroke: (bottom: 0.65pt + ink))[]
    #v(1mm)
    #answer-line(label: "Dohromady:")
    #h(3mm)
    #text(size: 12pt)[Kč]
    #v(1mm)
    #answer-line(label: "Zbude:")
    #h(3mm)
    #text(size: 12pt)[Kč]
  ]
}

#let render-m2-p4(page) = {
  let d = page.data
  math2-header(d)
  let stories = secs(d, "stories")
  if stories.len() > 0 {
    for (i, it) in stories.first().items.enumerate() {
      block(below: 1.15mm, breakable: false)[
        #text(size: 12pt, weight: "bold")[#str(i + 1). #it.label]
        #h(1.6mm)
        #text(size: task-size, it.text)
        #v(0.4mm)
        #grid(
          columns: (1fr, auto),
          column-gutter: 2.5mm,
          align: horizon,
          box(width: 100%, height: 7mm, stroke: (bottom: 0.65pt + ink))[],
          answer-line(),
        )
      ]
    }
  }
  for s2 in secs(d, "challenge_story") {
    render-challenge-story(s2)
  }
}

#let render-m2-p5(page) = {
  let d = page.data
  math2-header(d)
  let groups = secs(d, "groups")
  if groups.len() > 0 {
    let s1 = groups.first()
    sec-title(s1.title)
    for it in s1.items {
      block(below: 0.6mm, breakable: false)[
        #text(size: 12pt, weight: "bold")[#str(it.groups) skupiny po #str(it.each)]
        #v(0.25mm)
        #grid(
          columns: it.groups,
          column-gutter: 1.6mm,
          ..range(it.groups).map(_ => box(
            stroke: 0.65pt + ink,
            inset: 0.8mm,
            radius: 0.7mm,
            icon-row(it.kind, it.each, size: 3.5mm, gap: 0.45mm),
          )),
        )
        #v(0.45mm)
        #group-eq(it.groups, it.each)
      ]
    }
  }

  let arrays = secs(d, "array")
  if arrays.len() > 0 {
    let s2 = arrays.first()
    sec-title(s2.title + "  —  " + s2.instruction)
    grid(
      columns: (auto, 1fr),
      column-gutter: 3mm,
      align: horizon,
      grid(
        columns: s2.cols,
        column-gutter: 1.7mm,
        row-gutter: 1.5mm,
        ..range(s2.rows * s2.cols).map(_ => dot(r: 1.45mm)),
      ),
      text(size: 12.5pt)[
        Řad: #abox(w: 9mm, h: 8mm)
        #h(2mm)
        V řadě: #abox(w: 9mm, h: 8mm)
        #linebreak()
        #v(0.8mm)
        Celkem: #abox(w: 11mm, h: 8mm)
      ],
    )
  }

  let facts = secs(d, "facts")
  if facts.len() > 0 {
    sec-title(facts.first().title)
    calc-grid(facts.first().items, cols: 3)
  }

  for s4 in secs(d, "mult_seq") {
    sec-title(s4.title)
    for seq in s4.sequences { seq-row(seq) }
  }

  for s5 in secs(d, "word_mul") {
    sec-title(s5.title)
    work-block(s5.item.text)
  }
}

#let render-m2-p6(page) = {
  let d = page.data
  math2-header(d)
  let shares = secs(d, "share")
  let groupings = secs(d, "make_groups")
  if shares.len() > 0 and groupings.len() > 0 {
    let share = shares.first()
    let groups = groupings.first()
    sec-title("1. Dva významy dělení")
    grid(
      columns: (1fr, 1fr),
      column-gutter: 2.5mm,
      block(breakable: false)[
        #text(size: 11.5pt, weight: "bold", share.title)
        #v(0.25mm)
        #dot-field(share.total)
        #v(0.3mm)
        #grid(
          columns: share.parts,
          column-gutter: 0.8mm,
          ..range(share.parts).map(_ => child-icon()),
        )
        #v(0.25mm)
        #text(size: 11pt, share.text)
        #v(0.3mm)
        #answer-line(label: "Každé dítě:")
      ],
      block(breakable: false)[
        #text(size: 11.5pt, weight: "bold", groups.title)
        #v(0.25mm)
        #dot-field(groups.total)
        #v(0.3mm)
        #text(size: 11pt, groups.text)
        #v(0.3mm)
        #answer-line(label: "Skupin:")
      ],
    )
  }

  let divs = secs(d, "div_facts")
  if divs.len() > 0 {
    sec-title(divs.first().title)
    calc-grid(divs.first().items, cols: 3)
  }

  for s4 in secs(d, "families") {
    sec-title(s4.title)
    grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    ..s4.items.enumerate().map(((i, fam)) => {
      block(breakable: false)[
        #if i == 0 {
          text(size: 9pt, weight: "bold", "Vzor v prvním řádku")
          v(0.3mm)
        }
        #for row in fam.rows {
          block(below: 0.25mm)[
            #let cell(key) = {
              let value = row.at(key)
              if row.hide == none or row.hide != key {
                text(size: 14pt, str(value))
              } else {
                abox(w: 9mm, h: 7.4mm)
              }
            }
            #cell("x")
            #h(0.6mm)
            #text(size: 14pt, row.op)
            #h(0.6mm)
            #cell("y")
            #h(0.5mm)
            #text(size: 14pt, "=")
            #h(0.5mm)
            #cell("z")
          ]
        }
      ]
    }),
    )
  }

  for s5 in secs(d, "word_times") {
    sec-title(s5.title)
    text(size: 11.5pt, weight: "bold", s5.item.note)
    v(0.25mm)
    work-block(s5.item.text)
  }

  for s6 in secs(d, "challenge_mul") {
    v(0.6mm)
    block(width: 100%, stroke: 0.8pt + ink, inset: 1.4mm, radius: 0.8mm, breakable: false)[
      #text(size: 12pt, weight: "bold", s6.title)
      #h(1.5mm)
      #text(size: 11pt, s6.instruction)
      #v(0.45mm)
      #grid(
        columns: (1fr, 1fr, 1fr, 1fr),
        column-gutter: 1.2mm,
        ..s6.items.map(it => {
          text(size: 14pt, str(it.a))
          h(0.3mm)
          text(size: 14pt, it.op)
          h(0.3mm)
          text(size: 14pt, str(it.b))
          h(0.3mm)
          text(size: 14pt, "=")
          h(0.25mm)
          abox(w: 8.4mm, h: 7mm)
        }),
      )
    ]
  }
}

#let price-table(items) = {
  let cells = (text(weight: "bold", "Předmět"), text(weight: "bold", "Kč"))
  for it in items {
    cells.push(it.name)
    cells.push(str(it.price))
  }
  table(
    columns: (1fr, 16mm),
    stroke: 0.6pt + ink,
    inset: (x: 1.8mm, y: 1.05mm),
    align: (left, right),
    ..cells,
  )
}

#let render-m2-p7(page) = {
  let d = page.data
  math2-header(d)
  let s1 = d.sections.at(0)
  sec-title(s1.title)
  grid(
    columns: (58mm, 1fr),
    column-gutter: 3mm,
    price-table(s1.items),
    [
      #text(size: task-size, s1.buy_text)
      #v(0.8mm)
      #text(size: 12pt)[Cena:]
      #h(1mm)
      #abox(w: 14mm, h: 8mm)
      #h(1mm)
      #text(size: 12pt)[Kč]
      #v(1mm)
      #text(size: 12pt)[Zaplatíš #str(s1.pay) Kč. Zpět:]
      #h(1mm)
      #abox(w: 14mm, h: 8mm)
      #h(1mm)
      #text(size: 12pt)[Kč]
    ],
  )

  let s2 = d.sections.at(1)
  sec-title(s2.title + "  —  " + s2.instruction)
  for (i, c) in s2.coins.enumerate() {
    coin(c)
    if i + 1 < s2.coins.len() { h(1.3mm) }
  }
  h(2.5mm)
  text(size: 14pt, "=")
  h(1.2mm)
  abox(w: 14mm, h: 8.5mm)
  h(1mm)
  text(size: 12pt, "Kč")

  let s3 = d.sections.at(2)
  sec-title(s3.title)
  text(size: 11pt)[Napiš čas, například 7:00.]
  v(0.6mm)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 2mm,
    ..s3.items.map(it => align(center)[
      #clock-face(it.hour_deg, it.minute_deg, s3.hour_hand, s3.minute_hand)
      #v(0.5mm)
      #abox(w: 20mm, h: 8.2mm)
    ]),
  )

  let s4 = d.sections.at(3)
  sec-title(s4.title)
  text(size: task-size, s4.text)
  h(2mm)
  abox(w: 12mm, h: 8mm)
  h(1mm)
  text(size: 12pt, "hodin")

  let s5 = d.sections.at(4)
  sec-title(s5.title)
  let cells = s5.headers.map(h => text(weight: "bold", h))
  for row in s5.rows {
    cells.push(row.name)
    cells.push(text(size: 14pt, str(row.value)))
  }
  table(
    columns: (1fr, 28mm),
    stroke: 0.6pt + ink,
    inset: (x: 1.8mm, y: 1.05mm),
    align: (left, center),
    ..cells,
  )
  v(0.7mm)
  text(size: 12pt, s5.questions.at(0))
  h(1.5mm)
  abox(w: 28mm, h: 8mm)
  v(0.7mm)
  text(size: 12pt, s5.questions.at(1))
  h(1.5mm)
  abox(w: 14mm, h: 8mm)
}

#let name-under(drawing, width: 34mm) = {
  block(breakable: false)[
    #align(center)[
      #drawing
      #v(0.35mm)
      #box(width: width, height: 6.5mm, stroke: (bottom: 0.65pt + ink))[]
    ]
  ]
}

#let render-m2-p8(page) = {
  let d = page.data
  math2-header(d)
  let shapes = secs(d, "shapes2d")
  if shapes.len() > 0 {
    let s1 = shapes.first()
    sec-title(s1.title)
    text(size: 12pt)[Vyber: #s1.bank.join(", ")]
    v(0.6mm)
    grid(
      columns: (1fr, 1fr),
      column-gutter: 2mm,
      row-gutter: 1.2mm,
      ..s1.items.map(it => grid(
        columns: (16mm, 1fr),
        align: horizon,
        column-gutter: 1.5mm,
        align(center, shape-draw(it.id)),
        box(width: 100%, height: 7.2mm, stroke: (bottom: 0.65pt + ink))[],
      )),
    )
  }

  let lines = secs(d, "lines")
  if lines.len() > 0 {
    let s2 = lines.first()
    sec-title(s2.title)
    text(size: 12pt)[Vyber: #s2.bank.join(", ")]
    v(0.5mm)
    grid(
      columns: (1fr, 1fr, 1fr),
      column-gutter: 2.4mm,
      ..s2.items.map(it => name-under(line-kind(it.kind, letter: it.at("letter", default: "p")), width: 32mm)),
    )
  }

  let measures = secs(d, "measure")
  if measures.len() > 0 {
    let s3 = measures.first()
    sec-title(s3.title)
    text(size: 11.5pt, weight: "bold", s3.note)
    v(0.45mm)
    for it in s3.items {
      measured-segment(it.length_mm, it.left, it.right)
    }
  }

  let draws = secs(d, "draw")
  if draws.len() > 0 {
    sec-title(draws.first().title)
    for s4 in draws {
      text(size: task-size, s4.instruction)
      v(0.6mm)
      rect(width: 100%, height: if shapes.len() == 0 { 42mm } else { 11mm }, stroke: 0.55pt + ink)
      v(2.5mm)
    }
  }

  let units = secs(d, "units")
  if units.len() > 0 {
    let s5 = units.first()
    sec-title(s5.title)
    for it in s5.items {
      text(size: 15pt)[#str(it.amount) #it.left = #abox(w: 14mm, h: 8mm) #it.right]
      h(4mm)
    }
  }

  let solids = secs(d, "solids")
  if solids.len() > 0 {
    let s6 = solids.first()
    sec-title(s6.title)
    text(size: 12pt)[Vyber: #s6.bank.join(", ")]
    v(0.45mm)
    grid(
      columns: (1fr, 1fr, 1fr, 1fr),
      column-gutter: 1.2mm,
      ..s6.items.map(it => name-under(solid-draw(it.id), width: 26mm)),
    )
  }
}

#let render-math-grade2(page) = {
  let topic = page.data.topic
  let body = if topic == 1 { render-m2-p1(page) }
    else if topic == 2 { render-m2-p2(page) }
    else if topic == 3 { render-m2-p3(page) }
    else if topic == 4 { render-m2-p4(page) }
    else if topic == 5 { render-m2-p5(page) }
    else if topic == 6 { render-m2-p6(page) }
    else if topic == 7 { render-m2-p7(page) }
    else if topic == 8 { render-m2-p8(page) }
    else { text("Neznámé téma") }
  tight(body)
}

#let render-math-grade2-answers(page) = {
  let d = page.data
  text(size: 14pt, weight: "bold", page.title)
  v(0.6mm)
  text(size: 9.5pt, page.instructions)
  v(0.5mm)
  text(size: 8.5pt)[Vydání: #d.edition_date · část #str(d.part)/#str(d.parts)]
  v(0.7mm)
  line(length: 100%, stroke: 0.6pt + ink)
  v(0.7mm)
  for item in d.items {
    block(below: 1.8mm, breakable: false)[
      #text(size: 11pt, weight: "bold")[Strana #str(item.page) — #item.heading]
      #v(0.45mm)
      #for line in item.lines {
        text(size: 8.5pt)[• #line]
        linebreak()
      }
    ]
  }
}
