// Demo deck for the semantic layout layer.
//
// Every slide below is produced by a semantic component: the author fills
// content + roles + mode and the component measures, distributes whitespace,
// and exports telemetry.  Good slides pass the checker; the slides marked
// "problem" are deliberate content mistakes the checker is meant to catch
// (a component fixes spacing, but it cannot invent or remove content).

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

#let fig(label) = rect(
  width: 100%, height: 3.4cm, radius: 4pt,
  fill: gradient.linear(rgb("#8ecae6"), rgb("#bdd0f1")),
  align(center + horizon, text(weight: "bold", label)),
)

#title-slide()

= Good layouts

#duo-slide(
  title: [duo · balanced figure and takeaway],
  id: "good-duo",
  top: fig[Main visual],
  bottom: textbox[*Takeaway.* The visual and its explanation stay one readable group; the gap breathes without splitting the slide.],
  top-role: "main_visual",
  bottom-role: "takeaway",
  debug: true,
)

#focus-slide(
  title: [focus · a single centered message],
  id: "good-focus",
  body: textbox[*Main conclusion.* One idea, centered on the optical axis, with balanced margins above and below.],
  debug: true,
)

#grid-slide(
  title: [grid · three balanced peer columns],
  id: "good-grid",
  columns: (
    [*Method.* Measure each block at compile time.],
    [*Feedback.* Export normalized geometry as metadata.],
    [*Decision.* The agent reads numbers, not pixels.],
  ),
  roles: ("column", "column", "column"),
  debug: true,
)

#compare-slide(
  title: [compare · two options side by side],
  id: "good-compare",
  left: [*Rigid auto-layout.* Style converges, hard to express intent.],
  right: [*Observable semi-auto.* Component fixes spacing, agent tunes content.],
  debug: true,
)

#stack-slide(
  title: [stack · three blocks on one rhythm],
  id: "good-stack",
  blocks: (
    fig[Overview],
    textbox[*Step one.* Author picks a component.],
    textbox[*Step two.* Checker reports density and fit.],
  ),
  roles: ("main_visual", "explanation", "explanation"),
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
  fig: fig[Overview figure],
  caption: [Fig 1. Accuracy holds while cost drops across six datasets.],
  takeaway: textbox[*Takeaway.* The caption stays tight to the figure; the takeaway breathes below.],
  debug: true,
)

#sidebar-slide(
  title: [sidebar · label beside content],
  id: "good-sidebar",
  label: [Method],
  body: textbox[Measure each block at compile time, distribute whitespace by rhythm, and export telemetry the checker reads. The label tab matches the content card height.],
  debug: true,
)

= Problems the checker catches

#focus-slide(
  title: [problem · low density],
  id: "bad-lowdensity",
  body: textbox[*Ok.*],
  debug: true,
)

#grid-slide(
  title: [problem · column imbalance],
  id: "bad-imbalance",
  columns: (
    [*Short.* A line.],
    [*Very long.* #lorem(70)],
    [*Short.* Another line.],
  ),
  roles: ("column", "column", "column"),
  debug: true,
)

#duo-slide(
  title: [problem · content overflow],
  id: "bad-overflow",
  top: fig[Main visual],
  bottom: textbox[*Overflowing text.* #lorem(150)],
  debug: true,
)

#grid-slide(
  title: [problem · column taller than the body],
  id: "bad-grid-overflow",
  columns: (
    [*Overflowing column.* #lorem(130)],
    [*Short.* A line.],
  ),
  roles: ("column", "column"),
  debug: true,
)

#end-slide(title: [Telemetry first], body: [Spacing is handled. Feedback is numeric.])
