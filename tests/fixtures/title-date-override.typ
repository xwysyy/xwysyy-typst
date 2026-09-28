// title-slide named arguments override config-info for that one slide,
// including the date.  Probes record which date text actually renders.
#import "../../xwysyy.typ": *

#show: xwysyy-pre.with(
  config-info(title: [Date check], author: " ", institution: " ", date: [GLOBAL DATE]),
)

#show "LOCAL DATE": it => [#metadata("local") <date-probe>#it]
#show "GLOBAL DATE": it => [#metadata("global") <date-probe>#it]

#title-slide(date: [LOCAL DATE])
