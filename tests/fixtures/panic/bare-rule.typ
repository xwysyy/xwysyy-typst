// Must fail: a bare horizontal rule has no measurable height — it is
// decoration, not content.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#stack-slide(title: [x], items: (card(line(length: 3cm)),))
