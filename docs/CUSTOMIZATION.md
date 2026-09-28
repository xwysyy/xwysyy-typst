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
  skyll: rgb("#f5fbf7"),
  paper: rgb("#f7faf8"),
  page-fill: white,
)

#show: xwysyy-pre.with(theme: forest, ...)
```

The fields and their roles are listed in the [README theme table](../README.md#themes). Missing required fields fail compilation and name the missing field.

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
scripts/gen-previews
```

Then push, wait for the visual-regression run, and adopt its renders as the visual baseline with `scripts/adopt-baseline`.

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

`xwysyy-pre` takes font and language parameters:

```typst
#show: xwysyy-pre.with(
  font: ("Libertinus Serif",),
  code-font: "DejaVu Sans Mono",
  lang: "en",
  ...
)
```

Defaults:

| Entry | `font` | `heading-font` | `code-font` | `lang` |
|-------|--------|----------------|-------------|--------|
| `xwysyy-pre` | `("Times New Roman", "Noto Serif CJK SC")` | `("Libertinus Sans", "Noto Sans CJK SC")` | `("Maple Mono", "Noto Sans Mono CJK SC")` | `"en"` |

`heading-font` is used by the open header on content slides. The CJK entries in the `code-font` default keep CJK text inside code on a real mono font instead of the Unifont bitmap fallback.

Typst web app users can pass fonts available in the web environment. Local CI uses `fonts-dejavu-core`, `fonts-liberation`, `fonts-noto-cjk`, and `fonts-noto-cjk-extra`, plus Libertinus Sans OTFs from the pinned upstream release (v7.051).

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

Content slide header and footer are the `header(self)` and `footer(self)` functions of `_kinded-slide` in `src/slides.typ`, which the public `xwysyy-slide` wraps. Edit them there; the source is the reference.

The header is open: the slide title is set in `heading-font`, bold, at 1.45em, colored `sea` by default, and sits over a full-width 0.12em rule filled with a gradient running from the title color through `sky` and fading to fully transparent at 92% of the width. The optional theme field `header-text` overrides the title color.

The header block has a 1.1em top inset, and the page top margin set in `xwysyy-pre` is 4.35em; change the two together. Because the margin is fixed, a long title shrinks to fit on one line, down to 0.65 of its size. The header exports the applied scale and whether the title fits horizontally and vertically as `<xwysyy-header>` telemetry, which the layout checker reports as `header_shrunk` / `header_overflow`; a customized header should keep emitting it.

The footer shows only the page number in the bottom-right corner, in `neutral-dark` at 0.9em.

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

## 6. Show Rules

Show rules live in `src/elements.typ` inside `xwysyy-elements`.

Important split:

- `raw.where(block: true)` handles code blocks with `block(width: 100%)`
- `raw.where(block: false)` handles inline code with a `box` whose fill is painted with `outset: (y: 0.2em)`, so the chip does not push the code text below the surrounding baseline

Arrow replacements use math mode. Each rule is wrapped in a guard that skips text whose current first font family equals the `code-font` first family (case-insensitive), so `<=` and `->` inside code stay literal. Keep longer patterns before shorter patterns:

```typst
#show "-->": non-code([$-->$])
#show "->": non-code([$->$])
```

## 7. Handouts, Speaker Notes, And pdfpc

`xwysyy-pre` forwards `..args` to touying, so handout mode, `#speaker-note`, second-screen notes, and pdfpc export work as in touying. See [USAGE §5 Handouts](USAGE.md#5-handouts) and [USAGE §6 Speaker Notes And pdfpc](USAGE.md#6-speaker-notes-and-pdfpc).

## 8. Visual Regression And Previews

Regenerate README preview PNGs:

```bash
scripts/gen-previews
```

Adopt a completed GitHub Actions render as the visual baseline. Without an argument the script takes the latest visual-regression run on the current branch and refuses it unless that run rendered the local `HEAD`; pass a run id to adopt a specific run:

```bash
scripts/adopt-baseline
scripts/adopt-baseline <run-id>
```

Render the visual regression set manually:

```bash
scripts/render-visuals /tmp/xwysyy-visual-current
scripts/compare-png tests/visual-baseline /tmp/xwysyy-visual-current --diff-dir /tmp/xwysyy-diffs
```

The preview and visual scripts pass `--input visual-ci=true`. The visual examples use the fixed date `2026-07-10` together with Liberation Serif, Noto Serif CJK SC, and DejaVu Sans Mono, so repeated renders have stable inputs. `render-visuals` builds the complete set in a temporary sibling directory and publishes it only after every compile succeeds. Publication replaces only the PNG families owned by the script and preserves unrelated files in the target directory.

The GitHub Actions workflow runs:

1. Compile all examples, including handout output.
2. Check theme contrast.
3. Render the visual set.
4. Compare against `tests/visual-baseline`.
5. Upload current renders and diff images on failure.

Pure documentation pull requests are ignored by the visual workflow through `paths-ignore`.

## 9. Upgrade Checks

When changing `src/*.typ`, examples, template, themes, or scripts, run:

```bash
typst compile --root . examples/slides-sky.typ
typst compile --root . examples/slides-sunset.typ
scripts/check-theme-contrast
scripts/render-visuals /tmp/xwysyy-visual-current
scripts/compare-png tests/visual-baseline /tmp/xwysyy-visual-current
```

## 10. Universe Release Staging

The source repository is the authority for every published package version. Commit and validate release changes here before creating the `typst/packages` branch. The package copy must not receive manual fixes.

Build a package directory from a clean committed ref:

```bash
scripts/build-universe-package /tmp/xwysyy-universe-head --ref HEAD
```

After the release tag is created, build the final directory from that immutable ref:

```bash
scripts/build-universe-package /tmp/xwysyy-universe-v0.4.0 --ref v0.4.0
```

The builder copies only the package files: the manifest, MIT license, English README, thumbnail, the `xwysyy.typ` entrypoint, `src/`, and `template/`. Development scripts, tests, examples, and internal documentation remain in the source repository. The builder rejects a dirty source repository, an existing output path, an output path inside this repository, malformed package metadata, and missing required files. Extraction and verification happen in a temporary sibling directory, so a failed build leaves no partial output. Its final line reports a tree SHA-256 for review.

Create one branch per package version in the `xwysyy/packages` fork, based on the current `typst/packages:main`. Copy the generated directory to `packages/preview/xwysyy/<version>/`, run package-check and consumer-boundary compilation there, then open the upstream pull request. Apply reviewer changes to this source repository first and regenerate the directory.
