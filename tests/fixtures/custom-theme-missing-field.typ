#import "../../xwysyy.typ": *

#let broken-theme = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  header-fill: none,
  header-text: none,
)

#show: xwysyy-pre.with(theme: broken-theme)

== Missing field check

This file must fail because `page-fill` is missing.
