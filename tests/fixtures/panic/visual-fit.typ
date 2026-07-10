// Must fail: visual() fit must be "stretch" or "natural".
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#duo-slide(title: [x], top: visual([v], fit: "cover"), bottom: [b])
