// Must fail: sidebar slots take plain content, not typed items.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#sidebar-slide(title: [x], label: card([L]), body: [b])
