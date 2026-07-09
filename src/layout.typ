// Semantic layout layer for xwysyy-typst.
//
// Authors (human or AI) pick a semantic component and fill content + roles +
// mode.  Each component measures the real rendered height of every block,
// distributes whitespace by a rhythm rule (clamped so content never overflows
// or clusters), and exports the *measured* normalized geometry as
// `<xwysyy-slide-layout>` metadata for the Python checker.  Authors never write
// raw `v()` spacing or absolute coordinates; they adjust `mode` and read the
// numeric feedback the checker returns after each compile.

#import "slides.typ": xwysyy-slide
#import "elements.typ": textbox
#import "themes.typ": _theme-state

// Capture alignment references before any parameter named `top` / `bottom` /
// `left` shadows them inside a component body.
#let _atop = top
#let _abottom = bottom
#let _aleft = left
#let _acenter = center
#let _ahorizon = horizon

#let _note-mode() = sys.inputs.at("mode", default: "slides") == "note"
#let _clamp(x, lo, hi) = calc.min(calc.max(x, lo), hi)

// Optical center sits slightly above the geometric center so a centered group
// does not read as sinking.
#let _OPTICAL-CENTER = 0.46
// Split of the leftover outer whitespace: the top margin is smaller than the
// bottom margin, again to keep the group from dropping.
#let _TOP-MARGIN-FRAC = 0.40

// Fill-first distribution.  Instead of centering a measured group and letting
// the leftover space become large outer margins (which reads as a sparse,
// half-empty slide), components keep small fixed outer margins and let the
// primary content grow to occupy the body: figures become dominant, cards
// become tall.  A slide fills its frame by default.
#let _MARGIN-TOP = 0.07
#let _MARGIN-BOT = 0.09
#let _FILL = 1.0 - 0.07 - 0.09
// A card row occupies at least this fraction of the body height, so a row of
// short cards reads as substantial cards rather than tiles floating in space.
#let _CARD-FILL-MIN = 0.60

// Gap between semantically-related blocks, as a fraction of body height.  The
// three values are chosen to land inside the checker's proximity ranges so a
// correctly-generated slide passes without diagnostics.
#let _mode-gap(mode) = {
  if mode == "compact" { 0.06 } else if mode == "separated" { 0.22 } else { 0.13 }
}

// The proximity label the checker should hold a mode-driven gap to, so the
// rendered gap and the checked target stay consistent.
#let _mode-proximity(mode) = {
  if mode == "compact" { "compact" } else if mode == "separated" { "loose" } else { "medium" }
}

// ---------------------------------------------------------------------------
// telemetry primitives
// ---------------------------------------------------------------------------

#let _obj(id, role, x, y, w, h, group: none) = (
  id: id,
  role: role,
  group: group,
  x: x,
  y: y,
  w: w,
  h: h,
)

#let _rel(from, to, kind, axis, proximity) = (
  from: from,
  to: to,
  kind: kind,
  axis: axis,
  desired_proximity: proximity,
)

// Emit one slide's telemetry.  Must be produced in markup so the label binds
// (a label on `metadata(...)` in code mode is a Typst syntax error).
#let _emit(id, archetype, objects, relations, extra) = [
  #metadata((
    schema: "xwysyy-slide-layout/v1",
    id: id,
    archetype: archetype,
    coordinate_system: "normalized-slide-body",
    objects: objects,
    relations: relations,
    extra: extra,
  )) <xwysyy-slide-layout>
]

// Debug overlay: draw each measured bbox so a human can eyeball what the
// checker sees.  Colours cycle; ids are printed at the top-left corner.
#let _debug-palette = (
  rgb("#d7263d"), rgb("#2e86ab"), rgb("#4f772d"),
  rgb("#7b2cbf"), rgb("#f77f00"), rgb("#006d77"),
)
#let _debug-layer(objects, W, H) = {
  for (i, o) in objects.enumerate() {
    let c = _debug-palette.at(calc.rem(i, _debug-palette.len()))
    place(_atop + _aleft, dx: W * o.x, dy: H * o.y, rect(
      width: W * o.w, height: H * o.h,
      stroke: (paint: c, thickness: 0.7pt), fill: c.transparentize(93%),
    ))
    place(_atop + _aleft, dx: W * o.x + 0.2em, dy: H * o.y + 0.12em,
      text(fill: c, size: 0.5em, weight: "bold", o.id))
  }
}

#let _sep(n) = if n <= 0pt { 0pt } else { n }

// Column container for side-by-side layouts.  When `card` is set it draws the
// theme's rounded skyll card at a fixed height so every column reads as an
// equal-height card (the visible box, not just an invisible wrapper, is
// equalized); `h: auto` measures the natural carded height.  At a fixed height
// the content is vertically centred, so a short line sits in the middle of a
// tall filled card instead of clinging to the top with dead space below.
#let _card-box(cw, h, fill, body, card) = {
  let inner = if h == auto { body } else { align(_ahorizon, body) }
  if card {
    block(width: cw, height: h, fill: fill, inset: 0.9em, radius: 0.4em, inner)
  } else {
    block(width: cw, height: h, inner)
  }
}

// ---------------------------------------------------------------------------
// duo-slide — one vertical semantic pair (e.g. figure over takeaway)
// ---------------------------------------------------------------------------

#let duo-slide(
  title: auto,
  id: auto,
  top: none,
  bottom: none,
  mode: "balanced",
  top-role: "figure",
  bottom-role: "explanation",
  relation: "supports",
  top-width: 0.82,
  bottom-width: 0.74,
  debug: false,
) = {
  let sid = if id == auto { "duo" } else { id }
  let tc = if top == none { [] } else { top }
  let bc = if bottom == none { [] } else { bottom }
  if _note-mode() {
    xwysyy-slide(title: title)[
      #block(tc)
      #block(bc)
    ]
  } else {
    xwysyy-slide(title: title)[
      #layout(size => {
        let W = size.width
        let H = size.height
        let tw = W * top-width
        let bw = W * bottom-width
        let gap = H * _mode-gap(mode)
        let mtop = H * _MARGIN-TOP
        let mbot = H * _MARGIN-BOT
        // The takeaway keeps its natural (modest) height; the figure grows to
        // fill everything above it, so it dominates the slide instead of
        // floating at its natural size.
        let bh = measure(block(width: bw, bc)).height
        let fig-nat = measure(block(width: tw, tc)).height
        let avail = _sep(H - mtop - mbot - bh - gap)
        let overflow = fig-nat > avail
        let th = if overflow { fig-nat } else { avail }
        let y0 = if overflow { 0pt } else { mtop }

        place(_atop + _aleft, dx: (W - tw) / 2, dy: y0,
          block(width: tw, height: th, align(_ahorizon, tc)))
        place(_atop + _aleft, dx: (W - bw) / 2, dy: y0 + th + gap, block(width: bw, bc))

        let objects = (
          _obj(sid + ":top", top-role, (1.0 - top-width) / 2, y0 / H, top-width, th / H, group: sid),
          _obj(sid + ":bottom", bottom-role, (1.0 - bottom-width) / 2, (y0 + th + gap) / H, bottom-width, bh / H, group: sid),
        )
        let relations = (
          _rel(sid + ":top", sid + ":bottom", relation, "vertical", _mode-proximity(mode)),
        )
        _emit(sid, "duo", objects, relations, (
          mode: mode,
          gap_ratio: gap / H,
          free_ratio: _sep(H - th - bh - gap) / H,
          overflow: overflow,
        ))
        if debug { _debug-layer(objects, W, H) }
      })
    ]
  }
}

// ---------------------------------------------------------------------------
// focus-slide — a single centered block for low-content pages
// ---------------------------------------------------------------------------

#let focus-slide(
  title: auto,
  id: auto,
  body: none,
  role: "main_visual",
  width: 0.76,
  center-y: _OPTICAL-CENTER,
  debug: false,
) = {
  let sid = if id == auto { "focus" } else { id }
  let bc = if body == none { [] } else { body }
  if _note-mode() {
    xwysyy-slide(title: title)[#bc]
  } else {
    xwysyy-slide(title: title)[
      #layout(size => {
        let W = size.width
        let H = size.height
        let cw = W * width
        let bh = measure(block(width: cw, bc)).height
        let hr = bh / H
        let y = _clamp(center-y - hr / 2, 0.0, calc.max(1.0 - hr, 0.0))

        place(_atop + _aleft, dx: (W - cw) / 2, dy: H * y, block(width: cw, bc))

        let objects = (
          _obj(sid + ":focus", role, (1.0 - width) / 2, y, width, hr, group: sid),
        )
        _emit(sid, "focus", objects, (), (
          center_y: center-y,
          height_ratio: hr,
          overflow: hr > 1.0,
        ))
        if debug { _debug-layer(objects, W, H) }
      })
    ]
  }
}

// ---------------------------------------------------------------------------
// stack-slide — N vertical blocks on one rhythm (duo generalized)
// ---------------------------------------------------------------------------

#let stack-slide(
  title: auto,
  id: auto,
  blocks: (),
  roles: (),
  relation: "supports",
  mode: "balanced",
  width: 0.82,
  debug: false,
) = {
  let sid = if id == auto { "stack" } else { id }
  let n = blocks.len()
  if _note-mode() {
    xwysyy-slide(title: title)[#for b in blocks { block(b) }]
  } else {
    xwysyy-slide(title: title)[
      #layout(size => {
        let W = size.width
        let H = size.height
        let bw = W * width
        let heights = blocks.map(b => measure(block(width: bw, b)).height)
        let total = heights.fold(0pt, (a, h) => a + h)
        let gap = H * _mode-gap(mode)
        let content = total + gap * calc.max(n - 1, 0)
        let overflow = content > H
        let free = _sep(H - content)
        let g = if overflow { _sep((H - total) / calc.max(n - 1, 1)) } else { gap }
        let y0 = if overflow { 0pt } else { free * _TOP-MARGIN-FRAC }

        let objects = ()
        let relations = ()
        let cy = y0
        for (i, b) in blocks.enumerate() {
          let h = heights.at(i)
          place(_atop + _aleft, dx: (W - bw) / 2, dy: cy, block(width: bw, b))
          let role = roles.at(i, default: "content")
          let oid = sid + ":" + str(i)
          objects.push(_obj(oid, role, (1.0 - width) / 2, cy / H, width, h / H, group: sid))
          if i > 0 {
            relations.push(_rel(sid + ":" + str(i - 1), oid, relation, "vertical", _mode-proximity(mode)))
          }
          cy = cy + h + g
        }
        _emit(sid, "stack", objects, relations, (
          mode: mode,
          gap_ratio: g / H,
          free_ratio: free / H,
          overflow: overflow,
          count: n,
        ))
        if debug { _debug-layer(objects, W, H) }
      })
    ]
  }
}

// ---------------------------------------------------------------------------
// grid-slide — N equal-height peer columns
// ---------------------------------------------------------------------------

#let grid-slide(
  title: auto,
  id: auto,
  columns: (),
  roles: (),
  gutter: 0.04,
  card: true,
  center-y: _OPTICAL-CENTER,
  debug: false,
) = {
  let sid = if id == auto { "grid" } else { id }
  let n = columns.len()
  if n == 0 {
    xwysyy-slide(title: title)[]
  } else if _note-mode() {
    xwysyy-slide(title: title)[
      #grid(columns: (1fr,) * n, column-gutter: 1em,
        ..columns.map(c => if card { textbox(c) } else { c }))
    ]
  } else {
    xwysyy-slide(title: title)[
      #context {
        let cfill = _theme-state.get().skyll
        layout(size => {
          let W = size.width
          let H = size.height
          let cwn = (1.0 - gutter * calc.max(n - 1, 0)) / n
          if cwn <= 0.0 {
            panic("grid-slide: gutter " + repr(gutter) + " leaves no width for " + repr(n) + " columns")
          }
          let cw = W * cwn
          // Measure the natural carded height, then grow every card to a shared
          // fill height so the row occupies the body instead of floating as
          // short tiles; cards stay equal-height and content is centred inside.
          let heights = columns.map(c => measure(_card-box(cw, auto, cfill, c, card)).height)
          let natural = heights.fold(0pt, (a, h) => calc.max(a, h))
          let overflow = natural > _FILL * H
          let rh = if overflow { natural } else { _clamp(natural, _CARD-FILL-MIN * H, _FILL * H) }
          let rhr = rh / H
          let y = _clamp((1.0 - rhr) / 2, 0.0, calc.max(1.0 - rhr, 0.0))

          let objects = ()
          for (i, c) in columns.enumerate() {
            let xn = i * (cwn + gutter)
            place(_atop + _aleft, dx: W * xn, dy: H * y, _card-box(cw, rh, cfill, c, card))
            objects.push(_obj(sid + ":" + str(i), roles.at(i, default: "column"), xn, y, cwn, rhr, group: sid))
          }
          let hmax = heights.fold(0pt, (a, h) => calc.max(a, h))
          let hmin = heights.fold(rh, (a, h) => calc.min(a, h))
          _emit(sid, "grid", objects, (), (
            count: n,
            gutter: gutter,
            overflow: overflow,
            natural_height_variance: (hmax - hmin) / H,
          ))
          if debug { _debug-layer(objects, W, H) }
        })
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// compare-slide — two top-aligned blocks read as a contrast
// ---------------------------------------------------------------------------

#let compare-slide(
  title: auto,
  id: auto,
  left: none,
  right: none,
  left-role: "option",
  right-role: "option",
  gutter: 0.06,
  card: true,
  center-y: _OPTICAL-CENTER,
  debug: false,
) = {
  let sid = if id == auto { "compare" } else { id }
  let lc = if left == none { [] } else { left }
  let rc = if right == none { [] } else { right }
  if _note-mode() {
    xwysyy-slide(title: title)[
      #grid(columns: (1fr, 1fr), column-gutter: 1em,
        ..(lc, rc).map(c => if card { textbox(c) } else { c }))
    ]
  } else {
    xwysyy-slide(title: title)[
      #context {
        let cfill = _theme-state.get().skyll
        layout(size => {
          let W = size.width
          let H = size.height
          let cwn = (1.0 - gutter) / 2
          let cw = W * cwn
          let lh = measure(_card-box(cw, auto, cfill, lc, card)).height
          let rh = measure(_card-box(cw, auto, cfill, rc, card)).height
          let natural = calc.max(lh, rh)
          // Grow the two cards to a shared fill height so they read as two
          // substantial panels, not short tiles floating in the middle.
          let overflow = natural > _FILL * H
          let row = if overflow { natural } else { _clamp(natural, _CARD-FILL-MIN * H, _FILL * H) }
          let rowr = row / H
          let y = _clamp((1.0 - rowr) / 2, 0.0, calc.max(1.0 - rowr, 0.0))

          // Both sides drawn at the shared row height, so the two cards are equal.
          place(_atop + _aleft, dx: 0pt, dy: H * y, _card-box(cw, row, cfill, lc, card))
          place(_atop + _aleft, dx: W * (cwn + gutter), dy: H * y, _card-box(cw, row, cfill, rc, card))

          let objects = (
            _obj(sid + ":left", left-role, 0.0, y, cwn, rowr, group: sid),
            _obj(sid + ":right", right-role, cwn + gutter, y, cwn, rowr, group: sid),
          )
          let relations = (
            _rel(sid + ":left", sid + ":right", "contrast", "horizontal", "gutter"),
          )
          _emit(sid, "compare", objects, relations, (
            gutter: gutter,
            overflow: overflow,
            natural_height_variance: (calc.max(lh, rh) - calc.min(lh, rh)) / H,
          ))
          if debug { _debug-layer(objects, W, H) }
        })
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// stat-slide — a row of metric tiles (big value + label)
// ---------------------------------------------------------------------------
//
// Delegates the equal-height card row to grid-slide; only the tile formatting
// (large value over a muted label) lives here.  `stats` is a list of
// dictionaries `(value: [...], label: [...])`.

#let stat-slide(
  title: auto,
  id: auto,
  stats: (),
  gutter: 0.04,
  center-y: _OPTICAL-CENTER,
  debug: false,
) = {
  // The theme colour is resolved inside each tile (a `context` block) rather
  // than around the whole slide: touying rejects a slide wrapper returned from
  // inside `context`.
  let tiles = stats.map(s => context {
    let t = _theme-state.get()
    let val = s.at("value", default: [—])
    let lab = s.at("label", default: [])
    // Fit the value to the tile width so a long number (e.g. a currency figure)
    // shrinks instead of bleeding off the card and the slide.
    layout(size => {
      let vw = measure(text(size: 2.6em, weight: 700, val)).width
      let sc = if vw > size.width and vw > 0pt { size.width / vw } else { 1.0 }
      align(_acenter + _ahorizon, stack(
        spacing: 0.2em,
        align(_acenter, text(size: 2.6em * sc, weight: 700, fill: t.sea, val)),
        align(_acenter, text(size: 0.95em, fill: t.sea.lighten(12%), lab)),
      ))
    })
  })
  grid-slide(
    title: title,
    id: if id == auto { "stat" } else { id },
    columns: tiles,
    roles: stats.map(_ => "metric"),
    gutter: gutter,
    center-y: center-y,
    debug: debug,
  )
}

// ---------------------------------------------------------------------------
// figure-slide — a figure with a tight caption, plus an optional takeaway
// ---------------------------------------------------------------------------
//
// The figure and its caption form one tight group; the group and the takeaway
// form a supporting pair.  Composes focus-slide / duo-slide so the measured
// rhythm and telemetry are the tested ones.

#let figure-slide(
  title: auto,
  id: auto,
  fig: none,
  caption: none,
  takeaway: none,
  figure-width: 0.80,
  mode: "balanced",
  debug: false,
) = {
  let sid = if id == auto { "figure" } else { id }
  let group = {
    align(_acenter, if fig == none { [] } else { fig })
    if caption != none {
      v(0.5em, weak: true)
      align(_acenter, text(size: 0.85em, fill: luma(90), style: "italic", caption))
    }
  }
  if takeaway == none {
    focus-slide(title: title, id: sid, body: group, role: "figure", width: figure-width, debug: debug)
  } else {
    duo-slide(
      title: title, id: sid, top: group, bottom: takeaway,
      top-role: "figure", bottom-role: "takeaway", relation: "supports",
      mode: mode, top-width: figure-width, bottom-width: 0.74, debug: debug,
    )
  }
}

// ---------------------------------------------------------------------------
// sidebar-slide — a narrow label tab beside a wide content card
// ---------------------------------------------------------------------------

#let sidebar-slide(
  title: auto,
  id: auto,
  label: none,
  body: none,
  label-width: 0.26,
  gutter: 0.04,
  center-y: _OPTICAL-CENTER,
  debug: false,
) = {
  let sid = if id == auto { "sidebar" } else { id }
  let lc = if label == none { [] } else { label }
  let bc = if body == none { [] } else { body }
  if _note-mode() {
    xwysyy-slide(title: title)[
      #strong(lc) \
      #bc
    ]
  } else {
    xwysyy-slide(title: title)[
      #context {
        let t = _theme-state.get()
        layout(size => {
          let W = size.width
          let H = size.height
          let lwn = label-width
          let bwn = 1.0 - label-width - gutter
          if bwn <= 0.0 {
            panic("sidebar-slide: label-width " + repr(label-width) + " + gutter leaves no body width")
          }
          let lw = W * lwn
          let bw = W * bwn
          let lh = measure(block(width: lw, inset: 0.9em, strong(lc))).height
          let bh = measure(block(width: bw, inset: 0.9em, bc)).height
          let natural = calc.max(lh, bh)
          // Grow both cards to a shared fill height so the sidebar occupies the
          // body rather than a thin strip floating in the middle.
          let overflow = natural > _FILL * H
          let row = if overflow { natural } else { _clamp(natural, _CARD-FILL-MIN * H, _FILL * H) }
          let rowr = row / H
          let y = _clamp((1.0 - rowr) / 2, 0.0, calc.max(1.0 - rowr, 0.0))

          place(_atop + _aleft, dx: 0pt, dy: H * y,
            block(width: lw, height: row, fill: t.sea, inset: 0.9em, radius: 0.4em,
              align(_ahorizon + _aleft, {
                // Label text is light (paper) on the dark sea tab; inline code
                // keeps its light chip but takes dark (sea) text so it stays
                // readable instead of light-on-light.
                set text(fill: t.paper, weight: "bold")
                show raw: set text(fill: t.sea)
                lc
              })))
          place(_atop + _aleft, dx: W * (lwn + gutter), dy: H * y,
            block(width: bw, height: row, fill: t.skyll, inset: 0.9em, radius: 0.4em, align(_ahorizon, bc)))

          let objects = (
            _obj(sid + ":label", "label", 0.0, y, lwn, rowr, group: sid),
            _obj(sid + ":body", "content", lwn + gutter, y, bwn, rowr, group: sid),
          )
          let relations = (_rel(sid + ":label", sid + ":body", "labels", "horizontal", "gutter"),)
          _emit(sid, "sidebar", objects, relations, (
            label_width: lwn, gutter: gutter, overflow: row > H,
          ))
          if debug { _debug-layer(objects, W, H) }
        })
      }
    ]
  }
}
