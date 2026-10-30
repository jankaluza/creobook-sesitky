#import "theme.typ": *
#import "components.typ": *

#let days-full = (
  "Pondělí", "Úterý", "Středa", "Čtvrtek",
  "Pátek", "Sobota", "Neděle",
)

// ---------- Page 1 — Cover ----------

#let page-cover() = {
  cover-decorations()
  v(6mm)
  align(center, {
    text(size: 26pt, weight: "bold", fill: color-ink, tracking: 1pt, [MŮJ PLÁN])
    v(2.5mm)
    text(size: 11pt, fill: color-muted, [Můj školní a každodenní plánovač])
    v(3mm)
    line(length: 36mm, stroke: 1.1pt + color-accent)
  })
  v(8mm)
  rounded-panel({
    labeled-field("Jméno")
    v(3.5mm)
    labeled-field("Třída")
    v(3.5mm)
    labeled-field("Školní rok")
    v(3.5mm)
    labeled-field("Tento sešit začíná")
  })
  v(1fr)
  align(center, text(size: size-small, fill: color-muted, [
    Ozdob si obálku, jak chceš.
  ]))
  v(4mm)
}

// ---------- Page 2 — Timetable ----------

#let page-timetable() = {
  page-title("Můj rozvrh", icon: icon-star(size: 4.5mm))
  instruction[Napiš předměty do políček.]
  timetable()
  v(2.5mm)
  section-heading[Co si chci pamatovat]
  soft-box(height: 28mm, {
    writing-lines(4, spacing: 5.5mm)
  })
}

// ---------- Page 3 — Afternoons ----------

#let page-afternoons() = {
  page-title("Moje odpoledne", icon: icon-sun(size: 4.5mm))
  instruction[Naplánuj si čas po škole a o víkendu.]
  for day in days-full {
    afternoon-day(day)
  }
}

// ---------- Pages 4–6 — Routines ----------

#let page-routine(title, tip, footer-label: none, icon: none) = {
  page-title(title, icon: icon)
  instruction[#tip]
  for _ in range(8) {
    routine-row(height: 13.2mm)
  }
  if footer-label != none {
    v(1.5mm)
    labeled-field(footer-label)
  }
}

#let page-morning() = page-routine(
  "Moje ráno",
  [Napiš nebo nakresli, co chceš dělat po probuzení.],
  footer-label: "Chci být připraven/a do:",
  icon: icon-sun(size: 4.5mm),
)

#let page-after-school() = page-routine(
  "Po škole",
  [Napiš nebo nakresli, co chceš dělat, až přijdeš domů.],
  icon: icon-bag(size: 4.5mm),
)

#let page-bedtime() = page-routine(
  "Před spaním",
  [Napiš nebo nakresli, jak chceš zakončit den.],
  footer-label: "Chci jít spát v:",
  icon: icon-moon(size: 4.5mm),
)

// ---------- Page 7 — School bag ----------

#let page-school-bag() = {
  page-title("Moje školní taška", icon: icon-bag(size: 4.5mm))
  instruction[Napiš nebo nakresli, na co si chceš vzpomenout.]
  text(size: size-tiny, fill: color-muted, [Kroužky: můžeš odškrtnout víckrát.])
  v(1.5mm)
  for _ in range(12) {
    block(below: 1.1mm, checklist-row(repeat-checks: 3, height: 9.2mm))
  }
}

// ---------- Page 8 — Regular tasks ----------

#let page-regular-tasks() = {
  page-title("Moje pravidelné úkoly", icon: icon-check(size: 4.5mm))
  instruction[Napiš si své úkoly. Odškrtni je každý den.]
  weekly-tracker()
  v(5mm)
  labeled-field("Moje odměna nebo oslava:")
}

// ---------- Pages 9–20 — Weekly plans ----------

#let page-weekly-plan() = {
  page-title("Můj týden")
  grid(
    columns: (1fr, 1fr),
    column-gutter: 2.5mm,
    labeled-field("Týden od"),
    labeled-field("do"),
  )
  v(1.5mm)
  soft-box(inset: 1.6mm, {
    text(size: size-tiny, fill: color-muted, [Tento týden chci…])
    writing-lines(1, spacing: 5mm)
  })
  v(1.5mm)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 1.8mm,
    row-gutter: 1.6mm,
    day-panel("Pondělí"),
    day-panel("Úterý"),
    day-panel("Středa"),
    day-panel("Čtvrtek"),
  )
  v(1.2mm)
  day-panel("Pátek")
  v(1.2mm)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 1.8mm,
    day-panel("Sobota", compact: true),
    day-panel("Neděle", compact: true),
  )
  v(1.5mm)
  grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.5mm,
    soft-box(height: 14mm, inset: 1.4mm, {
      text(size: 7.5pt, weight: "bold", fill: color-ink, [Důležité])
      writing-lines(1, spacing: 4.5mm)
    }),
    soft-box(height: 14mm, inset: 1.4mm, {
      text(size: 7.5pt, weight: "bold", fill: color-ink, [Nezapomenout])
      writing-lines(1, spacing: 4.5mm)
    }),
    soft-box(height: 14mm, inset: 1.4mm, {
      text(size: 7.5pt, weight: "bold", fill: color-ink, [Čas pro sebe])
      writing-lines(1, spacing: 4.5mm)
    }),
  )
  v(1.5mm)
  grid(
    columns: (1fr, auto),
    column-gutter: 2.5mm,
    align: (horizon, horizon),
    soft-box(inset: 1.4mm, {
      text(size: 7.5pt, weight: "bold", fill: color-ink, [Něco, co se povedlo])
      writing-lines(1, spacing: 4.5mm)
    }),
    mood-selector(),
  )
}

// ---------- Page 21 — Important dates ----------

#let page-important-dates() = {
  page-title("Důležitá data", icon: icon-star(size: 4.5mm))
  instruction[Napiš data, která jsou pro tebe důležitá.]
  let cols = (20mm, 1fr, 1fr)
  let header = (
    box(height: 6.5mm, fill: color-panel, stroke: stroke-thin, inset: 1mm,
      align(horizon, text(size: size-tiny, weight: "bold", fill: color-ink, [Datum]))),
    box(height: 6.5mm, fill: color-panel, stroke: stroke-thin, inset: 1mm,
      align(horizon, text(size: size-tiny, weight: "bold", fill: color-ink, [Co se děje?]))),
    box(height: 6.5mm, fill: color-panel, stroke: stroke-thin, inset: 1mm,
      align(horizon, text(size: size-tiny, weight: "bold", fill: color-ink, [Pamatovat / připravit]))),
  )
  let rows = for _ in range(10) {
    (
      box(height: 12.5mm, stroke: stroke-thin, {}),
      box(height: 12.5mm, stroke: stroke-thin, {}),
      box(height: 12.5mm, stroke: stroke-thin, {}),
    )
  }
  grid(columns: cols, ..header, ..rows)
}

// ---------- Page 22 — My project ----------

#let page-project() = {
  page-title("Můj projekt", icon: icon-star(size: 4.5mm))
  instruction[Naplánuj něco, co chceš vytvořit nebo dokončit.]
  project-card()
  v(2mm)
  project-card()
}

// ---------- Page 23 — Looking back ----------

#let page-looking-back() = {
  page-title("Ohlédnutí", icon: icon-star(size: 4.5mm))
  instruction[Napiš nebo nakresli. Žádná odpověď není špatně.]
  let prompts = (
    "Jsem pyšný/á na…",
    "Naučil/a jsem se…",
    "Bavilo mě…",
    "Chtěl/a bych pomoct s…",
    "Příště chci zkusit…",
    "Někdo, kdo mi pomohl…",
  )
  for prompt in prompts {
    soft-box(height: 19mm, inset: 1.6mm, {
      text(size: size-small, weight: "bold", fill: color-ink, prompt)
      v(0.5mm)
      writing-lines(2, spacing: 4.8mm)
    })
    v(1.2mm)
  }
}

// ---------- Page 24 — Notes ----------

#let page-notes() = {
  page-title("Poznámky a nápady")
  section-heading[Piš sem]
  writing-lines(4, spacing: 6mm)
  v(2mm)
  section-heading[Kresli sem]
  soft-box(height: 78mm, {})
  v(2.5mm)
  rounded-panel(fill: color-panel, inset: 2.2mm, {
    text(size: size-small, weight: "bold", fill: color-ink, [Nápad, na který si chci vzpomenout])
    v(1mm)
    writing-lines(2, spacing: 5mm)
  })
}

// ---------- Book order ----------

#let all-pages = (
  page-cover,
  page-timetable,
  page-afternoons,
  page-morning,
  page-after-school,
  page-bedtime,
  page-school-bag,
  page-regular-tasks,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-weekly-plan,
  page-important-dates,
  page-project,
  page-looking-back,
  page-notes,
)
