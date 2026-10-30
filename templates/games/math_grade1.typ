// Matematika – 1. třída — page renderers (imported from pages.typ)
#import "../base.typ": *
#import "common.typ": game-header

#let box-s = 9mm
#let box-m = 11mm
#let num-size = 15pt
#let instr-size = 10.5pt
#let title-size = 13pt

#let tight-page(body) = {
  set par(leading: 0.85em, spacing: 0.45em)
  set block(spacing: 0.55em)
  body
}

#let answer-box(w: box-s, h: box-s) = {
  box(
    width: w,
    height: h,
    stroke: mm(theme.lines.rule_width_mm) + ink,
    radius: 0.6mm,
  )
}

#let sec-title(t) = {
  v(1.2mm)
  text(size: 10pt, weight: "bold", t)
  v(0.8mm)
}

#let tiny-icon(kind, size: 4.2mm) = {
  let s = size
  if kind == "apple" {
    box(width: s, height: s)[
      #place(center + horizon)[
        #circle(radius: s * 0.32, stroke: 0.45pt + ink, fill: none)
      ]
      #place(top + center, dy: s * 0.05)[
        #line(length: s * 0.18, angle: -70deg, stroke: 0.45pt + ink)
      ]
    ]
  } else if kind == "star" {
    box(width: s, height: s)[
      #place(center + horizon)[
        #polygon(
          fill: none,
          stroke: 0.45pt + ink,
          (s * 0.5, 0pt),
          (s * 0.62, s * 0.38),
          (s, s * 0.38),
          (s * 0.7, s * 0.62),
          (s * 0.82, s),
          (s * 0.5, s * 0.75),
          (s * 0.18, s),
          (s * 0.3, s * 0.62),
          (0pt, s * 0.38),
          (s * 0.38, s * 0.38),
        )
      ]
    ]
  } else if kind == "ball" {
    circle(radius: s * 0.34, stroke: 0.5pt + ink, fill: none)
  } else if kind == "block" {
    rect(width: s * 0.62, height: s * 0.62, stroke: 0.5pt + ink, fill: none)
  } else if kind == "flower" {
    box(width: s, height: s)[
      #place(center + horizon)[#circle(radius: s * 0.16, stroke: 0.4pt + ink)]
      #place(center + horizon, dy: -s * 0.22)[#circle(radius: s * 0.12, stroke: 0.35pt + ink)]
      #place(center + horizon, dy: s * 0.22)[#circle(radius: s * 0.12, stroke: 0.35pt + ink)]
      #place(center + horizon, dx: -s * 0.22)[#circle(radius: s * 0.12, stroke: 0.35pt + ink)]
      #place(center + horizon, dx: s * 0.22)[#circle(radius: s * 0.12, stroke: 0.35pt + ink)]
    ]
  } else if kind == "fish" {
    box(width: s * 1.1, height: s)[
      #place(center + horizon, dx: -0.3mm)[
        #ellipse(width: s * 0.7, height: s * 0.45, stroke: 0.45pt + ink)
      ]
      #place(right + horizon)[
        #polygon(
          fill: none,
          stroke: 0.45pt + ink,
          (0pt, 0pt),
          (s * 0.28, -s * 0.2),
          (s * 0.28, s * 0.2),
        )
      ]
    ]
  } else if kind == "heart" {
    box(width: s, height: s)[
      #place(center + horizon, dx: -s * 0.12, dy: -s * 0.08)[
        #circle(radius: s * 0.18, stroke: 0.4pt + ink)
      ]
      #place(center + horizon, dx: s * 0.12, dy: -s * 0.08)[
        #circle(radius: s * 0.18, stroke: 0.4pt + ink)
      ]
      #place(center + horizon, dy: s * 0.08)[
        #polygon(
          fill: none,
          stroke: 0.4pt + ink,
          (-s * 0.28, 0pt),
          (0pt, s * 0.35),
          (s * 0.28, 0pt),
        )
      ]
    ]
  } else if kind == "leaf" {
    box(width: s, height: s)[
      #place(center + horizon)[
        #ellipse(width: s * 0.45, height: s * 0.7, stroke: 0.45pt + ink)
      ]
      #place(center + horizon)[
        #line(length: s * 0.55, angle: 90deg, stroke: 0.4pt + ink)
      ]
    ]
  } else {
    circle(radius: s * 0.3, stroke: 0.45pt + ink)
  }
}

#let icon-row(kind, count, size: 4.0mm, gap: 0.7mm) = {
  if count == 0 {
    text(size: 8pt, fill: muted, "(prázdné)")
  } else {
    // Keep icons on one horizontal line (no wrapping).
    box(width: count * (size + gap), height: size + 0.5mm)[
      #for i in range(count) {
        place(dx: i * (size + gap), dy: 0mm)[#tiny-icon(kind, size: size)]
      }
    ]
  }
}

#let calc-item(a, op, b) = {
  text(size: num-size)[
    #str(a) #h(1mm) #op #h(1mm) #str(b) #h(1.5mm) = #h(1.5mm) #answer-box()
  ]
}

#let render-math-name-field() = {
  grid(
    columns: (auto, 1fr),
    column-gutter: 2mm,
    align: (left + horizon, left + horizon),
    text(size: 10pt, weight: "bold", "Jméno:"),
    box(
      width: 100%,
      stroke: (bottom: mm(theme.lines.rule_width_mm) + ink),
      inset: (bottom: 0.6mm),
      height: 4.5mm,
      [],
    ),
  )
}

#let math-page-header(d) = {
  if "show_name_field" in d.keys() and d.show_name_field {
    text(size: 13pt, weight: "bold", d.booklet_title)
    h(3mm)
    text(size: 11pt, weight: "bold", d.heading)
    v(1mm)
    render-math-name-field()
  } else {
    text(size: title-size, weight: "bold", d.heading)
    if "heading_note" in d.keys() and d.heading_note != "" {
      h(2mm)
      text(size: 9pt, fill: muted, d.heading_note)
    }
  }
  v(0.6mm)
}

#let render-math-page1(page) = {
  let d = page.data
  math-page-header(d)

  let sec = d.sections.at(0)
  sec-title(sec.title + " — " + sec.instruction)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 2mm,
    row-gutter: 1.4mm,
    ..sec.groups.map(g => {
      box(
        width: 100%,
        stroke: mm(theme.lines.rule_width_mm) * 0.8 + ink,
        inset: 1.2mm,
      )[
        #icon-row(g.kind, g.count, size: 3.4mm, gap: 0.4mm)
        #h(2mm)
        #answer-box(w: 8.5mm, h: 8.5mm)
      ]
    }),
  )

  let sec2 = d.sections.at(1)
  sec-title(sec2.title)
  for it in sec2.items {
    block(below: 1mm)[
      #text(size: 10pt, weight: "bold", it.instruction)
      #h(2mm)
      #icon-row(it.kind, it.have, size: 3.3mm)
      #h(1mm)
      #text(size: 8pt, fill: muted, "…")
    ]
  }

  let sec3 = d.sections.at(2)
  sec-title(sec3.title)
  for seq in sec3.sequences {
    block(below: 1.1mm)[
      #for (i, v) in seq.values.enumerate() {
        if v == none {
          box(baseline: 30%)[#answer-box(w: 8mm, h: 8mm)]
        } else {
          text(size: 14pt, str(v))
        }
        if i + 1 < seq.values.len() {
          h(1.2mm)
          text(size: 10pt, fill: muted, "–")
          h(1.2mm)
        }
      }
    ]
  }

  let sec4 = d.sections.at(3)
  sec-title(sec4.title)
  text(size: 9.5pt, sec4.tasks.map(t => t.text).join(" · "))
  v(1mm)
  align(center)[
    #for (i, k) in sec4.icons.enumerate() {
      box(inset: 0.6mm)[#tiny-icon(k, size: 4.8mm)]
      if i + 1 < sec4.icons.len() { h(1.8mm) }
    }
  ]
}

#let decomp-branch(n, left, right, example: false) = {
  let cell(v) = {
    if v == none {
      answer-box(w: 8mm, h: 8mm)
    } else {
      box(
        width: 8mm,
        height: 8mm,
        stroke: mm(theme.lines.rule_width_mm) + ink,
        align(center + horizon)[#text(size: 11pt, weight: "bold", str(v))],
      )
    }
  }
  block(breakable: false)[
    #align(center)[
      #cell(n)
      #v(0.4mm)
      #text(size: 8pt, "↙    ↘")
      #v(0.3mm)
      #grid(
        columns: 2,
        column-gutter: 2.5mm,
        cell(left),
        cell(right),
      )
      #if example {
        v(0.3mm)
        text(size: 6.5pt, fill: muted, "příklad")
      }
    ]
  ]
}

#let render-math-page2(page) = {
  let d = page.data
  math-page-header(d)

  let s1 = d.sections.at(0)
  sec-title(s1.title)
  for pair in s1.pairs {
    text(size: 9pt, pair.prompt)
    v(0.6mm)
    grid(
      columns: (1fr, 1fr, auto),
      column-gutter: 2mm,
      box(width: 100%, stroke: 0.35pt + ink, inset: 1.2mm)[
        #icon-row(pair.left.kind, pair.left.count, size: 3.2mm, gap: 0.4mm)
      ],
      box(width: 100%, stroke: 0.35pt + ink, inset: 1.2mm)[
        #icon-row(pair.right.kind, pair.right.count, size: 3.2mm, gap: 0.4mm)
      ],
      if pair.at("same", default: false) {
        text(size: 9pt)[ano #answer-box(w: 6.5mm, h: 6.5mm)\ ne #answer-box(w: 6.5mm, h: 6.5mm)]
      } else { [] },
    )
    v(1mm)
  }

  let s2 = d.sections.at(1)
  sec-title(s2.title)
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 2mm,
    row-gutter: 1.4mm,
    ..s2.items.map(it => {
      text(size: 14pt)[
        #str(it.a) #h(0.8mm) #answer-box(w: 7.5mm, h: 7.5mm) #h(0.8mm) #str(it.b)
      ]
    }),
  )

  let s3 = d.sections.at(2)
  sec-title(s3.title)
  text(size: 8pt, fill: muted, s3.instruction)
  v(1mm)
  grid(
    columns: (1fr,) * s3.items.len(),
    column-gutter: 1.2mm,
    ..s3.items.map(it => {
      decomp-branch(
        it.n,
        it.left,
        it.right,
        example: it.at("example", default: false),
      )
    }),
  )

  let s4 = d.sections.at(3)
  sec-title(s4.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    row-gutter: 1.4mm,
    ..s4.items.map(it => {
      text(size: 14pt)[
        #str(it.a) + #answer-box(w: 9mm, h: 9mm) = 10
      ]
    }),
  )

  let s5 = d.sections.at(4)
  sec-title(s5.title)
  text(size: 10pt)[Čísla: #s5.numbers.map(str).join(", ")#h(3mm)]
  for i in range(4) {
    answer-box(w: 9mm, h: 8.5mm)
    if i < 3 {
      h(1mm)
      text(size: 11pt, "<")
      h(1mm)
    }
  }
}

#let render-math-page3(page) = {
  let d = page.data
  math-page-header(d)
  v(1.4mm)

  let s1 = d.sections.at(0)
  sec-title(s1.title)
  for it in s1.items {
    block(below: 2.5mm)[
      #icon-row(it.left.kind, it.left.count)
      #h(2mm)#text(size: 14pt, "+")#h(2mm)
      #icon-row(it.right.kind, it.right.count)
      #h(3mm)
      #text(size: num-size)[
        #answer-box() + #answer-box() = #answer-box()
      ]
    ]
  }

  let s2 = d.sections.at(1)
  sec-title(s2.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 4mm,
    row-gutter: 2.2mm,
    ..s2.items.map(it => calc-item(it.a, "+", it.b)),
  )

  v(1.4mm)
  let s3 = d.sections.at(2)
  sec-title(s3.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 4mm,
    row-gutter: 2.2mm,
    ..s3.items.map(it => {
      text(size: num-size)[
        #str(it.a) + #answer-box() = #str(it.total)
      ]
    }),
  )

  v(1.4mm)
  let s4 = d.sections.at(3)
  sec-title(s4.title)
  for (i, it) in s4.items.enumerate() {
    block(below: 2.5mm)[
      #text(size: instr-size)[#str(i + 1). #it.text]
      #v(1.2mm)
      #text(size: 10pt, fill: muted, "Výpočet:")
      #h(1mm)#box(width: 35mm, stroke: (bottom: 0.4pt + ink), height: 5mm)[]
      #h(3mm)
      #text(size: 10pt, fill: muted, "Výsledek:")
      #h(1mm)#answer-box(w: box-m)
    ]
  }
}

#let render-math-page4(page) = {
  let d = page.data
  math-page-header(d)
  v(1.4mm)

  let s1 = d.sections.at(0)
  sec-title(s1.title)
  for it in s1.items {
    block(below: 2.5mm)[
      #text(size: 9.5pt, it.instruction)
      #v(1mm)
      #icon-row(it.icons.kind, it.icons.count, size: 5mm, gap: 1.2mm)
      #h(4mm)
      #text(size: 10pt, fill: muted, "Zbývá:")
      #h(1mm)#answer-box()
    ]
  }

  let s2 = d.sections.at(1)
  sec-title(s2.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 4mm,
    row-gutter: 2.2mm,
    ..s2.items.map(it => calc-item(it.a, "−", it.b)),
  )

  v(1.4mm)
  let s3 = d.sections.at(2)
  sec-title(s3.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 4mm,
    row-gutter: 2.2mm,
    ..s3.items.map(it => {
      if it.form == "a-x=r" {
        text(size: num-size)[
          #str(it.a) − #answer-box() = #str(it.result)
        ]
      } else {
        text(size: num-size)[
          #answer-box() − #str(it.b) = #str(it.result)
        ]
      }
    }),
  )

  v(1.4mm)
  let s4 = d.sections.at(3)
  sec-title(s4.title)
  for (i, it) in s4.items.enumerate() {
    block(below: 2.5mm)[
      #text(size: instr-size)[#str(i + 1). #it.text]
      #v(1.2mm)
      #text(size: 10pt, fill: muted, "Výpočet:")
      #h(1mm)#box(width: 35mm, stroke: (bottom: 0.4pt + ink), height: 5mm)[]
      #h(3mm)
      #text(size: 10pt, fill: muted, "Výsledek:")
      #h(1mm)#answer-box(w: box-m)
    ]
  }
}

#let ten-dots() = {
  let cell = 3.2mm
  grid(
    columns: 5,
    rows: 2,
    column-gutter: 0.8mm,
    row-gutter: 0.8mm,
    ..range(10).map(_ => circle(radius: cell * 0.35, stroke: 0.45pt + ink, fill: none)),
  )
}

#let render-math-page5(page) = {
  let d = page.data
  math-page-header(d)

  let s1 = d.sections.at(0)
  sec-title(s1.title)
  for seq in s1.sequences {
    block(below: 1.1mm)[
      #for (i, v) in seq.values.enumerate() {
        if v == none {
          box(baseline: 30%)[#answer-box(w: 7.5mm, h: 7.5mm)]
        } else {
          text(size: 13pt, str(v))
        }
        if i + 1 < seq.values.len() {
          h(1.1mm)
          text(size: 10pt, fill: muted, "–")
          h(1.1mm)
        }
      }
    ]
  }

  let s2 = d.sections.at(1)
  sec-title(s2.title + " — " + s2.instruction)
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 2mm,
    row-gutter: 1.2mm,
    ..s2.items.map(it => {
      text(size: 12pt)[
        #answer-box(w: 8mm, h: 8mm) #h(1mm)
        #box(
          width: 10mm,
          height: 8mm,
          stroke: mm(theme.lines.rule_width_mm) + ink,
          fill: luma(92%),
          align(center + horizon)[#text(size: 12pt, weight: "bold", str(it.n))],
        )
        #h(1mm)#answer-box(w: 8mm, h: 8mm)
      ]
    }),
  )

  let s3 = d.sections.at(2)
  sec-title(s3.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 2mm,
    row-gutter: 1.2mm,
    ..s3.items.map(it => {
      text(size: 13pt)[
        #str(it.a) #answer-box(w: 7.5mm, h: 7.5mm) #str(it.b)
      ]
    }),
  )

  let s4 = d.sections.at(3)
  sec-title(s4.title)
  text(size: 8pt, fill: muted, s4.instruction)
  v(0.8mm)
  grid(
    columns: (auto, 1fr),
    column-gutter: 2.5mm,
    ten-dots(),
    {
      for it in s4.items {
        block(below: 1mm)[
          #text(size: 14pt)[
            #str(it.n) = 10 + #answer-box(w: 9mm, h: 9mm)
          ]
        ]
      }
    },
  )

  let s5 = d.sections.at(4)
  sec-title(s5.title)
  let w = 118mm
  let n = 20
  let step = w / n
  box(width: w, height: 11mm)[
    #place(dy: 3.5mm)[
      #line(length: w, stroke: 0.65pt + ink)
    ]
    #for i in range(n + 1) {
      let x = i * step
      place(dx: x, dy: 2.2mm)[
        #line(length: 2.5mm, angle: 90deg, stroke: 0.5pt + ink)
      ]
      if s5.missing.contains(i) {
        place(dx: x - 3mm, dy: 6.2mm)[
          #box(width: 6mm, height: 4.5mm, stroke: 0.4pt + ink)
        ]
      } else if i == 0 or i == 10 or i == 20 or calc.rem(i, 5) == 0 {
        place(dx: x - 2mm, dy: 6.4mm)[
          #text(size: 6.5pt, str(i))
        ]
      } else {
        place(dx: x - 1.6mm, dy: 6.4mm)[
          #text(size: 6pt, str(i))
        ]
      }
    }
  ]
}

#let pyramid(item) = {
  let cell(v) = {
    if v == none {
      answer-box(w: 10mm, h: 9mm)
    } else {
      box(
        width: 10mm,
        height: 9mm,
        stroke: 0.5pt + ink,
        align(center + horizon)[#text(size: 13pt, weight: "bold", str(v))],
      )
    }
  }
  block(breakable: false)[
    #align(center)[
      #cell(item.top)
      #v(1mm)
      #grid(columns: 2, column-gutter: 3mm, cell(item.bottom.at(0)), cell(item.bottom.at(1)))
      #if item.at("example", default: false) {
        v(0.5mm)
        text(size: 7pt, fill: muted, "příklad")
      }
    ]
  ]
}

#let render-math-page6(page) = {
  let d = page.data
  math-page-header(d)
  v(1.1mm)

  let s1 = d.sections.at(0)
  sec-title(s1.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    row-gutter: 2mm,
    ..s1.items.map(it => calc-item(it.a, if it.op == "+" { "+" } else { "−" }, it.b)),
  )

  v(1.1mm)
  let s2 = d.sections.at(1)
  sec-title(s2.title)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    row-gutter: 2mm,
    ..s2.items.map(it => {
      text(size: num-size)[
        #str(it.a) + #answer-box() = #str(it.total)
      ]
    }),
  )

  v(1.1mm)
  let s3 = d.sections.at(2)
  sec-title(s3.title)
  text(size: 8.5pt, fill: muted, s3.instruction)
  v(1.2mm)
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 3mm,
    ..s3.items.map(pyramid),
  )

  v(1.4mm)
  let s4 = d.sections.at(3)
  box(
    width: 100%,
    stroke: 0.7pt + ink,
    inset: 2.5mm,
    radius: 1mm,
  )[
    #text(size: 11pt, weight: "bold", s4.title)
    #v(1mm)
    #text(size: 8.5pt, s4.instruction)
    #v(1.5mm)
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 3mm,
      row-gutter: 2mm,
      ..s4.items.map(it => calc-item(it.a, if it.op == "+" { "+" } else { "−" }, it.b)),
    )
  ]
}

#let coin(val) = {
  box(
    width: 9mm,
    height: 9mm,
    stroke: 0.7pt + ink,
    radius: 50%,
    align(center + horizon)[#text(size: 8pt, weight: "bold", str(val))],
  )
}

#let clock-face(hour) = {
  let r = 8mm
  box(width: 2 * r, height: 2 * r)[
    #place(center + horizon)[#circle(radius: r, stroke: 0.6pt + ink)]
    // hour hand roughly
    #let angle = (hour * 30deg) - 90deg
    #place(center + horizon)[
      #line(
        length: r * 0.55,
        angle: angle,
        stroke: 0.9pt + ink,
      )
    ]
    #place(center + horizon)[
      #circle(radius: 0.6mm, fill: ink, stroke: none)
    ]
  ]
}

#let render-math-page7(page) = {
  let d = page.data
  math-page-header(d)
  v(1.1mm)

  let s1 = d.sections.at(0)
  sec-title(s1.title)
  for (i, it) in s1.items.enumerate() {
    block(below: 2mm)[
      #text(size: 10pt)[#str(i + 1). #it.text]
      #v(1mm)
      #text(size: 9pt, fill: muted, "Výpočet:")
      #box(width: 30mm, stroke: (bottom: 0.4pt + ink), height: 4.5mm)[]
      #h(2mm)
      #text(size: 9pt, fill: muted, "Výsledek:")
      #answer-box(w: box-m, h: 8.5mm)
    ]
  }

  let s2 = d.sections.at(1)
  sec-title(s2.title)
  text(size: 8.5pt, fill: muted, s2.instruction)
  v(1.2mm)
  for it in s2.items {
    block(below: 2mm)[
      #for (i, c) in it.coins.enumerate() {
        coin(c)
        if i + 1 < it.coins.len() { h(1.5mm) }
      }
      #h(4mm)
      #text(size: 11pt, "= ")
      #answer-box(w: box-m)
      #h(1mm)#text(size: 10pt, "Kč")
    ]
  }

  let s3 = d.sections.at(2)
  sec-title(s3.title)
  let t = s3.table
  table(
    columns: 3,
    stroke: 0.45pt + ink,
    inset: 2mm,
    align: center,
    ..t.headers.map(h => text(weight: "bold", h)),
    ..t.values.map(v => text(size: 14pt, str(v))),
  )
  v(1.2mm)
  for q in t.questions {
    block(below: 1.5mm)[
      #text(size: 10pt, q.text)
      #h(2mm)#answer-box(w: box-m)
    ]
  }

  v(1.5mm)
  let s4 = d.sections.at(3)
  sec-title(s4.title)
  text(size: 9.5pt, s4.instruction)
  v(1.5mm)
  grid(
    columns: (1fr, 1fr, 1fr, auto),
    column-gutter: 3mm,
    align: center + horizon,
    ..s4.clocks.map(c => clock-face(c.hour)),
    box(
      stroke: 0.5pt + ink,
      inset: 2mm,
      text(size: 11pt, weight: "bold", s4.label),
    ),
  )
  v(1mm)
  text(size: 8pt, fill: muted, "Spoj čarou správné hodiny s nápisem.")
}

#let shape-draw(id) = {
  if id == "circle" {
    circle(radius: 5mm, stroke: 0.7pt + ink)
  } else if id == "square" {
    rect(width: 10mm, height: 10mm, stroke: 0.7pt + ink)
  } else if id == "rectangle" {
    rect(width: 14mm, height: 8mm, stroke: 0.7pt + ink)
  } else if id == "triangle" {
    polygon(fill: none, stroke: 0.7pt + ink, (0mm, 10mm), (5mm, 0mm), (10mm, 10mm))
  } else if id == "sphere" {
    circle(radius: 5mm, stroke: 0.7pt + ink)
  } else if id == "cube" {
    box(width: 12mm, height: 11mm)[
      #place(dx: 0mm, dy: 2mm)[#rect(width: 8mm, height: 8mm, stroke: 0.6pt + ink)]
      #place(dx: 2.5mm, dy: 0mm)[
        #polygon(fill: none, stroke: 0.6pt + ink, (0mm, 2mm), (3mm, 0mm), (11mm, 0mm), (8mm, 2mm))
      ]
      #place(dx: 8mm, dy: 2mm)[
        #polygon(fill: none, stroke: 0.6pt + ink, (0mm, 0mm), (3mm, -2mm), (3mm, 6mm), (0mm, 8mm))
      ]
    ]
  } else if id == "cuboid" {
    box(width: 16mm, height: 10mm)[
      #place(dx: 0mm, dy: 2.5mm)[#rect(width: 12mm, height: 6.5mm, stroke: 0.6pt + ink)]
      #place(dx: 2mm, dy: 0mm)[
        #polygon(fill: none, stroke: 0.6pt + ink, (0mm, 2.5mm), (3mm, 0mm), (15mm, 0mm), (12mm, 2.5mm))
      ]
    ]
  }
}

#let pattern-icon(id) = {
  if id == "circle" { circle(radius: 2.8mm, stroke: 0.55pt + ink) }
  else if id == "triangle" {
    polygon(fill: none, stroke: 0.55pt + ink, (0mm, 5.5mm), (2.8mm, 0mm), (5.6mm, 5.5mm))
  } else {
    rect(width: 5.2mm, height: 5.2mm, stroke: 0.55pt + ink)
  }
}

#let render-math-page8(page) = {
  let d = page.data
  math-page-header(d)

  let s1 = d.sections.at(0)
  sec-title(s1.title + " — Spoj tvar s názvem")
  grid(
    columns: (auto, auto, auto, auto, 1fr),
    column-gutter: 2mm,
    row-gutter: 1.2mm,
    ..{
      let cells = ()
      for s in s1.shapes {
        cells.push(box(width: 14mm, height: 10mm, align(center + horizon)[#shape-draw(s.id)]))
      }
      cells.push([])
      for name in s1.names {
        cells.push(
          box(width: 100%, stroke: 0.4pt + ink, inset: 1mm, text(size: 9pt, name))
        )
      }
      cells
    },
  )

  let s2 = d.sections.at(1)
  sec-title(s2.title)
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 2mm,
    ..s2.items.map(it => {
      align(center)[
        #shape-draw(it.id)
        #v(0.4mm)
        #text(size: 7.5pt, it.object + " → " + it.name)
      ]
    }),
  )

  let s3 = d.sections.at(2)
  sec-title(s3.title)
  text(size: 8.5pt, s3.scene.tasks.map(t => t.text).join(" · "))
  v(0.8mm)
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 2mm,
    ..s3.scene.items.map(it => {
      align(center)[
        #box(width: 20mm, height: 11mm, stroke: 0.4pt + ink, inset: 0.8mm)[
          #align(center + horizon)[
            #if it.id == "ball" {
              circle(radius: 3.2mm, stroke: 0.5pt + ink)
            } else if it.id == "book" {
              rect(width: 9mm, height: 6mm, stroke: 0.5pt + ink)
            } else {
              ellipse(width: 7mm, height: 8mm, stroke: 0.5pt + ink)
            }
          ]
        ]
        #v(0.3mm)
        #text(size: 7.5pt, it.label)
      ]
    }),
  )

  let s4 = d.sections.at(3)
  sec-title(s4.title)
  line(length: s4.short_mm * 1mm, stroke: 1pt + ink)
  v(1mm)
  line(length: s4.long_mm * 1mm, stroke: 1pt + ink)

  let s5 = d.sections.at(4)
  sec-title(s5.title)
  for it in s5.items {
    block(below: 1.1mm)[
      #for (i, p) in it.shown.enumerate() {
        box(inset: 0.4mm)[#pattern-icon(p)]
        h(0.7mm)
      }
      #text(size: 11pt, "→")
      #h(0.7mm)
      #for _ in it.next {
        box(inset: 0.4mm)[
          #box(width: 5.5mm, height: 5.5mm, stroke: 0.4pt + ink)
        ]
        h(0.7mm)
      }
    ]
  }

  let s6 = d.sections.at(5)
  sec-title(s6.title + " — " + s6.grid.instruction)
  let cell = 4.8mm
  let g = s6.grid.pattern
  grid(
    columns: 2,
    column-gutter: 6mm,
    table(
      columns: 3 * (cell,),
      rows: 3 * (cell,),
      stroke: 0.4pt + ink,
      inset: 0pt,
      ..{
        let cells = ()
        for row in g {
          for v in row {
            cells.push(if v == 1 { box(width: 100%, height: 100%, fill: ink) } else { [] })
          }
        }
        cells
      },
    ),
    table(
      columns: 3 * (cell,),
      rows: 3 * (cell,),
      stroke: 0.4pt + ink,
      inset: 0pt,
      ..range(9).map(_ => []),
    ),
  )
}

#let render-math-grade1(page) = {
  let topic = if "topic" in page.data.keys() { page.data.topic } else { page.data.page }
  let body = if topic == 1 { render-math-page1(page) }
    else if topic == 2 { render-math-page2(page) }
    else if topic == 3 { render-math-page3(page) }
    else if topic == 4 { render-math-page4(page) }
    else if topic == 5 { render-math-page5(page) }
    else if topic == 6 { render-math-page6(page) }
    else if topic == 7 { render-math-page7(page) }
    else if topic == 8 { render-math-page8(page) }
    else { text("Neznámé téma: " + str(topic)) }
  tight-page(body)
}

#let render-math-grade1-answers(page) = {
  let d = page.data
  text(size: 14pt, weight: "bold", page.title)
  v(1mm)
  text(size: 9pt, fill: muted, page.instructions)
  v(1mm)
  text(size: 8pt, fill: muted)[
    Vydání: #d.edition_date · část #str(d.part)/#str(d.parts)
  ]
  v(1.1mm)
  line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + ink)
  v(1.1mm)
  for item in d.items {
    block(below: 2.5mm, breakable: false)[
      #text(size: 11pt, weight: "bold")[
        Strana #str(item.page) — #item.heading
      ]
      #v(1mm)
      for line in item.lines {
        text(size: 8.5pt)[• #line]
        v(0.7mm)
      }
    ]
  }
}
