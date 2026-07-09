#!/usr/bin/env python3
"""Diagnose xwysyy slide layout telemetry.

The semantic layout components in ``src/layout.typ`` already guarantee sound
spacing: every block is measured at compile time and whitespace is distributed
by a rhythm rule.  This checker therefore does not try to "fix spacing".  It
reads the exported geometry and reports the content-level decisions a component
cannot make on its own:

  * the slide is too empty (merge it, or enlarge the visual);
  * the slide is too dense (split it, or trim);
  * a grid/compare column holds far more content than its peers;
  * a manually-authored pair is split or crowded or misaligned;
  * content overflowed the body.

Symmetric outer whitespace around a centered group is *not* a defect and is
never flagged; only asymmetric blank, in-pair gaps, density and imbalance are.

Input is the JSON emitted by::

    typst query deck.typ '<xwysyy-slide-layout>' --field value

A hand-written ``{"slides": [...]}`` object is also accepted.  Standard library
only.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


DEFAULT_RULES: dict[str, Any] = {
    # weighted visual centre should stay near the optical centre
    "center_y_min": 0.35,
    "center_y_max": 0.60,
    "clustered_blank_min": 0.30,
    # ink coverage floors/ceilings, per archetype (fraction of body area)
    "ink_floor": {
        "focus": 0.08,
        "duo": 0.15,
        "stack": 0.15,
        "grid": 0.12,
        "compare": 0.12,
        "_default": 0.15,
    },
    "ink_ceiling": 0.80,
    # semantic proximity gap ranges (fraction of body height for vertical pairs,
    # of body width for the horizontal "gutter" between side-by-side columns)
    "proximity_ranges": {
        "tight": [0.01, 0.07],
        "compact": [0.03, 0.12],
        "medium": [0.07, 0.20],
        "loose": [0.16, 0.30],
        "independent": [0.24, 0.46],
        "gutter": [0.02, 0.20],
    },
    "relation_center_delta_max": 0.10,
    "column_variance_max": 0.35,
    # largest vertical gap between two unrelated stacked content blocks
    "internal_gap_max": 0.30,
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
        "text": 1.00,
        "content": 1.00,
        "caption": 0.70,
        "decorative": 0.15,
    },
}

_DECORATIVE = {"decorative", "background"}


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


@dataclass
class Diagnostic:
    severity: str
    type: str
    message: str
    metrics: dict[str, Any]
    fix: str


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


def _num(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise TelemetryError(f"{field} must be numeric, got bool")
    if isinstance(value, (int, float)):
        f = float(value)
        if not math.isfinite(f):
            raise TelemetryError(f"{field} must be finite")
        return f
    if isinstance(value, str):
        try:
            f = float(value)
        except ValueError:
            raise TelemetryError(f"{field} must be numeric, got {value!r}") from None
        if not math.isfinite(f):
            raise TelemetryError(f"{field} must be finite")
        return f
    raise TelemetryError(f"{field} must be numeric, got {type(value).__name__}")


def _bbox(obj: dict[str, Any]) -> BBox:
    if "bbox" in obj:
        b = obj["bbox"]
        if isinstance(b, dict):
            return BBox(_num(b.get("x", 0.0), "bbox.x"), _num(b.get("y", 0.0), "bbox.y"),
                        _num(b.get("w", 0.0), "bbox.w"), _num(b.get("h", 0.0), "bbox.h"))
        if isinstance(b, (list, tuple)) and len(b) >= 4:
            return BBox(_num(b[0], "bbox[0]"), _num(b[1], "bbox[1]"),
                        _num(b[2], "bbox[2]"), _num(b[3], "bbox[3]"))
        raise TelemetryError(f"object {obj.get('id', '?')} has an invalid bbox")
    return BBox(_num(obj.get("x", 0.0), "x"), _num(obj.get("y", 0.0), "y"),
                _num(obj.get("w", 0.0), "w"), _num(obj.get("h", 0.0), "h"))


def _load_json(path: str | None) -> Any:
    if path in (None, "-"):
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _records(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict) and isinstance(raw.get("slides"), list):
        candidates = raw["slides"]
    elif isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, dict) and (raw.get("schema") == "xwysyy-slide-layout/v1" or "objects" in raw):
        candidates = [raw]
    else:
        raise TelemetryError("input must be a Typst query array, a metadata value, or {'slides': [...]}")

    out: list[dict[str, Any]] = []
    for item in candidates:
        value = item.get("value") if isinstance(item, dict) and "value" in item else item
        if isinstance(value, dict) and ("objects" in value or value.get("schema") == "xwysyy-slide-layout/v1"):
            out.append(value)
    return out


def _role_weight(role: str, rules: dict[str, Any]) -> float:
    return float(rules["role_weights"].get(role, 1.0))


def _union(bboxes: Iterable[BBox]) -> BBox | None:
    bboxes = list(bboxes)
    if not bboxes:
        return None
    left = min(b.x for b in bboxes)
    top = min(b.y for b in bboxes)
    right = max(b.right for b in bboxes)
    bottom = max(b.bottom for b in bboxes)
    return BBox(left, top, right - left, bottom - top)


def _proximity_range(relation: dict[str, Any], rules: dict[str, Any]) -> tuple[str, float, float]:
    desired = str(relation.get("desired_proximity", relation.get("desired-proximity", "medium")))
    ranges = rules["proximity_ranges"]
    if desired not in ranges:
        desired = "medium"
    lo, hi = ranges[desired]
    return desired, float(lo), float(hi)


def _relation_gap(a: BBox, b: BBox, axis: str) -> tuple[float, float]:
    if axis == "horizontal":
        if a.right <= b.x:
            gap = b.x - a.right
        elif b.right <= a.x:
            gap = a.x - b.right
        else:
            gap = 0.0
        return gap, abs(a.cy - b.cy)
    if a.bottom <= b.y:
        gap = b.y - a.bottom
    elif b.bottom <= a.y:
        gap = a.y - b.bottom
    else:
        gap = 0.0
    return gap, abs(a.cx - b.cx)


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {k: _round(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_round(v) for v in value]
    return value


def analyze_slide(record: dict[str, Any], rules: dict[str, Any]) -> SlideReport:
    sid = str(record.get("id", "slide"))
    archetype = str(record.get("archetype", "custom"))
    extra = record.get("extra", {}) or {}
    raw_objects = record.get("objects", []) or []
    if not isinstance(raw_objects, list):
        raise TelemetryError(f"slide {sid}: objects must be a list")

    diagnostics: list[Diagnostic] = []
    objects: list[tuple[dict[str, Any], BBox]] = []
    for obj in raw_objects:
        if not isinstance(obj, dict):
            diagnostics.append(Diagnostic("error", "invalid_object", "Object entry is not a dictionary.",
                                          {"object": repr(obj)}, "Emit objects as dicts with id, role, x, y, w, h."))
            continue
        try:
            bb = _bbox(obj)
        except TelemetryError as exc:
            diagnostics.append(Diagnostic("error", "invalid_bbox", str(exc),
                                          {"object_id": obj.get("id", "?")}, "Fix the normalized bbox numbers."))
            continue
        objects.append((obj, bb))
        if bb.w < 0 or bb.h < 0:
            diagnostics.append(Diagnostic("error", "negative_size", "Object has negative size.",
                                          {"object_id": obj.get("id", "?"), "bbox": bb.as_list()},
                                          "Use non-negative normalized width and height."))
        # When the component already set the slide-level overflow flag,
        # content_overflow summarises it; skip the per-object noise.
        if not bool(extra.get("overflow", False)) and (
            bb.x < -0.005 or bb.y < -0.005 or bb.right > 1.02 or bb.bottom > 1.02
        ):
            diagnostics.append(Diagnostic("error", "object_outside_body", "Object bbox exceeds the slide body.",
                                          {"object_id": obj.get("id", "?"), "bbox": bb.as_list()},
                                          "Reduce content or split the slide; the block does not fit."))

    content = [(o, b) for o, b in objects if str(o.get("role", "content")) not in _DECORATIVE]
    content_bbox = _union(b for _, b in content)
    metrics: dict[str, Any] = {"object_count": len(objects), "content_object_count": len(content)}

    if content_bbox is None:
        diagnostics.append(Diagnostic("warning", "empty_slide", "No content objects in telemetry.", {},
                                      "Add at least one non-decorative object."))
        return SlideReport(sid, archetype, metrics, diagnostics)

    # Cap at 1.0: bboxes can overlap or be forced to equal height, so the raw
    # area sum can exceed the body without meaning the slide is truly that full.
    ink = min(sum(b.area for _, b in content), 1.0)
    total_w = 0.0
    wy = 0.0
    for o, b in content:
        w = max(b.area, 0.01) * _role_weight(str(o.get("role", "content")), rules)
        total_w += w
        wy += w * b.cy
    weighted_cy = wy / total_w if total_w else content_bbox.cy
    top_blank = max(content_bbox.y, 0.0)
    bottom_blank = max(1.0 - content_bbox.bottom, 0.0)

    metrics.update({
        "content_bbox": content_bbox.as_list(),
        "ink_ratio": ink,
        "weighted_center_y": weighted_cy,
        "top_blank_ratio": top_blank,
        "bottom_blank_ratio": bottom_blank,
    })

    # ---- overflow (reported by the component) ----
    if bool(extra.get("overflow", False)):
        diagnostics.append(Diagnostic("error", "content_overflow",
                                      "Content is taller than the body; the component had to drop its margins.",
                                      {"free_ratio": extra.get("free_ratio")},
                                      "Split the slide or shorten the text; do not rely on clamping."))

    # ---- density (archetype-aware) ----
    floor = rules["ink_floor"].get(archetype, rules["ink_floor"]["_default"])
    if ink < floor:
        diagnostics.append(Diagnostic("warning", "low_density",
                                      "The slide inks very little of the body.",
                                      {"ink_ratio": ink, "floor": floor},
                                      "Enlarge the main visual, add explanation, merge with a neighbour, or accept a deliberately minimal slide."))
    elif ink > rules["ink_ceiling"] and archetype not in {"grid", "compare", "sidebar"}:
        # grid/compare/sidebar force blocks to equal height, so their ink is
        # dominated by boxed whitespace, not real content; density there is
        # governed by column_imbalance and overflow instead.
        diagnostics.append(Diagnostic("warning", "over_dense",
                                      "The slide inks most of the body.",
                                      {"ink_ratio": ink, "ceiling": rules["ink_ceiling"]},
                                      "Split the slide or move secondary content elsewhere."))

    # ---- asymmetric outer whitespace (clustering) ----
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

    # ---- column imbalance (grid / compare) ----
    variance = extra.get("natural_height_variance")
    if isinstance(variance, (int, float)) and float(variance) > rules["column_variance_max"]:
        diagnostics.append(Diagnostic("warning", "column_imbalance",
                                      "One column holds far more content than its peers.",
                                      {"natural_height_variance": float(variance), "max": rules["column_variance_max"]},
                                      "Rebalance text across columns or move the long column to its own slide."))

    # ---- semantic relations ----
    by_id = {str(o.get("id", i)): b for i, (o, b) in enumerate(objects)}
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
        gap, center_delta = _relation_gap(by_id[a], by_id[b], axis)
        name, lo, hi = _proximity_range(rel, rules)
        rm = {"from": a, "to": b, "axis": axis, "gap_ratio": gap,
              "center_delta": center_delta, "proximity": name, "target": [lo, hi]}
        rel_metrics.append(rm)
        related_pairs.add(frozenset((a, b)))
        if gap > hi and axis == "horizontal":
            # A wide gutter between side-by-side columns is a layout nudge, not a
            # broken semantic pair; the component accepts any gutter value.
            diagnostics.append(Diagnostic("warning", "wide_gutter",
                                          "Side-by-side columns are separated by an unusually wide gutter.",
                                          rm, "Reduce the gutter so the columns read as one row."))
        elif gap > hi:
            diagnostics.append(Diagnostic("error", "semantic_pair_split",
                                          "A related pair is separated by more whitespace than its proximity allows.",
                                          rm, "Tighten the mode (compact) or split the two blocks onto separate slides."))
        elif gap < lo:
            diagnostics.append(Diagnostic("warning", "crowded_related_pair",
                                          "A related pair is tighter than its proximity allows.",
                                          rm, "Loosen the mode or reduce block height."))
        if axis == "vertical" and center_delta > rules["relation_center_delta_max"]:
            diagnostics.append(Diagnostic("warning", "weak_relation_alignment",
                                          "A vertical pair has a large horizontal centre mismatch.",
                                          rm | {"max": rules["relation_center_delta_max"]},
                                          "Share a centre line or an edge between related blocks."))
    if rel_metrics:
        metrics["relations"] = rel_metrics

    # Trapped whitespace: a large vertical gap between two stacked content blocks
    # that carry no declared relation (the "figure and text drifted apart" case
    # when the author never marked them as a pair). Components declare their
    # pairs, so this only fires on hand-authored / mixed telemetry.
    ordered = sorted(content, key=lambda ob: ob[1].y)
    worst_gap = 0.0
    worst_pair: tuple[str, str] | None = None
    for i in range(len(ordered) - 1):
        (oa, ba), (ob, bb) = ordered[i], ordered[i + 1]
        if ba.bottom <= bb.y:
            ida, idb = str(oa.get("id", i)), str(ob.get("id", i + 1))
            if frozenset((ida, idb)) in related_pairs:
                continue
            gap = bb.y - ba.bottom
            if gap > worst_gap:
                worst_gap, worst_pair = gap, (ida, idb)
    if worst_pair is not None and worst_gap > rules["internal_gap_max"]:
        diagnostics.append(Diagnostic("warning", "trapped_whitespace",
                                      "Two unrelated stacked blocks are separated by a large vertical gap.",
                                      {"from": worst_pair[0], "to": worst_pair[1], "gap_ratio": worst_gap},
                                      "If the blocks belong together, mark them as a pair or use a stack/duo component; otherwise reduce the gap."))

    return SlideReport(sid, archetype, _round(metrics), diagnostics)


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
        "schema": "xwysyy-slide-layout-check/v1",
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
            lines.append(f"    fix: {d.fix}")
        m = r.metrics
        if "ink_ratio" in m:
            lines.append(f"  metrics: ink={m['ink_ratio']} center_y={m['weighted_center_y']} "
                         f"top_blank={m['top_blank_ratio']} bottom_blank={m['bottom_blank_ratio']}")
    return "\n".join(lines) if lines else "no telemetry records found"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", default="-", help="JSON file or '-' for stdin")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--rules", default=None, help="optional JSON/TOML rule overrides")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on any warning or error")
    parser.add_argument("--error-only", action="store_true", help="exit non-zero only on errors")
    args = parser.parse_args(argv)

    try:
        rules = _load_rules(args.rules)
        records = _records(_load_json(args.input))
        reports = [analyze_slide(rec, rules) for rec in records]
    except (OSError, json.JSONDecodeError, TelemetryError) as exc:
        print(f"slide-check: {exc}", file=sys.stderr)
        return 2

    print(_as_json(reports) if args.format == "json" else _as_text(reports))

    if args.error_only:
        return 1 if any(r.has_error for r in reports) else 0
    if args.strict:
        return 1 if any(r.has_problem for r in reports) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
