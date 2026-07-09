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
  bottom: textbox[*Takeaway.* Figure over explanation.],
)

#focus-slide(title: [focus], body: textbox[*One centered idea.*])

#grid-slide(title: [grid], columns: ([Left column.], [Right column.]))

#compare-slide(title: [compare], left: [Option A.], right: [Option B.])

#stack-slide(title: [stack], blocks: (textbox[First.], textbox[Second.], textbox[Third.]))
