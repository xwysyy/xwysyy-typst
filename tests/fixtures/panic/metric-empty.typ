// Must fail: a metric value must render non-empty.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#stat-slide(title: [x], stats: (metric([], [label]),))
