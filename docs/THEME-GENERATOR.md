# AI Theme Generator

Use this prompt with a multimodal model and your reference material. The output is a Typst dictionary that can be passed directly to `xwysyy-pre(theme: ...)` or `xwysyy-doc(theme: ...)`.

## Supported Inputs

- A screenshot of a slide, website, poster, or university page
- A PDF with an existing presentation style
- A color palette link or screenshot
- A text brief such as "deep green academic style" or "use #003366 as the school color"

## Prompt

Copy the full prompt below and attach your reference material.

````
I am using a Typst slide package named xwysyy. Please design a custom color theme dictionary.

## Output Format

Return a complete Typst dictionary named with an English lowercase name:

```typst
#let my-theme = (
  sea: rgb("#______"),
  sky: rgb("#______"),
  skyl: rgb("#______"),
  skyll: rgb("#______"),
  paper: rgb("#______"),
  page-fill: rgb("#______"),
)
```

These six fields are required. You may add an optional `header-text` field: when it is not `none`, it overrides the header title color; the default title color is `sea`.

## Fields

| Field | Visual Role |
|------|-------------|
| `sea` | Main dark color: default header title color, table header, links, outline badges |
| `sky` | Accent color: header rule gradient tail |
| `skyl` | Light background |
| `skyll` | Lightest component fill: code blocks, zebra rows, textboxes |
| `paper` | Text on dark backgrounds |
| `page-fill` | Slide page background |
| `header-text` (optional) | Header title color override; `none` falls back to `sea` |

## Hard Constraints

1. `paper` on `sea` must satisfy WCAG AA contrast, at least 4.5:1.
2. The header title color (`header-text` falling back to `sea`) on `page-fill` must satisfy WCAG AA contrast, at least 4.5:1.
3. `sea`, `sky`, `skyl`, and `skyll` should form a clear dark-to-light ramp.
4. `page-fill` must be visually separable from `skyll`, so code blocks and textboxes are visible.
5. Keep color temperature coherent. Warm main colors should use warm light backgrounds; cold main colors should use cold light backgrounds.

## Built-In References

sky:

```typst
#let sky-theme = (
  sea: rgb("#3b60a0"),
  sky: rgb("#bdd0f1"),
  skyl: rgb("#eff3ff"),
  skyll: rgb("#f4f9ff"),
  paper: rgb("#f5f6f8"),
  header-text: none,
  page-fill: white,
)
```

sunset:

```typst
#let sunset-theme = (
  sea: rgb("#970014"),
  sky: rgb("#D8A6A2"),
  skyl: rgb("#fdf0f0"),
  skyll: rgb("#FFF8F6"),
  paper: rgb("#f5f6f8"),
  header-text: none,
  page-fill: rgb("#fffefd"),
)
```

forest:

```typst
#let forest-theme = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  header-text: none,
  page-fill: white,
)
```

## Please Return

1. Theme name.
2. Complete Typst dictionary.
3. One-sentence style description.
4. Self-check report for the five constraints above.
````

## Use The Generated Theme

Paste the dictionary into your deck:

```typst
#import "@preview/xwysyy:0.4.0": *

#let forest = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  page-fill: white,
)

#show: xwysyy-pre.with(
  theme: forest,
  config-info(
    title: [My Talk],
    author: " ",
  ),
)
```

Compile:

```bash
typst compile main.typ
```

## Vendor Path For Maintainers

If you maintain a fork and want a named theme, add the dictionary to `src/themes.typ`:

```typst
#let themes = (
  sky: (...),
  sunset: (...),
  forest: (
    sea: rgb("#1f5d45"),
    sky: rgb("#a8d5ba"),
    skyl: rgb("#e9f5ee"),
    skyll: rgb("#f5fbf7"),
    paper: rgb("#f7faf8"),
    header-text: none,
    page-fill: white,
  ),
)
```

Then use:

```typst
#show: xwysyy-pre.with(theme: "forest", ...)
```

After changing built-in themes, run:

```bash
scripts/check-theme-contrast
scripts/gen-previews --with-baseline
```

## Tune An Existing Theme

Prompt:

````
Based on this xwysyy theme, adjust the main color to [your description].

```typst
#let forest = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  page-fill: white,
)
```

Return a complete replacement dictionary and a self-check report.
````
