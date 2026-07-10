// Must fail: tuning value outside its validated range.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#stack-slide(title: [x], items: ([a], [b]), tuning: ("width": 1.5))
