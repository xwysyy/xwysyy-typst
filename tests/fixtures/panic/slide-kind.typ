// Must fail: a content slide cannot declare a checker-exempt full-bleed kind.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#xwysyy-slide(title: [x], kind: "image")[not really an image page]
