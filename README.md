<h1 align="center">xwysyy</h1>

<p align="center">
  <a href="https://typst.app/universe/package/xwysyy"><img src="https://img.shields.io/badge/Typst%20Universe-available-239dad.svg" alt="Typst Universe"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://typst.app"><img src="https://img.shields.io/badge/Typst-%E2%89%A5%200.14.2-239dad.svg" alt="Typst version: >= 0.14.2"></a>
  <a href="https://github.com/touying-typ/touying"><img src="https://img.shields.io/badge/touying-0.7.4-blueviolet.svg" alt="touying version: 0.7.4"></a>
  <a href="#-themes"><img src="https://img.shields.io/badge/Themes-6%20built--in-ff69b4.svg" alt="Built-in themes"></a>
</p>

<p align="center">
  <a href="https://github.com/xwysyy/xwysyy-typst/blob/v0.3.0/README-zh.md">中文</a> | <b>English</b>
</p>

Academic presentation and note-taking templates built on [touying](https://github.com/touying-typ/touying). The package covers slide decks, handouts, speaker notes, and A4 notes from one Typst source. The visual theme is derived from [Carlos-Mero/may](https://github.com/Carlos-Mero/may) under MIT.

## Features

- Universe template support: `typst init @preview/xwysyy:0.3.0` creates a ready-to-compile deck.
- Six built-in themes: `sky`, `sunset`, `forest`, `midnight`, `violet`, and `graphite`.
- Custom theme dictionaries can be passed directly to `theme`, so users can customize colors without forking the package.
- `font`, `code-font`, and `lang` are shared between slide and note mode; slides additionally take `heading-font` for the header title.
- Touying handout mode, `#speaker-note`, and pdfpc export are documented and covered by examples.
- `xwysyy-doc` compiles one source as a 16:9 deck by default and as A4 notes with `--input mode=note`.
- CI scripts cover example compilation, visual regression, theme contrast, and README preview generation.

## Preview

```bash
typst compile --root . examples/slides-sky.typ
typst compile --root . examples/slides-sunset.typ
typst compile --root . examples/note.typ
typst compile --root . examples/dual-source.typ
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
```

### Slide Themes

| sky | sunset | forest |
|:---:|:---:|:---:|
| ![Sky theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-theme-sky-p1-01.png) | ![Sunset theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-theme-sunset-p1-01.png) | ![Forest theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-theme-forest-p1-01.png) |

| midnight | violet | graphite |
|:---:|:---:|:---:|
| ![Midnight theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-theme-midnight-p1-01.png) | ![Violet theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-theme-violet-p1-01.png) | ![Graphite theme cover](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-theme-graphite-p1-01.png) |

### Component Pages

| Sky cover | Sky components |
|:---:|:---:|
| ![Sky theme cover slide](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-sky-p1-01.png) | ![Sky theme textbox components](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-sky-p5-05.png) |

| Sunset cover | Sunset components |
|:---:|:---:|
| ![Sunset theme cover slide](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-sunset-p1-01.png) | ![Sunset theme textbox components](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-sunset-p5-05.png) |

| Note title | Note code | Note table |
|:---:|:---:|:---:|
| ![Note mode title and TOC](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-note-p1-1.png) | ![Note mode lists and code](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-note-p2-2.png) | ![Note mode tables and quotes](https://raw.githubusercontent.com/xwysyy/xwysyy-typst/v0.3.0/assets/preview-note-p3-3.png) |

## Quick Start

Create a new project from the Universe template:

```bash
typst init @preview/xwysyy:0.3.0 my-talk
cd my-talk
typst compile main.typ
```

Use the package in an existing Typst project:

```typst
#import "@preview/xwysyy:0.3.0": *

#show: xwysyy-pre.with(
  theme: "sunset",
  config-info(
    title: [My Presentation Title],
    subtitle: [Subtitle],
    author: " ",
    date: datetime.today(),
    institution: " ",
  ),
)

#title-slide()
#outline-slide()

= Section Title

== Slide Title

Body text with *bold* and #red[red highlight].

#textbox(
  [*Module A*

  First column],

  [*Module B*

  Second column],
)

#end-slide(title: [Thank You!], body: [Questions?])
```

## Themes

Select a built-in theme by name:

```typst
#show: xwysyy-pre.with(
  theme: "forest",
  config-info(title: [My Presentation]),
)
```

Pass a custom dictionary directly:

```typst
#let my-theme = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  header-text: none,
  page-fill: white,
)

#show: xwysyy-pre.with(
  theme: my-theme,
  config-info(title: [My Presentation]),
)
```

Six fields are required; `header-text` is optional:

| Field | Purpose |
|-------|---------|
| `sea` | Primary dark color for the header title, links, table heads, and badges |
| `sky` | Accent color, also the fade-out end of the header rule |
| `skyl` | Light background color |
| `skyll` | Code block, table row, and textbox fill |
| `paper` | Text on dark backgrounds |
| `header-text` | Optional header title color override, `none` falls back to `sea` |
| `page-fill` | Slide page background |

## Component Reference

| Category | API | Usage |
|----------|-----|-------|
| Slide entry | `xwysyy-pre` | `#show: xwysyy-pre.with(theme: "sky", ...)` |
| Dual-output entry | `xwysyy-doc` | default deck, `--input mode=note` for A4 notes |
| Title slide | `title-slide` | `#title-slide()` |
| Outline | `outline-slide` | `#outline-slide()` auto-collects section headings |
| Content slide | `xwysyy-slide` | `== Title` auto-triggers |
| Section transition | `new-section-slide` | `= Title` auto-triggers |
| Full-screen image | `image-slide` | `#image-slide(img: image("bg.png"))` |
| End slide | `end-slide` | `#end-slide(title: [...])` |
| Layout · pair | `duo-slide` | figure over text, measured spacing + telemetry |
| Layout · single | `focus-slide` | one centered block for sparse pages |
| Layout · columns | `grid-slide` | N equal-height peer columns |
| Layout · stack | `stack-slide` | N vertical blocks on one rhythm |
| Layout · compare | `compare-slide` | two top-aligned blocks read as a contrast |
| Layout · stats | `stat-slide` | a row of big-number metric tiles |
| Layout · figure | `figure-slide` | figure, tight caption, optional takeaway |
| Layout · sidebar | `sidebar-slide` | a label tab beside a content card |
| Text box | `textbox` | `#textbox[Content]` or `#textbox([Col 1], [Col 2])` |
| Highlight | `red` / `bred` | `#red[text]` / `#bred[bold red]` |
| Highlight | `yellow` / `byellow` | `#yellow[text]` / `#byellow[bold yellow]` |
| Note entry | `xwysyy-note` | `#show: xwysyy-note.with(title: [...])` |
| Extensions | `xwysyy-extras` | cetz, fletcher, and theorion integrations |

The layout components (`duo-slide`, `focus-slide`, `grid-slide`, `stack-slide`, `compare-slide`, `stat-slide`, `figure-slide`, `sidebar-slide`) measure real rendered heights, distribute whitespace by a rhythm rule, and export `<xwysyy-slide-layout>` telemetry that `scripts/slide-check.py` turns into numeric layout diagnostics. They replace hand-written `#v()` spacing when a slide is generated by an agent. See [`docs/LAYOUT.md`](docs/LAYOUT.md).

## Handouts And Speaker Notes

`examples/slides-sky.typ` reads `--input handout=true` and passes `config-common(handout: true)` to touying:

```bash
typst compile --root . examples/slides-sky.typ slides.pdf
typst compile --root . --input handout=true examples/slides-sky.typ slides-handout.pdf
```

Speaker notes are available because `xwysyy.typ` re-exports touying:

```typst
#speaker-note[
  Mention the ablation table before moving to the next section.
]
```

Export pdfpc metadata:

```bash
typst query --root . examples/slides-sky.typ --field value --one "<pdfpc-file>" > slides-sky.pdfpc
```

## One Source, Two Outputs

Use `xwysyy-doc` when one source should produce both deck and notes:

```typst
#import "@preview/xwysyy:0.3.0": *

#show: xwysyy-doc.with(
  title: [One Source, Two Outputs],
  subtitle: [Deck and A4 notes],
  theme: "forest",
)
```

Compile the deck:

```bash
typst compile --root . examples/dual-source.typ dual-slides.pdf
```

Compile the A4 notes:

```bash
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
```

## Requirements

- Typst 0.14.2
- touying 0.7.4, downloaded on first compile
- physica 0.9.8, downloaded on first compile
- Default local fonts: Times New Roman, Noto Serif CJK SC, Libertinus Sans, Noto Sans CJK SC, Maple Mono, and Noto Sans Mono CJK SC
- Typst web app users can pass web-available fonts with `font:`, `heading-font:`, and `code-font:`

## Maintenance

Regenerate README previews:

```bash
scripts/gen-previews
```

Adopt visual regression baselines from the latest CI run (requires a logged-in GitHub CLI):

```bash
scripts/adopt-baseline
```

Full API reference: [docs/USAGE.md](https://github.com/xwysyy/xwysyy-typst/blob/v0.3.0/docs/USAGE.md). Customization guide: [docs/CUSTOMIZATION.md](https://github.com/xwysyy/xwysyy-typst/blob/v0.3.0/docs/CUSTOMIZATION.md). Theme generator: [docs/THEME-GENERATOR.md](https://github.com/xwysyy/xwysyy-typst/blob/v0.3.0/docs/THEME-GENERATOR.md).

## Acknowledgements

- Theme derived from [Carlos-Mero/may](https://github.com/Carlos-Mero/may) under MIT
- Built on [touying](https://github.com/touying-typ/touying)

## License

[MIT](./LICENSE)
