// Must fail: focus-slide has exactly one frame; reveal-from must be rejected
// instead of silently ignored.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#focus-slide(title: [x], body: card([point], reveal-from: 2))
