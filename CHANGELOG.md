# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-07-11

### Added

- Deterministic `scripts/build-universe-package` staging from a clean Git ref, with an explicit package-file allowlist, fail-closed manifest and README validation, transactional output, executable-mode checks, and a reviewable tree SHA-256
- Lazy `xwysyy-extras()` module loader, which exposes cetz, fletcher, and theorion integrations through the package entrypoint without resolving their packages during a core import
- CI coverage for the declared Typst 0.14.0 minimum, the optional extras loader, the generated Universe package shape, and compilation through Typst's package resolver
- Semantic layout layer `src/layout.typ` with a shared allocator and layout telemetry v4: `duo-slide`, `focus-slide`, `grid-slide`, `stack-slide`, `compare-slide`, `stat-slide` (typed `metric(value, label)` tiles, value auto-shrink with a 0.6 floor exported as `extra.value_scales`, value and label measured separately instead of through the tile's forced width), `figure-slide` (caption measured first, figure slot gets an explicit height so stretch content fills it instead of escaping the wrapper), `sidebar-slide` (label tab + content card). All components degrade to linear content in note mode, and slot validation runs identically in both outputs (a deck cannot compile as a note while its slides build is broken)
- Typed items with declared sizing on every slot: `visual(fit: "stretch"|"natural")`, `card(...)`, `takeaway(...)`, `plain(...)`, `metric(...)`, validated centrally per slot policy. Sizing is never inferred from a zero measurement: required slots panic on `none`; visuals panic when they render empty (percent-sized content must be declared `visual(...)`); text slots panic on content with no measurable width or height (spacers, empty strings, bare rules); roles form a closed set (no `decorative` escape hatch); `grid-slide` needs at least 2 columns and, like `compare-slide` and the figure takeaway, rejects stretch visuals with a contract panic; components without reveal steps (`focus-slide`, `sidebar-slide`) reject `reveal-from` instead of ignoring it; `reveal-from` must be an integer within the step range and always wins over the `reveal: true` sugar; `tuning` validates key, type, and range; `xwysyy-slide` has no `kind` parameter (exempt pages are emitted only by their dedicated slide functions) and `image-slide` panics without an image
- Allocator with four fit states — `normal` / `compressed` (gaps squeezed below preferred) / `tight` (outer margins consumed) / `overflow` — under the hard invariant overflow ⇒ `body_overflow_ratio` > 0; stretch visuals carry a 0.28-body-height minimum, so text-heavy pages degrade honestly instead of starving the visual and reporting normal
- Telemetry v4 objects carry four boxes: `frame` (allocated), `preferred` (what the allocator saw), `payload` (2-D flow bbox of the inner content, horizontal included), and `paint` (visible card or null) with its `paint_fill` colour, plus per-axis `sizing`, `payload_source` (`measured` vs `declared` — a declared payload is a claim verified against pixels, never density evidence), `overflow_x` (unbreakable content wider than its slot), and closed `object_kind` / `semantic_role` sets
- One `<xwysyy-frame>` v2 mapping per physically rendered subslide, carrying the physical body geometry in pt, with a slide id that is stable across reveal subslides (touying's logical slide counter, not the physical page number): every frame joins its layout record, so a blank first reveal frame is an `empty_frame` error instead of an orphan buying coverage. Every slide layout exports an `<xwysyy-page>` manifest; content-page headers export `<xwysyy-header>` v2
- Content-page header titles shrink to fit one line (floor 0.65×) instead of wrapping into the header rule and the body on narrow ratios; the applied scale and the header height are telemetry (`header_shrunk` warning; `header_overflow` error covers both the width floor and a title too tall for the header band)
- `reveal: true` on `duo-slide`, `stack-slide`, `grid-slide`, `compare-slide`, `stat-slide`, and `figure-slide`: blocks appear one subslide at a time in semantic order, hidden steps keep their measured space, telemetry is emitted once with `visible_from` per object. Implemented with the callback-style `utils.uncover` because mark-based `#pause` cannot appear inside the components' `context`/`layout` closures (touying panics; the generation contract states this)
- `scripts/slide-check.py` v4: fail-closed parsing (missing fields, unknown enums, non-finite numbers, negative sizes, or an old schema exit 2 instead of being patched with defaults), fit-state machine invariants (`invalid_fit_state` on contradictions; `gap_scale` replaced by the real `gap_ratio`), a frame state machine (steps exactly 1..N on consecutive pages, handout carries exactly the final step, orphan frames and duplicate slide ids are structural errors rejected before any join), union-area coverage metrics with `payload_density` computed from measured payloads only, `empty_shell` / `underfilled_card` on measured payloads, two-axis `hollow_frame`, directed relations with closed kind/axis/proximity sets, per-rendered-frame checks (`empty_frame`, `sparse_frame` for near-empty early steps), `object_escapes_frame` (payload escaping its own frame, or `overflow_x` evidence), `column_imbalance` gated on the row archetypes, leaf-typed rule validation (a list or bool where a number belongs is a clean exit-2 rule error, not a TypeError traceback), machine-actionable `action` slugs, one shared severity policy table (`--profile agent` escalates content-adequacy findings), and `--dump-features` for future threshold-calibration corpora
- `scripts/xwysyy-check`: one-command QA that runs a single `typst query "metadata"` for all schemas, the geometry checker, and a pixel cross-check that is FORCED in the agent profile (geometry alone cannot verify declared payloads): page geometry comes from the frame v2 telemetry instead of hard-coded template constants; each page maps to its (record, reveal step) so only visible objects may explain ink (`render_telemetry_mismatch`, always an error); `edge_ink` keeps the sliding-window row peak; and `hollow_object` verifies every object's claimed payload box against real ink excluding the page background and the object's own card fill, so empty stretch visuals, `hide(...)`, and card-paint-backed fake payloads all surface
- Tests (106): 97 layout tests cover every diagnostic, the fail-closed parser, the frame machine, rule validation, real compilation, pixel true positives, adversarial fake-green cases, and seventeen panic fixtures in both outputs; nine release-staging and source-contract tests cover successful publication, reviewer-sensitive manifest metadata, manifest types and paths, README contracts, unsupported package subpaths, and failure cleanup
- CI compiles the layout demo and all layout fixtures (handout in both modes), runs the layout test suite, and includes the layout demo in the visual-regression PNG set
- `docs/LAYOUT.md` and the layout QA toolchain (`xwysyy-check`, `slide-check.py`, `compare-png`) ship with the Universe package, so template users get the full feedback loop; the template scaffold demonstrates the layout components
- The release builder installs the three QA tools into `template/scripts/`, so projects created with `typst init` can run `scripts/xwysyy-check` directly
- `heading-font` parameter on `xwysyy-pre` and `xwysyy-doc` (default `("Libertinus Sans", "Noto Sans CJK SC")`), used by the content-page header

### Changed

- Package metadata now declares Typst 0.14.0 as the tested minimum, omits a discipline filter because the template is generally applicable, and applies MIT-0 to `template/` while keeping package code and documentation under MIT; the package README uses self-contained commands and immutable `v0.4.0` links, and documents the optional extras loader explicitly
- The starter deck uses an editable `Date` placeholder, keeping its initialized cover deterministic and exactly aligned with `thumbnail.png`
- Layout components distribute space fill-first: outer margins are small and fixed (top 7%, bottom 9%) and the primary content grows to occupy the body instead of centring a small group in a large blank margin. Stretch visuals become dominant with the takeaway pinned near the bottom; `grid-slide`/`compare-slide`/`stat-slide`/`sidebar-slide` grow cards to at least 60% of body height; `stack-slide` gives its free space to stretch visuals or, in a pure-card stack, shares it evenly so every card grows tall. Natural-size visuals stay at their measured size (the group centres and the telemetry reports the low density honestly, instead of growing a transparent frame around a small image). `focus-slide` is the one deliberate exception and keeps its centered whitespace (telemetry carries `intent: "focus"`), but the safe-area rules still apply to it. `compare-slide` content is top-aligned so the two openings sit on the same line; other cards centre their content vertically. Card padding increased from 0.8em to 0.9em
- `sidebar-slide` measures its label with the same styled content it renders (a `set text` bold, not `strong`, whose show rule enlarges the run), and its fit reporting uses the safe-area threshold (natural height between 0.84H and 1.0H used to emit `overflow: false`)
- `alert` (touying) drops its 0.02em stroke to match `strong`'s no-stroke bold, so emphasis is consistent and does not muddy CJK glyph counters
- Vertical `object_outside_body` is suppressed when the fit state already reports the squeeze; horizontal escapes are checked in every fit state
- Content-page header redesigned: the solid color bar (`header-fill` background, white extrabold 1.56em title, fixed 2.5em height) is replaced by an open header, with the slide title in `heading-font` (bold, 1.45em, colored `sea`; the theme field `header-text` optionally overrides the color) over a full-width 0.12em rule filled with a gradient running from the title color through `sky` and fading to fully transparent at 92% of the width; page top margin changed from 3.7em to 4.35em
- Theme contract: required fields reduced from 8 to 6 (`sea`, `sky`, `skyl`, `skyll`, `paper`, `page-fill`); `header-text` is now optional (a non-`none` value overrides the open-header title color, default `sea`), and all 6 built-in themes ship `header-text: none`
- `strong` (markdown bold) now renders as a 1.1em weight-700 run with 0.03em tracking, 0.05em spacing on both sides, and a 0.035em baseline drop, replacing the 0.04em stroke (stroking filled CJK glyph counters); `bred`/`byellow` share the same recipe
- Table style: the 0.2em cell gutter is removed so fills are seamless; header row keeps `sea` fill with white bold text; body rows use true zebra striping (even rows `skyll`, odd rows unfilled); cell inset is 0.6em horizontal and 0.42em vertical; `table.hline` defaults to `0.5pt + sea.lighten(30%)`
- `code-font` default changed from `"Maple Mono"` to `("Maple Mono", "Noto Sans Mono CJK SC")` in `xwysyy-pre`, `xwysyy-doc`, `xwysyy-note`, and `xwysyy-elements`, so CJK inside code no longer falls back to the Unifont bitmap font
- Example `visual-code-font` values are now CJK-fallback font stacks
- `scripts/check-theme-contrast` now checks the header title on the page fill (`header-text` falling back to `sea`, against `page-fill` falling back to white) instead of header text on header fill; required parsed fields are now `sea`, `paper`, and `page-fill`
- Content-page footer reduced to the page number in the bottom-right corner; the left-side footer text slot is gone

### Removed

- The 0.1.0 fixed-layout `focus-slide` in `src/slides.typ` (both slide and note modes), its usages in `examples/slides-sky.typ`, `examples/slides-sunset.typ`, and `examples/dual-source.typ`, and its row in the dual-source degradation table. The `focus-slide` listed under Added is a different function: the measured, telemetry-emitting layout-layer component in `src/layout.typ`
- Theme field `header-fill`
- `footer` parameter on `xwysyy-pre` and `xwysyy-doc` (and its usage in `examples/dual-source.typ`)

### Fixed

- Inline code chip vertical padding is now painted with `outset` (0.2em; 0.15em in note mode) instead of `inset` plus `baseline`, so inline code text no longer sinks about 0.1em below the surrounding baseline
- Arrow replacement show rules (slides and note mode) now skip text whose current first font family equals the code font's first family (case-insensitive), so `<=` and `->` inside code blocks and inline code are no longer rewritten into math arrows

## [0.3.0] - 2026-07-02

### Added

- Universe template metadata and `template/main.typ` for `typst init @preview/xwysyy:0.3.0`
- `thumbnail.png` generated from the template first page
- Direct custom theme dictionaries for `xwysyy-pre(theme: ...)`
- Slide font parameters: `font`, `code-font`, and `lang`
- Language-aware `outline-slide(title: auto)` with `Contents` for English and `目录` for Chinese
- Built-in `forest`, `midnight`, `violet`, and `graphite` themes
- `xwysyy-doc` for one-source deck and A4 note output through `--input mode=note`
- Handout example through `--input handout=true` in `examples/slides-sky.typ`
- Speaker-note example and pdfpc query documentation
- `examples/theme-preview.typ` and `examples/dual-source.typ`
- GitHub Actions visual regression workflow
- Scripts for preview generation, visual rendering, PNG comparison, and theme contrast checks
- Visual regression baselines under `tests/visual-baseline`

### Changed

- Quick start now uses Typst Universe package import and template initialization
- `xwysyy-pre` now passes `code-font` through to `xwysyy-elements`
- README theme previews are generated by `scripts/gen-previews`
- Documentation now treats editing `src/themes.typ` as a maintainer/vendor path
- Typst compiler target updated to 0.14.2

## [0.1.0] - 2026-05-14

### Added

- 7 种 slide 版式：封面（`title-slide`）、目录（`outline-slide`）、章节过渡（`new-section-slide`）、内容页（`xwysyy-slide`）、焦点页（`focus-slide`）、全屏图片（`image-slide`）、结束页（`end-slide`）
- `outline-slide` 目录页支持自动收集 `=` 一级标题，也可手动传入章节数组
- `textbox` 多列等高文本框组件（基于 `components.lazy-layout`）
- 内置 **sky**（蓝色调）和 **sunset**（暖红色调）两套配色方案
- `red` / `bred` / `yellow` / `byellow` 四个颜色强调宏
- CJK 合成斜体（逐字符 synthetic skew）
- 笔记模式 `xwysyy-note`（A4 学术笔记排版，主题无关）
- 箭头符号自动替换（`->` / `=>` / `<=>` 等）
- AI 配色生成器文档（`docs/THEME-GENERATOR.md`）

### Changed

- 禁用 slide 模式的图片自动阴影 show rule，避免 `layout` / `measure` 与 touying slides 组合时的兼容性问题

### Removed

- 移除 `card` 组件；多列等高内容改用 `textbox`
