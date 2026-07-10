// Must fail: roles form a closed set; "decorative" is not an escape hatch
// that removes an object from the checker.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#stack-slide(title: [x], items: (plain([a], role: "decorative"),))
