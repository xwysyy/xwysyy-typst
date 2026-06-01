// Slides mode — touying-based slide variants and the xwysyy-pre entry.

#import "@preview/touying:0.7.3": *
#import "themes.typ": *
#import "elements.typ": *

#let xwysyy-slide(title: auto, ..args) = touying-slide-wrapper(self => {
  if title != auto {
    self.store.title = title
  }
  // set page
  let header(self) = {
    set align(top)
    block(
      width: 100% + 2em,
      height: 2.5em,
      fill: self.store.header-fill,
      inset: (x: 1em),
      {
        set align(horizon)
        text(fill: self.store.header-text, weight: "extrabold", size: 1.56em, {
          if self.store.title != none {
            utils.call-or-display(self, self.store.title)
          } else {
            utils.display-current-heading(level: 2)
          }
        })
      }
    )
  }
  let footer(self) = {
    set align(bottom)
    set text(fill: self.colors.neutral-dark, size: .9em)
    block(
      inset: (x: 0.5em, bottom: 0.4em),
      {
      utils.call-or-display(self, self.store.footer)
      h(1fr)
      context utils.slide-counter.display()
    }
    )
  }
  self = utils.merge-dicts(
    self,
    config-page(
      header: header,
      footer: footer,
    ),
  )
  touying-slide(self: self, ..args)
})

#let title-slide(..args) = touying-slide-wrapper(self => {
  self = utils.merge-dicts(
    self,
    config-page(margin: 0em),
  )
  let info = self.info + args.named()
  let body = {
    set align(center + horizon)
    line(length: 100%, stroke: self.colors.neutral-dark)
    v(-0.9em)
    block(
      fill: self.colors.neutral-dark,
      width: 100%,
      inset: (y: 1.2em),
      text(size: 2.2em, fill: self.colors.neutral-lightest, weight: "bold", info.title),
    )
    if info.subtitle != none {
      v(-0.9em)
      block(
        fill: self.colors.neutral-lighter,
        width: 100%,
        {
        line(length: 100%, stroke: self.colors.neutral-dark)
        v(-0.65em)
        text(size: 1.6em, fill: self.colors.neutral-dark, weight: "bold", info.subtitle)
        v(-0.65em)
        line(length: 100%, stroke: self.colors.neutral-dark)}
      )
    }
    set text(fill: self.colors.neutral-darkest)
    v(1em)
    if info.author != none {
      block(text(size: 1.1em, info.author))
    }
    if info.institution != none {
      block(text(size: 0.9em, style: "italic", info.institution))
    }
    if info.date != none {
      block(utils.display-info-date(self))
    }
  }
  touying-slide(self: self, body)
})

#let new-section-slide(self: none, body) = touying-slide-wrapper(self => {
  self = utils.merge-dicts(
    self,
    config-page(
      margin: 0em,
    ),
  )
  let main-body = {
    set align(center + horizon)
    set text(size: 2em, fill: self.colors.neutral-dark, weight: "bold", style: "italic")
    line(start: (17%, 0em), length: 83%, stroke: self.colors.neutral-dark)
    v(-0.97em)
    block(
      fill: self.colors.neutral-lighter,
      inset: (y: 0.42em),
      width: 100%,
      utils.display-current-heading(level: 1)
    )
    v(-0.97em)
    line(start: (-17%, 0em), length: 83%, stroke: self.colors.neutral-dark)
  }
  touying-slide(self: self, main-body)
})

#let focus-slide(body) = touying-slide-wrapper(self => {
  self = utils.merge-dicts(
    self,
    config-page(
      fill: self.colors.neutral-dark,
      margin: 0em,
    ),
  )
  set text(fill: self.colors.neutral-lightest, size: 2em, weight: "bold")
  touying-slide(self: self, align(horizon + center, body))
})

#let end-slide(title: [Thank You!], body: none) = touying-slide-wrapper(self => {
  self = utils.merge-dicts(self, config-page(
    fill: white,
    margin: 2em,
  ))
  let main-body = {
    set align(center + horizon)
    text(fill: self.colors.neutral-dark, size: 3em, weight: "bold", title)
    if body != none {
      v(0.5em)
      line(length: 20%, stroke: (thickness: 1.5pt, paint: self.colors.primary))
      v(0.5em)
      text(size: 1.3em, fill: self.colors.neutral-dark.lighten(30%), body)
    }
  }
  touying-slide(self: self, main-body)
})

#let outline-slide(chapters: auto) = {
  xwysyy-slide(title: [目录])[
    #context {
      let t = _theme-state.get()
      let chs = if chapters == auto {
        query(heading.where(level: 1))
          .filter(h => not h.has("label") or str(h.label) != "touying:hidden")
          .map(h => h.body)
      } else {
        chapters
      }
      let two-col = chs.len() > 5
      let bsz = if two-col { 2em } else { 2.6em }
      let tsz = if two-col { 1.4em } else { 2em }
      let badge(n) = box(
        width: bsz, height: bsz, fill: t.sea, radius: 50%,
        align(center + horizon, text(fill: t.paper, weight: "bold", size: bsz * 0.58, n))
      )
      let items = chs.enumerate().map(((i, ch)) => grid(
        columns: (auto, 1fr),
        column-gutter: if two-col { 1em } else { 1.4em },
        align: (center + horizon, left + horizon),
        badge(numbering("01", i + 1)),
        text(size: tsz, weight: "semibold", ch),
      ))
      if two-col {
        let mid = calc.ceil(items.len() / 2)
        v(0.5em)
        grid(
          columns: (1fr, 1fr),
          gutter: 1.5em,
          stack(spacing: 1.6em, ..items.slice(0, mid)),
          stack(spacing: 1.6em, ..items.slice(mid)),
        )
      } else {
        v(1em)
        stack(spacing: 2.4em, ..items)
      }
    }
  ]
}

#let image-slide(body: none, img: none) = touying-slide-wrapper(self => {
  self = utils.merge-dicts(
    self,
    config-page(
      background: img,
      margin: (x: 0em, y: 1.4em),
    ),
  )
  set text(fill: self.colors.neutral-dark, size: 1.4em)
  set image(width: 100%, height: auto)
  touying-slide(self: self, align(left + bottom,
    align(
      center,
      block(
        fill: self.colors.neutral-lighter,
        if body != none {
        line(length: 100%, stroke: self.colors.neutral-dark)
        v(-0.85em)
        body
        v(-0.85em)
        line(length: 100%, stroke: self.colors.neutral-dark)
      }
      ))))
})

#let xwysyy-pre(
  aspect-ratio: "16-9",
  footer: none,
  theme: "sky",
  ..args,
  body,
) = {
  let t = themes.at(theme)
  _theme-state.update(t)
  set text(
    font: ("Times New Roman", "Noto Serif CJK SC"),
    lang: "en",
    size: 5.5mm,
    weight: "semibold",
    style: "normal",
  )
  show: touying-slides.with(
    config-page(
      paper: "presentation-" + aspect-ratio,
      margin: (top: 3.7em, x: 1em, bottom: 1.4em)
    ),
    config-common(
      slide-fn: xwysyy-slide,
      new-section-slide-fn: new-section-slide,
      frozen-counters: (counter(figure), counter(math.equation)),
    ),
    config-colors(
      primary: t.sky,
      neutral-light: t.skyl,
      neutral-lighter: t.skyll,
      neutral-lightest: t.paper,
      neutral-dark: t.sea,
      neutral-darkest: black,
    ),
    config-methods(
      alert: (self: none, it) => text(weight: "bold", stroke: 0.02em, it),
    ),
    config-store(
      title: none,
      footer: footer,
      header-fill: if t.header-fill != none { t.header-fill } else { t.sea },
      header-text: if t.header-text != none { t.header-text } else { t.paper },
    ),
    config-page(
      fill: t.page-fill,
    ),
    ..args,
  )

  show: xwysyy-elements.with(t-sea: t.sea, t-sky: t.sky, t-skyll: t.skyll, t-paper: t.paper)

  body
}
