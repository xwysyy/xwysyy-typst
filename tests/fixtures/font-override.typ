#import "../../xwysyy.typ": *

#show: xwysyy-pre.with(
  font: ("Libertinus Serif",),
  code-font: "DejaVu Sans Mono",
  config-info(title: [Font Override], author: " "),
)

#title-slide()

== Font Surface

Body text and `inline code` use caller-provided font parameters.

```typst
#show: xwysyy-pre.with(font: ("Libertinus Serif",), code-font: "DejaVu Sans Mono")
```
