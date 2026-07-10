// Must fail: every stat needs both value and label.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#stat-slide(title: [x], stats: ((value: [38%]),))
