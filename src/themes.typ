// Theme color palettes, shared theme state, and inline highlight macros.

#let themes = (
  sky: (
    sea: rgb("#3b60a0"),
    sky: rgb("#bdd0f1"),
    skyl: rgb("#eff3ff"),
    skyll: rgb("#f4f9ff"),
    paper: rgb("#f5f6f8"),
    header-fill: none,
    header-text: none,
    page-fill: white,
  ),
  sunset: (
    sea: rgb("#970014"),
    sky: rgb("#D8A6A2"),
    skyl: rgb("#fdf0f0"),
    skyll: rgb("#FFF8F6"),
    paper: rgb("#f5f6f8"),
    header-fill: rgb("#F7EEE7"),
    header-text: rgb("#970014"),
    page-fill: rgb("#fffefd"),
  ),
)

// Default theme colors (sky)
#let sea = themes.sky.sea
#let sky = themes.sky.sky
#let skyl = themes.sky.skyl
#let skyll = themes.sky.skyll
#let paper = themes.sky.paper

// Theme state for dynamic components
#let _theme-state = state("xwysyy-theme", themes.sky)

#let red(body) = text(fill: rgb("#9c1d11"), body)
#let bred(body) = text(size: 1.1em, stroke: 0.02em + rgb("#9c1d11"), fill: rgb("#9c1d11"), body)
#let yellow(body) = text(fill: rgb("#d9ad20"), body)
#let byellow(body) = text(size: 1.1em, stroke: 0.02em + rgb("#d9ad20"), fill: rgb("#d9ad20"), body)
