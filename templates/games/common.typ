// Shared helpers for game pages
#import "../base.typ": *

#let game-header(title, difficulty: none, instructions: "") = {
  block(width: 100%, below: 2mm)[
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(size: 13pt, weight: "bold", fill: ink, title),
      if difficulty != none {
        text(size: 7pt, fill: muted, upper(str(difficulty)))
      },
    )
    #v(1mm)
    #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + ink)
    #if instructions != "" {
      v(1.5mm)
      text(size: 7.5pt, fill: muted, instructions)
      v(2mm)
    }
  ]
}

#let difficulty-label(d) = {
  if d == "easy" { "snadné" }
  else if d == "medium" { "střední" }
  else if d == "hard" { "těžké" }
  else { str(d) }
}
