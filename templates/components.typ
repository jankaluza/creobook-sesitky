// Shared CreoBook UI components — consume theme tokens only.

#import "base.typ": *

#let ruled-lines(spacing-mm, margin-line: false) = {
  layout(size => {
    let avail = size.height
    let spacing = mm(spacing-mm)
    let stroke = mm(theme.lines.rule_width_mm) + rule-color
    // Exact spacing steps only. A line at y = i * spacing is drawn only when
    // a full spacing band fits below it as well — so the last line is never
    // squeezed against the footer, and every gap is exactly `spacing`.
    let n = calc.max(0, calc.floor((avail - spacing) / spacing))
    // Margin line measured from page inner edge → convert to content x
    let margin-x = mm(theme.defaults.margin_line_from_inner_mm) - mm(theme.margins.inner_mm)

    box(width: size.width, height: avail)[
      #for i in range(1, n + 1) {
        let y = i * spacing
        place(top + left, dy: y)[
          #line(length: 100%, stroke: stroke)
        ]
      }
      #if margin-line {
        place(top + left, dx: margin-x)[
          #line(
            angle: 90deg,
            length: avail,
            stroke: mm(theme.lines.margin_line_width_mm) + rule-color,
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
            #circle(radius: diam / 2, fill: ink, stroke: none)
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
  let stroke = mm(theme.lines.checkbox_stroke_mm) + ink
  let row-h = mm(theme.defaults.ruled_spacing_mm)
  let gap = 3mm
  // Checkbox centered in the writing band above each rule so each box
  // clearly belongs to the line beneath it.
  layout(size => {
    // Same fitting rule as ruled-lines: only full row-h steps, with a
    // full row of clearance below the last line.
    let n-fit = calc.min(
      n,
      calc.max(0, calc.floor((size.height - row-h) / row-h)),
    )
    let line-w = size.width - box-size - gap
    box(width: size.width, height: size.height)[
      #for i in range(1, n-fit + 1) {
        let y = i * row-h
        place(
          top + left,
          dy: y - row-h / 2 - box-size / 2,
        )[
          #square(size: box-size, stroke: stroke)
        ]
        place(top + left, dx: box-size + gap, dy: y)[
          #line(
            length: line-w,
            stroke: mm(theme.lines.rule_width_mm) + rule-color,
          )
        ]
      }
    ]
  })
}
