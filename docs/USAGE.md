# USAGE - xwysyy API Reference

This document lists the public APIs exported by `xwysyy.typ`. Quick setup is in [README.md](../README.md). Color, font, layout, and CI maintenance notes are in [CUSTOMIZATION.md](./CUSTOMIZATION.md).

## 1. Install And Import

Create a new deck:

```bash
typst init @preview/xwysyy:0.4.0 my-talk
cd my-talk
typst compile main.typ
```

Import the package in an existing project:

```typst
#import "@preview/xwysyy:0.4.0": *
```

Local development examples in this repository use a relative import:

```typst
#import "../xwysyy.typ": *
```

Core dependencies are downloaded by Typst:

- `@preview/touying:0.7.4`
- `@preview/physica:0.9.8`

Optional drawing and theorem integrations load through `xwysyy-extras()`:

```typst
#import "@preview/xwysyy:0.4.0": *
#import xwysyy-extras(): *
```

The loader imports `xwysyy-extras.typ` only when called. A core import does not resolve the optional `cetz`, `fletcher`, or `theorion` packages.

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

### 3.7 Semantic Layout Components

For figure/text pages where spacing matters (especially agent-generated decks), use the semantic layout components instead of hand-written `#v()` spacing. Slots take typed items with declared sizing (`visual(fit: "stretch"|"natural")`, `card(...)`, `takeaway(...)`, `plain(...)`); each component measures every block, distributes space fill-first (stretch visuals grow dominant, cards grow tall), and exports `<xwysyy-slide-layout>` v4 telemetry (frame, preferred size, 2-D payload bbox with a measured/declared source, and paint box + fill per object) that `scripts/xwysyy-check` turns into numeric diagnostics with machine-actionable fixes, plus a pixel cross-check (`--pixels`, forced in the agent profile).

```typst
#duo-slide(title: [...], top: visual(image("fig.png", width: 100%, height: 100%, fit: "contain")),
  bottom: [*Takeaway.* ...], mode: "balanced")                    // plain bottom becomes a card
#focus-slide(title: [...], body: [*One idea.*])
#grid-slide(title: [...], columns: ([A], [B], [C]))               // equal-height cards, >= 2 columns
#stack-slide(title: [...], items: (
  visual(rect(width: 100%, height: 100%, fill: aqua)),            // stretch: grows dominant, never carded
  card([Explanation.]), takeaway([Conclusion.]),                  // theme cards
))
#compare-slide(title: [...], left: [Option A], right: [Option B]) // equal-height cards, top-aligned
#stat-slide(title: [...], stats: (metric([38%], [cost]), metric([0.4], [delta])))
#figure-slide(title: [...], fig: visual(image("f.png", width: 100%, height: 100%, fit: "contain")),
  caption: [Fig 1. ...], takeaway: [*Conclusion.*])
#sidebar-slide(title: [...], label: [Method], body: [Plain content, the component draws the card.])
```

Required slots panic on `none` and on content that renders empty; text slots (cards, plain blocks, metric fields) additionally require a measurable width and height, so spacers, empty strings, and bare rules fail at compile time. Percent-sized content must be wrapped in `visual(...)` (percent heights measure as zero outside a sized container). For stepwise reveal, pass `reveal: true` (duo/figure show the second block on step 2, stack/grid show block i on step i, compare shows the right side on step 2); an explicit `reveal-from` on a typed item always wins over that sugar, and components without reveal steps (focus, sidebar) reject it. Do not put `#pause` inside a component's content: touying panics; hidden reveal steps keep their measured space so the layout never shifts between subslides. Numeric knobs (widths, gutters) live in each component's `tuning` dictionary, validated for key, type, and range.

Check a deck with `scripts/xwysyy-check deck.typ` (`--profile agent` for AI-generated decks; the agent profile always renders pixels, because declared stretch payloads are verified against real ink). Full parameter reference, the telemetry schema, the checker diagnostic table, the pixel cross-checks, and the AI generation contract live in [`LAYOUT.md`](LAYOUT.md).

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

The same loader API works during local development:

```typst
#import "../xwysyy.typ": xwysyy-extras
#import xwysyy-extras(): *
```

The extras module wraps:

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
| Entries | `xwysyy-pre`, `xwysyy-doc`, `xwysyy-note`, `xwysyy-extras()` |
| Slide layouts | `title-slide`, `outline-slide`, `xwysyy-slide`, `new-section-slide`, `image-slide`, `end-slide` |
| Components | `textbox`, `info` |
| Highlight macros | `red`, `bred`, `yellow`, `byellow` |
| Theme values | `themes`, `sea`, `sky`, `skyl`, `skyll`, `paper` |
