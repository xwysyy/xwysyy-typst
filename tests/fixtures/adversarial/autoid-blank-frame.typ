// Adversarial regression (GPT review P0#1): both items reveal at step 2 and
// the slide has NO explicit id.  The auto id must stay stable across the
// reveal subslides so the checker joins the blank first frame to the record
// and reports empty_frame — with a page-number id this deck passed green.
#import "../../../xwysyy.typ": *
#show: xwysyy-pre.with(theme: "sky", config-info(title: [P], author: " ", institution: " "))
= S
#stack-slide(
  items: (
    card([First point appears at step two with a full sentence.], reveal-from: 2),
    card([Second point also appears at step two.], reveal-from: 2),
  ),
)
