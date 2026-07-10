// Must fail: grid-slide needs at least 2 columns.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#grid-slide(title: [x], columns: ([only one],))
