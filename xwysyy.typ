// xwysyy.typ — facade re-exporting every core submodule.
// Users do `#import "xwysyy.typ": *` to pull in themes, slides, and layout components.
// Optional cetz / fletcher / theorion integrations load through `xwysyy-extras()`.

#import "@preview/physica:0.9.8": *

#import "src/themes.typ": *
#import "src/elements.typ": *
#import "src/slides.typ": *
#import "src/layout.typ": *

#let xwysyy-extras() = {
  import "xwysyy-extras.typ" as extras
  extras
}

#show: super-T-as-transpose
