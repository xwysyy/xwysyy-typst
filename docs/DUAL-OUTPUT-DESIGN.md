# Dual Output Design

`xwysyy-doc` is the dual-output entry. It keeps `xwysyy-pre` and `xwysyy-note` as explicit lower-level entries, then dispatches by `sys.inputs.at("mode", default: "slides")`.

Compile slides:

```bash
typst compile --root . examples/dual-source.typ dual-slides.pdf
```

Compile A4 notes:

```bash
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
```

## Entry Shape

`xwysyy-doc` accepts the shared document metadata and visual parameters:

- `theme`
- `font`
- `code-font`
- `lang`
- `title`
- `subtitle`
- `author`
- `date`
- `institution`
- `footer`

In `slides` mode it calls `xwysyy-pre` and passes `config-info(...)`. In `note` mode it calls `xwysyy-note`.

## Layout Degradation

| Slide API | Note-mode behavior |
|-----------|--------------------|
| `title-slide` | Skipped because `xwysyy-note` renders the title block |
| `outline-slide` | Converted to `#outline(title: ..., depth: 1)` |
| `new-section-slide` | Skipped; the original level-one heading remains in the note |
| `xwysyy-slide` | Explicit calls render an optional heading and body |
| `focus-slide` | Converted to a gray emphasis block |
| `image-slide` | Converted to a figure when `img` is present |
| `end-slide` | Converted to a centered ending block |

## Pause Semantics

`#pause` is handled by touying in slide mode. In note mode, the document is rendered through `xwysyy-note`, so the note output keeps the complete content and does not create subslides.

## Shared Components

`textbox`, highlight macros, arrow replacements, tables, code blocks, and links remain available in both modes. `xwysyy-doc` updates `_theme-state` before rendering so `textbox` has a theme color in note output. Note typography and page setup still come from `xwysyy-note`, so the note artifact is A4 and does not include slide headers, footers, or presentation page size.
