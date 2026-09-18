// CreoBook quarterly planner — exactly 28 logical A5 pages.
// Czech labels and calendar data arrive from Python as JSON.

#import "base.typ": *

#let labels = data.labels
#let line-mm = data.at("line_spacing_mm", default: 6.5)
#let qid = data.quarter_id

#let planner-footer() = context {
  block(width: 100%)[
    #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + rule-color)
    #v(1.0mm)
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(size: 6.5pt, fill: light, theme.brand.name + " · Plánovač"),
      text(size: 6.5pt, fill: light, qid),
    )
  ]
}

#let section-title(title) = {
  text(size: 7pt, weight: "bold", fill: ink, tracking: 0.04em, title)
  v(0.8mm)
  line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.1 + accent)
  v(1.0mm)
}

#let writing-lines(n, checkbox: false) = {
  let spacing = mm(line-mm)
  let box-size = mm(theme.lines.checkbox_size_mm)
  let stroke = mm(theme.lines.checkbox_stroke_mm) + ink
  for i in range(n) {
    block(width: 100%, height: spacing, inset: 0pt)[
      #if checkbox {
        grid(
          columns: (box-size, 2mm, 1fr),
          align: (horizon + left, horizon, bottom),
          square(size: box-size, stroke: stroke),
          [],
          line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + rule-color),
        )
      } else {
        align(bottom)[
          #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + rule-color)
        ]
      }
    ]
  }
}

#let mini-calendar(month) = {
  block(width: 100%)[
    #align(center)[#text(size: 7pt, weight: "bold", month.name)]
    #v(0.8mm)
    #grid(
      columns: 7 * (1fr,),
      column-gutter: 0.2mm,
      row-gutter: 0.25mm,
      ..data.weekday_names.map(n => align(center)[
        #text(size: 4.8pt, fill: muted, upper(n))
      ]),
      ..month.weeks.map(week => week.days.map(day => {
        let fill = if not day.in_month {
          adjacent-color
        } else if day.holiday {
          holiday-color
        } else if day.weekend {
          weekend-color
        } else { ink }
        let weight = if day.holiday and day.in_month { "bold" } else { "regular" }
        align(center)[
          #box(width: 3.4mm, height: 3.4mm)[
            #if day.in_month {
              text(size: 5.2pt, fill: fill, weight: weight, str(day.day))
            }
          ]
        ]
      })).flatten(),
    )
  ]
}

#let annotate-days(days) = {
  let first-month = days.at(0).month
  let first-year = days.at(0).year
  let multi = days.any(d => d.month != first-month or d.year != first-year)
  days.map(d => (
    iso: d.iso,
    day: d.day,
    month: d.month,
    year: d.year,
    weekday_name: d.weekday_name,
    month_label: d.month_label,
    in_quarter: d.in_quarter,
    weekend: d.weekend,
    holiday: d.holiday,
    holiday_name: d.holiday_name,
    active: d.active,
    show_month: multi,
  ))
}

#let day-strip(day, lines: 3) = {
  let name-fill = if day.active { ink } else { adjacent-color }
  let num-fill = if day.holiday and day.active {
    holiday-color
  } else if day.weekend and day.active {
    weekend-color
  } else if day.active { ink } else { adjacent-color }
  let label = str(day.day) + "."
  if day.show_month { label = label + " " + day.month_label }
  block(width: 100%, breakable: false, below: 1.2mm)[
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(size: 7pt, weight: "bold", fill: name-fill, upper(day.weekday_name)),
      text(size: 7.5pt, weight: "bold", fill: num-fill, label),
    )
    #if day.holiday and day.active and day.holiday_name != none {
      text(size: 5pt, fill: muted, day.holiday_name)
    }
    #v(0.4mm)
    #if day.active {
      writing-lines(lines)
    } else {
      text(size: 6pt, fill: adjacent-color, "mimo čtvrtletí")
      v(1mm)
      line(length: 100%, stroke: mm(theme.lines.rule_width_mm) + adjacent-color)
    }
  ]
}

#let overview-page() = block(breakable: false, width: 100%)[
  #text(size: 15pt, weight: "bold", data.quarter_name)
  #v(0.8mm)
  #text(size: 8.5pt, fill: muted, data.range_label)
  #v(2.5mm)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 2.5mm,
    ..data.months.map(m => mini-calendar(m)),
  )

  #v(2.5mm)
  #section-title(labels.main_goal_quarter)
  #writing-lines(2)

  #v(2mm)
  #grid(
    columns: (1fr, 1fr),
    column-gutter: 3.5mm,
    {
      section-title(labels.personal_goals)
      writing-lines(4, checkbox: true)
    },
    {
      section-title(labels.work_projects)
      writing-lines(4, checkbox: true)
    },
  )

  #v(2mm)
  #section-title(labels.milestones)
  #writing-lines(3, checkbox: true)

  #v(2mm)
  #section-title(labels.notes)
  #writing-lines(3)
]

#let week-header(week) = {
  grid(
    columns: (1fr, auto),
    align: (left + horizon, right + horizon),
    text(size: 10.5pt, weight: "bold", week.label),
    text(size: 7.5pt, fill: muted, week.range_label),
  )
  v(0.8mm)
  line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.15 + accent)
  v(1.5mm)
  section-title(labels.main_goal_week)
  writing-lines(2)
  v(1.5mm)
}

#let standard-left(week) = block(breakable: false, width: 100%)[
  #let days = annotate-days(week.days)
  #week-header(week)
  #day-strip(days.at(0), lines: 4)
  #day-strip(days.at(1), lines: 4)
  #day-strip(days.at(2), lines: 4)
]

#let standard-right(week) = block(breakable: false, width: 100%)[
  #let days = annotate-days(week.days)
  #day-strip(days.at(3), lines: 4)
  #day-strip(days.at(4), lines: 4)
  #v(0.5mm)
  #grid(
    columns: (1fr, 1fr),
    column-gutter: 3mm,
    day-strip(days.at(5), lines: 2),
    day-strip(days.at(6), lines: 2),
  )
  #v(1.5mm)
  #section-title(labels.tasks_notes)
  #writing-lines(4, checkbox: true)
]

#let boundary-left(spread) = block(breakable: false, width: 100%)[
  #let week = spread.opening
  #let days = annotate-days(week.days)
  #text(size: 7.5pt, weight: "bold", fill: accent, labels.opening_period)
  #v(0.6mm)
  #grid(
    columns: (1fr, auto),
    align: (left + horizon, right + horizon),
    text(size: 10.5pt, weight: "bold", week.label),
    text(size: 7pt, fill: muted, spread.opening_range_label),
  )
  #v(0.6mm)
  #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.15 + accent)
  #v(1.2mm)
  #section-title(labels.main_goal_week)
  #writing-lines(1)
  #v(1mm)
  #for d in days {
    day-strip(d, lines: if d.active { 2 } else { 1 })
  }
]

#let boundary-right(spread) = block(breakable: false, width: 100%)[
  #let week = spread.closing
  #let days = annotate-days(week.days)
  #text(size: 7.5pt, weight: "bold", fill: accent, labels.closing_period)
  #v(0.6mm)
  #grid(
    columns: (1fr, auto),
    align: (left + horizon, right + horizon),
    text(size: 10.5pt, weight: "bold", week.label),
    text(size: 7pt, fill: muted, spread.closing_range_label),
  )
  #v(0.6mm)
  #line(length: 100%, stroke: mm(theme.lines.rule_width_mm) * 1.15 + accent)
  #v(1.2mm)
  #for d in days {
    day-strip(d, lines: if d.active { 2 } else { 1 })
  }
  #v(1mm)
  #section-title(labels.shared_notes)
  #writing-lines(3, checkbox: true)
]

#let transfer-page() = block(breakable: false, width: 100%)[
  #let nq = data.next_quarter
  #text(size: 13pt, weight: "bold", labels.transfer)
  #v(1mm)
  #text(size: 8.5pt, fill: muted, nq.quarter_name + " · " + nq.range_label)
  #v(3mm)

  #section-title(labels.unfinished)
  #writing-lines(4, checkbox: true)
  #v(2.5mm)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 3.5mm,
    {
      section-title(labels.keep)
      writing-lines(5)
    },
    {
      section-title(labels.change)
      writing-lines(5)
    },
  )
  #v(2.5mm)

  #section-title(labels.first_steps)
  #writing-lines(5, checkbox: true)
]

#show: creobook-page.with(
  show-header: false,
  show-footer: true,
  title: data.quarter_name,
)
#set page(footer: planner-footer())

#overview-page()

#for spread in data.spreads {
  pagebreak()
  if spread.kind == "boundary" {
    boundary-left(spread)
    pagebreak()
    boundary-right(spread)
  } else {
    standard-left(spread.week)
    pagebreak()
    standard-right(spread.week)
  }
}

#pagebreak()
#transfer-page()
