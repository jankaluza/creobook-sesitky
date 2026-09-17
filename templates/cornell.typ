#import "base.typ": *

#let count = int(data.at("page_count", default: 1))
#let spacing = data.at("spacing_mm", default: theme.defaults.ruled_spacing_mm)
#let cue-w = mm(theme.defaults.cornell_cue_width_mm)
#let summary-h = mm(theme.defaults.cornell_summary_height_mm)
#let rule-stroke = mm(theme.lines.rule_width_mm) + rule-color
#let accent-stroke = mm(theme.lines.margin_line_width_mm) + accent
#let title = data.at("title", default: none)

#let cornell-body() = {
  block(width: 100%, height: 1fr)[
    #layout(size => {
      let notes-h = calc.max(15mm, size.height - summary-h - 8mm)
      block(width: 100%, height: notes-h, clip: true)[
        #grid(
          columns: (cue-w, 1fr),
          column-gutter: 2mm,
          rows: notes-h,
          {
            text(size: 6.5pt, fill: muted, "podněty")
            v(1.5mm)
            layout(cue-size => {
              let n = calc.max(1, calc.floor(cue-size.height / mm(spacing)))
              box(width: 100%, height: cue-size.height)[
                #for i in range(1, n) {
                  place(top + left, dy: i * mm(spacing))[
                    #line(length: 100%, stroke: rule-stroke)
                  ]
                }
              ]
            })
          },
          {
            text(size: 6.5pt, fill: muted, "poznámky")
            v(1.5mm)
            layout(note-size => {
              let n = calc.max(1, calc.floor(note-size.height / mm(spacing)))
              box(width: 100%, height: note-size.height)[
                #place(top + left)[
                  #line(angle: 90deg, length: note-size.height, stroke: accent-stroke)
                ]
                #for i in range(1, n) {
                  place(top + left, dy: i * mm(spacing))[
                    #line(length: 100%, stroke: rule-stroke)
                  ]
                }
              ]
            })
          },
        )
      ]

      v(1.5mm)
      line(length: 100%, stroke: accent-stroke)
      v(1mm)
      text(size: 6.5pt, fill: muted, "shrnutí")
      v(1mm)
      box(width: 100%, height: summary-h, clip: true)[
        #let n = calc.max(1, calc.floor(summary-h / mm(spacing)))
        #for i in range(1, n) {
          place(top + left, dy: i * mm(spacing))[
            #line(length: 100%, stroke: rule-stroke)
          ]
        }
      ]
    })
  ]
}

#show: creobook-page.with(title: title, subtitle: "cornell")

#for page-i in range(count) {
  if page-i > 0 { pagebreak() }
  cornell-body()
}
