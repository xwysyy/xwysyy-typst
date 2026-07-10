// Semantic layout layer for xwysyy-typst — telemetry schema v3.
//
// Authors (human or AI) pick a semantic component and provide typed content
// items; each component measures the real rendered size of every block, runs
// a shared allocator, and exports the *measured* normalized geometry as
// `<xwysyy-slide-layout>` v3 metadata for scripts/slide-check.py.
//
// Honesty rules baked into the schema:
//   * sizing is DECLARED, never inferred: percent-sized content must be
//     wrapped in `visual(...)` (fit: "stretch"); required slots panic on
//     `none`, and content that renders empty panics instead of masquerading
//     as a full frame;
//   * every object carries `frame` (allocated), `preferred` (what the
//     allocator saw), `payload` (a 2-D flow bbox of the inner content —
//     approximate for wrapped text, exact for fixed-size content) and
//     `paint` (the visible card box, or none);
//   * the allocator has four states — normal / compressed (gaps squeezed
//     below their preferred size) / tight (outer margins consumed) /
//     overflow — with the invariant overflow => body_overflow_ratio > 0;
//   * one `<xwysyy-frame>` mapping is emitted per physically rendered
//     subslide, so checker coverage counts real pages (handout safe) instead
//     of reconstructing page ranges from a frame count.
//
// Authors never write raw `v()` spacing or absolute coordinates; they adjust
// `mode` and read the numeric feedback the checker returns after each
// compile.  Numeric layout knobs live in the `tuning` dictionary (validated
// for key, type, and range); the AI generation contract treats `tuning` as
// off-limits and the telemetry records whether it was used.
//
// Stepwise reveal: touying's `#pause` cannot be used inside these components
// (marks do not survive `context` / `layout` closures; touying panics).
// Components take `reveal: true` (or per-item `reveal-from`) instead, which
// shows blocks one subslide at a time via the callback-style `utils.uncover`
// — hidden steps keep their measured space, so the layout is identical on
// every subslide.

#import "@preview/touying:0.7.4": utils
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
// does not read as sinking.  Only focus-slide centers a group; every other
// component fills the body instead.
#let _OPTICAL-CENTER = 0.46

// Fill-first distribution.  Outer margins are pinned small; leftover space
// grows the content (figures become dominant, cards become tall) instead of
// becoming blank margin.
#let _MARGIN-TOP = 0.07
#let _MARGIN-BOT = 0.09
#let _FILL = 1.0 - 0.07 - 0.09
// A card row occupies at least this fraction of the body height, so a row of
// short cards reads as substantial cards rather than tiles floating in space.
#let _CARD-FILL-MIN = 0.60
// Hard minimum for a stretch visual: below this the visual is starved and the
// slide must degrade to tight/overflow instead of reporting normal.
#let _VISUAL-MIN = 0.28
// Semantic gaps compress down to this fraction of their preferred size before
// the slide starts consuming its outer margins.
#let _GAP-MIN = 0.4
// Card inner padding.
#let _CARD-PAD = 0.9em
// stat-slide shrinks a long value to fit its tile, but never below this scale
// (below it the value wraps and the tile grows, reported honestly by fit).
#let _STAT-SCALE-MIN = 0.6

#let _MODES = ("compact", "balanced", "separated")
#let _check-mode(mode) = {
  if mode not in _MODES {
    panic("unknown mode " + repr(mode) + "; use \"compact\" | \"balanced\" | \"separated\"")
  }
}

// Gap between semantically-related blocks, as a fraction of body height.  The
// three values land inside the checker's proximity ranges so a correctly
// generated slide passes without diagnostics.
#let _mode-gap(mode) = {
  if mode == "compact" { 0.06 } else if mode == "separated" { 0.22 } else { 0.13 }
}
#let _mode-proximity(mode) = {
  if mode == "compact" { "compact" } else if mode == "separated" { "loose" } else { "medium" }
}

// Numeric layout knobs, validated for key, type, and range so a typo or a
// nonsense value fails loudly instead of being silently ignored.
// `spec` maps key -> (default:, lo:, hi:).
#let _tuning(comp, given, spec) = {
  for (k, v) in given {
    if k not in spec {
      panic(comp + ": unknown tuning key " + repr(k) + "; allowed: " + repr(spec.keys()))
    }
    if type(v) != float and type(v) != int {
      panic(comp + ": tuning " + repr(k) + " must be a number, got " + repr(v))
    }
    let s = spec.at(k)
    if v < s.lo or v > s.hi {
      panic(comp + ": tuning " + repr(k) + " = " + repr(v) + " outside [" + repr(s.lo) + ", " + repr(s.hi) + "]")
    }
  }
  let out = (:)
  for (k, s) in spec { out.insert(k, float(given.at(k, default: s.default))) }
  out
}

#let _require(comp, slot, v) = {
  if v == none { panic(comp + ": " + slot + " is required") }
}

// Reveal gating.  The block becomes visible from subslide `step` (1-based);
// hidden steps keep their measured space.  Uses the callback-style
// `utils.uncover` because mark-based `#pause` / global `#uncover` panic inside
// `context` / `layout`.
#let _from(self, step, body) = {
  if step <= 1 { body } else { utils.uncover(self: self, str(step) + "-", body) }
}

// ---------------------------------------------------------------------------
// typed items (declared sizing; every component slot takes them)
// ---------------------------------------------------------------------------
//
// `visual(...)` marks the slide's visual payload: never carded, and with
// fit: "stretch" (the default) it absorbs free space and its content is told
// to fill the allocated frame (use `rect(height: 100%)`, or
// `image(width: 100%, height: 100%, fit: "contain")` for real images).
// fit: "natural" keeps the visual at its measured size (`image(width: 100%)`).
// `card(...)` / `takeaway(...)` draw the theme card behind their content.
// `plain(...)` is an uncarded text block.  Plain (untyped) content passed to
// a slot is coerced per component (documented at each component).

#let visual(body, fit: "stretch", role: "main_visual", reveal-from: auto) = {
  if fit not in ("stretch", "natural") {
    panic("visual: fit must be \"stretch\" or \"natural\", got " + repr(fit))
  }
  (xwysyy-item: true, kind: "visual", fit: fit, role: role, body: body, reveal-from: reveal-from)
}
#let card(body, role: "explanation", reveal-from: auto) = (
  xwysyy-item: true, kind: "card", fit: "natural", role: role, body: body, reveal-from: reveal-from,
)
#let takeaway(body, reveal-from: auto) = (
  xwysyy-item: true, kind: "takeaway", fit: "natural", role: "takeaway", body: body, reveal-from: reveal-from,
)
#let plain(body, role: "text", reveal-from: auto) = (
  xwysyy-item: true, kind: "plain", fit: "natural", role: role, body: body, reveal-from: reveal-from,
)

#let _as-item(x, default-kind) = {
  if type(x) == dictionary and x.at("xwysyy-item", default: false) { x }
  else if default-kind == "visual" {
    (xwysyy-item: true, kind: "visual", fit: "natural", role: "main_visual", body: x, reveal-from: auto)
  } else if default-kind == "takeaway" {
    (xwysyy-item: true, kind: "takeaway", fit: "natural", role: "takeaway", body: x, reveal-from: auto)
  } else if default-kind == "plain" {
    (xwysyy-item: true, kind: "plain", fit: "natural", role: "text", body: x, reveal-from: auto)
  } else {
    (xwysyy-item: true, kind: "card", fit: "natural", role: "explanation", body: x, reveal-from: auto)
  }
}

#let _painted(it) = it.kind in ("card", "takeaway")
#let _stretchy(it) = it.kind == "visual" and it.fit == "stretch"

// Resolve per-item reveal steps.  `reveal: true` reveals item i on subslide
// min(i+1, max-step); an explicit `reveal-from` must be an integer in
// [1, max-step].
#let _steps(comp, items, reveal, max-step) = {
  items.enumerate().map(((i, it)) => {
    let rf = it.at("reveal-from", default: auto)
    if rf == auto {
      if reveal { calc.min(i + 1, max-step) } else { 1 }
    } else {
      if type(rf) != int {
        panic(comp + ": reveal-from must be an integer >= 1, got " + repr(rf))
      }
      if rf < 1 or rf > max-step {
        panic(comp + ": reveal-from = " + str(rf) + " outside [1, " + str(max-step) + "]")
      }
      rf
    }
  })
}

// ---------------------------------------------------------------------------
// allocator
// ---------------------------------------------------------------------------
//
// Column: every item is a spec (min:, pref:, max:, grow:) in absolute
// lengths (max: none = unbounded); every gap is (min:, pref:).  Resolution
// order and states:
//   normal     — everything at preferred fits the safe area; free space goes
//                to grow-weighted items (water-filling against max); residual
//                free space centers the group inside the safe area
//   compressed — fits the safe area only with gaps squeezed below preferred
//                (but not below their min); gap_scale in (0, 1)
//   tight      — fits the page only by consuming the outer margins; gaps at
//                min, group centered on the page; margin_deficit_ratio > 0
//   overflow   — taller than the page even at minimums;
//                body_overflow_ratio > 0 (hard invariant)
#let _alloc-column(specs, gaps, H) = {
  let budget = H * _FILL
  let prefs = specs.map(s => calc.max(s.pref, s.min))
  let body = prefs.fold(0pt, (a, h) => a + h)
  let gap-pref = gaps.fold(0pt, (a, g) => a + g.pref)
  let gap-min = gaps.fold(0pt, (a, g) => a + g.min)
  let base = body + gap-pref
  if base <= budget {
    let heights = prefs
    let free = budget - base
    let frozen = specs.map(s => s.grow <= 0)
    while free > 0.05pt {
      let gsum = 0.0
      for (i, s) in specs.enumerate() {
        if not frozen.at(i) { gsum += s.grow }
      }
      if gsum == 0 { break }
      let spent = 0pt
      for (i, s) in specs.enumerate() {
        if frozen.at(i) { continue }
        let add = free * (s.grow / gsum)
        if s.max != none and heights.at(i) + add >= s.max {
          add = calc.max(s.max - heights.at(i), 0pt)
          frozen.at(i) = true
        }
        heights.at(i) += add
        spent += add
      }
      free -= spent
      if spent <= 0.05pt { break }
    }
    let used = heights.fold(0pt, (a, h) => a + h) + gap-pref
    (heights: heights, gaps: gaps.map(g => g.pref),
     y0: H * _MARGIN-TOP + calc.max(budget - used, 0pt) / 2,
     fit: (state: "normal", required_height_ratio: base / H, gap_scale: 1.0,
           margin_deficit_ratio: 0.0, body_overflow_ratio: 0.0))
  } else if body + gap-min <= budget {
    let span = gap-pref - gap-min
    let t = if span > 0pt { (budget - body - gap-min) / span } else { 1.0 }
    (heights: prefs, gaps: gaps.map(g => g.min + (g.pref - g.min) * t),
     y0: H * _MARGIN-TOP,
     fit: (state: "compressed", required_height_ratio: base / H, gap_scale: t,
           margin_deficit_ratio: 0.0, body_overflow_ratio: 0.0))
  } else if body + gap-min <= H {
    let total = body + gap-min
    (heights: prefs, gaps: gaps.map(g => g.min), y0: (H - total) / 2,
     fit: (state: "tight", required_height_ratio: base / H, gap_scale: 0.0,
           margin_deficit_ratio: (total - budget) / H, body_overflow_ratio: 0.0))
  } else {
    let total = body + gap-min
    (heights: prefs, gaps: gaps.map(g => g.min), y0: 0pt,
     fit: (state: "overflow", required_height_ratio: base / H, gap_scale: 0.0,
           margin_deficit_ratio: (H - budget) / H, body_overflow_ratio: (total - H) / H))
  }
}

// Row variant: one shared height for side-by-side cards.  No gaps to
// compress, so the states are normal / tight / overflow.
#let _fit-row(naturals, H) = {
  let natural = naturals.fold(0pt, (a, h) => calc.max(a, h))
  let budget = H * _FILL
  if natural <= budget {
    let row = _clamp(natural, _CARD-FILL-MIN * H, budget)
    (row: row, y: H * _MARGIN-TOP + (budget - row) / 2,
     fit: (state: "normal", required_height_ratio: natural / H, gap_scale: 1.0,
           margin_deficit_ratio: 0.0, body_overflow_ratio: 0.0))
  } else if natural <= H {
    (row: natural, y: (H - natural) / 2,
     fit: (state: "tight", required_height_ratio: natural / H, gap_scale: 1.0,
           margin_deficit_ratio: (natural - budget) / H, body_overflow_ratio: 0.0))
  } else {
    (row: natural, y: 0pt,
     fit: (state: "overflow", required_height_ratio: natural / H, gap_scale: 1.0,
           margin_deficit_ratio: (H - budget) / H, body_overflow_ratio: (natural - H) / H))
  }
}

// ---------------------------------------------------------------------------
// measurement
// ---------------------------------------------------------------------------

// Measure a natural item for a slot of width `w`.  Returns the outer size the
// allocator uses (including card padding), the 2-D payload flow bbox, and the
// padding.  Panics when the content renders empty: `measure` resolves percent
// heights to 0 in an unbounded context, so an empty measurement is either a
// genuinely empty slot or percent-sized content that must be declared
// `visual(...)` — both are authoring errors that must not produce telemetry.
#let _measure-item(comp, slot, it, w) = {
  let pad = if _painted(it) { _CARD-PAD.to-absolute() } else { 0pt }
  let iw = w - 2 * pad
  let mu = measure(it.body)
  let mc = measure(block(width: iw, it.body))
  if mu.width < 0.01pt and mu.height < 0.01pt and mc.height < 0.01pt {
    panic(comp + ": " + slot + " renders empty — pass real content; percent-sized content "
      + "measures as zero and must be declared visual() (fit: \"stretch\")")
  }
  (
    outer: mc.height + 2 * pad,
    pay-w: if mu.width < 0.01pt { iw } else { calc.min(mu.width, iw) },
    pay-h: mc.height,
    pad: pad,
  )
}

// Build the allocator spec and telemetry seed for one column/slot item.
// Stretch visuals get the hard minimum and a grow weight; natural items are
// pinned at their measured size (max = pref) unless the component grants
// cards a grow weight.
#let _item-slot(comp, slot, it, w, H) = {
  if _stretchy(it) {
    (stretch: true, painted: false, pad: 0pt,
     spec: (min: H * _VISUAL-MIN, pref: H * _VISUAL-MIN, max: none, grow: 1.0),
     pay-w: none, pay-h: none)
  } else {
    let m = _measure-item(comp, slot, it, w)
    (stretch: false, painted: _painted(it), pad: m.pad,
     spec: (min: m.outer, pref: m.outer, max: m.outer, grow: 0.0),
     pay-w: m.pay-w, pay-h: m.pay-h)
  }
}

// ---------------------------------------------------------------------------
// telemetry primitives (schema v3)
// ---------------------------------------------------------------------------

// One telemetry object.
//   frame     — the box the component allocated (normalized to the body)
//   preferred — the natural outer size the allocator saw
//   payload   — 2-D flow bbox of the inner content (inside card padding);
//               approximate for wrapped text (flow bbox, not glyph ink);
//               equals the padded frame for stretch content
//   paint     — the visible card box, or none for unpainted objects
// Payload height is NOT clamped to the frame: overflowing content reports a
// payload that runs past its frame, and the checker sees it.
#let _obj(
  id, kind, role, group,
  fx, fy, fw, fh,
  pref-w: none, pref-h: none,
  pay-w: none, pay-h: none,
  pad-x: 0.0, pad-y: 0.0,
  calign: "center", halign: "center",
  painted: false, visible-from: 1,
) = {
  let ix = fx + pad-x
  let iy = fy + pad-y
  let iw = calc.max(fw - 2 * pad-x, 0.0)
  let ih = calc.max(fh - 2 * pad-y, 0.0)
  let sx = if pay-w == none { "stretch" } else { "natural" }
  let sy = if pay-h == none { "stretch" } else { "natural" }
  let pw = if pay-w == none { iw } else { calc.min(pay-w, iw) }
  let ph = if pay-h == none { ih } else { pay-h }
  let px = if sx == "stretch" or halign == "left" { ix } else { ix + (iw - pw) / 2 }
  let py = if sy == "stretch" or calign == "top" { iy } else { iy + (ih - ph) / 2 }
  (
    id: id,
    object_kind: kind,
    semantic_role: role,
    group: group,
    frame: (x: fx, y: fy, w: fw, h: fh),
    preferred: (w: if pref-w == none { fw } else { pref-w },
                h: if pref-h == none { fh } else { pref-h }),
    payload: (x: px, y: py, w: pw, h: ph),
    paint: if painted { (x: fx, y: fy, w: fw, h: fh) } else { none },
    sizing: (x: sx, y: sy),
    visible_from: visible-from,
  )
}

#let _rel(from, to, kind, axis, proximity) = (
  from: from,
  to: to,
  kind: kind,
  axis: axis,
  desired_proximity: proximity,
)

// One frame mapping per physically rendered subslide.  In handout mode only
// the surviving subslide emits, so coverage counts real pages instead of
// reconstructing `page - frame_count + 1 .. page` (which wrongly covers the
// preceding page when subslides collapse).
#let _frame-mark(sid, self) = [
  #metadata((
    schema: "xwysyy-frame/v1",
    id: sid,
    step: self.subslide,
    steps: self.at("repeat", default: 1),
    page: here().position().page,
    handout: self.at("handout", default: false),
  )) <xwysyy-frame>
]

// Emit one slide's telemetry.  Must be produced in markup so the label binds
// (a label on `metadata(...)` in code mode is a Typst syntax error).
#let _emit(id, archetype, engine, page, frame-count, objects, relations, fit, extra) = [
  #metadata((
    schema: "xwysyy-slide-layout/v3",
    id: id,
    archetype: archetype,
    layout_engine: engine,
    page: page,
    frame_count: frame-count,
    coordinate_system: "normalized-slide-body",
    objects: objects,
    relations: relations,
    fit: fit,
    extra: extra,
  )) <xwysyy-slide-layout>
]

// Debug overlay: solid rect = frame, dashed rect = payload bbox.
#let _debug-palette = (
  rgb("#d7263d"), rgb("#2e86ab"), rgb("#4f772d"),
  rgb("#7b2cbf"), rgb("#f77f00"), rgb("#006d77"),
)
#let _debug-layer(objects, W, H) = {
  for (i, o) in objects.enumerate() {
    let c = _debug-palette.at(calc.rem(i, _debug-palette.len()))
    let f = o.frame
    place(_atop + _aleft, dx: W * f.x, dy: H * f.y, rect(
      width: W * f.w, height: H * f.h,
      stroke: (paint: c, thickness: 0.7pt), fill: c.transparentize(93%),
    ))
    if o.sizing.y == "natural" or o.sizing.x == "natural" {
      let p = o.payload
      place(_atop + _aleft, dx: W * p.x, dy: H * p.y, rect(
        width: W * p.w, height: H * p.h,
        stroke: (paint: c, thickness: 0.5pt, dash: "dashed"),
      ))
    }
    place(_atop + _aleft, dx: W * f.x + 0.2em, dy: H * f.y + 0.12em,
      text(fill: c, size: 0.5em, weight: "bold", o.id))
  }
}

// Column container for slot rendering.  Cards draw the theme's rounded skyll
// box; `calign` controls where content sits inside a fixed-height box.
#let _card-box(cw, h, fill, body, cardp, calign: _ahorizon) = {
  let inner = if h == auto { body } else { align(calign, body) }
  if cardp {
    block(width: cw, height: h, fill: fill, inset: _CARD-PAD, radius: 0.4em, inner)
  } else {
    block(width: cw, height: h, inner)
  }
}

// Render one typed item into its allocated slot.
#let _render-item(it, w, h, fill, calign: _ahorizon) = {
  if _painted(it) {
    _card-box(w, h, fill, it.body, true, calign: calign)
  } else {
    block(width: w, height: h, align(_acenter + calign, it.body))
  }
}

// Resolve the slide id: `auto` becomes "<base>@p<page>", so telemetry from
// multiple unnamed slides of the same archetype stays distinguishable and a
// diagnostic can be located.  Must run inside a context (layout closure).
#let _sid(id, base) = {
  if id == auto { base + "@p" + str(here().position().page) } else { id }
}

// ---------------------------------------------------------------------------
// duo-slide — one vertical semantic pair (e.g. figure over takeaway)
// ---------------------------------------------------------------------------
//
// `top` coerces plain content to visual(fit: "natural"); wrap percent-height
// content in visual() to make it the growing dominant block.  `bottom`
// coerces plain content to card() (painted).

#let duo-slide(
  title: auto,
  id: auto,
  top: none,
  bottom: none,
  mode: "balanced",
  relation: "supports",
  reveal: false,
  debug: false,
  tuning: (:),
) = {
  _check-mode(mode)
  _require("duo-slide", "top", top)
  _require("duo-slide", "bottom", bottom)
  let tn = _tuning("duo-slide", tuning, (
    "top-width": (default: 0.82, lo: 0.3, hi: 0.95),
    "bottom-width": (default: 0.74, lo: 0.3, hi: 0.95),
  ))
  let ti = _as-item(top, "visual")
  let bi = _as-item(bottom, "card")
  let steps = _steps("duo-slide", (ti, bi), false, 2)
  if reveal { steps.at(1) = calc.max(steps.at(1), 2) }
  let rep = calc.max(..steps, 1)
  if _note-mode() {
    xwysyy-slide(title: title)[
      #block(ti.body)
      #if _painted(bi) { textbox(bi.body) } else { block(bi.body) }
    ]
  } else {
    xwysyy-slide(title: title, repeat: rep, self => context {
      let cfill = _theme-state.get().skyll
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "duo")
        _frame-mark(sid, self)
        let twn = tn.at("top-width")
        let bwn = tn.at("bottom-width")
        let tw = W * twn
        let bw = W * bwn
        let gap = H * _mode-gap(mode)
        let ts = _item-slot("duo-slide", "top", ti, tw, H)
        let bs = _item-slot("duo-slide", "bottom", bi, bw, H)
        let alloc = _alloc-column((ts.spec, bs.spec), ((min: gap * _GAP-MIN, pref: gap),), H)
        let th = alloc.heights.at(0)
        let bh = alloc.heights.at(1)
        let g = alloc.gaps.at(0)
        let y0 = alloc.y0

        place(_atop + _aleft, dx: (W - tw) / 2, dy: y0,
          _from(self, steps.at(0), _render-item(ti, tw, th, cfill)))
        place(_atop + _aleft, dx: (W - bw) / 2, dy: y0 + th + g,
          _from(self, steps.at(1), _render-item(bi, bw, bh, cfill)))

        let objects = (
          _obj(sid + ":top", ti.kind, ti.role, sid,
            (1.0 - twn) / 2, y0 / H, twn, th / H,
            pref-h: ts.spec.pref / H,
            pay-w: if ts.stretch { none } else { ts.pay-w / W },
            pay-h: if ts.stretch { none } else { ts.pay-h / H },
            pad-x: ts.pad / W, pad-y: ts.pad / H,
            halign: if ts.painted { "left" } else { "center" },
            painted: ts.painted, visible-from: steps.at(0)),
          _obj(sid + ":bottom", bi.kind, bi.role, sid,
            (1.0 - bwn) / 2, (y0 + th + g) / H, bwn, bh / H,
            pref-h: bs.spec.pref / H,
            pay-w: if bs.stretch { none } else { bs.pay-w / W },
            pay-h: if bs.stretch { none } else { bs.pay-h / H },
            pad-x: bs.pad / W, pad-y: bs.pad / H,
            halign: if bs.painted { "left" } else { "center" },
            painted: bs.painted, visible-from: steps.at(1)),
        )
        let relations = (
          _rel(sid + ":top", sid + ":bottom", relation, "vertical", _mode-proximity(mode)),
        )
        if self.subslide == rep {
          _emit(sid, "duo", "column", here().position().page, rep, objects, relations,
            alloc.fit, (mode: mode, gap_ratio: g / H, tuned: tuning.len() > 0))
          if debug { _debug-layer(objects, W, H) }
        }
      })
    })
  }
}

// ---------------------------------------------------------------------------
// focus-slide — a single centered block for low-content pages
// ---------------------------------------------------------------------------
//
// The one deliberate exception to fill-first: a focus page states a single
// point and is allowed its symmetric whitespace.  Plain content is coerced to
// card().  Fit still honours the safe area: content taller than it reports
// tight, taller than the page reports overflow.

#let focus-slide(
  title: auto,
  id: auto,
  body: none,
  debug: false,
  tuning: (:),
) = {
  _require("focus-slide", "body", body)
  let tn = _tuning("focus-slide", tuning, (
    "width": (default: 0.76, lo: 0.3, hi: 0.95),
    "center-y": (default: _OPTICAL-CENTER, lo: 0.30, hi: 0.70),
  ))
  let it = _as-item(body, "card")
  if _note-mode() {
    xwysyy-slide(title: title)[
      #if _painted(it) { textbox(it.body) } else { block(it.body) }
    ]
  } else {
    xwysyy-slide(title: title, self => context {
      let cfill = _theme-state.get().skyll
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "focus")
        _frame-mark(sid, self)
        let wn = tn.at("width")
        let cw = W * wn
        let m = _measure-item("focus-slide", "body", it, cw)
        let hr = m.outer / H
        let fit = if hr <= _FILL {
          (state: "normal", required_height_ratio: hr, gap_scale: 1.0,
           margin_deficit_ratio: 0.0, body_overflow_ratio: 0.0)
        } else if hr <= 1.0 {
          (state: "tight", required_height_ratio: hr, gap_scale: 1.0,
           margin_deficit_ratio: hr - _FILL, body_overflow_ratio: 0.0)
        } else {
          (state: "overflow", required_height_ratio: hr, gap_scale: 1.0,
           margin_deficit_ratio: 1.0 - _FILL, body_overflow_ratio: hr - 1.0)
        }
        let y = if fit.state == "normal" {
          _clamp(tn.at("center-y") - hr / 2, _MARGIN-TOP,
            calc.max(1.0 - _MARGIN-BOT - hr, _MARGIN-TOP))
        } else if fit.state == "tight" { (1.0 - hr) / 2 } else { 0.0 }

        place(_atop + _aleft, dx: (W - cw) / 2, dy: H * y,
          _render-item(it, cw, m.outer, cfill))

        let objects = (
          _obj(sid + ":focus", it.kind, it.role, sid,
            (1.0 - wn) / 2, y, wn, hr,
            pref-h: hr,
            pay-w: m.pay-w / W, pay-h: m.pay-h / H,
            pad-x: m.pad / W, pad-y: m.pad / H,
            halign: if _painted(it) { "left" } else { "center" },
            painted: _painted(it)),
        )
        _emit(sid, "focus", "single", here().position().page, 1, objects, (), fit,
          (center_y: tn.at("center-y"), intent: "focus", tuned: tuning.len() > 0))
        if debug { _debug-layer(objects, W, H) }
      })
    })
  }
}

// ---------------------------------------------------------------------------
// stack-slide — N vertical blocks, fill-first (duo generalized)
// ---------------------------------------------------------------------------
//
// Takes typed items; plain content is coerced to card().  Stretch visuals
// absorb the free space; a stack with no stretch visual grows its cards so
// every card reads tall.  With `reveal: true` item i appears on subslide i
// (override per item with `reveal-from`).

#let stack-slide(
  title: auto,
  id: auto,
  items: (),
  relation: "supports",
  mode: "balanced",
  reveal: false,
  debug: false,
  tuning: (:),
) = {
  _check-mode(mode)
  let tn = _tuning("stack-slide", tuning, (
    "width": (default: 0.82, lo: 0.3, hi: 0.95),
  ))
  let its = items.map(x => _as-item(x, "card"))
  let n = its.len()
  if n == 0 {
    panic("stack-slide: items is empty")
  }
  let steps = _steps("stack-slide", its, reveal, n)
  let rep = calc.max(..steps, 1)
  if _note-mode() {
    xwysyy-slide(title: title)[
      #for it in its {
        if _painted(it) { textbox(it.body) } else { block(it.body) }
      }
    ]
  } else {
    xwysyy-slide(title: title, repeat: rep, self => context {
      let cfill = _theme-state.get().skyll
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "stack")
        _frame-mark(sid, self)
        let wn = tn.at("width")
        let bw = W * wn
        let slots = its.enumerate().map(((i, it)) =>
          _item-slot("stack-slide", "items[" + str(i) + "]", it, bw, H))
        // Grow policy: stretch visuals absorb free space; without one, the
        // cards share it so a pure-text stack reads as tall cards.
        let has-stretch = slots.any(s => s.stretch)
        let specs = slots.enumerate().map(((i, s)) => {
          if s.stretch { s.spec }
          else if not has-stretch and its.at(i).kind == "card" {
            (min: s.spec.min, pref: s.spec.pref, max: none, grow: 1.0)
          } else { s.spec }
        })
        let gap = H * _mode-gap(mode)
        let alloc = _alloc-column(specs, ((min: gap * _GAP-MIN, pref: gap),) * (n - 1), H)

        let objects = ()
        let relations = ()
        let cy = alloc.y0
        for (i, it) in its.enumerate() {
          let h = alloc.heights.at(i)
          let s = slots.at(i)
          place(_atop + _aleft, dx: (W - bw) / 2, dy: cy,
            _from(self, steps.at(i), _render-item(it, bw, h, cfill)))
          let oid = sid + ":" + str(i)
          objects.push(_obj(oid, it.kind, it.role, sid,
            (1.0 - wn) / 2, cy / H, wn, h / H,
            pref-h: specs.at(i).pref / H,
            pay-w: if s.stretch { none } else { s.pay-w / W },
            pay-h: if s.stretch { none } else { s.pay-h / H },
            pad-x: s.pad / W, pad-y: s.pad / H,
            halign: if s.painted { "left" } else { "center" },
            painted: s.painted, visible-from: steps.at(i)))
          if i > 0 {
            relations.push(_rel(sid + ":" + str(i - 1), oid, relation, "vertical", _mode-proximity(mode)))
          }
          cy = cy + h + if i < n - 1 { alloc.gaps.at(i) } else { 0pt }
        }
        if self.subslide == rep {
          _emit(sid, "stack", "column", here().position().page, rep, objects, relations,
            alloc.fit, (mode: mode, count: n, tuned: tuning.len() > 0,
              gap_ratio: if n > 1 { alloc.gaps.at(0) / H } else { 0.0 }))
          if debug { _debug-layer(objects, W, H) }
        }
      })
    })
  }
}

// ---------------------------------------------------------------------------
// grid-slide — N equal-height peer columns (N >= 2)
// ---------------------------------------------------------------------------
//
// Columns take typed items; plain content is coerced to card().  Consecutive
// columns carry a `peer` relation so the checker validates the gutter.

#let grid-slide(
  title: auto,
  id: auto,
  columns: (),
  reveal: false,
  debug: false,
  tuning: (:),
) = {
  let tn = _tuning("grid-slide", tuning, (
    "gutter": (default: 0.04, lo: 0.0, hi: 0.2),
  ))
  let its = columns.map(x => _as-item(x, "card"))
  let n = its.len()
  if n < 2 {
    panic("grid-slide: needs at least 2 columns (use stack-slide or focus-slide for one block)")
  }
  let steps = _steps("grid-slide", its, reveal, n)
  let rep = calc.max(..steps, 1)
  if _note-mode() {
    xwysyy-slide(title: title)[
      #grid(columns: (1fr,) * n, column-gutter: 1em,
        ..its.map(it => if _painted(it) { textbox(it.body) } else { it.body }))
    ]
  } else {
    xwysyy-slide(title: title, repeat: rep, self => context {
      let cfill = _theme-state.get().skyll
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "grid")
        _frame-mark(sid, self)
        let gutter = tn.at("gutter")
        let cwn = (1.0 - gutter * (n - 1)) / n
        if cwn <= 0.0 {
          panic("grid-slide: gutter " + repr(gutter) + " leaves no width for " + repr(n) + " columns")
        }
        let cw = W * cwn
        let slots = its.enumerate().map(((i, it)) => {
          if _stretchy(it) {
            panic("grid-slide: columns[" + str(i) + "] is visual(fit: \"stretch\"); "
              + "row layouts size columns by their natural height — use fit: \"natural\"")
          }
          _item-slot("grid-slide", "columns[" + str(i) + "]", it, cw, H)
        })
        let naturals = slots.map(s => s.spec.pref)
        let row = _fit-row(naturals, H)

        let objects = ()
        let relations = ()
        for (i, it) in its.enumerate() {
          let s = slots.at(i)
          let xn = i * (cwn + gutter)
          place(_atop + _aleft, dx: W * xn, dy: row.y,
            _from(self, steps.at(i), _render-item(it, cw, row.row, cfill)))
          let oid = sid + ":" + str(i)
          objects.push(_obj(oid, it.kind, it.role, sid,
            xn, row.y / H, cwn, row.row / H,
            pref-h: s.spec.pref / H,
            pay-w: s.pay-w / W, pay-h: s.pay-h / H,
            pad-x: s.pad / W, pad-y: s.pad / H,
            halign: if s.painted { "left" } else { "center" },
            painted: s.painted, visible-from: steps.at(i)))
          if i > 0 {
            relations.push(_rel(sid + ":" + str(i - 1), oid, "peer", "horizontal", "gutter"))
          }
        }
        let nmax = naturals.fold(0pt, (a, h) => calc.max(a, h))
        let nmin = naturals.fold(nmax, (a, h) => calc.min(a, h))
        if self.subslide == rep {
          _emit(sid, "grid", "row", here().position().page, rep, objects, relations, row.fit, (
            count: n,
            gutter: gutter,
            natural_height_variance: (nmax - nmin) / H,
            tuned: tuning.len() > 0,
          ))
          if debug { _debug-layer(objects, W, H) }
        }
      })
    })
  }
}

// ---------------------------------------------------------------------------
// compare-slide — two equal-height cards read as a contrast
// ---------------------------------------------------------------------------
//
// Cards share one row height; content is TOP-aligned so the two openings sit
// on the same line, which is how a contrast is read.  Both sides are
// required; plain content is coerced to card().

#let compare-slide(
  title: auto,
  id: auto,
  left: none,
  right: none,
  reveal: false,
  debug: false,
  tuning: (:),
) = {
  _require("compare-slide", "left", left)
  _require("compare-slide", "right", right)
  let tn = _tuning("compare-slide", tuning, (
    "gutter": (default: 0.06, lo: 0.0, hi: 0.2),
  ))
  let li = _as-item(left, "card")
  let ri = _as-item(right, "card")
  let steps = _steps("compare-slide", (li, ri), false, 2)
  if reveal { steps.at(1) = calc.max(steps.at(1), 2) }
  let rep = calc.max(..steps, 1)
  if _note-mode() {
    xwysyy-slide(title: title)[
      #grid(columns: (1fr, 1fr), column-gutter: 1em,
        ..(li, ri).map(it => if _painted(it) { textbox(it.body) } else { it.body }))
    ]
  } else {
    xwysyy-slide(title: title, repeat: rep, self => context {
      let cfill = _theme-state.get().skyll
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "compare")
        _frame-mark(sid, self)
        let gutter = tn.at("gutter")
        let cwn = (1.0 - gutter) / 2
        let cw = W * cwn
        let ls = _item-slot("compare-slide", "left", li, cw, H)
        let rs = _item-slot("compare-slide", "right", ri, cw, H)
        if ls.stretch or rs.stretch {
          panic("compare-slide: sides are sized by their natural height — use fit: \"natural\" visuals")
        }
        let row = _fit-row((ls.spec.pref, rs.spec.pref), H)

        place(_atop + _aleft, dx: 0pt, dy: row.y,
          _from(self, steps.at(0), _render-item(li, cw, row.row, cfill, calign: _atop)))
        place(_atop + _aleft, dx: W * (cwn + gutter), dy: row.y,
          _from(self, steps.at(1), _render-item(ri, cw, row.row, cfill, calign: _atop)))

        let objects = (
          _obj(sid + ":left", li.kind, li.role, sid,
            0.0, row.y / H, cwn, row.row / H,
            pref-h: ls.spec.pref / H,
            pay-w: ls.pay-w / W, pay-h: ls.pay-h / H,
            pad-x: ls.pad / W, pad-y: ls.pad / H,
            calign: "top", halign: if ls.painted { "left" } else { "center" },
            painted: ls.painted, visible-from: steps.at(0)),
          _obj(sid + ":right", ri.kind, ri.role, sid,
            cwn + gutter, row.y / H, cwn, row.row / H,
            pref-h: rs.spec.pref / H,
            pay-w: rs.pay-w / W, pay-h: rs.pay-h / H,
            pad-x: rs.pad / W, pad-y: rs.pad / H,
            calign: "top", halign: if rs.painted { "left" } else { "center" },
            painted: rs.painted, visible-from: steps.at(1)),
        )
        let relations = (
          _rel(sid + ":left", sid + ":right", "contrast", "horizontal", "gutter"),
        )
        if self.subslide == rep {
          _emit(sid, "compare", "row", here().position().page, rep, objects, relations, row.fit, (
            gutter: gutter,
            natural_height_variance: calc.abs(ls.spec.pref - rs.spec.pref) / H,
            tuned: tuning.len() > 0,
          ))
          if debug { _debug-layer(objects, W, H) }
        }
      })
    })
  }
}

// ---------------------------------------------------------------------------
// stat-slide — a row of metric tiles (big value + label)
// ---------------------------------------------------------------------------
//
// Standalone row engine (shares `_fit-row`), so the value auto-shrink scale
// is measured here and exported in the telemetry.  `stats` is a list of
// dictionaries `(value: [...], label: [...])`; both fields are required.

#let stat-slide(
  title: auto,
  id: auto,
  stats: (),
  reveal: false,
  debug: false,
  tuning: (:),
) = {
  let n = stats.len()
  if n == 0 {
    panic("stat-slide: stats is empty")
  }
  for (i, s) in stats.enumerate() {
    if type(s) != dictionary or "value" not in s or "label" not in s or s.value == none or s.label == none {
      panic("stat-slide: stats[" + str(i) + "] must be (value: [...], label: [...])")
    }
  }
  let tn = _tuning("stat-slide", tuning, (
    "gutter": (default: 0.04, lo: 0.0, hi: 0.2),
  ))
  let steps = range(n).map(i => if reveal { i + 1 } else { 1 })
  let rep = calc.max(..steps, 1)
  if _note-mode() {
    xwysyy-slide(title: title)[
      #grid(columns: (1fr,) * n, column-gutter: 1em,
        ..stats.map(s => textbox[#align(_acenter, strong(s.value)) #align(_acenter, s.label)]))
    ]
  } else {
    xwysyy-slide(title: title, repeat: rep, self => context {
      let t = _theme-state.get()
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "stat")
        _frame-mark(sid, self)
        let gutter = tn.at("gutter")
        let cwn = (1.0 - gutter * (n - 1)) / n
        if cwn <= 0.0 {
          panic("stat-slide: gutter " + repr(gutter) + " leaves no width for " + repr(n) + " tiles")
        }
        let cw = W * cwn
        let pad = _CARD-PAD.to-absolute()
        let iw = cw - 2 * pad
        // Fit each value to its tile: shrink down to the floor scale, below
        // which the value wraps and the tile grows (reported by fit).
        let scales = stats.map(s => {
          let vw = measure(text(size: 2.6em, weight: 700, s.value)).width
          if vw > iw and vw > 0pt { calc.max(iw / vw, _STAT-SCALE-MIN) } else { 1.0 }
        })
        let tile(i) = {
          let s = stats.at(i)
          align(_acenter + _ahorizon, stack(
            spacing: 0.2em,
            align(_acenter, text(size: 2.6em * scales.at(i), weight: 700, fill: t.sea, s.value)),
            align(_acenter, text(size: 0.95em, fill: t.sea.lighten(12%), s.label)),
          ))
        }
        let pays = range(n).map(i => measure(block(width: iw, tile(i))))
        let naturals = pays.map(m => m.height + 2 * pad)
        let row = _fit-row(naturals, H)

        let objects = ()
        let relations = ()
        for i in range(n) {
          let xn = i * (cwn + gutter)
          place(_atop + _aleft, dx: W * xn, dy: row.y,
            _from(self, steps.at(i),
              block(width: cw, height: row.row, fill: t.skyll, inset: _CARD-PAD,
                radius: 0.4em, align(_ahorizon, tile(i)))))
          let oid = sid + ":" + str(i)
          objects.push(_obj(oid, "card", "metric", sid,
            xn, row.y / H, cwn, row.row / H,
            pref-h: naturals.at(i) / H,
            pay-w: calc.min(pays.at(i).width, iw) / W, pay-h: pays.at(i).height / H,
            pad-x: pad / W, pad-y: pad / H,
            painted: true, visible-from: steps.at(i)))
          if i > 0 {
            relations.push(_rel(sid + ":" + str(i - 1), oid, "peer", "horizontal", "gutter"))
          }
        }
        if self.subslide == rep {
          _emit(sid, "stat", "row", here().position().page, rep, objects, relations, row.fit, (
            count: n,
            gutter: gutter,
            value_scales: scales,
            tuned: tuning.len() > 0,
          ))
          if debug { _debug-layer(objects, W, H) }
        }
      })
    })
  }
}

// ---------------------------------------------------------------------------
// figure-slide — figure, tight caption, optional takeaway
// ---------------------------------------------------------------------------
//
// The caption is measured first and subtracted, then the figure slot receives
// an explicit height, so a stretch figure fills its slot instead of escaping
// the wrapper (Typst measures percentage heights as 0 in an unbounded
// context).  `fig` coerces plain content to visual(fit: "natural"); wrap it
// in visual() to make it fill.  `takeaway` coerces to a painted takeaway card.

#let figure-slide(
  title: auto,
  id: auto,
  fig: none,
  caption: none,
  takeaway: none,
  mode: "balanced",
  reveal: false,
  debug: false,
  tuning: (:),
) = {
  _check-mode(mode)
  _require("figure-slide", "fig", fig)
  let tn = _tuning("figure-slide", tuning, (
    "figure-width": (default: 0.80, lo: 0.3, hi: 0.95),
    "takeaway-width": (default: 0.74, lo: 0.3, hi: 0.95),
  ))
  let fi = _as-item(fig, "visual")
  let ki = if takeaway == none { none } else { _as-item(takeaway, "takeaway") }
  let cap = if caption == none { none } else {
    context text(size: 0.85em, fill: _theme-state.get().sea.lighten(12%), style: "italic", caption)
  }
  if _note-mode() {
    xwysyy-slide(title: title)[
      #align(_acenter, fi.body)
      #if cap != none { align(_acenter, cap) }
      #if ki != none { textbox(ki.body) }
    ]
  } else {
    let rep = if reveal and ki != none { 2 } else { 1 }
    xwysyy-slide(title: title, repeat: rep, self => context {
      let cfill = _theme-state.get().skyll
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "figure")
        _frame-mark(sid, self)
        let fwn = tn.at("figure-width")
        let twn = tn.at("takeaway-width")
        let fw = W * fwn
        let tw = W * twn
        let cap-gap = 0.5em.to-absolute()
        let mode-gap = H * _mode-gap(mode)

        let fs = _item-slot("figure-slide", "fig", fi, fw, H)
        let specs = (fs.spec,)
        let gaps = ()
        let cap-m = if cap != none {
          let m = measure(block(width: fw, cap))
          specs.push((min: m.height, pref: m.height, max: m.height, grow: 0.0))
          // The caption gap is tight by design and not compressible.
          gaps.push((min: cap-gap, pref: cap-gap))
          m
        } else { none }
        let ks = if ki != none {
          let s = _item-slot("figure-slide", "takeaway", ki, tw, H)
          specs.push(s.spec)
          gaps.push((min: mode-gap * _GAP-MIN, pref: mode-gap))
          s
        } else { none }
        let alloc = _alloc-column(specs, gaps, H)

        let objects = ()
        let relations = ()
        let cy = alloc.y0
        let idx = 0
        let fh = alloc.heights.at(idx)
        place(_atop + _aleft, dx: (W - fw) / 2, dy: cy, _render-item(fi, fw, fh, cfill))
        objects.push(_obj(sid + ":figure", fi.kind, fi.role, sid,
          (1.0 - fwn) / 2, cy / H, fwn, fh / H,
          pref-h: fs.spec.pref / H,
          pay-w: if fs.stretch { none } else { fs.pay-w / W },
          pay-h: if fs.stretch { none } else { fs.pay-h / H },
          pad-x: fs.pad / W, pad-y: fs.pad / H,
          painted: fs.painted))
        cy = cy + fh
        idx += 1
        if cap != none {
          cy = cy + alloc.gaps.at(idx - 1)
          let ch = alloc.heights.at(idx)
          place(_atop + _aleft, dx: (W - fw) / 2, dy: cy, block(width: fw, align(_acenter, cap)))
          let cm = measure(cap)
          objects.push(_obj(sid + ":caption", "plain", "caption", sid,
            (1.0 - fwn) / 2, cy / H, fwn, ch / H,
            pref-h: ch / H,
            pay-w: calc.min(cm.width, fw) / W, pay-h: cap-m.height / H))
          relations.push(_rel(sid + ":figure", sid + ":caption", "caption", "vertical", "tight"))
          cy = cy + ch
          idx += 1
        }
        if ki != none {
          cy = cy + alloc.gaps.at(idx - 1)
          let th = alloc.heights.at(idx)
          place(_atop + _aleft, dx: (W - tw) / 2, dy: cy,
            _from(self, if reveal { 2 } else { 1 }, _render-item(ki, tw, th, cfill)))
          let anchor = if cap != none { sid + ":caption" } else { sid + ":figure" }
          objects.push(_obj(sid + ":takeaway", ki.kind, ki.role, sid,
            (1.0 - twn) / 2, cy / H, twn, th / H,
            pref-h: ks.spec.pref / H,
            pay-w: ks.pay-w / W, pay-h: ks.pay-h / H,
            pad-x: ks.pad / W, pad-y: ks.pad / H,
            halign: if ks.painted { "left" } else { "center" },
            painted: ks.painted, visible-from: if reveal { 2 } else { 1 }))
          relations.push(_rel(anchor, sid + ":takeaway", "supports", "vertical", _mode-proximity(mode)))
        }
        if self.subslide == rep {
          _emit(sid, "figure", "column", here().position().page, rep, objects, relations,
            alloc.fit, (mode: mode, has_caption: cap != none, has_takeaway: ki != none,
              tuned: tuning.len() > 0))
          if debug { _debug-layer(objects, W, H) }
        }
      })
    })
  }
}

// ---------------------------------------------------------------------------
// sidebar-slide — a narrow label tab beside a wide content card
// ---------------------------------------------------------------------------
//
// No `reveal`: the label and its content have no presentation order.  Both
// slots take plain content (the component paints its own boxes; do not wrap
// the body in `textbox`).

#let sidebar-slide(
  title: auto,
  id: auto,
  label: none,
  body: none,
  debug: false,
  tuning: (:),
) = {
  _require("sidebar-slide", "label", label)
  _require("sidebar-slide", "body", body)
  let tn = _tuning("sidebar-slide", tuning, (
    "label-width": (default: 0.26, lo: 0.1, hi: 0.5),
    "gutter": (default: 0.04, lo: 0.0, hi: 0.2),
  ))
  if _note-mode() {
    xwysyy-slide(title: title)[
      #strong(label) \
      #body
    ]
  } else {
    xwysyy-slide(title: title, self => context {
      let t = _theme-state.get()
      layout(size => {
        let W = size.width
        let H = size.height
        let sid = _sid(id, "sidebar")
        _frame-mark(sid, self)
        let lwn = tn.at("label-width")
        let gutter = tn.at("gutter")
        let bwn = 1.0 - lwn - gutter
        if bwn <= 0.0 {
          panic("sidebar-slide: label-width " + repr(lwn) + " + gutter leaves no body width")
        }
        let lw = W * lwn
        let bw = W * bwn
        let pad = _CARD-PAD.to-absolute()
        // The label is measured with the same styled content it is rendered
        // with (bold via `set text`, not `strong`, whose show rule enlarges
        // the run and would make the measurement disagree with the render).
        let label-inner = {
          set text(weight: "bold")
          show raw: set text(fill: t.sea)
          label
        }
        let lm-u = measure(label-inner)
        let lm = measure(block(width: lw - 2 * pad, label-inner))
        let bm-u = measure(body)
        let bm = measure(block(width: bw - 2 * pad, body))
        if lm-u.width < 0.01pt and lm-u.height < 0.01pt and lm.height < 0.01pt {
          panic("sidebar-slide: label renders empty")
        }
        if bm-u.width < 0.01pt and bm-u.height < 0.01pt and bm.height < 0.01pt {
          panic("sidebar-slide: body renders empty")
        }
        let lh = lm.height + 2 * pad
        let bh = bm.height + 2 * pad
        let row = _fit-row((lh, bh), H)

        place(_atop + _aleft, dx: 0pt, dy: row.y,
          block(width: lw, height: row.row, fill: t.sea, inset: pad, radius: 0.4em,
            align(_ahorizon + _aleft, {
              // Label text is light (paper) on the dark sea tab; inline code
              // keeps its light chip but takes dark (sea) text so it stays
              // readable instead of light-on-light.
              set text(fill: t.paper)
              label-inner
            })))
        place(_atop + _aleft, dx: W * (lwn + gutter), dy: row.y,
          block(width: bw, height: row.row, fill: t.skyll, inset: pad, radius: 0.4em,
            align(_ahorizon, body)))

        let objects = (
          _obj(sid + ":label", "card", "label", sid,
            0.0, row.y / H, lwn, row.row / H,
            pref-h: lh / H,
            pay-w: (if lm-u.width < 0.01pt { lw - 2 * pad } else { calc.min(lm-u.width, lw - 2 * pad) }) / W,
            pay-h: lm.height / H,
            pad-x: pad / W, pad-y: pad / H,
            halign: "left", painted: true),
          _obj(sid + ":body", "card", "content", sid,
            lwn + gutter, row.y / H, bwn, row.row / H,
            pref-h: bh / H,
            pay-w: (if bm-u.width < 0.01pt { bw - 2 * pad } else { calc.min(bm-u.width, bw - 2 * pad) }) / W,
            pay-h: bm.height / H,
            pad-x: pad / W, pad-y: pad / H,
            halign: "left", painted: true),
        )
        let relations = (_rel(sid + ":label", sid + ":body", "labels", "horizontal", "gutter"),)
        _emit(sid, "sidebar", "row", here().position().page, 1, objects, relations, row.fit,
          (label_width: lwn, gutter: gutter, tuned: tuning.len() > 0))
        if debug { _debug-layer(objects, W, H) }
      })
    })
  }
}
