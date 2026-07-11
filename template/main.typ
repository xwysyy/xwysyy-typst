#import "@preview/xwysyy:0.4.0": *

#show: xwysyy-pre.with(
  theme: "sky",
  config-info(
    title: [xwysyy Starter Deck],
    subtitle: [Academic slides in Typst],
    author: " ",
    date: [Date],
    institution: " ",
  ),
)

#title-slide()

#outline-slide()

= Motivation

#grid-slide(
  title: [One Minute Setup],
  columns: (
    [*Start editing.* This project came from `typst init @preview/xwysyy:0.4.0`; edit `main.typ` and reuse `textbox`, #red[red highlights], tables, code blocks, and touying animations.],
    [*Control the theme.* Switch built-in themes with `theme: "sunset"` or pass a custom color dictionary directly.],
  ),
)

= Semantic layouts

// The layout components measure every block, distribute space, and export
// telemetry that the template's scripts/xwysyy-check turns into numeric
// layout diagnostics. See the package's docs/LAYOUT.md.

#duo-slide(
  title: [A figure over its takeaway],
  top: visual(rect(
    width: 100%, height: 100%, radius: 4pt,
    fill: gradient.linear(rgb("#8ecae6"), rgb("#bdd0f1")),
    align(center + horizon, [Replace with `image(width: 100%, height: 100%, fit: "contain")`]),
  )),
  bottom: [*Takeaway.* The visual grows to fill the body; this card stays pinned below it.],
)

#grid-slide(
  title: [Three equal columns],
  columns: (
    [*Measure.* Every block's height is known at compile time.],
    [*Distribute.* Free space grows the cards, not the margins.],
    [*Check.* Run `scripts/xwysyy-check main.typ` after adding your content.],
  ),
)

#end-slide(
  title: [Thank You!],
  body: [Questions?],
)
