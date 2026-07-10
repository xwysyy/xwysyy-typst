#!/usr/bin/env python3
"""Diagnose xwysyy slide layout telemetry (schema v3).

The semantic layout components in ``src/layout.typ`` already guarantee sound
spacing: every block is measured at compile time and space is distributed by
a shared allocator with declared sizing.  This checker therefore does not try
to "fix spacing".  It reads the exported geometry and reports the
content-level decisions a component cannot make on its own:

  * the slide is too empty or too dense (payload, not just painted area);
  * a card is painted but nearly empty (underfilled shell);
  * a natural visual sits small inside a much larger frame (hollow frame);
  * a grid/compare column holds far more content than its peers;
  * a related pair is split, crowded, colliding, or misaligned;
  * the allocator ran out of room (gaps compressed, margins consumed, or a
    true overflow);
  * a slide title had to shrink (or still does not fit) in the page header;
  * content pages that carry no layout telemetry at all.

Schema v3 objects carry four boxes:

  frame      the box the component allocated
  preferred  the natural outer size the allocator saw
  payload    2-D flow bbox of the inner content (approximate for wrapped
             text; equals the padded frame for declared-stretch content)
  paint      the visible card box, or null for unpainted objects

plus per-axis ``sizing`` (natural/stretch) and ``visible_from``.  Reveal
frames arrive as ``<xwysyy-frame>`` mappings — one per physically rendered
subslide — so coverage counts real pages (handout safe).

Input: JSON from ``typst query`` — either one merged ``metadata`` query or
separate ``<xwysyy-slide-layout>`` / ``<xwysyy-page>`` / ``<xwysyy-frame>`` /
``<xwysyy-header>`` queries.  Records are recognised by their ``schema``
field, so any input file may contain any mixture.

Profiles: ``--profile human`` (default) reports coverage gaps and tuning use
as warnings; ``--profile agent`` escalates them to errors (an AI-generated
deck must not skip the layer or touch the manual tuning knobs).

Exit codes: 2 broken input, 1 any error diagnostic (or any warning with
``--strict``), 0 otherwise (always 0 with ``--advisory``).  Empty telemetry
exits 1: a deck that uses no layout component must not pass silently.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "xwysyy-slide-layout/v3"
PAGE_SCHEMA = "xwysyy-page/v1"
FRAME_SCHEMA = "xwysyy-frame/v1"
HEADER_SCHEMA = "xwysyy-header/v1"
# Page kinds that legitimately carry no layout telemetry.
EXEMPT_KINDS = {"title", "section", "end", "image", "outline"}
OBJECT_KINDS = {"visual", "card", "takeaway", "plain"}

DEFAULT_RULES: dict[str, Any] = {
    # weighted visual centre should stay near the optical centre
    "center_y_min": 0.35,
    "center_y_max": 0.60,
    "clustered_blank_min": 0.30,
    # rendered-ink floors per archetype (union of paint + payload boxes);
    # anchored on the demo's good pages, which all measure >= 0.45
    "ink_floor": {
        "focus": 0.06,
        "duo": 0.28,
        "stack": 0.25,
        "grid": 0.30,
        "compare": 0.30,
        "stat": 0.30,
        "figure": 0.30,
        "sidebar": 0.30,
        "_default": 0.25,
    },
    # payload floors per archetype: painted cards do not count here, so a row
    # of near-empty cards is caught even though it paints a lot of area
    "payload_floor": {
        "focus": 0.004,
        "_default": 0.010,
    },
    # payload above this fraction of the body reads as overloaded
    "dense_ceiling": 0.80,
    # a painted card whose payload area is below this while its paint area is
    # above paint_min is an underfilled shell
    "underfilled_payload_max": 0.004,
    "underfilled_paint_min": 0.20,
    # payload area at or below this is an empty shell (nothing inside)
    "empty_shell_max": 0.0002,
    # a natural visual filling less than this fraction of its frame (either
    # axis, frame large enough on that axis) is a hollow frame
    "hollow_utilization_min": 0.50,
    "hollow_frame_min": 0.30,
    # semantic proximity gap ranges (fraction of body height for vertical
    # pairs, of body width for the horizontal "gutter")
    "proximity_ranges": {
        "tight": [0.01, 0.07],
        "compact": [0.03, 0.12],
        "medium": [0.07, 0.20],
        "loose": [0.16, 0.30],
        "independent": [0.24, 0.46],
        "gutter": [0.02, 0.20],
    },
    "relation_center_delta_max": 0.10,
    # column imbalance: relative spread of the columns' natural heights AND a
    # real absolute spread (fractions of body height)
    "column_relative_max": 0.55,
    "column_absolute_min": 0.12,
    # largest vertical gap between two unrelated stacked content blocks
    "internal_gap_max": 0.30,
    # two unrelated frames overlapping by more than this share of the smaller
    # frame are colliding
    "overlap_ratio_max": 0.05,
    # symmetric out-of-body tolerance
    "outside_epsilon": 0.01,
    # visual weight by role, for the weighted centre estimate
    "role_weights": {
        "title": 1.30,
        "main_visual": 1.45,
        "figure": 1.25,
        "image": 1.25,
        "chart": 1.25,
        "visual": 1.25,
        "table": 1.10,
        "formula": 1.15,
        "callout": 1.15,
        "takeaway": 1.15,
        "option": 1.05,
        "column": 1.00,
        "explanation": 1.00,
        "label": 1.00,
        "metric": 1.05,
        "text": 1.00,
        "content": 1.00,
        "caption": 0.70,
        "decorative": 0.15,
    },
}

_DECORATIVE = {"decorative", "background"}

# Machine-actionable fix slug per diagnostic type (for agent loops).
ACTIONS: dict[str, str] = {
    "content_overflow": "split_slide",
    "margin_squeeze": "trim_or_split",
    "gap_compressed": "trim_or_set_mode_compact",
    "low_density": "merge_or_enlarge_visual",
    "over_dense": "split_slide",
    "underfilled_card": "add_content_or_merge",
    "empty_shell": "add_content",
    "hollow_frame": "change_visual_fit",
    "column_imbalance": "rebalance_columns",
    "semantic_pair_split": "set_mode_compact",
    "crowded_related_pair": "set_mode_separated",
    "wide_gutter": "reduce_gutter",
    "object_overlap": "split_slide",
    "object_outside_body": "trim_content",
    "weak_relation_alignment": "align_pair",
    "trapped_whitespace": "declare_relation_or_reduce_gap",
    "content_clustered_top": "recenter_content",
    "content_clustered_bottom": "recenter_content",
    "empty_frame": "fix_reveal_order",
    "header_shrunk": "shorten_title",
    "header_overflow": "shorten_title",
    "telemetry_gap": "use_layout_component",
    "manifest_gap": "use_slide_layouts",
    "tuning_used": "remove_tuning",
}


@dataclass
class BBox:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def area(self) -> float:
        return max(self.w, 0.0) * max(self.h, 0.0)

    def as_list(self) -> list[float]:
        return [round(self.x, 4), round(self.y, 4), round(self.w, 4), round(self.h, 4)]

    def intersection(self, other: "BBox") -> float:
        w = min(self.right, other.right) - max(self.x, other.x)
        h = min(self.bottom, other.bottom) - max(self.y, other.y)
        return max(w, 0.0) * max(h, 0.0)


def union_area(boxes: Iterable[BBox]) -> float:
    """Exact area of the union of axis-aligned rectangles (sweep over x)."""
    boxes = [b for b in boxes if b.w > 0 and b.h > 0]
    if not boxes:
        return 0.0
    xs = sorted({b.x for b in boxes} | {b.right for b in boxes})
    total = 0.0
    for x0, x1 in zip(xs, xs[1:]):
        if x1 <= x0:
            continue
        spans = sorted((b.y, b.bottom) for b in boxes if b.x <= x0 and b.right >= x1)
        covered = 0.0
        cur_lo, cur_hi = math.inf, -math.inf
        for lo, hi in spans:
            if cur_hi < cur_lo:
                cur_lo, cur_hi = lo, hi
            elif lo > cur_hi:
                covered += cur_hi - cur_lo
                cur_lo, cur_hi = lo, hi
            else:
                cur_hi = max(cur_hi, hi)
        if cur_hi >= cur_lo:
            covered += cur_hi - cur_lo
        total += covered * (x1 - x0)
    return total


@dataclass
class Obj:
    raw: dict[str, Any]
    frame: BBox
    payload: BBox
    paint: BBox | None
    preferred_h: float
    sizing_x: str
    sizing_y: str
    visible_from: int

    @property
    def id(self) -> str:
        return str(self.raw.get("id", "?"))

    @property
    def kind(self) -> str:
        return str(self.raw.get("object_kind", "?"))

    @property
    def role(self) -> str:
        return str(self.raw.get("semantic_role", "content"))

    @property
    def painted(self) -> bool:
        return self.paint is not None

    @property
    def ink(self) -> BBox:
        # A painted card is visible ink over its whole box; an unpainted
        # object only inks its payload.
        return self.paint if self.paint is not None else self.payload

    def ink_boxes(self) -> list[BBox]:
        return [self.paint, self.payload] if self.paint is not None else [self.payload]


@dataclass
class Diagnostic:
    severity: str
    type: str
    message: str
    metrics: dict[str, Any]
    fix: str
    action: str = ""

    def __post_init__(self) -> None:
        if not self.action:
            self.action = ACTIONS.get(self.type, "review_manually")


@dataclass
class SlideReport:
    id: str
    archetype: str
    metrics: dict[str, Any]
    diagnostics: list[Diagnostic]

    @property
    def has_error(self) -> bool:
        return any(d.severity == "error" for d in self.diagnostics)

    @property
    def has_problem(self) -> bool:
        return bool(self.diagnostics)


class TelemetryError(ValueError):
    pass


def _num(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TelemetryError(f"{field_name} must be numeric, got {type(value).__name__}")
    f = float(value)
    if not math.isfinite(f):
        raise TelemetryError(f"{field_name} must be finite")
    return f


def _bbox(value: Any, field_name: str) -> BBox:
    if not isinstance(value, dict):
        raise TelemetryError(f"{field_name} must be a dict with x/y/w/h")
    for key in ("x", "y", "w", "h"):
        if key not in value:
            raise TelemetryError(f"{field_name} is missing {key!r}")
    return BBox(_num(value["x"], f"{field_name}.x"), _num(value["y"], f"{field_name}.y"),
                _num(value["w"], f"{field_name}.w"), _num(value["h"], f"{field_name}.h"))


def _parse_obj(obj: dict[str, Any]) -> Obj:
    frame = _bbox(obj.get("frame"), "frame")
    payload = _bbox(obj.get("payload"), "payload")
    paint_raw = obj.get("paint")
    if paint_raw is not None and not isinstance(paint_raw, dict):
        raise TelemetryError(f"paint must be a dict or null, got {type(paint_raw).__name__}")
    paint = _bbox(paint_raw, "paint") if paint_raw is not None else None
    sizing = obj.get("sizing")
    if not isinstance(sizing, dict):
        raise TelemetryError("sizing must be a dict with x/y")
    sx, sy = str(sizing.get("x")), str(sizing.get("y"))
    if sx not in ("natural", "stretch") or sy not in ("natural", "stretch"):
        raise TelemetryError(f"sizing axes must be natural/stretch, got ({sx}, {sy})")
    preferred = obj.get("preferred") or {}
    pref_h = _num(preferred.get("h", frame.h), "preferred.h") if isinstance(preferred, dict) else frame.h
    vf = obj.get("visible_from", 1)
    if not isinstance(vf, int) or isinstance(vf, bool) or vf < 1:
        raise TelemetryError(f"visible_from must be an integer >= 1, got {vf!r}")
    return Obj(raw=obj, frame=frame, payload=payload, paint=paint,
               preferred_h=pref_h, sizing_x=sx, sizing_y=sy, visible_from=vf)


def _load_json(path: str | None) -> Any:
    if path in (None, "-"):
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _values(raw: Any) -> list[dict[str, Any]]:
    """Flatten a typst query result (array of elements or of values) into
    the value dicts."""
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise TelemetryError("input must be a typst query JSON array")
    out = []
    for item in raw:
        value = item.get("value") if isinstance(item, dict) and "value" in item else item
        if isinstance(value, dict):
            out.append(value)
    return out


def split_records(values: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {"layout": [], "pages": [], "frames": [], "headers": [], "unknown": []}
    for v in values:
        schema = str(v.get("schema", ""))
        if schema == SCHEMA or schema.startswith("xwysyy-slide-layout"):
            buckets["layout"].append(v)
        elif schema == PAGE_SCHEMA:
            buckets["pages"].append(v)
        elif schema == FRAME_SCHEMA:
            buckets["frames"].append(v)
        elif schema == HEADER_SCHEMA:
            buckets["headers"].append(v)
    return buckets


def _role_weight(role: str, rules: dict[str, Any]) -> float:
    return float(rules["role_weights"].get(role, 1.0))


def _proximity_range(relation: dict[str, Any], rules: dict[str, Any]) -> tuple[str, float, float, bool]:
    desired = str(relation.get("desired_proximity", "medium"))
    ranges = rules["proximity_ranges"]
    known = desired in ranges
    if not known:
        desired = "medium"
    lo, hi = ranges[desired]
    return desired, float(lo), float(hi), known


def _directed_gap(a: BBox, b: BBox, axis: str) -> tuple[float, float, bool]:
    """Directed gap from `a` to `b` (reading order: a above / left of b).
    Returns (gap, centre mismatch on the cross axis, reversed?)."""
    if axis == "horizontal":
        reverse = b.cx < a.cx
        gap = (a.x - b.right) if reverse else (b.x - a.right)
        return gap, abs(a.cy - b.cy), reverse
    reverse = b.cy < a.cy
    gap = (a.y - b.bottom) if reverse else (b.y - a.bottom)
    return gap, abs(a.cx - b.cx), reverse


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {k: _round(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_round(v) for v in value]
    return value


def analyze_slide(record: dict[str, Any], rules: dict[str, Any],
                  frames: list[dict[str, Any]] | None = None,
                  profile: str = "human") -> SlideReport:
    sid = str(record.get("id", "slide"))
    archetype = str(record.get("archetype", "custom"))
    extra = record.get("extra", {}) or {}
    fit = record.get("fit", {}) or {}
    frames = frames or []

    diagnostics: list[Diagnostic] = []
    schema = str(record.get("schema", ""))
    if schema != SCHEMA:
        diagnostics.append(Diagnostic(
            "error" if profile == "agent" else "warning", "schema_mismatch",
            f"Record schema is {schema or 'missing'}, expected {SCHEMA}; record skipped.",
            {"schema": schema}, "Re-export the telemetry with the current layout layer."))
        return SlideReport(sid, archetype, {}, diagnostics)

    raw_objects = record.get("objects", []) or []
    if not isinstance(raw_objects, list):
        raise TelemetryError(f"slide {sid}: objects must be a list")

    objects: list[Obj] = []
    seen_ids: set[str] = set()
    state = str(fit.get("state", "normal"))
    eps = float(rules["outside_epsilon"])
    for raw in raw_objects:
        if not isinstance(raw, dict):
            diagnostics.append(Diagnostic("error", "invalid_object", "Object entry is not a dictionary.",
                                          {"object": repr(raw)}, "Emit objects as schema-v3 dictionaries."))
            continue
        try:
            obj = _parse_obj(raw)
        except TelemetryError as exc:
            diagnostics.append(Diagnostic("error", "invalid_object", str(exc),
                                          {"object_id": raw.get("id", "?")}, "Fix the telemetry object fields."))
            continue
        if obj.id in seen_ids:
            diagnostics.append(Diagnostic("warning", "duplicate_object_id",
                                          "Two objects share one id; diagnostics cannot address them.",
                                          {"object_id": obj.id}, "Give every object a unique id."))
        seen_ids.add(obj.id)
        if obj.kind not in OBJECT_KINDS:
            diagnostics.append(Diagnostic("warning", "unknown_object_kind",
                                          f"Object kind {obj.kind!r} is not one of {sorted(OBJECT_KINDS)}.",
                                          {"object_id": obj.id}, "Use the typed item constructors."))
        objects.append(obj)
        if obj.frame.w < 0 or obj.frame.h < 0 or obj.payload.w < 0 or obj.payload.h < 0:
            diagnostics.append(Diagnostic("error", "negative_size", "Object has negative size.",
                                          {"object_id": obj.id, "frame": obj.frame.as_list()},
                                          "Use non-negative normalized width and height."))
        # Horizontal escape is checked in every fit state; vertical escape is
        # redundant once the allocator already reported tight/overflow.
        boxes = [("frame", obj.frame), ("payload", obj.payload)] + ([("paint", obj.paint)] if obj.paint else [])
        for kind_name, bb in boxes:
            if bb.x < -eps or bb.right > 1 + eps:
                diagnostics.append(Diagnostic("error", "object_outside_body",
                                              f"Object {kind_name} exceeds the slide body horizontally.",
                                              {"object_id": obj.id, "bbox": bb.as_list()},
                                              "Reduce content width or fix the tuning; the block does not fit."))
                break
            if state in ("normal", "compressed") and (bb.y < -eps or bb.bottom > 1 + eps):
                diagnostics.append(Diagnostic("error", "object_outside_body",
                                              f"Object {kind_name} exceeds the slide body vertically.",
                                              {"object_id": obj.id, "bbox": bb.as_list()},
                                              "Reduce content or split the slide; the block does not fit."))
                break

    content_objs = [o for o in objects if o.role not in _DECORATIVE]
    metrics: dict[str, Any] = {"object_count": len(objects), "content_object_count": len(content_objs)}

    if not content_objs:
        diagnostics.append(Diagnostic("warning", "empty_slide", "No content objects in telemetry.", {},
                                      "Add at least one non-decorative object."))
        return SlideReport(sid, archetype, metrics, diagnostics)

    # ---- coverage metrics (union of boxes, not clamped sums) ----
    ink_boxes = [b for o in content_objs for b in o.ink_boxes()]
    container_coverage = union_area(o.frame for o in content_objs)
    visual_coverage = union_area(ink_boxes)
    payload_density = union_area(o.payload for o in content_objs)
    frame_area_sum = sum(o.frame.area for o in content_objs)
    payload_utilization = (sum(o.payload.area for o in content_objs) / frame_area_sum) if frame_area_sum > 0 else 1.0

    xs = [o.ink for o in content_objs]
    left = min(b.x for b in xs)
    top = min(b.y for b in xs)
    right = max(b.right for b in xs)
    bot = max(b.bottom for b in xs)
    total_w = 0.0
    wy = 0.0
    for o in content_objs:
        w = max(o.ink.area, 0.01) * _role_weight(o.role, rules)
        total_w += w
        wy += w * o.ink.cy
    weighted_cy = wy / total_w if total_w else (top + bot) / 2

    metrics.update({
        "ink_bbox": BBox(left, top, right - left, bot - top).as_list(),
        "container_coverage": container_coverage,
        "visual_coverage": visual_coverage,
        "payload_density": payload_density,
        "payload_utilization": min(payload_utilization, 1.0),
        "weighted_center_y": weighted_cy,
        "top_blank_ratio": max(top, 0.0),
        "bottom_blank_ratio": max(1.0 - bot, 0.0),
    })

    # ---- fit (reported by the component's allocator) ----
    if state == "overflow":
        body_overflow = fit.get("body_overflow_ratio", 0.0)
        diagnostics.append(Diagnostic("error", "content_overflow",
                                      "Content is taller than the page even at minimum gaps.",
                                      {"required_height_ratio": fit.get("required_height_ratio"),
                                       "body_overflow_ratio": body_overflow},
                                      "Split the slide or shorten the text; do not rely on clamping."))
        if not (isinstance(body_overflow, (int, float)) and body_overflow > 0):
            diagnostics.append(Diagnostic("error", "invalid_fit_state",
                                          "Fit reports overflow but body_overflow_ratio is not > 0.",
                                          {"fit": fit}, "The allocator state machine is inconsistent; fix the exporter."))
    elif state == "tight":
        diagnostics.append(Diagnostic("error", "margin_squeeze",
                                      "Content only fits by consuming the outer margins.",
                                      {"required_height_ratio": fit.get("required_height_ratio"),
                                       "margin_deficit_ratio": fit.get("margin_deficit_ratio")},
                                      "Trim the content or split the slide to restore breathing room."))
    elif state == "compressed":
        diagnostics.append(Diagnostic("warning", "gap_compressed",
                                      "Semantic gaps were squeezed below their preferred size to fit the safe area.",
                                      {"required_height_ratio": fit.get("required_height_ratio"),
                                       "gap_scale": fit.get("gap_scale")},
                                      "Trim the content slightly, or accept the tighter rhythm."))
    elif state != "normal":
        diagnostics.append(Diagnostic("warning", "invalid_fit_state",
                                      f"Unknown fit state {state!r}.",
                                      {"fit": fit}, "Use normal/compressed/tight/overflow."))

    # ---- density ----
    floor = rules["ink_floor"].get(archetype, rules["ink_floor"]["_default"])
    pfloor = rules["payload_floor"].get(archetype, rules["payload_floor"]["_default"])
    if visual_coverage < floor or payload_density < pfloor:
        diagnostics.append(Diagnostic("warning", "low_density",
                                      "The slide carries very little real content.",
                                      {"visual_coverage": visual_coverage, "ink_floor": floor,
                                       "payload_density": payload_density, "payload_floor": pfloor},
                                      "Enlarge the main visual, add explanation, merge with a neighbour, or accept a deliberately minimal slide."))
    elif payload_density > rules["dense_ceiling"]:
        diagnostics.append(Diagnostic("warning", "over_dense",
                                      "The content payload inks most of the body.",
                                      {"payload_density": payload_density, "ceiling": rules["dense_ceiling"]},
                                      "Split the slide or move secondary content elsewhere."))

    # ---- per-object shells and hollow frames ----
    for o in content_objs:
        pay_area = o.payload.area
        if pay_area <= rules["empty_shell_max"]:
            diagnostics.append(Diagnostic("error", "empty_shell",
                                          "An object's payload is effectively empty.",
                                          {"object_id": o.id, "payload": o.payload.as_list()},
                                          "Put real content in the slot or remove the object."))
        elif (o.painted and pay_area < rules["underfilled_payload_max"]
              and o.paint is not None and o.paint.area > rules["underfilled_paint_min"]):
            diagnostics.append(Diagnostic("warning", "underfilled_card",
                                          "A large painted card holds almost no content.",
                                          {"object_id": o.id, "payload_area": pay_area,
                                           "paint_area": o.paint.area},
                                          "Add content to the card, merge cards, or drop the block."))
        if o.kind == "visual":
            for axis, fdim, pdim in (("y", o.frame.h, o.payload.h), ("x", o.frame.w, o.payload.w)):
                if (o.sizing_y == "natural" if axis == "y" else o.sizing_x == "natural") \
                        and fdim >= rules["hollow_frame_min"] and fdim > 0 and pdim / fdim < rules["hollow_utilization_min"]:
                    diagnostics.append(Diagnostic("warning", "hollow_frame",
                                                  "A visual sits small inside a much larger allocated frame.",
                                                  {"object_id": o.id, "axis": axis, "frame_dim": fdim,
                                                   "payload_dim": pdim, "utilization": pdim / fdim},
                                                  "Let the visual fill its slot (visual(fit: \"stretch\") with image(width: 100%, height: 100%, fit: \"contain\")) or shrink the slide's content."))
                    break

    # ---- asymmetric outer whitespace (clustering) ----
    top_blank = metrics["top_blank_ratio"]
    bottom_blank = metrics["bottom_blank_ratio"]
    if weighted_cy < rules["center_y_min"] and bottom_blank > rules["clustered_blank_min"]:
        diagnostics.append(Diagnostic("warning", "content_clustered_top",
                                      "Content sits high and leaves a large bottom blank.",
                                      {"weighted_center_y": weighted_cy, "bottom_blank_ratio": bottom_blank},
                                      "Move the group toward the optical centre or distribute it vertically."))
    elif weighted_cy > rules["center_y_max"] and top_blank > rules["clustered_blank_min"]:
        diagnostics.append(Diagnostic("warning", "content_clustered_bottom",
                                      "Content sits low and leaves a large top blank.",
                                      {"weighted_center_y": weighted_cy, "top_blank_ratio": top_blank},
                                      "Move the group toward the optical centre."))

    # ---- column imbalance (grid / compare / stat) ----
    if "natural_height_variance" in extra and len(content_objs) >= 2:
        prefs = [o.preferred_h for o in content_objs]
        absolute = max(prefs) - min(prefs)
        relative = absolute / max(max(prefs), 1e-9)
        metrics["column_absolute_spread"] = absolute
        metrics["column_relative_spread"] = relative
        if relative > rules["column_relative_max"] and absolute > rules["column_absolute_min"]:
            diagnostics.append(Diagnostic("warning", "column_imbalance",
                                          "One column holds far more content than its peers.",
                                          {"relative_spread": relative, "absolute_spread": absolute,
                                           "max_relative": rules["column_relative_max"],
                                           "min_absolute": rules["column_absolute_min"]},
                                          "Rebalance text across columns or move the long column to its own slide."))

    # ---- semantic relations (measured on visible ink, directed) ----
    by_id = {o.id: o for o in objects}
    rel_metrics: list[dict[str, Any]] = []
    related_pairs: set[frozenset[str]] = set()
    for rel in (record.get("relations", []) or []):
        if not isinstance(rel, dict):
            continue
        a, b = str(rel.get("from", "")), str(rel.get("to", ""))
        if a not in by_id or b not in by_id:
            diagnostics.append(Diagnostic("warning", "missing_relation_target",
                                          "Relation references an unknown object id.",
                                          {"from": a, "to": b}, "Check the object ids in the relation."))
            continue
        axis = str(rel.get("axis", "vertical"))
        if axis not in ("vertical", "horizontal"):
            diagnostics.append(Diagnostic("warning", "invalid_relation_axis",
                                          f"Relation axis {axis!r} is not vertical/horizontal.",
                                          {"from": a, "to": b, "axis": axis}, "Fix the relation axis."))
            continue
        oa, ob = by_id[a], by_id[b]
        gap, center_delta, reversed_ = _directed_gap(oa.ink, ob.ink, axis)
        name, lo, hi, known = _proximity_range(rel, rules)
        if not known:
            diagnostics.append(Diagnostic("warning", "unknown_proximity",
                                          "Relation names an unknown proximity; medium assumed.",
                                          {"from": a, "to": b,
                                           "desired_proximity": rel.get("desired_proximity")},
                                          "Use tight/compact/medium/loose/independent/gutter."))
        if reversed_:
            diagnostics.append(Diagnostic("warning", "invalid_relation_direction",
                                          "Relation runs against reading order (from is below/right of to).",
                                          {"from": a, "to": b, "axis": axis},
                                          "Swap from/to so relations follow reading order."))
        rm = {"from": a, "to": b, "axis": axis, "gap_ratio": gap,
              "center_delta": center_delta, "proximity": name, "target": [lo, hi]}
        rel_metrics.append(rm)
        related_pairs.add(frozenset((a, b)))
        if gap < -eps and oa.ink.intersection(ob.ink) > eps * eps:
            diagnostics.append(Diagnostic("error", "object_overlap",
                                          "Two related blocks overlap.",
                                          rm | {"overlap_depth": -gap},
                                          "Reduce block heights or split the slide; blocks must not collide."))
        elif gap > hi and axis == "horizontal":
            diagnostics.append(Diagnostic("warning", "wide_gutter",
                                          "Side-by-side columns are separated by an unusually wide gutter.",
                                          rm, "Reduce the gutter so the columns read as one row."))
        elif gap > hi:
            diagnostics.append(Diagnostic("error", "semantic_pair_split",
                                          "A related pair is separated by more whitespace than its proximity allows.",
                                          rm, "Tighten the mode (compact) or split the two blocks onto separate slides."))
        elif gap < lo and state == "normal":
            # A compressed/tight/overflowing slide squeezes its gaps by
            # design; the fit diagnostic already covers it.
            diagnostics.append(Diagnostic("warning", "crowded_related_pair",
                                          "A related pair is tighter than its proximity allows.",
                                          rm, "Loosen the mode or reduce block height."))
        if center_delta > rules["relation_center_delta_max"]:
            diagnostics.append(Diagnostic("warning", "weak_relation_alignment",
                                          "A related pair has a large centre mismatch across its axis.",
                                          rm | {"max": rules["relation_center_delta_max"]},
                                          "Share a centre line or an edge between related blocks."))
    if rel_metrics:
        metrics["relations"] = rel_metrics

    # ---- reveal frames: real rendered steps from <xwysyy-frame> ----
    steps = sorted({f["step"] for f in frames if isinstance(f.get("step"), int)}) or [1]
    frame_stats = []
    for step in steps:
        vis = [o for o in content_objs if o.visible_from <= step]
        frame_stats.append({
            "step": step,
            "visible_objects": len(vis),
            "visual_coverage": union_area(b for o in vis for b in o.ink_boxes()),
        })
        if not vis:
            diagnostics.append(Diagnostic("error", "empty_frame",
                                          "A rendered reveal step shows no objects at all.",
                                          {"step": step}, "Fix the reveal-from order; every step must show content."))
    if len(steps) > 1 or len(frame_stats) > 1:
        metrics["frames"] = frame_stats

    # ---- unrelated collisions, checked per rendered step ----
    reported_overlap: set[frozenset[str]] = set()
    for step in steps:
        vis = [o for o in content_objs if o.visible_from <= step]
        for i in range(len(vis)):
            for j in range(i + 1, len(vis)):
                a, b = vis[i], vis[j]
                key = frozenset((a.id, b.id))
                if key in related_pairs or key in reported_overlap:
                    continue
                inter = a.frame.intersection(b.frame)
                smaller = min(a.frame.area, b.frame.area)
                if smaller > 0 and inter / smaller > rules["overlap_ratio_max"]:
                    reported_overlap.add(key)
                    diagnostics.append(Diagnostic("warning", "object_overlap",
                                                  "Two unrelated blocks overlap.",
                                                  {"a": a.id, "b": b.id,
                                                   "overlap_share": inter / smaller, "step": step},
                                                  "Check the slide: unrelated blocks should not collide."))

    # ---- trapped whitespace between unrelated stacked blocks ----
    ordered = sorted(content_objs, key=lambda o: o.ink.y)
    worst_gap = 0.0
    worst_pair: tuple[str, str] | None = None
    for i in range(len(ordered) - 1):
        # Only the first x-overlapping successor is "the block below": objects
        # further down are separated by that neighbour, and diagonal objects
        # (no x overlap) are not stacked at all.
        for j in range(i + 1, len(ordered)):
            a, b = ordered[i], ordered[j]
            ax, bx = a.ink, b.ink
            x_overlap = min(ax.right, bx.right) - max(ax.x, bx.x)
            if x_overlap < 0.3 * min(ax.w, bx.w):
                continue
            if frozenset((a.id, b.id)) not in related_pairs and ax.bottom <= bx.y:
                gap = bx.y - ax.bottom
                if gap > worst_gap:
                    worst_gap, worst_pair = gap, (a.id, b.id)
            break
    if worst_pair is not None and worst_gap > rules["internal_gap_max"]:
        diagnostics.append(Diagnostic("warning", "trapped_whitespace",
                                      "Two unrelated stacked blocks are separated by a large vertical gap.",
                                      {"from": worst_pair[0], "to": worst_pair[1], "gap_ratio": worst_gap},
                                      "If the blocks belong together, mark them as a pair or use a stack/duo component; otherwise reduce the gap."))

    # ---- manual tuning (off-limits under the AI generation contract) ----
    if extra.get("tuned") is True:
        diagnostics.append(Diagnostic("error" if profile == "agent" else "warning", "tuning_used",
                                      "The slide overrides manual tuning knobs.",
                                      {}, "Remove the tuning dictionary; tuning is reserved for humans."))

    return SlideReport(sid, archetype, _round(metrics), diagnostics)


def coverage_report(records: list[dict[str, Any]], frames: list[dict[str, Any]],
                    pages: list[dict[str, Any]], profile: str = "human",
                    page_count: int | None = None) -> SlideReport:
    """Which content pages carry no layout telemetry at all.

    Covered pages come from the per-rendered-subslide frame mappings plus the
    record pages themselves — never from `page - frame_count + 1` ranges,
    which break in handout mode."""
    covered: set[int] = set()
    for f in frames:
        if isinstance(f.get("page"), int):
            covered.add(f["page"])
    for rec in records:
        if isinstance(rec.get("page"), int):
            covered.add(rec["page"])
    manifest_pages = {p["page"]: str(p.get("kind", "content")) for p in pages
                      if isinstance(p.get("page"), int)}
    content_pages = sorted(p for p, k in manifest_pages.items() if k not in EXEMPT_KINDS)
    exempt_pages = sorted(p for p, k in manifest_pages.items() if k in EXEMPT_KINDS)
    missing = [p for p in content_pages if p not in covered]
    metrics = {
        "content_pages": len(content_pages),
        "exempt_pages": len(exempt_pages),
        "covered_pages": len(content_pages) - len(missing),
        "missing_pages": missing,
    }
    gap_severity = "error" if profile == "agent" else "warning"
    diagnostics = []
    if missing:
        diagnostics.append(Diagnostic(gap_severity, "telemetry_gap",
                                      f"{len(missing)} content page(s) carry no layout telemetry.",
                                      {"pages": missing},
                                      "Build these pages with layout components, or mark them as deliberate exceptions."))
    known = max(manifest_pages, default=0)
    total = page_count if page_count is not None else known
    unmanifested = [p for p in range(1, total + 1) if p not in manifest_pages]
    if unmanifested:
        metrics["unmanifested_pages"] = unmanifested
        diagnostics.append(Diagnostic(gap_severity, "manifest_gap",
                                      f"{len(unmanifested)} page(s) carry no page manifest at all.",
                                      {"pages": unmanifested},
                                      "Produce every page with an xwysyy slide layout so it declares its kind."))
    return SlideReport("<deck>", "coverage", metrics, diagnostics)


def header_report(headers: list[dict[str, Any]]) -> SlideReport:
    """Header telemetry: titles that had to shrink, or still do not fit."""
    diagnostics = []
    shrunk = []
    for h in headers:
        page = h.get("page")
        scale = h.get("scale", 1.0)
        fits = h.get("fits", True)
        if not isinstance(scale, (int, float)):
            continue
        if fits is not True:
            diagnostics.append(Diagnostic("error", "header_overflow",
                                          "A slide title does not fit the header even at the minimum scale.",
                                          {"page": page, "scale": scale},
                                          "Shorten the slide title."))
        elif scale < 0.999:
            shrunk.append({"page": page, "scale": round(float(scale), 3)})
    if shrunk:
        diagnostics.append(Diagnostic("warning", "header_shrunk",
                                      f"{len(shrunk)} slide title(s) shrank to fit the header.",
                                      {"pages": shrunk}, "Consider shorter titles."))
    return SlideReport("<headers>", "header", {"header_records": len(headers)}, diagnostics)


def _validate_rules(base: dict[str, Any], override: dict[str, Any], path: str = "") -> None:
    for k, v in override.items():
        here = f"{path}{k}"
        if k not in base:
            raise TelemetryError(f"unknown rule {here!r}")
        if isinstance(base[k], dict):
            if not isinstance(v, dict):
                raise TelemetryError(f"rule {here!r} must be a table")
            # role_weights / ink_floor / payload_floor accept new keys with
            # numeric values; nested known keys are validated recursively.
            for kk, vv in v.items():
                if isinstance(base[k].get(kk), (dict, list)):
                    _validate_rules(base[k], {kk: vv}, path=f"{here}.")
                elif not isinstance(vv, (int, float, list)):
                    raise TelemetryError(f"rule {here}.{kk} must be numeric")
        elif isinstance(base[k], list):
            if not isinstance(v, list):
                raise TelemetryError(f"rule {here!r} must be a list")
        elif not isinstance(v, (int, float)):
            raise TelemetryError(f"rule {here!r} must be numeric")


def _load_rules(path: str | None) -> dict[str, Any]:
    rules = json.loads(json.dumps(DEFAULT_RULES))
    if not path:
        return rules
    p = Path(path)
    if not p.exists():
        raise TelemetryError(f"rules file does not exist: {path}")
    if p.suffix.lower() == ".json":
        override = json.loads(p.read_text(encoding="utf-8"))
    elif p.suffix.lower() == ".toml":
        import tomllib
        override = tomllib.loads(p.read_text(encoding="utf-8"))
    else:
        raise TelemetryError("rules file must be .json or .toml")
    if not isinstance(override, dict):
        raise TelemetryError("rules file must contain a table/object")
    _validate_rules(rules, override)

    def merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
        for k, v in extra.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                merge(base[k], v)
            else:
                base[k] = v
        return base

    return merge(rules, override)


def _as_json(reports: list[SlideReport]) -> str:
    return json.dumps({
        "schema": "xwysyy-slide-layout-check/v3",
        "summary": {
            "slides": len(reports),
            "errors": sum(1 for r in reports for d in r.diagnostics if d.severity == "error"),
            "warnings": sum(1 for r in reports for d in r.diagnostics if d.severity == "warning"),
        },
        "slides": [{"id": r.id, "archetype": r.archetype, "metrics": r.metrics,
                    "diagnostics": [asdict(d) for d in r.diagnostics]} for r in reports],
    }, ensure_ascii=False, indent=2)


def _as_text(reports: list[SlideReport]) -> str:
    lines: list[str] = []
    for r in reports:
        lines.append(f"slide {r.id} [{r.archetype}]")
        if not r.diagnostics:
            lines.append("  ok")
        for d in r.diagnostics:
            lines.append(f"  {d.severity} {d.type}: {d.message}")
            if d.metrics:
                lines.append("    " + " ".join(f"{k}={_round(v)}" for k, v in d.metrics.items()))
            lines.append(f"    fix: {d.fix}  [{d.action}]")
        m = r.metrics
        if "visual_coverage" in m:
            lines.append(f"  metrics: ink={m['visual_coverage']} payload={m['payload_density']} "
                         f"container={m['container_coverage']} util={m['payload_utilization']} "
                         f"center_y={m['weighted_center_y']}")
        if "content_pages" in m:
            lines.append(f"  coverage: {m['covered_pages']}/{m['content_pages']} content pages, "
                         f"{m['exempt_pages']} exempt, missing={m['missing_pages']}")
    return "\n".join(lines) if lines else "no telemetry records found"


def _features(reports: list[SlideReport]) -> list[dict[str, Any]]:
    out = []
    for r in reports:
        if r.archetype in ("coverage", "header"):
            continue
        flat: dict[str, Any] = {"id": r.id, "archetype": r.archetype}
        for k, v in r.metrics.items():
            if isinstance(v, (int, float)):
                flat[k] = v
        flat["diagnostics"] = sorted({d.type for d in r.diagnostics})
        out.append(flat)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", default="-",
                        help="JSON file or '-' for stdin; may contain any mixture of xwysyy schemas")
    parser.add_argument("--pages", default=None, help="additional page-manifest JSON")
    parser.add_argument("--frames", default=None, help="additional frame-mapping JSON")
    parser.add_argument("--headers", default=None, help="additional header-telemetry JSON")
    parser.add_argument("--page-count", type=int, default=None,
                        help="total physical page count (for manifest completeness)")
    parser.add_argument("--profile", choices=("human", "agent"), default="human",
                        help="agent escalates coverage gaps and tuning use to errors")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--rules", default=None, help="optional JSON/TOML rule overrides")
    parser.add_argument("--dump-features", default=None, metavar="PATH",
                        help="write flat per-slide feature vectors (for threshold calibration corpora)")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on any warning or error")
    parser.add_argument("--advisory", action="store_true", help="always exit zero (report only)")
    args = parser.parse_args(argv)

    try:
        rules = _load_rules(args.rules)
        buckets = split_records(_values(_load_json(args.input)))
        for flag in (args.pages, args.frames, args.headers):
            if flag:
                extra = split_records(_values(_load_json(flag)))
                for k in buckets:
                    buckets[k].extend(extra[k])
        records = buckets["layout"]
        frames_by_id: dict[str, list[dict[str, Any]]] = {}
        for f in buckets["frames"]:
            frames_by_id.setdefault(str(f.get("id", "?")), []).append(f)
        reports = [analyze_slide(rec, rules, frames_by_id.get(str(rec.get("id", ""))), args.profile)
                   for rec in records]
        if buckets["headers"]:
            reports.append(header_report(buckets["headers"]))
        if buckets["pages"]:
            reports.append(coverage_report(records, buckets["frames"], buckets["pages"],
                                           args.profile, args.page_count))
    except (OSError, json.JSONDecodeError, TelemetryError) as exc:
        print(f"slide-check: {exc}", file=sys.stderr)
        return 2

    # Empty telemetry means the deck does not use any layout component, so
    # there is nothing to guard — that must fail loudly, or a deck that
    # bypasses the layer entirely would pass every check.
    if not records:
        print("slide-check: no telemetry records found — the deck does not use "
              "any layout component", file=sys.stderr)
        return 0 if args.advisory else 1

    # Duplicate slide ids across records make diagnostics ambiguous.
    seen: set[str] = set()
    for r in reports:
        if r.id in seen:
            r.diagnostics.append(Diagnostic("warning", "duplicate_slide_id",
                                            "Two slides share one telemetry id.",
                                            {"id": r.id}, "Give each slide a unique explicit id."))
        seen.add(r.id)

    if args.dump_features:
        Path(args.dump_features).write_text(
            json.dumps(_features(reports), ensure_ascii=False, indent=2), encoding="utf-8")

    print(_as_json(reports) if args.format == "json" else _as_text(reports))

    if args.advisory:
        return 0
    if args.strict:
        return 1 if any(r.has_problem for r in reports) else 0
    return 1 if any(r.has_error for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
