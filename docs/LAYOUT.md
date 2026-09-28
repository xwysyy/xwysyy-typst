# Semantic Layout Layer and Layout Telemetry (schema v4)

## The Problem

When AI generates slides, spacing is unreliable: content often crowds the top of the page and leaves a large empty area at the bottom, or a figure and its explanation are split apart by an oversized gap. The underlying cause is missing data rather than the model's taste: after compilation the model cannot get layout information at a fine enough grain. It sees the source or one whole-page screenshot, so it cannot reliably know a block's real rendered height, the normalized gap between two blocks, how much of the page the bottom whitespace takes, or where the visual center of gravity lies. It can only guess spacing with hand-written `v(6em)`, and words such as "moderate" or "not too empty" do not map reliably to numbers.

This layer leaves composition to the author, because a fully automatic layout engine would make decks converge on one style and make intent hard to express. What it provides is a layout expressed as numbers that can be measured, compared, and checked. The author picks a semantic component and fills it with typed items; the component measures real sizes, allocates space according to the declared sizing, and exports normalized geometry; the checker reads that geometry and reports content-level diagnostics; the pixel stage cross-checks the real rendering against the telemetry. The AI adjusts from numeric feedback instead of guessing coordinates.

Building on the honest measurement of v3, schema v4 tightens the **trust boundary** into five principles:

1. **Sizing is declared, not guessed.** Content that should fill its slot must be written as `visual(...)` (fit defaults to `"stretch"`); passing `none` to a required slot panics; content in a text slot (card / takeaway / plain / metric fields) must have a measurable width and height. Pure spacers, empty strings, and bare rules panic at compile time instead of being inflated into a fake payload.
2. **A declared payload is a claim, not evidence.** The payload of a stretch slot or of percent-width media is marked `payload_source: "declared"` and does not count toward density or empty-shell checks; its evidence comes from the pixel stage's per-object ink check (the agent profile forces pixel rendering).
3. **Identity is stable.** Automatic slide ids are bound to touying's logical slide counter (not the physical page number), so every reveal frame joins back to its layout record. Orphan frames, missing steps, mismatched frame counts, and duplicate ids are structural errors, and coverage counts only frames that joined successfully.
4. **Every object carries four boxes plus a source.** `frame` (the allocated container), `preferred` (the natural outer box the allocator saw), `payload` (the real 2-D flow bbox of the content), and `paint` (the visible card area, with its fill color in `paint_fill`). Content that cannot wrap and exceeds its width exports `overflow_x` evidence.
5. **Parsing fails closed.** Missing fields, unknown enum values, non-finite numbers, negative sizes, and older schemas all exit as input errors (exit 2) with no default-value fallback. Each of the four fit states carries numeric invariants, and a self-contradictory state is an error.

## Four Parts

The component layer `src/layout.typ` provides eight semantic layouts (`duo` / `focus` / `grid` / `stack` / `compare` / `stat` / `figure` / `sidebar`) that share one allocator and export `<xwysyy-slide-layout>` v4 metadata. Every slide layout (including the title and section pages) also exports one `<xwysyy-page>` page manifest; every actually rendered subslide exports one `<xwysyy-frame>` v2 mapping (including the physical geometry of that page's body area); content-page headers export `<xwysyy-header>` v2 (the title scale and whether the title fits horizontally and vertically).

The checker `scripts/slide-check.py` reads the output of `typst query` (records are recognized by their `schema` field, so any mix of inputs works). It first validates structure (frame state machine, fit invariants, out-of-bounds objects, and escapes), then computes density, visual center, whitespace, semantic-relation gaps, and telemetry coverage, and reports the content-level problems the author has to decide. It does not fix spacing, which the components guarantee. It judges only what the components cannot decide on their own: too little content, too much content, empty-shell cards, unbalanced columns, split semantic pairs, overflow, and missing telemetry. Every diagnostic carries a machine-actionable `action` tag, and its severity comes from one shared policy table.

The unified CLI `scripts/xwysyy-check` runs the whole loop in one command: a single `typst query "metadata"` fetches all four schemas and runs the geometry checks; with `--pixels` it also renders PNGs for the pixel cross-check. **`--profile agent` forces pixels on**: the geometry layer explicitly does not vouch for declared payloads, so the loop cannot close without rendering. `scripts/slide-check.py` remains a standalone geometry engine for input that is already JSON.

The checker lives only in the source repository and is not shipped with the Universe package. Run the commands below from the repository root of the matching version; importing the package and compiling the template do not depend on the checker.

```bash
scripts/xwysyy-check deck.typ                 # geometry checks (human profile)
scripts/xwysyy-check deck.typ --profile agent # geometry + pixels + agent contract (pixels forced)
```

The generation contract is at the end of this document and is also written into `AGENTS.md`. It restricts AI to the components, forbids hand-written spacing and coordinates as well as any change to `tuning`, and requires reading the checker's numbers after compiling before adjusting.

## Fill-First and the Four Fit States

By default a component lets the main content fill the body area; it does not center the content as a small group and turn the remaining space into large outer margins. Outer margins are pinned small and fixed (7% top, 9% bottom, safe area 0.84H), and spare space goes to blocks that can grow: stretch visuals become the dominant element, and cards grow taller and fuller. In multi-column layouts (`grid` / `compare` / `stat` / `sidebar`) cards take at least 60% of the body height; in `stack` a stretch visual absorbs all spare space, while a pure-text stack spreads it evenly so that every card grows taller. When there is no growable block (for example a natural-size figure with a short note), the component centers the whole group inside the safe area and the telemetry honestly reports low density, instead of inflating transparent boxes to fake a full page. The only exception is `focus`: a single-point page keeps symmetric centered whitespace, though the safe-area rules still apply.

The allocator solves over each item's spec (min / preferred / max / grow) and each gap's (min / preferred), and reports one of four states, each with numeric invariants that the checker enforces:

| State | Meaning | Invariant | Checker response |
| --- | --- | --- | --- |
| `normal` | Every preferred size fits in the safe area; spare space is distributed by grow (water-level redistribution after items cap at max) | `gap_ratio == 1`, zero deficit / overflow | none |
| `compressed` | Semantic gaps must drop below preferred (never below min, i.e. 0.4×) to fit in the safe area | `gap_ratio < 1`, zero deficit / overflow | `gap_compressed` warning |
| `tight` | Content fits only by eating into the outer margins (gaps already at min) | `margin_deficit_ratio > 0`, zero overflow | `margin_squeeze` error |
| `overflow` | Content exceeds the whole page even with every value at its minimum | `body_overflow_ratio > 0` | `content_overflow` error |

`gap_ratio` is the true ratio of the actual gap to the preferred gap (always 1 for layouts without gaps), not an interpolation parameter. Violating an invariant (for example reporting normal with a positive overflow) is an `invalid_fit_state` error: the exporter is broken or the telemetry was forged. Stretch visuals have a hard minimum of 0.28H: when text squeezes the visual below that minimum, the page honestly degrades to tight / overflow instead of starving the main visual down to 0.01H while still reporting normal. Row layouts (grid / compare / stat / sidebar) have no compressible gaps and use only three states: normal / tight / overflow.

## Typed Items and Declared Sizing

Every component slot accepts typed items; plain content is wrapped automatically according to the component's semantics (see each component below):

```typst
visual(body, fit: "stretch")    // visual block without a card; stretch = fill the allocated slot
visual(body, fit: "natural")    // visual with intrinsic size (image(width: 100%) and similar)
card(body, role: "explanation") // theme card
takeaway(body)                  // conclusion card (role fixed to takeaway)
plain(body, role: "text")       // text block without a card
metric(value, label)            // metric entry for stat-slide
```

`role` is a closed set (`main_visual` / `figure` / `explanation` / `takeaway` / `text` / `caption`, and others; see `_ROLES`). It only affects the weights used to estimate the visual center and cannot change the checker's control flow: there is no escape hatch such as `decorative` that removes an object from the checks, and an unknown role panics at compile time.

To fill a stretch visual, use a placeholder `rect(width: 100%, height: 100%)` or a real image `image("f.png", width: 100%, height: 100%, fit: "contain")`. For a natural visual, use `image("f.png", width: 100%)`. Percent-sized content **must** be wrapped in `visual(...)`: a text slot that receives content with zero measured width panics (percent-width media and spacers have the same measurement signature), and only visual slots may register a payload at slot width, marked `declared` and verified by the pixel stage.

All validation happens at compile time and fails with a panic when: a required slot is `none`; visual content renders completely empty; text-slot content has no measurable width (spacers, empty strings) or no measurable height (bare rules); `grid` has fewer than 2 columns (use `stack` or `focus` for a single block); a `grid` / `compare` column holds `visual(fit: "stretch")` (row layouts are sized by natural height); the `figure` takeaway slot holds a stretch visual; a `stat` entry is not a `metric(...)` or its value / label renders empty; `focus` receives a `reveal-from` greater than 1 (it has a single frame); a `sidebar` slot receives a typed item (it draws its own cards); `reveal-from` is not an integer in `[1, step count]`; a `tuning` key is misspelled, has the wrong type, or is out of range; the `fit` of a `visual` is not `"stretch"` / `"natural"`; a role is outside the closed set; `xwysyy-slide` receives a `kind` argument (exempt pages can only come from their own layouts such as `outline-slide` / `title-slide`); `image-slide` gets no image.

Known limits: `place(...)` inside slot content leaves the document flow, so geometry telemetry cannot measure it; `hide(...)` keeps its full layout size, so the geometry layer cannot see it either. The pixel stage covers both cases (stray-ink and per-object hollow checks).

## Stepwise Reveal and the `#pause` Ban

touying's `#pause` / global `#uncover` depend on marks in markup, which cannot reach the `context` / `layout` closures inside a component; touying panics when they appear in component content. Components with a presentation order therefore provide `reveal: true`: blocks appear one subslide at a time in semantic order. Every component uses the same resolver: **an explicit `reveal-from` always takes precedence over the `reveal: true` sugar** (the sugar only applies to items without `reveal-from`). By default the second block of `duo` / `compare` appears at step 2, block i of `stack` / `grid` at step i, and in `figure` the image at step 1 and the takeaway at step 2 (the caption always follows the image); the `metric(...)` entries of `stat` also accept `reveal-from`. `focus` has a single frame and panics on a `reveal-from` greater than 1 instead of silently ignoring it; `sidebar` takes plain content only, so typed items and their `reveal-from` are rejected. Hidden steps keep their measured space, so every subslide has exactly the same layout.

Every actually rendered subslide emits one `<xwysyy-frame>` v2 mapping (id, step, steps, physical page number, handout flag, and the physical geometry of the body area); the full telemetry record is exported once, on the last frame, with `visible_from` on each object. Automatic ids come from touying's logical slide counter (`"<archetype>@s<n>"`) and stay stable across subslides and handout mode, so every frame joins back to its record. The checker validates the frame state machine (normal output is exactly steps 1..N on consecutive physical pages; handout mode has a single entry, for the last frame) and reconstructs every actually rendered frame, checking each one for overlap, empty frames (a step that shows nothing is an error), and sparse frames (an early frame with almost no content is `sparse_frame`, an error under agent). Pages that need more complex animation should not use layout components; fall back to a hand-written `xwysyy-slide` with `#pause`.

```typst
#duo-slide(title: [Main result], top: visual(image("fig.png", width: 100%, height: 100%, fit: "contain")),
  bottom: [*Conclusion.* Appears at step 2; the layout does not move.], reveal: true)
```

## Component API

All coordinates are normalized to `[0, 1]` relative to the current slide body (the content area inside the header and footer). Authors never write coordinates; the components measure and export them automatically. `id: auto` expands to `"<archetype>@s<logical slide number>"` (stable across reveal subslides); explicit names are still recommended when several pages use the same component. All numeric fine-tuning parameters live in the `tuning` dictionary (key, type, and range are validated; violations panic). The AI generation contract forbids changing `tuning`; the telemetry field `extra.tuned` records whether it was used, and under the agent profile any use is an error.

Every component accepts `debug: true`: solid lines draw the allocated frame and dashed lines draw the payload box, so a person can check that what the checker sees matches the rendering.

### duo-slide

A top/bottom semantic pair, such as a figure above its conclusion. Plain content in `top` is wrapped as `visual(fit: "natural")` (write `visual(...)` explicitly to fill the slot); plain content in `bottom` is wrapped with `card()`.

```typst
#duo-slide(
  title: [Key finding],
  top: visual(image("overview.png", width: 100%, height: 100%, fit: "contain")),
  bottom: card([*Conclusion.* The method lowers inference cost while staying interpretable.], role: "takeaway"),
  mode: "balanced",
)
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `top` / `bottom` | required | top block / bottom block (typed item or plain content) |
| `mode` | `"balanced"` | `compact` / `balanced` / `separated`; controls the spacing density between the two blocks |
| `relation` | `"supports"` | semantic relation label, closed set `supports` / `contrast` |
| `reveal` | `false` | when `true`, the bottom block appears on subslide 2 (`reveal-from` can override) |
| `tuning` | `(:)` | `top-width` (0.82), `bottom-width` (0.74), range [0.3, 0.95] |

### focus-slide

A single centered focus page for sparse content; plain content is wrapped with `card()`. It is the one exception to fill-first: the page keeps symmetric centered whitespace, the telemetry carries `intent: "focus"`, and density is guarded by the checker's `low_density`; content that exceeds the safe area is still reported as tight / overflow. As a single-frame component, it panics on a `reveal-from` greater than 1 and on stretch visuals. `tuning`: `width` (0.76, [0.3, 0.95]), `center-y` (0.46, [0.30, 0.70]).

```typst
#focus-slide(title: [One-line conclusion], body: [*Main conclusion.* This page makes one point.])
```

### stack-slide

N vertical blocks, the multi-block generalization of duo. Plain content is wrapped with `card()`.

```typst
#stack-slide(
  title: [Overview and key points],
  items: (
    visual(rect(width: 100%, height: 100%, fill: aqua)),
    card([*Point one.* Real heights are measured at compile time.]),
    takeaway([*Conclusion.* Spare space goes into the cards, not the gaps.]),
  ),
)
```

A stretch visual absorbs all spare space; without one, every `card` takes an equal share of the spare space and grows taller (`takeaway` / `plain` / natural visuals keep their natural height). The distance between blocks is set by `mode`. Each item accepts `reveal-from: <n>` (with `reveal: true`, block i appears at step i by default). An empty `items` panics. `tuning`: `width` (0.82, [0.3, 0.95]).

### grid-slide

N equal-height peer columns (N ≥ 2; use stack / focus for a single block). Plain content is wrapped with `card()` into equal-height theme cards, and the column height is the largest natural height (at least 0.6H). Adjacent columns carry a `peer` relation, and the checker validates the gutter. With `reveal: true`, column i appears on subslide i. Row layouts are sized by natural height, so `visual(fit: "stretch")` in a column panics at compile time. `tuning`: `gutter` (0.04, [0, 0.2]).

```typst
#grid-slide(
  title: [Three-step process],
  columns: ([*Measure.* Real heights at compile time], [*Report.* Export normalized geometry], [*Decide.* The agent reads the numbers]),
)
```

### compare-slide

Two equal-height cards, left and right (both required), read as a contrast. Their content is top-aligned: both sides start on the same line, which keeps the comparison readable. Plain content is wrapped with `card()`; stretch visuals panic. With `reveal: true`, the right side appears on subslide 2 (`reveal-from` can override). `tuning`: `gutter` (0.06, [0, 0.2]).

```typst
#compare-slide(
  title: [Two approaches],
  left: [*Approach A.* Styles converge and intent is hard to express.],
  right: [*Approach B.* Components guarantee spacing; the agent adjusts content.],
)
```

### stat-slide

A row of metric cards, each with one big number and a label, laid out by its own row engine. Entries must be built with `metric(value, label, reveal-from: auto)`; a value or label that renders empty panics. The payload measures the real widths of the value and the label separately, not the wrapper that is forced to full row width. An overlong value shrinks automatically to fit the card width (down to 0.6×; below that it wraps, the card grows taller, and fit reports it honestly), and the applied scale is exported in `extra.value_scales`. With `reveal: true`, card i appears at step i. `tuning`: `gutter` (0.04, [0, 0.2]).

```typst
#stat-slide(title: [Key metrics], stats: (
  metric([38%], [cost reduction]),
  metric([0.4], [accuracy loss]),
  metric([6], [datasets]),
))
```

### figure-slide

A figure with a tight caption and an optional takeaway. The caption is measured first and the figure slot then gets an explicit height, so a stretch figure safely fills its slot (Typst's `measure` returns 0 for percent heights in an unbounded context, and composing them directly would let content escape its box). Plain content in `fig` is wrapped as `visual(fit: "natural")`; write `visual(...)` to fill the slot. Plain content in `takeaway` is wrapped with `takeaway()`, and a stretch visual there panics. The caption gap is fixed at 0.5em and never compressed. Reveal uses the shared resolver: with `reveal: true` the figure appears at step 1 and the takeaway at step 2 (each `reveal-from` can override; the caption follows the figure). `tuning`: `figure-width` (0.80), `takeaway-width` (0.74), range [0.3, 0.95].

```typst
#figure-slide(
  title: [Main result],
  fig: visual(image("overview.png", width: 100%, height: 100%, fit: "contain")),
  caption: [Figure 1. Cost drops while accuracy holds.],
  takeaway: [*Conclusion.* Inference cost drops while interpretability is preserved.],
)
```

### sidebar-slide

A narrow label tab in the dark theme color next to a wide content card: an asymmetric two-column layout with equal column heights. `label` and `body` are both required and take plain content (the component draws its own cards: a typed item panics, and a `textbox` would produce a double card). There is no `reveal`, because the label and the content have no presentation order. `tuning`: `label-width` (0.26, [0.1, 0.5]), `gutter` (0.04, [0, 0.2]).

```typst
#sidebar-slide(
  title: [Method overview],
  label: [Method],
  body: [Measure real heights at compile time, allocate whitespace by rhythm, export telemetry.],
)
```

## Telemetry Schema v4

Every page exports one metadata record labelled `<xwysyy-slide-layout>`:

```json
{
  "schema": "xwysyy-slide-layout/v4",
  "id": "good-duo",
  "archetype": "duo",
  "layout_engine": "column",
  "page": 4,
  "frame_count": 1,
  "coordinate_system": "normalized-slide-body",
  "objects": [
    { "id": "good-duo:top", "object_kind": "visual", "semantic_role": "main_visual",
      "group": "good-duo",
      "frame":     { "x": 0.09, "y": 0.07, "w": 0.82, "h": 0.607 },
      "preferred": { "w": 0.82, "h": 0.28 },
      "payload":   { "x": 0.09, "y": 0.07, "w": 0.82, "h": 0.607 },
      "paint": null,
      "paint_fill": null,
      "payload_source": "declared",
      "overflow_x": false,
      "sizing": { "x": "stretch", "y": "stretch" },
      "visible_from": 1 }
  ],
  "relations": [
    { "from": "good-duo:top", "to": "good-duo:bottom",
      "kind": "supports", "axis": "vertical", "desired_proximity": "medium" }
  ],
  "fit": { "state": "normal", "required_height_ratio": 0.51, "gap_ratio": 1.0,
           "margin_deficit_ratio": 0, "body_overflow_ratio": 0 },
  "extra": { "mode": "balanced", "tuned": false }
}
```

The four boxes divide the work as follows. `frame` is the container the component allocated. `preferred` is the natural outer box the allocator saw, used to audit allocation decisions. `payload` is the content's real 2-D flow bbox, horizontal extent included: a narrow image's payload width is the image width rather than a copy of the frame width, and for wrapped text it is an approximate box, not glyph ink. `paint` is the visible card area and `paint_fill` its fill color, which the pixel stage uses to tell card background apart from card content ink. `payload_source` distinguishes measured from declared values: `declared` payloads (stretch slots, percent-width media) do not count toward density or empty-shell checks and are verified by the pixel stage. `overflow_x` is evidence that unwrappable content exceeds the slot width (wrappable text is clamped honestly and not falsely reported). Payload height is not clipped to the frame: overflowing content pushes the payload outside the box, where the checker can see it. A payload that extends horizontally beyond its own frame, or vertically beyond it in the normal / compressed states, is an `object_escapes_frame` error.

`object_kind` (`visual` / `card` / `takeaway` / `plain`) and `semantic_role` are both closed sets; an unknown value is a parse error (exit 2), not a warning. `archetype` is the semantic type and `layout_engine` the underlying engine (`column` / `row` / `single`).

Three companion records:

- `<xwysyy-page>` (`{"kind": "content|title|section|end|image|outline", "page": n}`): exempt kinds can only be produced by the corresponding layout functions, and two manifests on one physical page are an error.
- `<xwysyy-frame>` v2, one per actually rendered subslide: `id` / `step` / `steps` / `page` / `handout`, plus the physical pt geometry of `body` (which the pixel stage uses to convert coordinates instead of relying on hard-coded template constants) and `page_size`.
- `<xwysyy-header>` v2, one per content page: the title `scale`, horizontal `fits`, the actual title `height`, and vertical `fits_v`. An explicit line break or an oversized title hits the header band and reports an error.

## Checker Diagnostics

```bash
scripts/xwysyy-check deck.typ                          # one query, every schema
scripts/xwysyy-check deck.typ --input handout=true --format json
scripts/slide-check.py merged.json --page-count 21     # geometry engine for existing JSON
```

All coverage metrics use rectangle unions: `container_coverage` (union of frames), `visual_coverage` (union of paint and payload, the ink the eye sees), `payload_density` (union of **measured** payloads, the real content), `declared_payload` (union of declared payloads, for reference), and `payload_utilization` (the payload union as a share of the frame union). `low_density` looks at both visual_coverage and payload_density (when a page has no measured objects at all, the payload lower bound is left to the pixel stage); `over_dense` uses payload_density.

Severity comes from one shared policy table: structural, identity, escape, and determinism diagnostics are always errors; content-sufficiency diagnostics (`sparse_frame` / `telemetry_gap` / `manifest_gap` / `tuning_used` / `page_count_unknown` / `hollow_object` / `edge_ink`) are raised to errors under `--profile agent`; aesthetic diagnostics stay warnings.

| Diagnostic | Severity | Trigger | action |
| --- | --- | --- | --- |
| `content_overflow` | error | fit is `overflow` (which implies body_overflow_ratio > 0) | `split_slide` |
| `margin_squeeze` | error | fit is `tight`: content fits only by eating into the outer margins | `trim_or_split` |
| `gap_compressed` | warning | fit is `compressed`: semantic gaps were pushed below preferred | `trim_or_set_mode_compact` |
| `invalid_fit_state` | error | the fit state contradicts its numeric invariants (broken exporter or forged telemetry) | `report_bug` |
| `object_escapes_frame` | error | `overflow_x` is true; the payload extends horizontally beyond its own frame; under normal / compressed the payload extends vertically beyond it | `trim_content` |
| `object_outside_body` | error | horizontal out-of-bounds is checked in every fit state; vertical out-of-bounds only under normal / compressed | `trim_content` |
| `frame_integrity` | error | the frame state machine is broken: missing step, duplicate step, steps disagreeing with frame_count, non-consecutive subslides, a handout frame that is not the last one, or a record page that is not the last frame's page | `report_bug` |
| `orphan_frame` | error | a frame joins no record (deck level) | `report_bug` |
| `duplicate_slide_id` | error | two pages share one id, so frames cannot be attributed (deck level) | `use_unique_ids` |
| `empty_frame` | error | an actually rendered frame shows no object at all | `fix_reveal_order` |
| `sparse_frame` | warning¹ | the visible ink of an early frame is below half of the archetype's minimum | `fix_reveal_order` |
| `semantic_pair_split` | error | the gap of a semantic pair (weighted by visible ink) exceeds the proximity upper bound | `set_mode_compact` |
| `object_overlap` | error / warning¹ | a related pair overlaps on its axis and intersects in 2-D (error); unrelated blocks are checked per actually rendered frame (error under agent) | `split_slide` |
| `empty_shell` | error | an object's measured payload area approaches zero | `add_content` |
| `underfilled_card` | warning | a large card holds almost no content (a single word in a card 60% tall) | `add_content_or_merge` |
| `low_density` | warning | visual_coverage or payload_density is below the archetype's minimum | `merge_or_enlarge_visual` |
| `over_dense` | warning | payload_density is above 0.80 | `split_slide` |
| `hollow_frame` | warning | a natural visual's payload covers less than half of its frame on either axis | `change_visual_fit` |
| `column_imbalance` | warning | in a row layout, the preferred column heights differ by more than 0.55 relatively and more than 0.12 absolutely | `rebalance_columns` |
| `crowded_related_pair` | warning | a semantic pair's gap is below the lower bound (not reported when fit is not normal) | `set_mode_separated` |
| `wide_gutter` / `weak_relation_alignment` | warning | the horizontal gutter is too wide / the cross-axis center offset exceeds 0.10 | `reduce_gutter` / `align_pair` |
| `invalid_relation_direction` | warning | a relation runs against reading order (from lies below or to the right of to) | `review_manually` |
| `missing_relation_target` | error | a relation references an object id that does not exist | `report_bug` |
| `trapped_whitespace` | warning | the vertical gap between adjacent unrelated blocks exceeds 0.30 | `declare_relation_or_reduce_gap` |
| `content_clustered_top` / `_bottom` | warning | the weighted center is off and the whitespace on that side is too large | `recenter_content` |
| `header_shrunk` / `header_overflow` | warning / error | the header title was shrunk / still does not fit at 0.65 or hits the header band vertically | `shorten_title` |
| `telemetry_gap` | warning¹ | a content page has no layout telemetry (only joined frames count, so handout mode is safe) | `use_layout_component` |
| `manifest_gap` | warning¹ | a physical page lacks a page manifest (the total page count comes from pixel rendering or `--page-count`) | `use_slide_layouts` |
| `manifest_duplicate` | error | one physical page has two page manifests | `report_bug` |
| `page_count_unknown` | warning¹ | there is no source for the total page count, so manifest completeness cannot be judged | `pass_page_count` |
| `tuning_used` | warning¹ | the page overrides `tuning` (the contract reserves it for humans) | `remove_tuning` |

¹ Raised to error under `--profile agent`.

Parsing fails closed: a bbox with missing fields, paint with a negative size or without `paint_fill`, an unknown kind / role / state / payload_source, `visible_from` out of range, duplicate object ids within a record, relations that are not a list or whose kind / axis / proximity falls outside the closed set, and older schemas all exit as input errors (exit 2) and never produce a report filled with default values. A `--rules` override file is validated down to its leaves: scalars must be finite numbers (bools do not count as numbers), proximity ranges must be two-element lists with `0 <= lo <= hi`, and unknown rule names are rejected.

Exit codes: 2 for corrupt input; 1 when any error diagnostic exists (warnings count too under `--strict`); `--advisory` turns 1 into 0 but still exits 2 for corrupt input. Empty telemetry (a deck that uses no layout component at all) exits nonzero directly.

Thresholds are heuristic starting values anchored on the demo's good pages (every good page passes and each bad page hits its target), and they can be overridden with `--rules rules.json`. `--dump-features features.json` exports a flat per-page metric vector so that thresholds can later be calibrated from the distribution of past high-quality decks (use quantiles rather than means, and give focus its own distribution); do not reuse corpora sampled before the metrics themselves were corrected.

## Pixel Cross-Check

```bash
scripts/xwysyy-check deck.typ --pixels            # geometry + pixels in one run
scripts/xwysyy-check deck.typ --profile agent     # pixels always on under agent
```

This stage renders real PNGs and runs three checks that geometry telemetry cannot see. All page coordinate conversion uses the physical body geometry exported by `<xwysyy-frame>` v2 rather than hard-coded template margin constants. Every physical page is first joined to its (record, reveal step), and only objects with `visible_from <= step` take part in explaining the ink:

1. **`render_telemetry_mismatch`** (always error): ink inside the body area but outside the frames of the objects visible at the current step. It catches `place(...)` escapes, content drawn outside its allocated box, and **content that appears before its own step** (ink in the empty slot of a future object counts too).
2. **`edge_ink`** (error under agent): ink in the outer edge band of the page (horizontal overflow or suspected clipping). Besides an area threshold, a sliding-window row-peak detector catches a single long token or URL that touches the edge on one line. Full-bleed pages (title / section / end / image) are exempt according to the page manifest.
3. **`hollow_object`** (error under agent): per-object verification. On the record's last-frame page, it checks whether each object's payload box contains real ink, **excluding the page background and the object's own card fill** (`paint_fill`). Empty stretch visuals, `hide(...)`, and fake payloads propped up by card backgrounds all show up here. This step is the only evidence for a declared payload.

The pixel stage also gives the coverage checks the real total page count, which makes `manifest_gap` / `page_count_unknown` precise. Geometry telemetry is the main loop. Under the human profile, `--pixels` is for releases or for cases where telemetry and rendering seem to disagree; under the agent profile it is always on.

## AI Tuning Loop

```bash
scripts/xwysyy-check deck.typ --profile agent --format json
```

Fix according to each diagnostic's `action`: `split_slide` (split the page or cut text), `change_visual_fit` (turn the figure into `visual()` with `fit: "contain"` so it fills the slot), `merge_or_enlarge_visual` (enlarge the main visual, add explanation, or merge pages), `rebalance_columns` (move a long column to its own page), `set_mode_compact` (tighten the mode), `use_layout_component` (turn a hand-written page back into a component), `shorten_title` (shorten the title), `fix_reveal_order` (show a substantive block first), `add_content` (fill empty slots with real content). Rerun after each change until no errors remain; warnings are left to human judgment. `content_clustered_*` should normally not appear, because the components already allocate space; when it does, hand-written coordinates were used, so switch back to components. `report_bug` diagnostics (frame_integrity / orphan_frame / render_telemetry_mismatch / invalid_fit_state) should not be silenced by editing content: they mean the exporter or the telemetry itself is broken.

## Generation Contract

**Forbidden**: hand-written `#v(...)` to create large gaps; absolute coordinates or `place` to position ordinary body text; `align(bottom)` to push body text to the bottom; stacking several unconstrained blocks on one page; **changing any component's `tuning` dictionary** (numeric fine-tuning belongs to the human layer, and `extra.tuned` records it); **using `#pause` / `#meanwhile` / global `#uncover` inside layout component content** (touying panics; use the component's `reveal: true` for stepwise reveal); passing `kind` to `xwysyy-slide` (it is not a parameter and panics; exempt pages must use dedicated layouts such as `outline-slide` / `title-slide`); filling slots with spacers / empty strings / `hide(...)` / empty stretch visuals (compile-time panic or pixel-stage `hollow_object`).

**Required**: `duo-slide` for figure-over-text structure; `focus-slide` for a single conclusion with little content; `grid-slide` for multi-column peer information; `stack-slide` for several blocks with the same rhythm; `compare-slide` for a left/right contrast; `stat-slide` for a row of key numbers (entries via `metric(value, label)`); `figure-slide` for a figure with caption and conclusion; `sidebar-slide` for a narrow label with wide content (pass plain content, do not wrap it in `textbox`); write `visual(...)` explicitly for visuals that should fill their slot, and use `image(width: 100%)` for intrinsic-size images; use `reveal: true` for stepwise reveal (`reveal-from` for exact steps; explicit values always win); adjust density only through `mode: compact | balanced | separated`; after compiling, run `scripts/xwysyy-check deck.typ --profile agent` (pixels forced on), fix according to the returned actions, and do not stop iterating because the page "looks about right".

There are two audiences. AI follows the contract above: the agent profile treats every content-sufficiency diagnostic as an error and forces pixel verification. Human maintainers may tune numbers with `tuning` and use the default human profile, which treats coverage as warnings.

To use the checker, clone the source repository at the matching version and run `scripts/xwysyy-check` from the repository root.
