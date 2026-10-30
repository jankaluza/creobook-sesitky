#import "theme.typ": *

// ---------- icons (pure vector) ----------

#let icon-star(size: 4mm, fill: color-accent) = {
  box(width: size, height: size, {
    place(center + horizon, polygon(
      fill: fill.transparentize(55%),
      stroke: 0.5pt + fill,
      (50%, 0%), (61%, 35%), (100%, 38%), (70%, 62%),
      (79%, 100%), (50%, 78%), (21%, 100%), (30%, 62%),
      (0%, 38%), (39%, 35%),
    ))
  })
}

#let icon-circle(size: 3.5mm, fill: color-panel, stroke: stroke-mid) = {
  circle(radius: size / 2, fill: fill, stroke: stroke)
}

#let icon-sun(size: 5mm) = {
  box(width: size, height: size, {
    let r = size * 0.22
    place(center + horizon, circle(radius: r, fill: none, stroke: stroke-accent))
    for i in range(8) {
      place(center + horizon, rotate(i * 45deg, line(
        length: size * 0.42,
        stroke: 0.55pt + color-accent,
      )))
    }
  })
}

#let icon-moon(size: 5mm) = {
  box(width: size, height: size, {
    place(center + horizon, {
      circle(radius: size * 0.32, fill: none, stroke: stroke-ink)
      place(dx: size * 0.12, dy: -size * 0.06, circle(
        radius: size * 0.26,
        fill: color-white,
        stroke: none,
      ))
    })
  })
}

#let icon-bag(size: 5mm) = {
  box(width: size, height: size, {
    place(center + horizon, rect(
      width: size * 0.62,
      height: size * 0.5,
      radius: 0.6mm,
      fill: none,
      stroke: stroke-ink,
    ))
    place(center + horizon, dy: -size * 0.22, path(
      stroke: stroke-ink,
      ((20%, 45%), (0%, 0%)),
      ((50%, 28%), (0%, 0%)),
      ((80%, 45%), (0%, 0%)),
    ))
  })
}

#let icon-check(size: 4mm) = {
  box(width: size, height: size, {
    place(center + horizon, path(
      stroke: 0.9pt + color-accent,
      ((18%, 52%), (0%, 0%)),
      ((42%, 78%), (0%, 0%)),
      ((82%, 22%), (0%, 0%)),
    ))
  })
}

// ---------- basics ----------

#let page-title(title, icon: none) = {
  block(width: 100%, below: 2mm, {
    grid(
      columns: if icon == none { (1fr,) } else { (auto, 1fr) },
      column-gutter: 2mm,
      align: horizon,
      if icon != none { icon },
      text(size: size-title, weight: "bold", fill: color-ink, title),
    )
    v(0.8mm)
    line(length: 100%, stroke: 1pt + color-accent.transparentize(25%))
  })
}

#let section-heading(title) = {
  block(below: 1.2mm, above: 0.2mm, {
    text(size: size-heading, weight: "bold", fill: color-ink, title)
  })
}

#let instruction(body) = {
  block(below: 1.8mm, {
    text(size: size-body, fill: color-muted, style: "italic", body)
  })
}

#let rounded-panel(body, fill: color-panel, inset: 2.5mm, height: auto) = {
  block(
    width: 100%,
    height: height,
    fill: fill,
    stroke: stroke-mid,
    radius: panel-radius,
    inset: inset,
    body,
  )
}

#let soft-box(body, height: auto, inset: 2mm) = {
  block(
    width: 100%,
    height: height,
    fill: color-soft,
    stroke: stroke-thin,
    radius: 2mm,
    inset: inset,
    body,
  )
}

#let labeled-field(label, width: 100%) = {
  block(width: width, {
    grid(
      columns: (auto, 1fr),
      column-gutter: 1.5mm,
      align: horizon,
      text(size: size-small, fill: color-muted, label),
      box(width: 100%, {
        line(length: 100%, stroke: stroke-thin)
      }),
    )
  })
}

#let blank-line(length: 100%, spacing: 5.5mm) = {
  box(width: length, height: spacing, {
    place(bottom, dy: -0.8mm, line(length: 100%, stroke: stroke-thin))
  })
}

#let writing-lines(n, length: 100%, spacing: 5.5mm) = {
  for _ in range(n) {
    blank-line(length: length, spacing: spacing)
  }
}

#let checkbox(size: checkbox-size) = {
  square(size: size, radius: 0.55mm, fill: none, stroke: stroke-ink)
}

#let check-circle(size: circle-check-size) = {
  circle(radius: size / 2, fill: none, stroke: stroke-ink)
}

#let page-number(n, total: 24) = {
  place(bottom + center, dy: 7.5mm, {
    text(size: size-tiny, fill: color-muted, [#n])
  })
}

// ---------- rows ----------

#let checklist-row(repeat-checks: 0, height: 8mm) = {
  block(width: 100%, height: height, stroke: stroke-thin, radius: 1.2mm, inset: (x: 1.5mm, y: 1.2mm), {
    grid(
      columns: (checkbox-size, 1fr) + if repeat-checks > 0 { (auto,) } else { () },
      column-gutter: 1.8mm,
      align: horizon,
      checkbox(),
      box(width: 100%, height: 100%, {
        place(bottom, dy: -0.3mm, line(length: 100%, stroke: stroke-thin))
      }),
      if repeat-checks > 0 {
        grid(
          columns: (circle-check-size + 1mm,) * repeat-checks,
          column-gutter: 0.8mm,
          align: horizon,
          ..range(repeat-checks).map(_ => check-circle()),
        )
      },
    )
  })
}

#let routine-row(height: 12.5mm) = {
  block(width: 100%, height: height, stroke: stroke-thin, radius: 1.5mm, inset: (x: 1.8mm, y: 1.4mm), below: 1.2mm, {
    grid(
      columns: (checkbox-size, 13mm, 1fr),
      column-gutter: 2mm,
      align: (horizon, horizon, top),
      checkbox(),
      {
        text(size: size-tiny, fill: color-muted, "čas")
        v(0.2mm)
        box(width: 100%, height: 4.5mm, stroke: stroke-thin, radius: 0.8mm)
      },
      box(width: 100%, height: 100%),
    )
  })
}

#let afternoon-day(day) = {
  block(width: 100%, height: 19.5mm, stroke: stroke-thin, radius: 1.5mm, inset: (x: 1.5mm, y: 1.2mm), below: 1mm, {
    text(size: size-small, weight: "bold", fill: color-ink, day)
    v(0.5mm)
    grid(
      columns: (1fr, 1fr),
      column-gutter: 1.5mm,
      row-gutter: 0.9mm,
      labeled-field("Čas"),
      labeled-field("Místo"),
      grid.cell(colspan: 2, labeled-field("Co")),
      grid.cell(colspan: 2, labeled-field("Poznámka")),
    )
  })
}

// ---------- timetable ----------

#let timetable(days: ("Po", "Út", "St", "Čt", "Pá"), lessons: 7) = {
  let cols = (7mm,) + (1fr,) * days.len()
  let header = (
    box(height: 6mm, align(center + horizon, text(size: size-tiny, fill: color-muted, "#"))),
    ..days.map(d => box(
      height: 6mm,
      fill: color-panel,
      stroke: stroke-thin,
      align(center + horizon, text(size: size-small, weight: "bold", fill: color-ink, d)),
    )),
  )
  let rows = for i in range(1, lessons + 1) {
    (
      box(
        height: 10.5mm,
        fill: color-soft,
        stroke: stroke-thin,
        align(center + horizon, text(size: size-small, fill: color-ink, str(i))),
      ),
      ..days.map(_ => box(height: 10.5mm, stroke: stroke-thin, {})),
    )
  }
  grid(columns: cols, stroke: stroke-thin, ..header, ..rows)
}

// ---------- weekly habit tracker ----------

#let weekly-tracker(task-rows: 7, days: ("Po", "Út", "St", "Čt", "Pá", "So", "Ne")) = {
  let cols = (1fr,) + (7.5mm,) * days.len()
  let header = (
    box(height: 6mm, inset: (left: 1mm), align(horizon, text(size: size-tiny, fill: color-muted, "Moje úkoly"))),
    ..days.map(d => box(
      height: 6mm,
      align(center + horizon, text(size: size-tiny, weight: "bold", fill: color-ink, d)),
    )),
  )
  let body = for _ in range(task-rows) {
    (
      box(height: 11mm, stroke: stroke-thin, inset: (x: 1.2mm, y: 1mm), {
        place(bottom, dy: -0.6mm, line(length: 100%, stroke: stroke-thin))
      }),
      ..days.map(_ => box(
        height: 11mm,
        stroke: stroke-thin,
        align(center + horizon, check-circle()),
      )),
    )
  }
  grid(columns: cols, ..header, ..body)
}

// ---------- day panel (weekly plan) ----------

#let day-panel(day, compact: false) = {
  let h = if compact { 14mm } else { 17.5mm }
  block(width: 100%, height: h, stroke: stroke-thin, radius: 1.4mm, inset: 1.4mm, {
    grid(
      columns: (1fr, checkbox-size),
      column-gutter: 1mm,
      align: horizon,
      text(size: size-small, weight: "bold", fill: color-ink, day),
      checkbox(size: 3.6mm),
    )
    v(0.5mm)
    grid(
      columns: (12mm, 1fr),
      column-gutter: 1.2mm,
      align: (top, top),
      {
        text(size: 7pt, fill: color-muted, "čas")
        v(0.2mm)
        box(width: 100%, height: 3.6mm, stroke: stroke-thin, radius: 0.6mm)
      },
      {
        let lines = if compact { 2 } else { 2 }
        for _ in range(lines) {
          box(width: 100%, height: if compact { 3.8mm } else { 5mm }, {
            place(bottom, dy: -0.3mm, line(length: 100%, stroke: stroke-thin))
          })
        }
      },
    )
  })
}

// ---------- project card ----------

#let project-card() = {
  rounded-panel(fill: color-soft, inset: 1.8mm, {
    labeled-field("Název projektu")
    v(1mm)
    labeled-field("Hotovo do")
    v(1.1mm)
    text(size: size-tiny, fill: color-muted, "Co chci udělat nebo dokázat?")
    writing-lines(1, spacing: 4.2mm)
    v(0.6mm)
    text(size: size-tiny, fill: color-muted, "Co budu potřebovat?")
    writing-lines(1, spacing: 4.2mm)
    v(0.6mm)
    text(size: size-tiny, fill: color-muted, "První krok")
    writing-lines(1, spacing: 4.2mm)
    v(0.5mm)
    text(size: size-tiny, fill: color-muted, "Další kroky")
    writing-lines(1, spacing: 4.2mm)
    v(0.8mm)
    labeled-field("Kdo mi může pomoct?")
    v(1mm)
    grid(
      columns: (checkbox-size, auto),
      column-gutter: 1.5mm,
      align: horizon,
      checkbox(),
      text(size: size-small, fill: color-ink, "Hotovo"),
    )
  })
}

// ---------- mood selector ----------

#let mood-face(kind) = {
  // Simple faces drawn with absolute millimetre coordinates (no bezier bugs)
  box(width: 9mm, height: 9mm, {
    place(dx: 0.8mm, dy: 0.8mm, circle(radius: 3.7mm, fill: none, stroke: stroke-ink))
    place(dx: 3.0mm, dy: 3.2mm, circle(radius: 0.45mm, fill: color-ink))
    place(dx: 5.4mm, dy: 3.2mm, circle(radius: 0.45mm, fill: color-ink))
    if kind == "happy" {
      // upward arc via three short line segments
      place(dx: 2.6mm, dy: 5.6mm, line(start: (0mm, 0mm), end: (1.2mm, 1.1mm), stroke: 0.75pt + color-ink))
      place(dx: 3.8mm, dy: 6.7mm, line(start: (0mm, 0mm), end: (1.4mm, 0mm), stroke: 0.75pt + color-ink))
      place(dx: 5.2mm, dy: 6.7mm, line(start: (0mm, 0mm), end: (1.2mm, -1.1mm), stroke: 0.75pt + color-ink))
    } else if kind == "sad" {
      place(dx: 2.6mm, dy: 6.8mm, line(start: (0mm, 0mm), end: (1.2mm, -1.1mm), stroke: 0.75pt + color-ink))
      place(dx: 3.8mm, dy: 5.7mm, line(start: (0mm, 0mm), end: (1.4mm, 0mm), stroke: 0.75pt + color-ink))
      place(dx: 5.2mm, dy: 5.7mm, line(start: (0mm, 0mm), end: (1.2mm, 1.1mm), stroke: 0.75pt + color-ink))
    } else {
      place(dx: 2.8mm, dy: 6.2mm, line(length: 3.4mm, stroke: 0.75pt + color-ink))
    }
  })
}

#let mood-selector() = {
  grid(
    columns: (auto, auto, auto),
    column-gutter: 4mm,
    align: center,
    {
      mood-face("happy")
      v(0.8mm)
      checkbox(size: 3.2mm)
      v(0.4mm)
      text(size: size-tiny, fill: color-muted, "veselé")
    },
    {
      mood-face("neutral")
      v(0.8mm)
      checkbox(size: 3.2mm)
      v(0.4mm)
      text(size: size-tiny, fill: color-muted, "v pohodě")
    },
    {
      mood-face("sad")
      v(0.8mm)
      checkbox(size: 3.2mm)
      v(0.4mm)
      text(size: size-tiny, fill: color-muted, "těžké")
    },
  )
}

// ---------- cover decorations ----------

#let cover-decorations() = {
  place(top + left, dx: -1mm, dy: 1mm, icon-star(size: 5.5mm))
  place(top + right, dx: 0mm, dy: 6mm, icon-circle(size: 4.5mm, fill: color-panel))
  place(top + right, dx: -7mm, dy: 1mm, icon-star(size: 3.5mm, fill: color-ink))
  place(bottom + left, dx: 2mm, dy: -16mm, {
    path(
      stroke: 1pt + color-accent.transparentize(35%),
      ((0mm, 7mm), (3mm, 0mm)),
      ((10mm, 0mm), (0mm, 0mm)),
      ((18mm, 8mm), (2mm, 0mm)),
      ((30mm, 1mm), (0mm, 0mm)),
      ((40mm, 10mm), (0mm, 0mm)),
    )
  })
  place(bottom + right, dx: -4mm, dy: -18mm, icon-circle(size: 6mm, fill: none, stroke: stroke-accent))
  place(bottom + right, dx: -14mm, dy: -12mm, checkbox(size: 3.5mm))
  place(bottom + right, dx: -9mm, dy: -12mm, checkbox(size: 3.5mm))
}
