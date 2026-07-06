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
  page-fill: white,
)

#show: xwysyy-pre.with(theme: forest, ...)
```

The dictionary must contain 6 fields:

| Field | Used For |
|------|----------|
| `sea` | Default header title color, links, table head, outline badge |
| `sky` | Header rule gradient tail and secondary marks |
| `skyl` | Reserved light color |
| `skyll` | Textbox, code block, and zebra-row fill |
| `paper` | Text on dark backgrounds |
| `page-fill` | Slide page fill |

An optional `header-text` field overrides the header title color; when it is absent or `none`, the title uses `sea`. All built-in themes ship `header-text: none`.

Missing required fields fail compilation and name the missing field.

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
- header title on page fill (`header-text` falling back to `sea`, against `page-fill` falling back to white)

Each contrast ratio must be at least 4.5:1. The script requires the parsed fields `sea`, `paper`, and `page-fill`.

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

| Entry | `font` | `heading-font` | `code-font` | `lang` |
|-------|--------|----------------|-------------|--------|
| `xwysyy-pre` | `("Times New Roman", "Noto Serif CJK SC")` | `("Libertinus Sans", "Noto Sans CJK SC")` | `("Maple Mono", "Noto Sans Mono CJK SC")` | `"en"` |
| `xwysyy-note` | `("Times New Roman", "Noto Serif CJK SC")` | none | `("Maple Mono", "Noto Sans Mono CJK SC")` | `"en"` |
| `xwysyy-doc` | Same as slide mode | Same as slide mode | Same as slide mode | `"en"` |

`heading-font` is used by the open header on content slides. The CJK entries in the `code-font` default keep CJK text inside code on a real mono font instead of the Unifont bitmap fallback.

Typst web app users can pass fonts available in the web environment. Local CI uses `fonts-dejavu-core`, `fonts-liberation`, `fonts-noto-cjk`, `fonts-noto-cjk-extra`, and `fonts-libertinus`.

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

The header is open: the slide title is set in `heading-font`, bold, at 1.45em, colored `sea` by default, and sits over a full-width 0.12em rule filled with a gradient running from the title color through `sky` and fading to fully transparent at 92% of the width. The page top margin is 4.35em.

Header:

```typst
let header(self) = {
  block(
    width: 100% + 2em,
    inset: (x: 1em, top: 1.1em),
    {
      block(text(
        font: self.store.heading-font,
        fill: self.store.header-color,
        weight: "bold",
        size: 1.45em,
        ...
      ))
      v(0.65em, weak: true)
      rect(
        width: 100%,
        height: 0.12em,
        radius: (left: 0.06em),
        fill: gradient.linear(
          (self.store.header-color, 0%),
          (self.colors.primary, 42%),
          (self.colors.primary.transparentize(100%), 92%),
          (self.colors.primary.transparentize(100%), 100%),
        ),
      )
    },
  )
}
```

Footer (page number in the bottom-right corner only):

```typst
let footer(self) = {
  set align(bottom + right)
  set text(fill: self.colors.neutral-dark, size: .9em)
  block(
    inset: (x: 0.5em, bottom: 0.4em),
    context utils.slide-counter.display(),
  )
}
```

The optional theme field `header-text` overrides the title color.

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

If the layout should work with `xwysyy-doc`, add a `mode=note` degradation branch similar to `image-slide` or `end-slide`.

## 6. Show Rules

Slide show rules live in `src/elements.typ` inside `xwysyy-elements`.

Important split:

- `raw.where(block: true)` handles code blocks with `block(width: 100%)`
- `raw.where(block: false)` handles inline code with a `box` whose fill is painted with `outset: (y: 0.2em)`, so the chip does not push the code text below the surrounding baseline

Arrow replacements use math mode. Each rule is wrapped in a guard that skips text whose current first font family equals the `code-font` first family (case-insensitive), so `<=` and `->` inside code stay literal. Keep longer patterns before shorter patterns:

```typst
#show "-->": non-code([$-->$])
#show "->": non-code([$->$])
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
