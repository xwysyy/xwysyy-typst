#import "@preview/xwysyy:0.4.0": *

#show: xwysyy-pre.with(
  theme: "sky",
  config-info(
    title: [xwysyy Starter Deck],
    subtitle: [Academic slides in Typst],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)

#title-slide()

#outline-slide()

= Motivation

== One Minute Setup

Use `typst init @preview/xwysyy:0.4.0` to create this deck, then edit `main.typ`.

#textbox(
  [*Reusable components*

  `textbox`, #red[red highlights], #yellow[yellow highlights], tables, code blocks, and touying animations share one theme.],

  [*Theme control*

  Switch built-in themes with `theme: "sunset"` or pass a custom color dictionary directly.],
)

= Semantic layouts

// Layout components measure every block and distribute available space.

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
    [*Compose.* Choose the component that matches the slide's structure.],
  ),
)

#end-slide(
  title: [Thank You!],
  body: [Questions?],
)
