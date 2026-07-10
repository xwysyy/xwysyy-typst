// Handout-coverage regression fixture.
//
// A hand-written content page followed by a reveal component.  In handout
// mode only the final subslide of the reveal survives, so coverage must come
// from the per-rendered-subslide <xwysyy-frame> mappings: reconstructing
// `page - frame_count + 1 .. page` would wrongly mark the hand-written page
// as covered and mask its telemetry_gap.
#import "../../xwysyy.typ": *

#let handout = sys.inputs.at("handout", default: "false") == "true"

#show: xwysyy-pre.with(
  theme: "sky",
  lang: "en",
  config-info(title: [Handout coverage], author: " ", institution: " "),
  config-common(handout: handout),
)

= Coverage

== Hand-written page

This page uses no layout component and must be reported as a telemetry gap
in both normal and handout builds.

#stack-slide(
  id: "rev",
  title: [reveal stack],
  items: (
    [*First.* Appears on step one.],
    [*Second.* Appears on step two.],
  ),
  reveal: true,
)
