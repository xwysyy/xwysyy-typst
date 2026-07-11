#import "../../xwysyy.typ": *

#let visual-ci = sys.inputs.at("visual-ci", default: "false") == "true"
#let visual-font = if visual-ci { ("Liberation Serif", "Noto Serif CJK SC") } else { ("Times New Roman", "Noto Serif CJK SC") }

#show: xwysyy-pre.with(
  aspect-ratio: "4-3",
  theme: "sky",
  font: visual-font,
  config-info(title: [T], author: " ", institution: " "),
)

= S

== A very long slide title that keeps going and wraps onto a second line in four by three

Body.

#stack-slide(items: ([*A.* one], [*B.* two]))
