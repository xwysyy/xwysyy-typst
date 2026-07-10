// Pixel cross-check fixture: geometry telemetry looks clean on both pages,
// so only the pixel stage of scripts/xwysyy-check can catch them.
//   * escape — a place() block paints into the semantic gap outside every
//     allocated frame (render_telemetry_mismatch);
//   * wide — an unbreakable token runs off the right page edge; the ink area
//     in the edge band is small, so the sliding-window row peak must flag it
//     (edge_ink).
#import "../../xwysyy.typ": *

#let visual-ci = sys.inputs.at("visual-ci", default: "false") == "true"
#let visual-font = if visual-ci { ("Liberation Serif", "Noto Serif CJK SC") } else { ("Times New Roman", "Noto Serif CJK SC") }

#show: xwysyy-pre.with(
  theme: "sky",
  lang: "en",
  font: visual-font,
  config-info(title: [Pixel cross-checks], author: " ", institution: " "),
)

= Pixels

#duo-slide(
  id: "escape",
  title: [escaping content],
  top: visual(rect(width: 100%, height: 100%, fill: rgb("#8ecae6"))),
  bottom: [
    *Sneaky.* This block also paints into the semantic gap above it:
    #place(top + left, dx: 1cm, dy: -1.6cm, rect(width: 6cm, height: 1.1cm, fill: rgb("#d00000")))
  ],
)

#stack-slide(
  id: "wide",
  title: [wide unbreakable token],
  items: (
    // A thin unbreakable strip instead of a long raw() token: its width must
    // not depend on which monospace font the environment resolves (CI has no
    // Maple Mono, so a glyph-based token renders at a different width there).
    [*Long token.* #box(rect(width: 28cm, height: 0.45em, fill: rgb("#219ebc")))],
    [*Normal.* A second card so the stack has rhythm.],
  ),
)
