# USAGE - xwysyy API Reference

This document lists the public APIs exported by `xwysyy.typ`. Quick setup is in [README.md](../README.md). Color, font, layout, and CI maintenance notes are in [CUSTOMIZATION.md](./CUSTOMIZATION.md).

## 1. Install And Import

Create a new deck:

```bash
typst init @preview/xwysyy:0.3.0 my-talk
cd my-talk
typst compile main.typ
```

Import the package in an existing project:

```typst
#import "@preview/xwysyy:0.3.0": *
```

Local development examples in this repository use a relative import:

```typst
#import "../xwysyy.typ": *
```

Core dependencies are downloaded by Typst:

- `@preview/touying:0.7.4`
- `@preview/physica:0.9.8`

Optional drawing and theorem integrations live in `xwysyy-extras.typ`:

```typst
#import "@preview/xwysyy:0.3.0": *
#import "@preview/xwysyy:0.3.0/xwysyy-extras.typ": *
```

For local development, import `xwysyy-extras.typ` from the repository root. The extras entry adds `cetz`, `fletcher`, and `theorion`.

## 2. Slide Entry: `xwysyy-pre`

`xwysyy-pre` applies touying slide configuration, theme colors, font settings, and the slide show-chain.

### Signature

```typst
#let xwysyy-pre(
  aspect-ratio: "16-9",
  theme: "sky",
  font: ("Times New Roman", "Noto Serif CJK SC"),
  heading-font: ("Libertinus Sans", "Noto Sans CJK SC"),
  code-font: ("Maple Mono", "Noto Sans Mono CJK SC"),
  lang: "en",
  ..args,
  body,
)
```

### Parameters

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `aspect-ratio` | `"16-9"` | Presentation paper ratio, passed to touying as `presentation-<ratio>` |
| `theme` | `"sky"` | Built-in theme name or a complete theme dictionary |
| `font` | `("Times New Roman", "Noto Serif CJK SC")` | Body font fallback list |
| `heading-font` | `("Libertinus Sans", "Noto Sans CJK SC")` | Font for the open-header slide title |
| `code-font` | `("Maple Mono", "Noto Sans Mono CJK SC")` | Font fallback list for inline and block raw code |
| `lang` | `"en"` | Typst text language |
| `..args` | none | Extra touying configs such as `config-info(...)` or `config-common(...)` |
| `body` | required | Deck content |

### Example

```typst
#show: xwysyy-pre.with(
  theme: "sunset",
  font: ("Libertinus Serif",),
  code-font: "DejaVu Sans Mono",
  config-info(
    title: [Presentation Title],
    author: " ",
    date: datetime.today(),
  ),
)
```

### Theme Names And Dictionaries

Built-in themes:

```typst
theme: "sky"
theme: "sunset"
theme: "forest"
theme: "midnight"
theme: "violet"
theme: "graphite"
```

Direct dictionary:

```typst
#let forest = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  page-fill: white,
)

#show: xwysyy-pre.with(theme: forest, ...)
```

The dictionary must include all six fields: `sea`, `sky`, `skyl`, `skyll`, `paper`, and `page-fill`. An optional `header-text` field overrides the header title color; when it is absent or `none`, the title uses `sea`. All built-in themes ship `header-text: none`.

If a field is missing, compilation fails with the missing field name.

## 3. Slide Layouts

### 3.1 `title-slide`

```typst
#title-slide()
#title-slide(title: [Temporary title])
```

The slide reads `title`, `subtitle`, `author`, `institution`, and `date` from touying `config-info(...)`. Named arguments override the values for one title slide.

### 3.2 `outline-slide`

```typst
#let outline-slide(chapters: auto, title: auto)
```

`chapters: auto` collects level-one headings and filters `<touying:hidden>`. More than five sections switch to a two-column layout.

`title: auto` uses the current `text.lang`: `zh` gives `目录`, other languages give `Contents`.

```typst
#outline-slide()
#outline-slide(title: [Agenda])
#outline-slide(chapters: ([Intro], [Method], [Result]))
```

### 3.3 `xwysyy-slide`

Content slides are triggered by level-two headings:

```typst
== Slide Title

Content.
```

Explicit call:

```typst
#xwysyy-slide(title: [Custom Title])[
  Content.
]
```

### 3.4 `new-section-slide`

Level-one headings trigger section transition slides:

```typst
= Section Title
```

### 3.5 `image-slide`

```typst
#image-slide(
  img: image("screenshot.png"),
  body: [Caption text],
)
```

### 3.6 `end-slide`

```typst
#end-slide(title: [Thank You!], body: [Questions?])
```

## 4. Components

### 4.1 `textbox`

```typst
#let textbox(inset: 0.8em, radius: 0.4em, width: 100%, gutter: 0.6em, ..bodies)
```

One body creates one full-width box. Multiple bodies create equal-height columns.

```typst
#textbox[
  Single callout.
]

#textbox(
  [*Left*

  Content A],
  [*Right*

  Content B],
)
```

`textbox` reads `_theme-state`; slide mode uses the active theme and note mode uses the theme selected by `xwysyy-doc` or the default `sky` state.

### 4.2 `info`

```typst
#info[Project][xwysyy-typst]
```

Renders a left label and right description with flexible space between them.

### 4.3 Highlight Macros

| Macro | Output |
|-------|--------|
| `red(body)` | Red text |
| `bred(body)` | Larger red text with a light stroke |
| `yellow(body)` | Yellow text |
| `byellow(body)` | Larger yellow text with a light stroke |

## 5. Note Entry: `xwysyy-note`

```typst
#let xwysyy-note(
  doc,
  title: none,
  subtitle: none,
  font: ("Times New Roman", "Noto Serif CJK SC"),
  code-font: ("Maple Mono", "Noto Sans Mono CJK SC"),
  base-size: 10pt,
  lang: "en",
)
```

`xwysyy-note` is an A4 document entry with independent gray-scale show rules:

```typst
#show: xwysyy-note.with(
  title: "My Notes",
  subtitle: "2026",
  font: ("Libertinus Serif",),
  code-font: "DejaVu Sans Mono",
)
```

It sets A4 paper, 2 cm margins, numbered headings, gray table styles, gray code blocks, fixed blue links, and `>|` quote decoration.

## 6. Dual Output Entry: `xwysyy-doc`

`xwysyy-doc` routes one source to slides or notes. The default mode is `slides`; `--input mode=note` switches to A4 notes.

### Signature

```typst
#let xwysyy-doc(
  aspect-ratio: "16-9",
  theme: "sky",
  font: ("Times New Roman", "Noto Serif CJK SC"),
  heading-font: ("Libertinus Sans", "Noto Sans CJK SC"),
  code-font: ("Maple Mono", "Noto Sans Mono CJK SC"),
  lang: "en",
  base-size: 10pt,
  title: none,
  subtitle: none,
  author: " ",
  date: none,
  institution: " ",
  ..args,
  body,
)
```

### Example

```typst
#show: xwysyy-doc.with(
  title: [One Source, Two Outputs],
  subtitle: [Deck and A4 notes],
  theme: "forest",
)
```

Compile slides:

```bash
typst compile --root . examples/dual-source.typ dual-slides.pdf
```

Compile notes:

```bash
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
```

### Note-Mode Degradation Rules

| Slide API | Note-mode behavior |
|-----------|--------------------|
| `title-slide` | Skipped because `xwysyy-note` renders the title block |
| `outline-slide` | Converted to `#outline(title: ..., depth: 1)` |
| `new-section-slide` | Skipped; the original level-one heading remains in the note |
| `xwysyy-slide` | Explicit calls render an optional heading and body |
| `image-slide` | Converted to a figure when `img` is present |
| `end-slide` | Converted to a centered ending block |
| `#pause` | Note output keeps the complete content and does not create subslides |

## 7. Handouts

Touying handout mode is available through `config-common(handout: true)`. `examples/slides-sky.typ` exposes a command-line switch:

```typst
#let handout-mode = sys.inputs.at("handout", default: "false") == "true"

#show: xwysyy-pre.with(
  config-common(handout: handout-mode),
  ...
)
```

Compile the normal deck:

```bash
typst compile --root . examples/slides-sky.typ slides.pdf
```

Compile the handout:

```bash
typst compile --root . --input handout=true examples/slides-sky.typ slides-handout.pdf
```

Touying options such as `handout-subslides` and the `<touying:handout>` label can be passed through `config-common(...)` because `xwysyy-pre` forwards `..args` to `touying-slides`.

## 8. Speaker Notes And pdfpc

`xwysyy.typ` re-exports touying, so `#speaker-note` is available after importing xwysyy:

```typst
== Result

Main slide content.

#speaker-note[
  Mention the ablation table and the failure case.
]
```

Show notes on a second screen:

```typst
#show: xwysyy-pre.with(
  config-common(show-notes-on-second-screen: right),
  ...
)
```

Export pdfpc metadata:

```bash
typst query --root . examples/slides-sky.typ --field value --one "<pdfpc-file>" > slides-sky.pdfpc
```

The query output is JSON with page overlays and note text.

## 9. Show Rules

`xwysyy-elements` applies only in slide mode:

| Rule | Behavior |
|------|----------|
| `show strong` | Enlarges to 1.1em at weight 700 with slight tracking and baseline compensation, matching `bred` and `byellow` |
| `set list` and `set enum` | Theme-colored markers and spacing |
| `show emph` | Synthetic skew for CJK-friendly emphasis |
| `show figure.caption` | Smaller gray captions |
| `show figure.where(kind: table)` | Table captions on top |
| `show raw.where(block: true)` | Full-width code blocks with `code-font` |
| `show raw.where(block: false)` | Inline code chips with `code-font`; the chip fill is painted with `outset` so the code text keeps the surrounding baseline |
| `show link` | Underlined theme-colored links |
| Arrow string rules | `->`, `=>`, `<=>`, and related patterns render as math arrows; text already set in the `code-font` first family is skipped, so code content stays literal |
| `set table` and `show table.cell` | Seamless `sea` header row with bold `paper` text, zebra body rows (`skyll` on even rows), and `table.hline` defaulting to `0.5pt + sea.lighten(30%)` |

`xwysyy-note` has its own A4-focused show rules.

## 10. Optional Extras

Local development import:

```typst
#import "../xwysyy-extras.typ": *
```

Published-package users can copy the extras entry when they need drawing or theorem environments. The extras module wraps:

- `cetz-canvas` with touying reducer support
- `fletcher-diagram` with touying reducer support
- theorion environments such as `definition`, `theorem`, `lemma`, `proof`, and `remark`

When passing custom `frozen-counters`, include the defaults:

```typst
#show: xwysyy-pre.with(
  config-common(frozen-counters: (
    counter(figure), counter(math.equation), theorem-counter,
  )),
  ...
)
```

## 11. API Index

| Category | API |
|----------|-----|
| Entries | `xwysyy-pre`, `xwysyy-doc`, `xwysyy-note` |
| Slide layouts | `title-slide`, `outline-slide`, `xwysyy-slide`, `new-section-slide`, `image-slide`, `end-slide` |
| Components | `textbox`, `info` |
| Highlight macros | `red`, `bred`, `yellow`, `byellow` |
| Theme values | `themes`, `sea`, `sky`, `skyl`, `skyll`, `paper` |
