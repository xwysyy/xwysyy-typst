// Adversarial regression (GPT review P0#2): a stretch visual with empty
// content claims its full allocated frame as payload.  Geometry cannot see
// it (declared payload), so the pixel stage must report hollow_object.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#duo-slide(
  top: visual([]),
  bottom: [Explanation text about a figure which does not exist.],
)
