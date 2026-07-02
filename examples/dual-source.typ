#import "../xwysyy.typ": *

#let visual-ci = sys.inputs.at("visual-ci", default: "false") == "true"
#let visual-font = if visual-ci { ("Liberation Serif", "Noto Serif CJK SC") } else { ("Times New Roman", "Noto Serif CJK SC") }
#let visual-code-font = if visual-ci { "DejaVu Sans Mono" } else { "Maple Mono" }

#show: xwysyy-doc.with(
  theme: "forest",
  font: visual-font,
  code-font: visual-code-font,
  title: [One Source, Two Outputs],
  subtitle: [Deck by default, A4 notes with --input mode=note],
  author: " ",
  date: datetime.today(),
  institution: " ",
  footer: [xwysyy-doc],
)

#title-slide()

#outline-slide()

= Motivation

== One File

The same source can be compiled as a 16:9 slide deck or as an A4 note handout.

#pause

The note output keeps the complete content and drops slide-only chrome.

#textbox(
  [*Deck mode*

  Uses `xwysyy-pre`, touying slides, section pages, headers, footers, and animations.],

  [*Note mode*

  Uses `xwysyy-note`, A4 pages, ordinary headings, and the same content blocks.],
)

= Shared Components

== Theme-Aware Blocks

#textbox[
  `textbox` remains available in both outputs. In note mode it uses the active theme state as a quiet callout color.
]

#figure(
  table(
    columns: (auto, auto),
    [Slide-only layout], [Note-mode degradation],
    [`title-slide`], [document title block],
    [`outline-slide`], [`#outline()`],
    [`new-section-slide`], [ordinary level-one heading],
    [`focus-slide`], [emphasis block],
    [`image-slide`], [figure],
    [`end-slide`], [centered ending block],
  ),
  caption: [Dual-output degradation rules],
)

#focus-slide[
  Focus Slide

  This becomes an emphasis block in note mode.
]

#image-slide(
  img: rect(width: 100%, height: 9em, fill: gradient.linear(sea, sky, angle: 135deg), radius: 0.4em),
  body: [Image slide becomes a figure in note mode.],
)

#end-slide(
  title: [End],
  body: [Compile with `typst compile --root . --input mode=note examples/dual-source.typ`.],
)
