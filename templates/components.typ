// Shared CreoBook UI components — consume theme tokens only.

#import "base.typ": *

#let ruled-lines(spacing-mm, margin-line: false) = {
  layout(size => {
    let avail = size.height
    let spacing = mm(spacing-mm)
    let stroke = mm(theme.lines.rule_width_mm) + rule-color
    let n = calc.max(1, calc.floor(avail / spacing))
    // Margin line measured from page inner edge → convert to content x
    let margin-x = mm(theme.defaults.margin_line_from_inner_mm) - mm(theme.margins.inner_mm)

    box(width: size.width, height: avail)[
      #for i in range(1, n + 1) {
        let y = i * spacing
        if y <= avail {
          place(top + left, dy: y)[
            #line(length: 100%, stroke: stroke)
          ]
        }
      }
      #if margin-line {
        place(top + left, dx: margin-x)[
          #line(
            angle: 90deg,
            length: avail,
            stroke: mm(theme.lines.margin_line_width_mm) + accent,
          )
        ]
      }
    ]
  })
}

#let dot-grid(spacing-mm) = {
  layout(size => {
    let spacing = mm(spacing-mm)
    let cols = calc.max(1, calc.floor(size.width / spacing))
    let rows = calc.max(1, calc.floor(size.height / spacing))
    let diam = mm(theme.lines.dot_diameter_mm)
    box(width: size.width, height: size.height)[
      #for r in range(rows + 1) {
        for c in range(cols + 1) {
          place(
            top + left,
            dx: c * spacing - diam / 2,
            dy: r * spacing - diam / 2,
          )[
            #circle(radius: diam / 2, fill: rule-color, stroke: none)
          ]
        }
      }
    ]
  })
}

#let square-grid(spacing-mm) = {
  layout(size => {
    let spacing = mm(spacing-mm)
    let stroke = mm(theme.lines.grid_width_mm) + rule-color
    let cols = calc.max(1, calc.floor(size.width / spacing))
    let rows = calc.max(1, calc.floor(size.height / spacing))
    let grid-h = rows * spacing
    let grid-w = cols * spacing
    box(width: size.width, height: size.height)[
      #for c in range(cols + 1) {
        place(top + left, dx: c * spacing)[
          #line(angle: 90deg, length: grid-h, stroke: stroke)
        ]
      }
      #for r in range(rows + 1) {
        place(top + left, dy: r * spacing)[
          #line(length: grid-w, stroke: stroke)
        ]
      }
    ]
  })
}

#let checklist-rows(n) = {
  let box-size = mm(theme.lines.checkbox_size_mm)
  let stroke = mm(theme.lines.checkbox_stroke_mm) + muted
  let row-h = mm(theme.defaults.ruled_spacing_mm)
  for i in range(n) {
    block(width: 100%, height: row-h, inset: (bottom: 1mm))[
      #grid(
        columns: (box-size, 3mm, 1fr),
        align: (horizon, horizon, horizon),
        square(size: box-size, stroke: stroke),
        [],
        line(
          length: 100%,
          stroke: mm(theme.lines.rule_width_mm) + rule-color,
        ),
      )
    ]
  }
}
