#import "base.typ": *

#let year = data.year
#let weekday-names = data.weekday_names
#let months = data.months

#let day-fill(day) = {
  if not day.in_month {
    adjacent-color
  } else if day.holiday {
    holiday-color
  } else if day.weekend {
    weekend-color
  } else {
    ink
  }
}

#let day-weight(day) = {
  if day.holiday and day.in_month { "bold" } else { "regular" }
}

#let month-page(month-data) = {
  let col-gutter = 1.0mm
  let week-label-w = 6.5mm
  let cols = (week-label-w, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr)

  // Fixed header block
  block(width: 100%, below: 2mm)[
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(size: 15pt, weight: "bold", fill: ink, month-data.name),
      text(size: 10pt, fill: muted, str(month-data.year)),
    )
    #v(1.5mm)
    #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.4 + accent)
  ]

  block(width: 100%, below: 1mm)[
    #grid(
      columns: cols,
      column-gutter: col-gutter,
      align: center,
      text(size: 6pt, fill: light, "týd"),
      ..weekday-names.enumerate().map(((i, name)) => {
        let fill = if i >= 5 { weekend-color } else { muted }
        text(size: 7pt, weight: "bold", fill: fill, upper(name))
      }),
    )
  ]

  line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + rule-color)
  v(1mm)

  // Remaining page height → exactly six week rows
  block(width: 100%, height: 1fr)[
    #layout(size => {
      let row-h = size.height / 6
      for week in month-data.weeks {
        block(
          width: 100%,
          height: row-h,
          clip: true,
          inset: (x: 0.2mm, y: 0.4mm),
        )[
          #grid(
            columns: cols,
            column-gutter: col-gutter,
            rows: (row-h - 1mm,),
            align: (center + top, left + top, left + top, left + top, left + top, left + top, left + top, left + top),
            text(size: 6pt, fill: light, str(week.iso_week)),
            ..week.days.map(day => {
              let bg = if day.holiday and day.in_month {
                rgb(theme.colors.holiday_bg)
              } else if day.weekend and day.in_month {
                rgb(theme.colors.weekend_bg)
              } else {
                none
              }
              block(
                width: 100%,
                height: 100%,
                inset: (x: 0.6mm, y: 0.5mm),
                fill: bg,
                radius: 0.3mm,
                clip: true,
              )[
                #text(
                  size: 9pt,
                  weight: day-weight(day),
                  fill: day-fill(day),
                  str(day.day),
                )
                #if day.holiday and day.in_month {
                  h(0.8mm)
                  text(size: 5.5pt, fill: accent, "★")
                }
              ]
            }),
          )
          #place(bottom + left)[
            #line(
              length: 100%,
              stroke: mm(theme.lines.rule_width_mm) * 0.7 + rule-color,
            )
          ]
        ]
      }
    })
  ]
}

#show: creobook-page.with(show-header: false, show-footer: true)

#for (i, month-data) in months.enumerate() {
  if i > 0 { pagebreak() }
  month-page(month-data)
}
