#!/usr/bin/env python3
"""Diagnose xwysyy slide layout telemetry (schema v4).

The semantic layout components in ``src/layout.typ`` already guarantee sound
spacing: every block is measured at compile time and space is distributed by
a shared allocator with declared sizing.  This checker therefore does not try
to "fix spacing".  It reads the exported geometry and reports the
content-level decisions a component cannot make on its own:

  * the slide is too empty or too dense (measured payload, not painted area);
  * a card is painted but nearly empty (underfilled shell);
  * a natural visual sits small inside a much larger frame (hollow frame);
  * a grid/compare column holds far more content than its peers;
  * a related pair is split, crowded, colliding, or misaligned;
  * the allocator ran out of room (gaps compressed, margins consumed, or a
    true overflow);
  * a slide title had to shrink (or still does not fit) in the page header;
  * content pages that carry no layout telemetry at all.

Trust boundaries (v4):

  * parsing is FAIL-CLOSED: missing fields, unknown enums, non-finite
    numbers, negative sizes, or a non-v4 schema abort with a schema error
    (exit 2) instead of being patched with defaults;
  * every reveal frame must join exactly one layout record through a stable
    slide id; orphan frames, missing steps, duplicate ids, and frame counts
    that disagree with the record are structural errors;
  * the fit state machine is validated against its numeric invariants
    (overflow => body_overflow_ratio > 0, compressed => gap_ratio < 1, ...);
  * a "declared" payload (stretch slots, percent-width media) is a claim,
    never evidence: it does not count toward payload density or empty-shell
    passing — the pixel cross-check (scripts/xwysyy-check) verifies it;
  * coverage only counts frames that joined a valid record, and every
    physical page must carry exactly one page manifest.

Schema v4 objects carry four boxes (frame / preferred / payload / paint)
plus ``paint_fill``, ``payload_source``, ``overflow_x``, per-axis ``sizing``
and ``visible_from``.  Reveal frames arrive as ``<xwysyy-frame>`` v2
mappings — one per physically rendered subslide, with the physical body
geometry in pt.

Input: JSON from ``typst query`` — either one merged ``metadata`` query or
separate ``<xwysyy-slide-layout>`` / ``<xwysyy-page>`` / ``<xwysyy-frame>`` /
``<xwysyy-header>`` queries.  Records are recognised by their ``schema``
field, so any input file may contain any mixture.

Profiles: ``--profile human`` (default) keeps content-adequacy findings as
warnings; ``--profile agent`` escalates them to errors (an AI-generated deck
must not skip the layer, leave pages sparse, or touch the manual tuning
knobs).  Structural findings are errors in both profiles.

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

SCHEMA = "xwysyy-slide-layout/v4"
PAGE_SCHEMA = "xwysyy-page/v1"
FRAME_SCHEMA = "xwysyy-frame/v2"
HEADER_SCHEMA = "xwysyy-header/v2"
# Page kinds that legitimately carry no layout telemetry.  They cannot be
# spoofed: xwysyy-slide has no kind parameter, and the exempt kinds are
# emitted only by their dedicated slide functions.
EXEMPT_KINDS = {"title", "section", "end", "image", "outline"}
OBJECT_KINDS = {"visual", "card", "takeaway", "plain"}
# Mirror of the closed role set in src/layout.typ (no decorative escape
# hatch: roles weight metrics, they never change checker control flow).
ROLES = {
    "main_visual", "figure", "image", "chart", "visual", "table", "formula",
    "callout", "takeaway", "option", "column", "explanation", "label",
    "metric", "text", "content", "caption",
}
REL_KINDS = {"supports", "contrast", "peer", "caption", "labels"}
REL_AXES = {"vertical", "horizontal"}
FIT_STATES = {"normal", "compressed", "tight", "overflow"}
PAYLOAD_SOURCES = {"measured", "declared"}
COORDINATE_SYSTEM = "normalized-slide-body"

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
    # measured-payload floors per archetype: painted cards and declared
    # (stretch) payloads do not count here, so a row of near-empty cards is
    # caught even though it paints a lot of area.  Skipped when a slide has
    # no measured payload at all (pixel evidence covers declared slots).
    "payload_floor": {
        "focus": 0.004,
        "_default": 0.010,
    },
    # payload above this fraction of the body reads as overloaded
    "dense_ceiling": 0.80,
    # a painted card whose measured payload area is below this while its
    # paint area is above paint_min is an underfilled shell
    "underfilled_payload_max": 0.004,
    "underfilled_paint_min": 0.20,
    # measured payload area at or below this is an empty shell
    "empty_shell_max": 0.0002,
    # a natural visual filling less than this fraction of its frame (either
    # axis, frame large enough on that axis) is a hollow frame
    "hollow_utilization_min": 0.50,
    "hollow_frame_min": 0.30,
    # a reveal step whose visible ink is below this fraction of the
    # archetype's ink floor is a sparse frame (final step is covered by the
    # page-level density check instead)
    "step_ink_scale": 0.5,
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
    # payload containment tolerance against its own frame
    "escape_epsilon": 0.01,
    # visual weight by role, for the weighted centre estimate
    "role_weights": {
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
    },
}

# Machine-actionable fix slug per diagnostic type (for agent loops).
ACTIONS: dict[str, str] = {
    "content_overflow": "split_slide",
    "margin_squeeze": "trim_or_split",
    "gap_compressed": "trim_or_set_mode_compact",
    "invalid_fit_state": "report_bug",
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
    "object_escapes_frame": "trim_content",
    "weak_relation_alignment": "align_pair",
    "trapped_whitespace": "declare_relation_or_reduce_gap",
    "content_clustered_top": "recenter_content",
    "content_clustered_bottom": "recenter_content",
    "empty_frame": "fix_reveal_order",
    "sparse_frame": "fix_reveal_order",
    "frame_integrity": "report_bug",
    "orphan_frame": "report_bug",
    "duplicate_slide_id": "use_unique_ids",
    "duplicate_object_id": "use_unique_ids",
    "missing_relation_target": "report_bug",
    "empty_slide": "add_content",
    "header_shrunk": "shorten_title",
    "header_overflow": "shorten_title",
    "telemetry_gap": "use_layout_component",
    "manifest_gap": "use_slide_layouts",
    "manifest_duplicate": "report_bug",
    "page_count_unknown": "pass_page_count",
    "tuning_used": "remove_tuning",
    # pixel cross-check (scripts/xwysyy-check)
    "render_telemetry_mismatch": "report_bug",
    "hollow_object": "add_content",
    "edge_ink": "trim_content",
}

# Severity policy: type -> (human profile, agent profile).
#   * structural / provenance / geometry-escape findings are errors in every
#     profile — they mean the telemetry no longer describes the deck;
#   * content-adequacy findings escalate to errors for AI-generated decks;
#   * aesthetic findings stay warnings (humans and agents decide).
_EE = ("error", "error")
_WE = ("warning", "error")
_WW = ("warning", "warning")
SEVERITY: dict[str, tuple[str, str]] = {
    "content_overflow": _EE,
    "margin_squeeze": _EE,
    "invalid_fit_state": _EE,
    "object_outside_body": _EE,
    "object_escapes_frame": _EE,
    "empty_frame": _EE,
    "empty_shell": _EE,
    "frame_integrity": _EE,
    "orphan_frame": _EE,
    "duplicate_slide_id": _EE,
    "duplicate_object_id": _EE,
    "missing_relation_target": _EE,
    "semantic_pair_split": _EE,
    "header_overflow": _EE,
    "manifest_duplicate": _EE,
    "render_telemetry_mismatch": _EE,
    "hollow_object": _WE,
    "edge_ink": _WE,
    "empty_slide": _WE,
    "telemetry_gap": _WE,
    "manifest_gap": _WE,
    "page_count_unknown": _WE,
    "tuning_used": _WE,
    "sparse_frame": _WE,
    "gap_compressed": _WW,
    "low_density": _WW,
    "over_dense": _WW,
    "underfilled_card": _WW,
    "hollow_frame": _WW,
    "column_imbalance": _WW,
    "crowded_related_pair": _WW,
    "wide_gutter": _WW,
    "weak_relation_alignment": _WW,
    "trapped_whitespace": _WW,
    "content_clustered_top": _WW,
    "content_clustered_bottom": _WW,
    "header_shrunk": _WW,
}
# object_overlap: related pairs are hard errors, unrelated pairs escalate in
# the agent profile only (see call sites).


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
    paint_fill: str | None
    preferred_h: float
    payload_source: str
    overflow_x: bool
    sizing_x: str
    sizing_y: str
    visible_from: int

    @property
    def id(self) -> str:
        return str(self.raw["id"])

    @property
    def kind(self) -> str:
        return str(self.raw["object_kind"])

    @property
    def role(self) -> str:
        return str(self.raw["semantic_role"])

    @property
    def painted(self) -> bool:
        return self.paint is not None

    @property
    def measured(self) -> bool:
        return self.payload_source == "measured"

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


def _diag(profile: str, dtype: str, message: str, metrics: dict[str, Any], fix: str,
          action: str = "") -> Diagnostic:
    human, agent = SEVERITY.get(dtype, _WW)
    return Diagnostic(agent if profile == "agent" else human, dtype, message, metrics, fix, action)


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


# ---------------------------------------------------------------------------
# fail-closed parsing
# ---------------------------------------------------------------------------

def _num(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TelemetryError(f"{field_name} must be numeric, got {type(value).__name__}")
    f = float(value)
    if not math.isfinite(f):
        raise TelemetryError(f"{field_name} must be finite")
    return f


def _int(value: Any, field_name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TelemetryError(f"{field_name} must be an integer, got {value!r}")
    if value < minimum:
        raise TelemetryError(f"{field_name} must be >= {minimum}, got {value}")
    return value


def _str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise TelemetryError(f"{field_name} must be a non-empty string, got {value!r}")
    return value


def _bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TelemetryError(f"{field_name} must be a boolean, got {value!r}")
    return value


def _enum(value: Any, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise TelemetryError(f"{field_name} must be one of {sorted(allowed)}, got {value!r}")
    return value


def _bbox(value: Any, field_name: str, non_negative: bool = True) -> BBox:
    if not isinstance(value, dict):
        raise TelemetryError(f"{field_name} must be a dict with x/y/w/h")
    for key in ("x", "y", "w", "h"):
        if key not in value:
            raise TelemetryError(f"{field_name} is missing {key!r}")
    box = BBox(_num(value["x"], f"{field_name}.x"), _num(value["y"], f"{field_name}.y"),
               _num(value["w"], f"{field_name}.w"), _num(value["h"], f"{field_name}.h"))
    if non_negative and (box.w < 0 or box.h < 0):
        raise TelemetryError(f"{field_name} has a negative size")
    return box


def _parse_obj(obj: Any, frame_count: int, where: str) -> Obj:
    if not isinstance(obj, dict):
        raise TelemetryError(f"{where}: object entry is not a dictionary")
    oid = _str(obj.get("id"), f"{where}.id")
    _enum(obj.get("object_kind"), OBJECT_KINDS, f"{where}[{oid}].object_kind")
    _enum(obj.get("semantic_role"), ROLES, f"{where}[{oid}].semantic_role")
    frame = _bbox(obj.get("frame"), f"{where}[{oid}].frame")
    preferred = obj.get("preferred")
    if not isinstance(preferred, dict) or "w" not in preferred or "h" not in preferred:
        raise TelemetryError(f"{where}[{oid}].preferred must be a dict with w/h")
    pref_w = _num(preferred["w"], f"{where}[{oid}].preferred.w")
    pref_h = _num(preferred["h"], f"{where}[{oid}].preferred.h")
    if pref_w < 0 or pref_h < 0:
        raise TelemetryError(f"{where}[{oid}].preferred has a negative size")
    payload = _bbox(obj.get("payload"), f"{where}[{oid}].payload")
    paint_raw = obj.get("paint")
    paint = None
    paint_fill = None
    if paint_raw is not None:
        paint = _bbox(paint_raw, f"{where}[{oid}].paint")
        paint_fill = _str(obj.get("paint_fill"), f"{where}[{oid}].paint_fill")
    elif obj.get("paint_fill") is not None:
        raise TelemetryError(f"{where}[{oid}].paint_fill is set on an unpainted object")
    source = _enum(obj.get("payload_source"), PAYLOAD_SOURCES, f"{where}[{oid}].payload_source")
    over_x = _bool(obj.get("overflow_x"), f"{where}[{oid}].overflow_x")
    sizing = obj.get("sizing")
    if not isinstance(sizing, dict):
        raise TelemetryError(f"{where}[{oid}].sizing must be a dict with x/y")
    sx = _enum(sizing.get("x"), {"natural", "stretch"}, f"{where}[{oid}].sizing.x")
    sy = _enum(sizing.get("y"), {"natural", "stretch"}, f"{where}[{oid}].sizing.y")
    vf = _int(obj.get("visible_from", 1), f"{where}[{oid}].visible_from")
    if vf > frame_count:
        raise TelemetryError(f"{where}[{oid}].visible_from = {vf} exceeds frame_count = {frame_count}")
    return Obj(raw=obj, frame=frame, payload=payload, paint=paint, paint_fill=paint_fill,
               preferred_h=pref_h, payload_source=source, overflow_x=over_x,
               sizing_x=sx, sizing_y=sy, visible_from=vf)


def _parse_fit(fit: Any, where: str) -> dict[str, Any]:
    if not isinstance(fit, dict):
        raise TelemetryError(f"{where}.fit must be a dict")
    state = _enum(fit.get("state"), FIT_STATES, f"{where}.fit.state")
    out: dict[str, Any] = {"state": state}
    for key in ("required_height_ratio", "gap_ratio", "margin_deficit_ratio", "body_overflow_ratio"):
        val = _num(fit.get(key), f"{where}.fit.{key}")
        if val < 0:
            raise TelemetryError(f"{where}.fit.{key} must be >= 0, got {val}")
        out[key] = val
    return out


def _parse_relation(rel: Any, where: str) -> dict[str, Any]:
    if not isinstance(rel, dict):
        raise TelemetryError(f"{where}: relation entry is not a dictionary")
    return {
        "from": _str(rel.get("from"), f"{where}.from"),
        "to": _str(rel.get("to"), f"{where}.to"),
        "kind": _enum(rel.get("kind"), REL_KINDS, f"{where}.kind"),
        "axis": _enum(rel.get("axis"), REL_AXES, f"{where}.axis"),
        "desired_proximity": _enum(rel.get("desired_proximity"),
                                   set(DEFAULT_RULES["proximity_ranges"]),
                                   f"{where}.desired_proximity"),
    }


@dataclass
class Record:
    raw: dict[str, Any]
    id: str
    archetype: str
    page: int
    frame_count: int
    objects: list[Obj]
    relations: list[dict[str, Any]]
    fit: dict[str, Any]
    extra: dict[str, Any]


def parse_record(rec: dict[str, Any]) -> Record:
    schema = rec.get("schema")
    if schema != SCHEMA:
        raise TelemetryError(f"record schema is {schema!r}, expected {SCHEMA!r}; "
                             "re-export the telemetry with the current layout layer")
    rid = _str(rec.get("id"), "record.id")
    where = f"slide {rid}"
    archetype = _str(rec.get("archetype"), f"{where}.archetype")
    _str(rec.get("layout_engine"), f"{where}.layout_engine")
    if rec.get("coordinate_system") != COORDINATE_SYSTEM:
        raise TelemetryError(f"{where}.coordinate_system must be {COORDINATE_SYSTEM!r}")
    page = _int(rec.get("page"), f"{where}.page")
    frame_count = _int(rec.get("frame_count"), f"{where}.frame_count")
    raw_objects = rec.get("objects")
    if not isinstance(raw_objects, list) or not raw_objects:
        raise TelemetryError(f"{where}.objects must be a non-empty list")
    objects = [_parse_obj(o, frame_count, where) for o in raw_objects]
    seen: set[str] = set()
    for o in objects:
        if o.id in seen:
            raise TelemetryError(f"{where}: duplicate object id {o.id!r}")
        seen.add(o.id)
    raw_relations = rec.get("relations")
    if not isinstance(raw_relations, list):
        raise TelemetryError(f"{where}.relations must be a list")
    relations = [_parse_relation(r, f"{where}.relations") for r in raw_relations]
    fit = _parse_fit(rec.get("fit"), where)
    extra = rec.get("extra")
    if not isinstance(extra, dict):
        raise TelemetryError(f"{where}.extra must be a dict")
    return Record(raw=rec, id=rid, archetype=archetype, page=page,
                  frame_count=frame_count, objects=objects, relations=relations,
                  fit=fit, extra=extra)


def parse_frame(f: dict[str, Any]) -> dict[str, Any]:
    schema = f.get("schema")
    if schema != FRAME_SCHEMA:
        raise TelemetryError(f"frame schema is {schema!r}, expected {FRAME_SCHEMA!r}")
    fid = _str(f.get("id"), "frame.id")
    where = f"frame {fid}"
    out = {
        "id": fid,
        "step": _int(f.get("step"), f"{where}.step"),
        "steps": _int(f.get("steps"), f"{where}.steps"),
        "page": _int(f.get("page"), f"{where}.page"),
        "handout": _bool(f.get("handout"), f"{where}.handout"),
    }
    body = f.get("body")
    if not isinstance(body, dict):
        raise TelemetryError(f"{where}.body must be a dict with x/y/w/h")
    out["body"] = {k: _num(body.get(k), f"{where}.body.{k}") for k in ("x", "y", "w", "h")}
    if out["body"]["w"] <= 0 or out["body"]["h"] <= 0:
        raise TelemetryError(f"{where}.body must have a positive size")
    page_size = f.get("page_size")
    if not isinstance(page_size, dict):
        raise TelemetryError(f"{where}.page_size must be a dict with w/h")
    out["page_size"] = {k: _num(page_size.get(k), f"{where}.page_size.{k}") for k in ("w", "h")}
    if out["page_size"]["w"] <= 0 or out["page_size"]["h"] <= 0:
        raise TelemetryError(f"{where}.page_size must have a positive size")
    return out


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
    buckets: dict[str, list[dict[str, Any]]] = {"layout": [], "pages": [], "frames": [], "headers": []}
    for v in values:
        schema = str(v.get("schema", ""))
        if schema.startswith("xwysyy-slide-layout"):
            buckets["layout"].append(v)
        elif schema.startswith("xwysyy-page"):
            buckets["pages"].append(v)
        elif schema.startswith("xwysyy-frame"):
            buckets["frames"].append(v)
        elif schema.startswith("xwysyy-header"):
            buckets["headers"].append(v)
    return buckets


def join_frames(records: list[Record], raw_frames: list[dict[str, Any]]) -> tuple[
        dict[str, list[dict[str, Any]]], list[dict[str, Any]], set[str]]:
    """Parse frames and join them to records by id.  Returns (frames by
    record id, orphan frames, duplicate record ids)."""
    frames = [parse_frame(f) for f in raw_frames]
    ids: set[str] = set()
    dup_ids: set[str] = set()
    for r in records:
        if r.id in ids:
            dup_ids.add(r.id)
        ids.add(r.id)
    by_id: dict[str, list[dict[str, Any]]] = {}
    orphans: list[dict[str, Any]] = []
    for f in frames:
        if f["id"] in ids:
            by_id.setdefault(f["id"], []).append(f)
        else:
            orphans.append(f)
    return by_id, orphans, dup_ids


# ---------------------------------------------------------------------------
# analysis
# ---------------------------------------------------------------------------

def _role_weight(role: str, rules: dict[str, Any]) -> float:
    return float(rules["role_weights"].get(role, 1.0))


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


def _check_fit_invariants(fit: dict[str, Any], diagnostics: list[Diagnostic],
                          profile: str) -> None:
    """The four states carry hard numeric invariants; a contradiction means
    the exporter (or a forger) produced a fit the allocator cannot emit."""
    state = fit["state"]
    gr = fit["gap_ratio"]
    md = fit["margin_deficit_ratio"]
    bo = fit["body_overflow_ratio"]
    eps = 1e-6
    bad = None
    if state == "normal" and (abs(gr - 1.0) > eps or md > eps or bo > eps):
        bad = "normal requires gap_ratio == 1 and zero deficit/overflow"
    elif state == "compressed" and (gr >= 1.0 - eps or md > eps or bo > eps):
        bad = "compressed requires gap_ratio < 1 and zero deficit/overflow"
    elif state == "tight" and (md <= eps or bo > eps):
        bad = "tight requires margin_deficit_ratio > 0 and zero overflow"
    elif state == "overflow" and bo <= eps:
        bad = "overflow requires body_overflow_ratio > 0"
    if bad:
        diagnostics.append(_diag(profile, "invalid_fit_state",
                                 f"Fit state {state!r} contradicts its numbers: {bad}.",
                                 {"fit": fit},
                                 "The allocator state machine is inconsistent; fix the exporter."))


def _check_frame_machine(rec: Record, frames: list[dict[str, Any]],
                         diagnostics: list[Diagnostic], profile: str) -> list[int]:
    """Validate the frame set against the record and return the rendered
    steps.  Normal output must carry exactly steps 1..frame_count on
    consecutive pages; handout output carries exactly the final step."""
    def integrity(msg: str, metrics: dict[str, Any]) -> None:
        diagnostics.append(_diag(profile, "frame_integrity",
                                 msg, metrics,
                                 "Frame mappings disagree with the layout record; fix the exporter."))

    if not frames:
        integrity("The record has no rendered frame mapping at all.",
                  {"frame_count": rec.frame_count})
        return []
    for f in frames:
        if f["steps"] != rec.frame_count:
            integrity("A frame declares a different total step count than the record.",
                      {"frame_steps": f["steps"], "frame_count": rec.frame_count})
    handouts = {f["handout"] for f in frames}
    if len(handouts) > 1:
        integrity("Frames disagree on handout mode.", {})
        return sorted({f["step"] for f in frames})
    steps = sorted(f["step"] for f in frames)
    if len(set(steps)) != len(steps):
        integrity("Two frames share one reveal step.", {"steps": steps})
    pages = [f["page"] for f in sorted(frames, key=lambda f: f["step"])]
    if handouts == {True}:
        if steps != [rec.frame_count]:
            integrity("Handout output must carry exactly the final step.",
                      {"steps": steps, "frame_count": rec.frame_count})
    else:
        if sorted(set(steps)) != list(range(1, rec.frame_count + 1)):
            integrity("Rendered steps are not exactly 1..frame_count.",
                      {"steps": steps, "frame_count": rec.frame_count})
        elif any(b - a != 1 for a, b in zip(pages, pages[1:])):
            integrity("Reveal subslides are not on consecutive pages.", {"pages": pages})
    if rec.page != pages[-1]:
        integrity("The record page is not the final frame's page.",
                  {"record_page": rec.page, "frame_pages": pages})
    return sorted(set(steps))


def analyze_slide(rec: Record, rules: dict[str, Any],
                  frames: list[dict[str, Any]] | None = None,
                  profile: str = "human") -> SlideReport:
    sid = rec.id
    archetype = rec.archetype
    extra = rec.extra
    fit = rec.fit
    objects = rec.objects
    frames = frames or []

    diagnostics: list[Diagnostic] = []
    metrics: dict[str, Any] = {"object_count": len(objects)}

    # ---- structural checks run FIRST and never depend on content filters ----
    _check_fit_invariants(fit, diagnostics, profile)
    steps = _check_frame_machine(rec, frames, diagnostics, profile)

    state = fit["state"]
    eps = float(rules["outside_epsilon"])
    esc = float(rules["escape_epsilon"])
    for o in objects:
        if o.overflow_x:
            diagnostics.append(_diag(profile, "object_escapes_frame",
                                     "Unbreakable content is wider than its slot and escapes horizontally.",
                                     {"object_id": o.id, "frame": o.frame.as_list()},
                                     "Break the content (or shrink it) so it fits its slot width."))
        if o.payload.x < o.frame.x - esc or o.payload.right > o.frame.right + esc:
            diagnostics.append(_diag(profile, "object_escapes_frame",
                                     "An object's payload runs outside its own frame horizontally.",
                                     {"object_id": o.id, "frame": o.frame.as_list(),
                                      "payload": o.payload.as_list()},
                                     "The exporter clamps payloads to their frame; fix the telemetry."))
        if state in ("normal", "compressed") and o.payload.bottom > o.frame.bottom + esc:
            diagnostics.append(_diag(profile, "object_escapes_frame",
                                     "An object's payload runs below its frame although the fit state is relaxed.",
                                     {"object_id": o.id, "frame": o.frame.as_list(),
                                      "payload": o.payload.as_list(), "state": state},
                                     "A payload taller than its frame must degrade the fit state."))
        # Horizontal escape out of the body is checked in every fit state;
        # vertical escape is redundant once the allocator reported
        # tight/overflow.
        boxes = [("frame", o.frame), ("payload", o.payload)] + ([("paint", o.paint)] if o.paint else [])
        for kind_name, bb in boxes:
            if bb.x < -eps or bb.right > 1 + eps:
                diagnostics.append(_diag(profile, "object_outside_body",
                                         f"Object {kind_name} exceeds the slide body horizontally.",
                                         {"object_id": o.id, "bbox": bb.as_list()},
                                         "Reduce content width or fix the tuning; the block does not fit."))
                break
            if state in ("normal", "compressed") and (bb.y < -eps or bb.bottom > 1 + eps):
                diagnostics.append(_diag(profile, "object_outside_body",
                                         f"Object {kind_name} exceeds the slide body vertically.",
                                         {"object_id": o.id, "bbox": bb.as_list()},
                                         "Reduce content or split the slide; the block does not fit."))
                break

    # ---- fit (reported by the component's allocator) ----
    if state == "overflow":
        diagnostics.append(_diag(profile, "content_overflow",
                                 "Content is taller than the page even at minimum gaps.",
                                 {"required_height_ratio": fit["required_height_ratio"],
                                  "body_overflow_ratio": fit["body_overflow_ratio"]},
                                 "Split the slide or shorten the text; do not rely on clamping."))
    elif state == "tight":
        diagnostics.append(_diag(profile, "margin_squeeze",
                                 "Content only fits by consuming the outer margins.",
                                 {"required_height_ratio": fit["required_height_ratio"],
                                  "margin_deficit_ratio": fit["margin_deficit_ratio"]},
                                 "Trim the content or split the slide to restore breathing room."))
    elif state == "compressed":
        diagnostics.append(_diag(profile, "gap_compressed",
                                 "Semantic gaps were squeezed below their preferred size to fit the safe area.",
                                 {"required_height_ratio": fit["required_height_ratio"],
                                  "gap_ratio": fit["gap_ratio"]},
                                 "Trim the content slightly, or accept the tighter rhythm."))

    # ---- manual tuning (off-limits under the AI generation contract) ----
    if extra.get("tuned") is True:
        diagnostics.append(_diag(profile, "tuning_used",
                                 "The slide overrides manual tuning knobs.",
                                 {}, "Remove the tuning dictionary; tuning is reserved for humans."))

    # ---- coverage metrics (union of boxes, not clamped sums) ----
    ink_boxes = [b for o in objects for b in o.ink_boxes()]
    measured = [o for o in objects if o.measured]
    container_coverage = union_area(o.frame for o in objects)
    visual_coverage = union_area(ink_boxes)
    payload_density = union_area(o.payload for o in measured)
    declared_payload = union_area(o.payload for o in objects if not o.measured)
    payload_utilization = (union_area(o.payload for o in objects) / container_coverage) \
        if container_coverage > 0 else 1.0

    xs = [o.ink for o in objects]
    left = min(b.x for b in xs)
    top = min(b.y for b in xs)
    right = max(b.right for b in xs)
    bot = max(b.bottom for b in xs)
    total_w = 0.0
    wy = 0.0
    for o in objects:
        w = max(o.ink.area, 0.01) * _role_weight(o.role, rules)
        total_w += w
        wy += w * o.ink.cy
    weighted_cy = wy / total_w if total_w else (top + bot) / 2

    metrics.update({
        "ink_bbox": BBox(left, top, right - left, bot - top).as_list(),
        "container_coverage": container_coverage,
        "visual_coverage": visual_coverage,
        "payload_density": payload_density,
        "declared_payload": declared_payload,
        "payload_utilization": min(payload_utilization, 1.0),
        "weighted_center_y": weighted_cy,
        "top_blank_ratio": max(top, 0.0),
        "bottom_blank_ratio": max(1.0 - bot, 0.0),
    })

    # ---- density ----
    floor = rules["ink_floor"].get(archetype, rules["ink_floor"]["_default"])
    pfloor = rules["payload_floor"].get(archetype, rules["payload_floor"]["_default"])
    payload_low = bool(measured) and payload_density < pfloor
    if visual_coverage < floor or payload_low:
        diagnostics.append(_diag(profile, "low_density",
                                 "The slide carries very little real content.",
                                 {"visual_coverage": visual_coverage, "ink_floor": floor,
                                  "payload_density": payload_density, "payload_floor": pfloor},
                                 "Enlarge the main visual, add explanation, merge with a neighbour, or accept a deliberately minimal slide."))
    elif payload_density > rules["dense_ceiling"]:
        diagnostics.append(_diag(profile, "over_dense",
                                 "The content payload inks most of the body.",
                                 {"payload_density": payload_density, "ceiling": rules["dense_ceiling"]},
                                 "Split the slide or move secondary content elsewhere."))

    # ---- per-object shells and hollow frames (measured payloads only:
    # declared payloads are verified against pixels, not trusted) ----
    for o in objects:
        if not o.measured:
            continue
        pay_area = o.payload.area
        if pay_area <= rules["empty_shell_max"]:
            diagnostics.append(_diag(profile, "empty_shell",
                                     "An object's measured payload is effectively empty.",
                                     {"object_id": o.id, "payload": o.payload.as_list()},
                                     "Put real content in the slot or remove the object."))
        elif (o.painted and pay_area < rules["underfilled_payload_max"]
              and o.paint is not None and o.paint.area > rules["underfilled_paint_min"]):
            diagnostics.append(_diag(profile, "underfilled_card",
                                     "A large painted card holds almost no content.",
                                     {"object_id": o.id, "payload_area": pay_area,
                                      "paint_area": o.paint.area},
                                     "Add content to the card, merge cards, or drop the block."))
        if o.kind == "visual":
            for axis, fdim, pdim in (("y", o.frame.h, o.payload.h), ("x", o.frame.w, o.payload.w)):
                if (o.sizing_y == "natural" if axis == "y" else o.sizing_x == "natural") \
                        and fdim >= rules["hollow_frame_min"] and fdim > 0 and pdim / fdim < rules["hollow_utilization_min"]:
                    diagnostics.append(_diag(profile, "hollow_frame",
                                             "A visual sits small inside a much larger allocated frame.",
                                             {"object_id": o.id, "axis": axis, "frame_dim": fdim,
                                              "payload_dim": pdim, "utilization": pdim / fdim},
                                             "Let the visual fill its slot (visual(fit: \"stretch\") with image(width: 100%, height: 100%, fit: \"contain\")) or shrink the slide's content."))
                    break

    # ---- asymmetric outer whitespace (clustering) ----
    top_blank = metrics["top_blank_ratio"]
    bottom_blank = metrics["bottom_blank_ratio"]
    if weighted_cy < rules["center_y_min"] and bottom_blank > rules["clustered_blank_min"]:
        diagnostics.append(_diag(profile, "content_clustered_top",
                                 "Content sits high and leaves a large bottom blank.",
                                 {"weighted_center_y": weighted_cy, "bottom_blank_ratio": bottom_blank},
                                 "Move the group toward the optical centre or distribute it vertically."))
    elif weighted_cy > rules["center_y_max"] and top_blank > rules["clustered_blank_min"]:
        diagnostics.append(_diag(profile, "content_clustered_bottom",
                                 "Content sits low and leaves a large top blank.",
                                 {"weighted_center_y": weighted_cy, "top_blank_ratio": top_blank},
                                 "Move the group toward the optical centre."))

    # ---- column imbalance (row archetypes) ----
    if archetype in ("grid", "compare", "stat") and len(objects) >= 2:
        prefs = [o.preferred_h for o in objects]
        absolute = max(prefs) - min(prefs)
        relative = absolute / max(max(prefs), 1e-9)
        metrics["column_absolute_spread"] = absolute
        metrics["column_relative_spread"] = relative
        if relative > rules["column_relative_max"] and absolute > rules["column_absolute_min"]:
            diagnostics.append(_diag(profile, "column_imbalance",
                                     "One column holds far more content than its peers.",
                                     {"relative_spread": relative, "absolute_spread": absolute,
                                      "max_relative": rules["column_relative_max"],
                                      "min_absolute": rules["column_absolute_min"]},
                                     "Rebalance text across columns or move the long column to its own slide."))

    # ---- semantic relations (measured on visible ink, directed) ----
    by_id = {o.id: o for o in objects}
    rel_metrics: list[dict[str, Any]] = []
    related_pairs: set[frozenset[str]] = set()
    for rel in rec.relations:
        a, b = rel["from"], rel["to"]
        if a not in by_id or b not in by_id:
            diagnostics.append(_diag(profile, "missing_relation_target",
                                     "Relation references an unknown object id.",
                                     {"from": a, "to": b}, "Check the object ids in the relation."))
            continue
        axis = rel["axis"]
        oa, ob = by_id[a], by_id[b]
        gap, center_delta, reversed_ = _directed_gap(oa.ink, ob.ink, axis)
        name = rel["desired_proximity"]
        lo, hi = (float(v) for v in rules["proximity_ranges"][name])
        if reversed_:
            diagnostics.append(_diag(profile, "invalid_relation_direction",
                                     "Relation runs against reading order (from is below/right of to).",
                                     {"from": a, "to": b, "axis": axis},
                                     "Swap from/to so relations follow reading order."))
        rm = {"from": a, "to": b, "kind": rel["kind"], "axis": axis, "gap_ratio": gap,
              "center_delta": center_delta, "proximity": name, "target": [lo, hi]}
        rel_metrics.append(rm)
        related_pairs.add(frozenset((a, b)))
        if gap < -eps and oa.ink.intersection(ob.ink) > eps * eps:
            diagnostics.append(Diagnostic("error", "object_overlap",
                                          "Two related blocks overlap.",
                                          rm | {"overlap_depth": -gap},
                                          "Reduce block heights or split the slide; blocks must not collide."))
        elif gap > hi and axis == "horizontal":
            diagnostics.append(_diag(profile, "wide_gutter",
                                     "Side-by-side columns are separated by an unusually wide gutter.",
                                     rm, "Reduce the gutter so the columns read as one row."))
        elif gap > hi:
            diagnostics.append(_diag(profile, "semantic_pair_split",
                                     "A related pair is separated by more whitespace than its proximity allows.",
                                     rm, "Tighten the mode (compact) or split the two blocks onto separate slides."))
        elif gap < lo and state == "normal":
            # A compressed/tight/overflowing slide squeezes its gaps by
            # design; the fit diagnostic already covers it.
            diagnostics.append(_diag(profile, "crowded_related_pair",
                                     "A related pair is tighter than its proximity allows.",
                                     rm, "Loosen the mode or reduce block height."))
        if center_delta > rules["relation_center_delta_max"]:
            diagnostics.append(_diag(profile, "weak_relation_alignment",
                                     "A related pair has a large centre mismatch across its axis.",
                                     rm | {"max": rules["relation_center_delta_max"]},
                                     "Share a centre line or an edge between related blocks."))
    if rel_metrics:
        metrics["relations"] = rel_metrics

    # ---- per-frame checks: every rendered step must show substance ----
    frame_stats = []
    max_step = max(steps) if steps else 1
    for step in steps or [1]:
        vis = [o for o in objects if o.visible_from <= step]
        step_ink = union_area(b for o in vis for b in o.ink_boxes())
        frame_stats.append({
            "step": step,
            "visible_objects": len(vis),
            "visual_coverage": step_ink,
        })
        if not vis:
            diagnostics.append(_diag(profile, "empty_frame",
                                     "A rendered reveal step shows no objects at all.",
                                     {"step": step}, "Fix the reveal-from order; every step must show content."))
        elif step < max_step and step_ink < rules["step_ink_scale"] * floor:
            diagnostics.append(_diag(profile, "sparse_frame",
                                     "An early reveal step shows almost no content.",
                                     {"step": step, "visual_coverage": step_ink,
                                      "floor": rules["step_ink_scale"] * floor},
                                     "Reveal a substantial block first, or start the reveal at a later step."))
    if len(frame_stats) > 1:
        metrics["frames"] = frame_stats

    # ---- unrelated collisions, checked per rendered step ----
    reported_overlap: set[frozenset[str]] = set()
    for step in steps or [1]:
        vis = [o for o in objects if o.visible_from <= step]
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
                    diagnostics.append(Diagnostic(
                        "error" if profile == "agent" else "warning", "object_overlap",
                        "Two unrelated blocks overlap.",
                        {"a": a.id, "b": b.id,
                         "overlap_share": inter / smaller, "step": step},
                        "Check the slide: unrelated blocks should not collide."))

    # ---- trapped whitespace between unrelated stacked blocks ----
    ordered = sorted(objects, key=lambda o: o.ink.y)
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
        diagnostics.append(_diag(profile, "trapped_whitespace",
                                 "Two unrelated stacked blocks are separated by a large vertical gap.",
                                 {"from": worst_pair[0], "to": worst_pair[1], "gap_ratio": worst_gap},
                                 "If the blocks belong together, mark them as a pair or use a stack/duo component; otherwise reduce the gap."))

    return SlideReport(sid, archetype, _round(metrics), diagnostics)


def structure_report(orphans: list[dict[str, Any]], dup_ids: set[str],
                     profile: str) -> SlideReport | None:
    """Deck-level provenance: orphan frames and duplicate record ids."""
    diagnostics: list[Diagnostic] = []
    for oid in sorted({f["id"] for f in orphans}):
        pages = sorted(f["page"] for f in orphans if f["id"] == oid)
        diagnostics.append(_diag(profile, "orphan_frame",
                                 "A rendered frame does not belong to any layout record.",
                                 {"id": oid, "pages": pages},
                                 "Every frame must join a record; fix the slide id or the exporter."))
    for rid in sorted(dup_ids):
        diagnostics.append(_diag(profile, "duplicate_slide_id",
                                 "Two slides share one telemetry id; frames cannot be attributed.",
                                 {"id": rid}, "Give each slide a unique explicit id."))
    if not diagnostics:
        return None
    return SlideReport("<deck>", "structure", {}, diagnostics)


def coverage_report(records: list[Record], joined_frames: list[dict[str, Any]],
                    pages: list[dict[str, Any]], profile: str = "human",
                    page_count: int | None = None) -> SlideReport:
    """Which content pages carry no layout telemetry at all.

    Covered pages come ONLY from frames that joined a valid record (plus the
    record pages themselves): an orphan frame must not buy coverage."""
    covered: set[int] = set()
    for f in joined_frames:
        covered.add(f["page"])
    for rec in records:
        covered.add(rec.page)
    diagnostics: list[Diagnostic] = []
    manifest_pages: dict[int, str] = {}
    for p in pages:
        page = p.get("page")
        kind = str(p.get("kind", "content"))
        if not isinstance(page, int) or isinstance(page, bool):
            raise TelemetryError(f"page manifest without an integer page: {p!r}")
        if page in manifest_pages:
            diagnostics.append(_diag(profile, "manifest_duplicate",
                                     "Two page manifests land on one physical page.",
                                     {"page": page, "kinds": [manifest_pages[page], kind]},
                                     "One physical page must carry exactly one manifest; fix the deck."))
        manifest_pages[page] = kind
    content_pages = sorted(p for p, k in manifest_pages.items() if k not in EXEMPT_KINDS)
    exempt_pages = sorted(p for p, k in manifest_pages.items() if k in EXEMPT_KINDS)
    missing = [p for p in content_pages if p not in covered]
    metrics = {
        "content_pages": len(content_pages),
        "exempt_pages": len(exempt_pages),
        "covered_pages": len(content_pages) - len(missing),
        "missing_pages": missing,
    }
    if missing:
        diagnostics.append(_diag(profile, "telemetry_gap",
                                 f"{len(missing)} content page(s) carry no layout telemetry.",
                                 {"pages": missing},
                                 "Build these pages with layout components, or mark them as deliberate exceptions."))
    known = max(manifest_pages, default=0)
    if page_count is None:
        diagnostics.append(_diag(profile, "page_count_unknown",
                                 "The physical page count was not provided; trailing bare pages are invisible.",
                                 {"max_manifest_page": known},
                                 "Pass --page-count (or run xwysyy-check, which renders and counts pages)."))
    total = page_count if page_count is not None else known
    unmanifested = [p for p in range(1, total + 1) if p not in manifest_pages]
    if unmanifested:
        metrics["unmanifested_pages"] = unmanifested
        diagnostics.append(_diag(profile, "manifest_gap",
                                 f"{len(unmanifested)} page(s) carry no page manifest at all.",
                                 {"pages": unmanifested},
                                 "Produce every page with an xwysyy slide layout so it declares its kind."))
    return SlideReport("<deck>", "coverage", metrics, diagnostics)


def header_report(headers: list[dict[str, Any]], profile: str = "human") -> SlideReport:
    """Header telemetry: titles that had to shrink, do not fit horizontally,
    or are too tall for the fixed header band."""
    diagnostics = []
    shrunk = []
    for h in headers:
        if str(h.get("schema", "")) != HEADER_SCHEMA:
            raise TelemetryError(f"header schema is {h.get('schema')!r}, expected {HEADER_SCHEMA!r}")
        page = _int(h.get("page"), "header.page")
        scale = _num(h.get("scale"), "header.scale")
        fits = _bool(h.get("fits"), "header.fits")
        fits_v = _bool(h.get("fits_v"), "header.fits_v")
        _num(h.get("height"), "header.height")
        if not fits:
            diagnostics.append(_diag(profile, "header_overflow",
                                     "A slide title does not fit the header even at the minimum scale.",
                                     {"page": page, "scale": scale},
                                     "Shorten the slide title."))
        elif not fits_v:
            diagnostics.append(_diag(profile, "header_overflow",
                                     "A slide title is taller than the header band (wrapped or oversized).",
                                     {"page": page, "height": h.get("height")},
                                     "Keep the title on one line; shorten it."))
        elif scale < 0.999:
            shrunk.append({"page": page, "scale": round(float(scale), 3)})
    if shrunk:
        diagnostics.append(_diag(profile, "header_shrunk",
                                 f"{len(shrunk)} slide title(s) shrank to fit the header.",
                                 {"pages": shrunk}, "Consider shorter titles."))
    return SlideReport("<headers>", "header", {"header_records": len(headers)}, diagnostics)


# ---------------------------------------------------------------------------
# rules
# ---------------------------------------------------------------------------

def _rule_num(value: Any, where: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise TelemetryError(f"rule {where} must be a finite number, got {value!r}")


def _rule_range(value: Any, where: str) -> None:
    if not isinstance(value, list) or len(value) != 2:
        raise TelemetryError(f"rule {where} must be a two-element [lo, hi] list")
    for v in value:
        _rule_num(v, where)
    lo, hi = float(value[0]), float(value[1])
    if lo < 0 or lo > hi:
        raise TelemetryError(f"rule {where} must satisfy 0 <= lo <= hi, got [{lo}, {hi}]")


def _validate_rules(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Leaf-typed validation: scalar rules take finite numbers (bool is not a
    number), table rules take numeric leaves, and proximity ranges take
    two-element [lo, hi] lists.  Unknown keys are rejected."""
    for k, v in override.items():
        if k not in base:
            raise TelemetryError(f"unknown rule {k!r}")
        if k == "proximity_ranges":
            if not isinstance(v, dict):
                raise TelemetryError(f"rule {k!r} must be a table")
            for kk, vv in v.items():
                _rule_range(vv, f"{k}.{kk}")
        elif isinstance(base[k], dict):
            if not isinstance(v, dict):
                raise TelemetryError(f"rule {k!r} must be a table")
            for kk, vv in v.items():
                _rule_num(vv, f"{k}.{kk}")
        else:
            _rule_num(v, k)


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


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------

def _as_json(reports: list[SlideReport]) -> str:
    return json.dumps({
        "schema": "xwysyy-slide-layout-check/v4",
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
        if r.archetype in ("coverage", "header", "structure", "pixels"):
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
                        help="agent escalates content-adequacy findings to errors")
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
        records = [parse_record(rec) for rec in buckets["layout"]]
        frames_by_id, orphans, dup_ids = join_frames(records, buckets["frames"])
        reports = [analyze_slide(rec, rules, frames_by_id.get(rec.id), args.profile)
                   for rec in records]
        structure = structure_report(orphans, dup_ids, args.profile)
        if structure is not None:
            reports.append(structure)
        if buckets["headers"]:
            reports.append(header_report(buckets["headers"], args.profile))
        if buckets["pages"] or records:
            joined = [f for fs in frames_by_id.values() for f in fs]
            reports.append(coverage_report(records, joined, buckets["pages"],
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
