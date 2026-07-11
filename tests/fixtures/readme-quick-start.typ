#import "@preview/xwysyy:0.4.0": *

#show: xwysyy-pre.with(
  theme: "sunset",
  config-info(
    title: [My Presentation Title],
    subtitle: [Subtitle],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)

#title-slide()
#outline-slide()

= Section Title

== Slide Title

Body text with *bold* and #red[red highlight].

#textbox(
  [*Module A*

  First column],

  [*Module B*

  Second column],
)

#end-slide(title: [Thank You!], body: [Questions?])
