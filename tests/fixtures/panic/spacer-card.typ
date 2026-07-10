// Must fail: a card holding only vertical spacing has no measurable width
// (formerly its payload was silently expanded to the full slot width).
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#grid-slide(title: [x], columns: (card(v(6em)), card(v(6em))))
