// Must fail: an empty slot renders as zero-size content (formerly it was
// silently reported as a full stretch frame).
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#duo-slide(title: [x], top: [], bottom: [b])
