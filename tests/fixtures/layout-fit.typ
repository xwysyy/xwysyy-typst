// Fit-state regression fixture (allocator v3).
//
// Review findings live here as permanent regressions:
//   * sidebar-tight — natural height between the safe area (0.84H) and the
//     page (1.0H) must report fit.state == "tight" (an early exporter
//     compared against H, not the safe area, and reported overflow: false);
//   * duo-overflow-starved — a stretch visual carries a hard minimum
//     (0.28H), so a bottom block near 0.9H must produce a true overflow with
//     body_overflow_ratio > 0 (the v2 allocator reported "normal" and
//     rendered the visual at 0.01H);
//   * duo-compressed — content that fits the safe area only after squeezing
//     the semantic gap must report "compressed", not "overflow" (the v2
//     state machine called any gap squeeze an overflow, with
//     body_overflow_ratio == 0).
#import "../../xwysyy.typ": *

#let visual-ci = sys.inputs.at("visual-ci", default: "false") == "true"
#let visual-font = if visual-ci { ("Liberation Serif", "Noto Serif CJK SC") } else { ("Times New Roman", "Noto Serif CJK SC") }

#show: xwysyy-pre.with(
  theme: "sky",
  lang: "en",
  font: visual-font,
  config-info(title: [Fit states], subtitle: [ ], author: " ", institution: " "),
)

= Fit

#sidebar-slide(
  id: "sidebar-tight",
  title: [sidebar in the tight window],
  label: [Label],
  body: [#lorem(180)],
)

#duo-slide(
  id: "duo-overflow-starved",
  title: [duo overflow with a starved stretch visual],
  top: visual(rect(width: 100%, height: 100%, fill: rgb("#8ecae6"))),
  bottom: [#lorem(230)],
)

#duo-slide(
  id: "duo-compressed",
  title: [duo that fits only with a squeezed gap],
  top: rect(width: 100%, height: 3.4cm, fill: rgb("#8ecae6")),
  bottom: [#lorem(100)],
)
