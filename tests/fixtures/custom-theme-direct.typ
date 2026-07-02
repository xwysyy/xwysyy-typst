#import "../../xwysyy.typ": *

#let forest-direct = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  header-fill: none,
  header-text: none,
  page-fill: white,
)

#show: xwysyy-pre.with(
  theme: forest-direct,
  config-info(
    title: [Custom Theme Dictionary],
    subtitle: [Direct theme parameter],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)

#title-slide()

#outline-slide()

= Surface

== Components

#textbox[
  This fixture checks that a generated theme dictionary can be passed directly to `theme`.
]

#figure(
  table(
    columns: (auto, auto),
    [Field], [Status],
    [Header], [Theme color],
    [Textbox], [Theme color],
  ),
  caption: [Custom theme dictionary check],
)
