#import "../../xwysyy.typ": *

#show: xwysyy-pre.with(
  theme: "forest",
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
