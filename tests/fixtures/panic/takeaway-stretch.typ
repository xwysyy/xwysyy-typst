// Must fail: the figure takeaway slot is sized by its natural height; a
// stretch visual must be rejected with a contract panic (formerly it crashed
// with a raw arithmetic error).
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#figure-slide(title: [x], fig: [figure body], takeaway: visual([t], fit: "stretch"))
