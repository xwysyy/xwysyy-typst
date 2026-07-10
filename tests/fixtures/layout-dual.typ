// Dual-output fixture for the semantic layout components: the same source must
// compile as a slide deck (default) and as an A4 note (`--input mode=note`),
// where every component degrades to linear content.
#import "../../xwysyy.typ": *

#show: xwysyy-doc.with(
  title: [Layout components · dual output],
  author: " ",
  institution: " ",
)

= Components

#duo-slide(
  title: [duo],
  top: rect(width: 100%, height: 3cm, fill: rgb("#8ecae6")),
  bottom: [*Takeaway.* Figure over explanation.],
  reveal: true,
)

#focus-slide(title: [focus], body: [*One centered idea.*])

#grid-slide(title: [grid], columns: ([Left column.], [Right column.]))

#compare-slide(title: [compare], left: [Option A.], right: [Option B.])

#stack-slide(
  title: [stack],
  items: (visual(rect(width: 100%, height: 100%, fill: rgb("#bdd0f1"))), card([Second.]), takeaway([Third.])),
  reveal: true,
)

#stat-slide(title: [stat], stats: ((value: [38%], label: [metric]),))

#figure-slide(
  title: [figure],
  fig: rect(width: 100%, height: 2cm, fill: rgb("#8ecae6")),
  caption: [A caption.],
  takeaway: [*Takeaway.*],
)

#sidebar-slide(title: [sidebar], label: [Label], body: [Body text.])
