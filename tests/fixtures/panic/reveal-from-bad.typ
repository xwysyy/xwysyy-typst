// Must fail: reveal-from must be an integer in [1, item count].
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#stack-slide(title: [x], items: (card([a], reveal-from: 0), [b]))
