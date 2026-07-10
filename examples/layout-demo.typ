// Demo deck for the semantic layout layer (telemetry schema v3).
//
// Every slide below is produced by a semantic component: the author fills
// typed content items and the component measures, allocates, and exports
// telemetry.  Good slides pass the checker; the slides marked "problem" are
// deliberate content mistakes the checker is meant to catch (a component
// fixes spacing, but it cannot invent or remove content).
//
// Run: scripts/xwysyy-check examples/layout-demo.typ --pixels

#import "../xwysyy.typ": *

#let visual-ci = sys.inputs.at("visual-ci", default: "false") == "true"
#let visual-font = if visual-ci { ("Liberation Serif", "Noto Serif CJK SC") } else { ("Times New Roman", "Noto Serif CJK SC") }

#show: xwysyy-pre.with(
  theme: "sky",
  lang: "en",
  font: visual-font,
  config-info(
    title: [Semantic layout layer],
    subtitle: [Measured geometry, numeric feedback],
    author: " ",
    institution: " ",
  ),
)

// Placeholder visual.  Wrapped in `visual(...)` it fills the allocated frame
// (the layout contract for real images is
// `image(width: 100%, height: 100%, fit: "contain")`); pass a fixed height
// for a natural-size figure.
#let fig(label, h: 100%) = rect(
  width: 100%, height: h, radius: 4pt,
  fill: gradient.linear(rgb("#8ecae6"), rgb("#bdd0f1")),
  align(center + horizon, text(weight: "bold", label)),
)

#title-slide()

= Good layouts

#duo-slide(
  title: [duo · balanced figure and takeaway],
  id: "good-duo",
  top: visual(fig[Main visual]),
  bottom: card([*Takeaway.* The visual and its explanation stay one readable group; the gap breathes without splitting the slide.], role: "takeaway"),
  debug: true,
)

#focus-slide(
  title: [focus · a single centered message],
  id: "good-focus",
  body: [*Main conclusion.* One idea, centered on the optical axis, with balanced margins above and below.],
  debug: true,
)

#grid-slide(
  title: [grid · three balanced peer columns],
  id: "good-grid",
  columns: (
    [*Method.* Measure each block at compile time and allocate the body by declared sizing.],
    [*Feedback.* Export the measured geometry as machine-readable metadata.],
    [*Decision.* The agent reads numeric diagnostics, not rendered pixels.],
  ),
  debug: true,
)

#compare-slide(
  title: [compare · two options side by side],
  id: "good-compare",
  left: [*Rigid auto-layout.* Style converges, but authors cannot express intent.],
  right: [*Observable semi-auto.* The component fixes spacing, the agent tunes content.],
  debug: true,
)

#stack-slide(
  title: [stack · a dominant figure over two explanations],
  id: "good-stack",
  items: (
    visual(fig[Overview]),
    card([*Step one.* The author picks a semantic component and fills typed items.]),
    card([*Step two.* The checker reports density, fit, and relation quality.]),
  ),
  debug: true,
)

#stack-slide(
  title: [stack · pure text grows into tall cards],
  id: "good-stack-cards",
  items: (
    [*Measure.* Every block's rendered height is known at compile time.],
    [*Distribute.* Free space grows the cards instead of the margins.],
    [*Report.* The checker reads the exported geometry, not the source.],
  ),
  debug: true,
)

#duo-slide(
  title: [duo · reveal, takeaway on step two],
  id: "good-reveal",
  top: visual(fig[Main visual]),
  bottom: card([*Takeaway.* Appears on the second subslide; the layout does not shift.], role: "takeaway"),
  reveal: true,
  debug: true,
)

#stat-slide(
  title: [stat · a row of metric tiles],
  id: "good-stat",
  stats: (
    (value: [38%], label: [cost reduction]),
    (value: [0.4], label: [accuracy delta]),
    (value: [6], label: [datasets]),
  ),
  debug: true,
)

#figure-slide(
  title: [figure · figure, caption, takeaway],
  id: "good-figure",
  fig: visual(fig[Overview figure]),
  caption: [Fig 1. Accuracy holds while cost drops across six datasets.],
  takeaway: [*Takeaway.* The caption stays tight to the figure; the takeaway breathes below.],
  debug: true,
)

#sidebar-slide(
  title: [sidebar · label beside content],
  id: "good-sidebar",
  label: [Method],
  body: [Measure each block at compile time, distribute whitespace by rhythm, and export telemetry the checker reads. The label tab matches the content card height.],
  debug: true,
)

= Problems the checker catches

#focus-slide(
  title: [problem · low density],
  id: "bad-lowdensity",
  body: [*Ok.*],
  debug: true,
)

#duo-slide(
  title: [problem · small natural figure],
  id: "bad-smallfig",
  top: fig(h: 1.6cm)[Small fixed figure],
  bottom: [*Takeaway.* The figure keeps its tiny natural size, so the page barely inks the body.],
  debug: true,
)

#grid-slide(
  title: [problem · column imbalance],
  id: "bad-imbalance",
  columns: (
    [*Short.* A line.],
    [*Very long.* #lorem(40)],
    [*Short.* Another line.],
  ),
  debug: true,
)

#grid-slide(
  title: [problem · a large card holding one word],
  id: "bad-empty-card",
  columns: (
    [Ok.],
    [*Substantial.* This column actually explains something, so the row grows tall and the left card turns into an underfilled shell.],
  ),
  debug: true,
)

#duo-slide(
  title: [problem · content overflow],
  id: "bad-overflow",
  top: visual(fig[Main visual]),
  bottom: [*Overflowing text.* #lorem(230)],
  debug: true,
)

#grid-slide(
  title: [problem · column taller than the body],
  id: "bad-grid-overflow",
  columns: (
    [*Overflowing column.* #lorem(130)],
    [*Short.* A line.],
  ),
  debug: true,
)

#end-slide(title: [Telemetry first], body: [Spacing is handled. Feedback is numeric.])
