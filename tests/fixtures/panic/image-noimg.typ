// Must fail: an image slide without an image would be a spoofed full-bleed
// exemption carrying arbitrary body content.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#image-slide(body: [caption without an image])
