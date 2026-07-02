# CUSTOMIZATION - xwysyy Guide

This guide covers color themes, fonts, layout edits, touying options, and maintenance scripts. API signatures are in [USAGE.md](./USAGE.md).

## 1. Theme Colors

### Use A Built-In Theme

```typst
#show: xwysyy-pre.with(theme: "midnight", ...)
```

Built-in themes are defined in `src/themes.typ`:

- `sky`
- `sunset`
- `forest`
- `midnight`
- `violet`
- `graphite`

### Pass A Custom Theme Dictionary

Most users should pass a dictionary directly:

```typst
#let forest = (
  sea: rgb("#1f5d45"),
  sky: rgb("#a8d5ba"),
  skyl: rgb("#e9f5ee"),
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  header-fill: none,
  header-text: none,
  page-fill: white,
)

#show: xwysyy-pre.with(theme: forest, ...)
```

The dictionary must contain 8 fields:

| Field | Used For |
|------|----------|
| `sea` | Header fallback, links, table head, outline badge, focus slide |
| `sky` | Accent line and secondary marks |
| `skyl` | Reserved light color |
| `skyll` | Textbox, code block, and data-row fill |
| `paper` | Text on dark backgrounds |
| `header-fill` | Header fill, `none` falls back to `sea` |
| `header-text` | Header text, `none` falls back to `paper` |
| `page-fill` | Slide page fill |

Missing fields fail compilation and name the missing field.

### Vendor A Theme Into The Package

If you maintain a private fork and want named themes, edit `src/themes.typ` and add a key to `themes`:

```typst
#let themes = (
  sky: (...),
  sunset: (...),
  forest: (...),
)
```

After changing built-in themes, run:

```bash
scripts/check-theme-contrast
scripts/gen-previews --with-baseline
```

### Theme Contrast

`scripts/check-theme-contrast` parses `src/themes.typ` by default. Pass another file path to test a temporary candidate:

```bash
scripts/check-theme-contrast
scripts/check-theme-contrast /tmp/themes-candidate.typ
```

- `paper` on `sea`
- effective `header-text` on effective `header-fill`

Each contrast ratio must be at least 4.5:1.

## 2. Fonts And Language

Slide mode and note mode share parameter names:

```typst
#show: xwysyy-pre.with(
  font: ("Libertinus Serif",),
  code-font: "DejaVu Sans Mono",
  lang: "en",
  ...
)
```

```typst
#show: xwysyy-note.with(
  font: ("Libertinus Serif",),
  code-font: "DejaVu Sans Mono",
  lang: "zh",
)
```

Defaults:

| Entry | `font` | `code-font` | `lang` |
|-------|--------|-------------|--------|
| `xwysyy-pre` | `("Times New Roman", "Noto Serif CJK SC")` | `"Maple Mono"` | `"en"` |
| `xwysyy-note` | `("Times New Roman", "Noto Serif CJK SC")` | `"Maple Mono"` | `"en"` |
| `xwysyy-doc` | Same as slide mode | Same as slide mode | `"en"` |

Typst web app users can pass fonts available in the web environment. Local CI uses `fonts-dejavu-core`, `fonts-liberation`, and `fonts-noto-cjk`.

`outline-slide(title: auto)` follows `text.lang`: `zh` gives `目录`; other languages give `Contents`. A manual title always wins:

```typst
#outline-slide(title: [Agenda])
```

## 3. Aspect Ratio

```typst
#show: xwysyy-pre.with(
  aspect-ratio: "16-10",
  ...
)
```

`xwysyy-pre` maps this to touying page paper `presentation-<aspect-ratio>`.

## 4. Header And Footer

Content slide header and footer are implemented in `src/slides.typ` inside `xwysyy-slide`.

Header:

```typst
let header(self) = {
  block(
    width: 100% + 2em,
    height: 2.5em,
    fill: self.store.header-fill,
    ...
  )
}
```

Footer:

```typst
let footer(self) = {
  utils.call-or-display(self, self.store.footer)
  h(1fr)
  context utils.slide-counter.display()
}
```

Theme fields control header colors. `footer:` on `xwysyy-pre` controls footer text.

## 5. Add A Slide Layout

New slide layouts should follow the existing pattern:

```typst
#let warning-slide(body) = touying-slide-wrapper(self => {
  self = utils.merge-dicts(
    self,
    config-page(fill: rgb("#ffe5e5"), margin: 0em),
  )
  touying-slide(self: self, align(horizon + center, body))
})
```

Use `utils.merge-dicts(self, config-page(...))` inside the wrapper. This avoids ghost slides in touying 0.7.x.

If the layout should work with `xwysyy-doc`, add a `mode=note` degradation branch similar to `focus-slide` or `image-slide`.

## 6. Show Rules

Slide show rules live in `src/elements.typ` inside `xwysyy-elements`.

Important split:

- `raw.where(block: true)` handles code blocks with `block(width: 100%)`
- `raw.where(block: false)` handles inline code with `box(baseline: 0.2em)`

Arrow replacements use math mode. Keep longer patterns before shorter patterns:

```typst
#show "-->": [$-->$]
#show "->": [$->$]
```

Note mode show rules live in `src/note.typ` and are independent from slide themes.

## 7. Handout Mode

`xwysyy-pre` forwards `..args` to touying. You can pass handout config directly:

```typst
#show: xwysyy-pre.with(
  config-common(handout: true),
  ...
)
```

`examples/slides-sky.typ` exposes a command-line switch:

```bash
typst compile --root . examples/slides-sky.typ slides.pdf
typst compile --root . --input handout=true examples/slides-sky.typ slides-handout.pdf
```

Use touying's `handout-subslides` and `<touying:handout>` label through `config-common(...)`.

## 8. Speaker Notes And pdfpc

`xwysyy.typ` re-exports touying, so `#speaker-note` is available:

```typst
#speaker-note[
  Emphasize the main failure case here.
]
```

Second-screen notes:

```typst
#show: xwysyy-pre.with(
  config-common(show-notes-on-second-screen: right),
  ...
)
```

pdfpc export:

```bash
typst query --root . examples/slides-sky.typ --field value --one "<pdfpc-file>" > slides-sky.pdfpc
```

## 9. One Source, Two Outputs

Use `xwysyy-doc` for a source that compiles as slides or notes:

```typst
#show: xwysyy-doc.with(
  title: [One Source, Two Outputs],
  theme: "forest",
)
```

Deck:

```bash
typst compile --root . examples/dual-source.typ dual-slides.pdf
```

Notes:

```bash
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
```

`xwysyy-doc` keeps the slide API available and converts slide-only layouts according to [USAGE.md §6](./USAGE.md#6-dual-output-entry-xwysyy-doc).

## 10. Visual Regression And Previews

Regenerate README preview PNGs:

```bash
scripts/gen-previews
```

Regenerate previews and visual baselines:

```bash
scripts/gen-previews --with-baseline
```

Render the visual regression set manually:

```bash
scripts/render-visuals /tmp/xwysyy-visual-current
scripts/compare-png tests/visual-baseline /tmp/xwysyy-visual-current --diff-dir /tmp/xwysyy-diffs
```

The preview and visual scripts pass `--input visual-ci=true`. The examples then use Liberation Serif, Noto Serif CJK SC, and DejaVu Sans Mono so local baselines match the GitHub Actions font environment.

The GitHub Actions workflow runs:

1. Compile all examples, including handout and note output.
2. Check theme contrast.
3. Render the visual set.
4. Compare against `tests/visual-baseline`.
5. Upload current renders and diff images on failure.

Pure documentation pull requests are ignored by the visual workflow through `paths-ignore`.

## 11. Upgrade Checks

When changing `src/*.typ`, examples, template, themes, or scripts, run:

```bash
typst compile --root . examples/slides-sky.typ
typst compile --root . examples/slides-sunset.typ
typst compile --root . examples/note.typ
typst compile --root . examples/dual-source.typ
typst compile --root . --input mode=note examples/dual-source.typ dual-note.pdf
scripts/check-theme-contrast
scripts/render-visuals /tmp/xwysyy-visual-current
scripts/compare-png tests/visual-baseline /tmp/xwysyy-visual-current
```
