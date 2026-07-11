"""Tests for scripts/slide-check.py (telemetry schema v4) and scripts/xwysyy-check.

Unit tests build synthetic v4 records; integration tests (skipped when typst
is not on PATH) compile the demo and the fixtures and assert the real
end-to-end behaviour: good pages pass, deliberate mistakes are flagged,
panic fixtures fail to compile, the adversarial fixtures (fake-greens found
in external review) fail the checker, and the pixel stage catches what
geometry cannot.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
CHECKER = SCRIPTS / "slide-check.py"
XCHECK = SCRIPTS / "xwysyy-check"
FIXTURES = REPO / "tests" / "fixtures"
HAS_TYPST = shutil.which("typst") is not None


def _load_checker():
    loader = importlib.machinery.SourceFileLoader("slide_check_under_test", str(CHECKER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


sc = _load_checker()

BODY = {"x": 15.59, "y": 67.82, "w": 810.71, "h": 383.92}
PAGE_SIZE = {"w": 841.89, "h": 473.56}


def _box(x, y, w, h):
    return {"x": x, "y": y, "w": w, "h": h}


def _obj(oid, kind="card", role="explanation", frame=(0.09, 0.07, 0.82, 0.7),
         payload=None, painted=True, sizing=("natural", "natural"),
         source="measured", overflow_x=False, visible_from=1, preferred_h=None):
    fx, fy, fw, fh = frame
    if payload is None:
        payload = (fx + 0.05, fy + 0.05, fw - 0.1, fh - 0.1)
    return {
        "id": oid, "object_kind": kind, "semantic_role": role, "group": "g",
        "frame": _box(*frame),
        "preferred": {"w": fw, "h": preferred_h if preferred_h is not None else fh},
        "payload": _box(*payload),
        "paint": _box(*frame) if painted else None,
        "paint_fill": "#dde8f0" if painted else None,
        "payload_source": source,
        "overflow_x": overflow_x,
        "sizing": {"x": sizing[0], "y": sizing[1]},
        "visible_from": visible_from,
    }


def _fit(state="normal", required=0.5, gap_ratio=None, margin_deficit=0.0, body_overflow=0.0):
    if gap_ratio is None:
        gap_ratio = 0.6 if state == "compressed" else 1.0
    return {"state": state, "required_height_ratio": required, "gap_ratio": gap_ratio,
            "margin_deficit_ratio": margin_deficit, "body_overflow_ratio": body_overflow}


def _rec(rid="s", archetype="stack", objects=None, relations=None, fit=None,
         extra=None, page=2, frame_count=1):
    return {
        "schema": sc.SCHEMA, "id": rid, "archetype": archetype,
        "layout_engine": "column", "page": page, "frame_count": frame_count,
        "coordinate_system": "normalized-slide-body",
        "objects": objects if objects is not None else [_obj(f"{rid}:0")],
        "relations": relations or [],
        "fit": fit or _fit(),
        "extra": extra or {},
    }


def _frame(fid="s", step=1, steps=1, page=2, handout=False):
    return {"schema": sc.FRAME_SCHEMA, "id": fid, "step": step, "steps": steps,
            "page": page, "handout": handout,
            "body": dict(BODY), "page_size": dict(PAGE_SIZE)}


def _frames_for(record):
    """A valid frame set for a record: steps 1..N on consecutive pages ending
    at the record page."""
    n = record["frame_count"]
    return [_frame(record["id"], step=s, steps=n, page=record["page"] - n + s)
            for s in range(1, n + 1)]


def _diag_types(report):
    return [d.type for d in report.diagnostics]


def _process_output(proc):
    return f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


def _analyze(record, frames=None, profile="human", rules=None):
    rec = sc.parse_record(record)
    raw = _frames_for(record) if frames is None else frames
    parsed = [sc.parse_frame(f) for f in raw]
    return sc.analyze_slide(rec, rules or sc._load_rules(None), parsed, profile)


class UnionAreaTests(unittest.TestCase):
    def test_disjoint(self):
        a, b = sc.BBox(0, 0, 0.2, 0.2), sc.BBox(0.5, 0.5, 0.2, 0.2)
        self.assertAlmostEqual(sc.union_area([a, b]), 0.08)

    def test_nested_and_overlap(self):
        outer, inner = sc.BBox(0, 0, 0.5, 0.5), sc.BBox(0.1, 0.1, 0.2, 0.2)
        self.assertAlmostEqual(sc.union_area([outer, inner]), 0.25)
        c, d = sc.BBox(0, 0, 0.4, 0.4), sc.BBox(0.2, 0.2, 0.4, 0.4)
        self.assertAlmostEqual(sc.union_area([c, d]), 0.16 + 0.16 - 0.04)

    def test_empty(self):
        self.assertEqual(sc.union_area([]), 0.0)


class FailClosedParsingTests(unittest.TestCase):
    """Schema violations abort with TelemetryError (exit 2), never defaults."""

    def _bad(self, record):
        with self.assertRaises(sc.TelemetryError):
            sc.parse_record(record)

    def test_missing_bbox_key(self):
        rec = _rec()
        del rec["objects"][0]["frame"]["h"]
        self._bad(rec)

    def test_missing_preferred(self):
        rec = _rec()
        del rec["objects"][0]["preferred"]
        self._bad(rec)

    def test_paint_must_be_dict_or_null(self):
        rec = _rec()
        rec["objects"][0]["paint"] = "false"
        self._bad(rec)

    def test_negative_paint_size(self):
        rec = _rec()
        rec["objects"][0]["paint"] = _box(0.1, 0.1, -0.5, 0.4)
        self._bad(rec)

    def test_paint_without_fill(self):
        rec = _rec()
        rec["objects"][0]["paint_fill"] = None
        self._bad(rec)

    def test_sizing_required(self):
        rec = _rec()
        rec["objects"][0]["sizing"] = "natural"
        self._bad(rec)

    def test_visible_from_must_be_positive_int(self):
        rec = _rec()
        rec["objects"][0]["visible_from"] = 0
        self._bad(rec)

    def test_visible_from_bounded_by_frame_count(self):
        rec = _rec(frame_count=2, page=3)
        rec["objects"][0]["visible_from"] = 3
        self._bad(rec)

    def test_bool_is_not_a_number(self):
        rec = _rec()
        rec["objects"][0]["frame"]["w"] = True
        self._bad(rec)

    def test_non_finite_rejected(self):
        rec = _rec()
        rec["objects"][0]["frame"]["w"] = float("nan")
        self._bad(rec)

    def test_old_schema_rejected(self):
        rec = _rec()
        rec["schema"] = "xwysyy-slide-layout/v3"
        self._bad(rec)

    def test_unknown_object_kind_rejected(self):
        rec = _rec(objects=[_obj("s:0", kind="main-visual")])
        self._bad(rec)

    def test_unknown_role_rejected(self):
        rec = _rec(objects=[_obj("s:0", role="decorative")])
        self._bad(rec)

    def test_unknown_payload_source_rejected(self):
        rec = _rec(objects=[_obj("s:0", source="guessed")])
        self._bad(rec)

    def test_duplicate_object_id_rejected(self):
        rec = _rec(objects=[_obj("s:0"), _obj("s:0", frame=(0.09, 0.8, 0.8, 0.15))])
        self._bad(rec)

    def test_unknown_fit_state_rejected(self):
        rec = _rec()
        rec["fit"]["state"] = "squished"
        self._bad(rec)

    def test_relation_kind_closed(self):
        rec = _rec(objects=[_obj("s:0"), _obj("s:1", frame=(0.09, 0.8, 0.8, 0.15))],
                   relations=[{"from": "s:0", "to": "s:1", "kind": "friends",
                               "axis": "vertical", "desired_proximity": "medium"}])
        self._bad(rec)

    def test_relations_must_be_list(self):
        rec = _rec()
        rec["relations"] = "none"
        self._bad(rec)

    def test_coordinate_system_pinned(self):
        rec = _rec()
        rec["coordinate_system"] = "page"
        self._bad(rec)

    def test_frame_schema_v1_rejected(self):
        with self.assertRaises(sc.TelemetryError):
            sc.parse_frame({"schema": "xwysyy-frame/v1", "id": "s", "step": 1,
                            "steps": 1, "page": 2})


class FitStateTests(unittest.TestCase):
    def test_clean_slide_passes(self):
        report = _analyze(_rec())
        self.assertEqual(report.diagnostics, [])

    def test_overflow_is_error_and_needs_positive_ratio(self):
        report = _analyze(_rec(fit=_fit("overflow", required=1.2, body_overflow=0.12)))
        self.assertIn("content_overflow", _diag_types(report))
        self.assertNotIn("invalid_fit_state", _diag_types(report))
        report = _analyze(_rec(fit=_fit("overflow", required=1.1, body_overflow=0.0)))
        self.assertIn("invalid_fit_state", _diag_types(report))

    def test_tight_and_compressed(self):
        report = _analyze(_rec(fit=_fit("tight", required=0.9, margin_deficit=0.06)))
        self.assertIn("margin_squeeze", _diag_types(report))
        report = _analyze(_rec(fit=_fit("compressed", required=0.88, gap_ratio=0.4)))
        self.assertIn("gap_compressed", _diag_types(report))
        self.assertFalse(report.has_error)

    def test_state_number_contradictions(self):
        # normal with a squeezed gap ratio
        report = _analyze(_rec(fit=_fit("normal", gap_ratio=0.5)))
        self.assertIn("invalid_fit_state", _diag_types(report))
        # compressed with an uncompressed gap ratio
        report = _analyze(_rec(fit=_fit("compressed", required=0.9, gap_ratio=1.0)))
        self.assertIn("invalid_fit_state", _diag_types(report))
        # tight without a margin deficit
        report = _analyze(_rec(fit=_fit("tight", required=0.9, margin_deficit=0.0)))
        self.assertIn("invalid_fit_state", _diag_types(report))
        # normal with a hidden overflow
        report = _analyze(_rec(fit=_fit("normal", body_overflow=0.1)))
        self.assertIn("invalid_fit_state", _diag_types(report))


class DensityTests(unittest.TestCase):
    def test_low_density_by_payload_even_when_painted(self):
        # The review's fake-green case: big painted cards, almost no content.
        objects = [
            _obj("s:0", frame=(0.05, 0.1, 0.4, 0.6), payload=(0.06, 0.35, 0.05, 0.02)),
            _obj("s:1", frame=(0.55, 0.1, 0.4, 0.6), payload=(0.56, 0.35, 0.05, 0.02)),
        ]
        report = _analyze(_rec(archetype="grid", objects=objects))
        self.assertIn("low_density", _diag_types(report))
        self.assertGreater(report.metrics["visual_coverage"], 0.4)
        self.assertLess(report.metrics["payload_density"], 0.01)

    def test_over_dense(self):
        objects = [_obj("s:0", frame=(0.02, 0.02, 0.96, 0.96),
                        payload=(0.03, 0.03, 0.94, 0.94))]
        report = _analyze(_rec(objects=objects))
        self.assertIn("over_dense", _diag_types(report))

    def test_narrow_payload_is_not_full_coverage(self):
        objects = [_obj("s:0", kind="visual", role="main_visual", painted=False,
                        frame=(0.09, 0.07, 0.82, 0.84),
                        payload=(0.45, 0.07, 0.10, 0.84))]
        report = _analyze(_rec(archetype="focus", objects=objects))
        self.assertLess(report.metrics["visual_coverage"], 0.12)

    def test_declared_payload_is_not_density_evidence(self):
        # A declared (stretch) payload fills its frame but must not satisfy
        # the payload floor; with no measured object the floor is skipped and
        # the pixel stage owns the verdict.
        objects = [_obj("s:0", kind="visual", role="main_visual", painted=False,
                        frame=(0.09, 0.07, 0.82, 0.7),
                        payload=(0.09, 0.07, 0.82, 0.7),
                        sizing=("stretch", "stretch"), source="declared")]
        report = _analyze(_rec(archetype="duo", objects=objects))
        self.assertEqual(report.metrics["payload_density"], 0.0)
        self.assertGreater(report.metrics["declared_payload"], 0.5)
        self.assertNotIn("low_density", _diag_types(report))
        self.assertNotIn("empty_shell", _diag_types(report))


class ShellTests(unittest.TestCase):
    def test_empty_shell_is_error(self):
        objects = [_obj("s:0", payload=(0.1, 0.1, 0.001, 0.001))]
        report = _analyze(_rec(objects=objects))
        self.assertIn("empty_shell", _diag_types(report))
        self.assertTrue(report.has_error)

    def test_underfilled_card(self):
        objects = [_obj("s:0", frame=(0.09, 0.1, 0.45, 0.6), payload=(0.1, 0.35, 0.06, 0.03)),
                   _obj("s:1", frame=(0.56, 0.1, 0.4, 0.6), payload=(0.57, 0.12, 0.35, 0.5))]
        report = _analyze(_rec(archetype="grid", objects=objects))
        self.assertIn("underfilled_card", _diag_types(report))

    def test_hollow_frame_both_axes(self):
        tall = _obj("s:0", kind="visual", role="main_visual", painted=False,
                    frame=(0.09, 0.07, 0.82, 0.6), payload=(0.09, 0.27, 0.82, 0.2))
        report = _analyze(_rec(objects=[tall]))
        self.assertIn("hollow_frame", _diag_types(report))
        narrow = _obj("s:0", kind="visual", role="main_visual", painted=False,
                      frame=(0.09, 0.07, 0.82, 0.6), payload=(0.35, 0.07, 0.3, 0.6))
        report = _analyze(_rec(objects=[narrow]))
        self.assertIn("hollow_frame", _diag_types(report))


class EscapeTests(unittest.TestCase):
    def test_horizontal_body_escape_checked_in_every_state(self):
        objects = [_obj("s:0", frame=(0.5, 0.1, 0.6, 0.4), payload=(0.52, 0.12, 0.56, 0.36))]
        report = _analyze(_rec(objects=objects, fit=_fit("tight", margin_deficit=0.05)))
        self.assertIn("object_outside_body", _diag_types(report))

    def test_vertical_escape_suppressed_when_fit_reports_it(self):
        objects = [_obj("s:0", frame=(0.09, 0.5, 0.8, 0.6), payload=(0.1, 0.52, 0.7, 0.56))]
        report = _analyze(_rec(objects=objects, fit=_fit("tight", margin_deficit=0.05)))
        self.assertNotIn("object_outside_body", _diag_types(report))
        report = _analyze(_rec(objects=objects))
        self.assertIn("object_outside_body", _diag_types(report))

    def test_overflow_x_is_error(self):
        objects = [_obj("s:0", overflow_x=True)]
        report = _analyze(_rec(objects=objects))
        self.assertIn("object_escapes_frame", _diag_types(report))
        self.assertTrue(report.has_error)

    def test_payload_outside_own_frame_horizontally(self):
        objects = [_obj("s:0", frame=(0.09, 0.1, 0.5, 0.4), payload=(0.05, 0.12, 0.6, 0.3))]
        report = _analyze(_rec(objects=objects))
        self.assertIn("object_escapes_frame", _diag_types(report))

    def test_payload_below_frame_only_allowed_when_fit_degrades(self):
        objects = [_obj("s:0", frame=(0.09, 0.1, 0.8, 0.3), payload=(0.1, 0.11, 0.7, 0.5))]
        report = _analyze(_rec(objects=objects))
        self.assertIn("object_escapes_frame", _diag_types(report))
        report = _analyze(_rec(objects=objects, fit=_fit("tight", margin_deficit=0.05)))
        self.assertNotIn("object_escapes_frame", _diag_types(report))


class RelationTests(unittest.TestCase):
    def _pair(self, a_frame, b_frame, axis="vertical", proximity="medium"):
        objects = [
            _obj("s:a", frame=a_frame),
            _obj("s:b", frame=b_frame),
        ]
        relations = [{"from": "s:a", "to": "s:b", "kind": "supports",
                      "axis": axis, "desired_proximity": proximity}]
        return _rec(objects=objects, relations=relations)

    def test_good_gap_passes(self):
        rec = self._pair((0.09, 0.07, 0.82, 0.4), (0.13, 0.60, 0.74, 0.25))
        self.assertEqual(_diag_types(_analyze(rec)), [])

    def test_pair_split_is_error(self):
        rec = self._pair((0.09, 0.05, 0.82, 0.2), (0.13, 0.72, 0.74, 0.2))
        self.assertIn("semantic_pair_split", _diag_types(_analyze(rec)))

    def test_overlap_needs_2d_intersection(self):
        rec = self._pair((0.05, 0.1, 0.3, 0.4), (0.6, 0.35, 0.3, 0.4))
        self.assertNotIn("object_overlap", _diag_types(_analyze(rec)))
        rec = self._pair((0.09, 0.1, 0.8, 0.4), (0.09, 0.35, 0.8, 0.4))
        self.assertIn("object_overlap", _diag_types(_analyze(rec)))

    def test_reversed_direction_warns(self):
        rec = self._pair((0.13, 0.60, 0.74, 0.25), (0.09, 0.07, 0.82, 0.4))
        self.assertIn("invalid_relation_direction", _diag_types(_analyze(rec)))

    def test_crowded_suppressed_when_not_normal(self):
        rec = self._pair((0.09, 0.07, 0.82, 0.4), (0.13, 0.48, 0.74, 0.25))
        self.assertIn("crowded_related_pair", _diag_types(_analyze(rec)))
        rec["fit"] = _fit("compressed", required=0.9, gap_ratio=0.3)
        self.assertNotIn("crowded_related_pair", _diag_types(_analyze(rec)))

    def test_wide_gutter_and_alignment(self):
        rec = self._pair((0.0, 0.2, 0.3, 0.5), (0.65, 0.2, 0.3, 0.5),
                         axis="horizontal", proximity="gutter")
        self.assertIn("wide_gutter", _diag_types(_analyze(rec)))
        rec = self._pair((0.0, 0.1, 0.45, 0.3), (0.5, 0.45, 0.45, 0.3),
                         axis="horizontal", proximity="gutter")
        self.assertIn("weak_relation_alignment", _diag_types(_analyze(rec)))

    def test_missing_target_is_error(self):
        rec = _rec(relations=[{"from": "s:0", "to": "s:ghost", "kind": "supports",
                               "axis": "vertical", "desired_proximity": "medium"}])
        report = _analyze(rec)
        self.assertIn("missing_relation_target", _diag_types(report))
        self.assertTrue(report.has_error)


class ColumnImbalanceTests(unittest.TestCase):
    def _grid(self, pref_hs):
        objects = []
        n = len(pref_hs)
        for i, ph in enumerate(pref_hs):
            x = 0.02 + i * (0.96 / n)
            objects.append(_obj(f"s:{i}", frame=(x, 0.2, 0.9 / n, 0.6),
                                payload=(x + 0.02, 0.22, 0.9 / n - 0.04, max(ph - 0.05, 0.05)),
                                preferred_h=ph))
        return _rec(archetype="grid", objects=objects)

    def test_imbalance_flagged_without_extra_hint(self):
        # v4 gates on the archetype, not on an optional extra key.
        report = _analyze(self._grid([0.08, 0.62, 0.10]))
        self.assertIn("column_imbalance", _diag_types(report))

    def test_small_absolute_spread_passes(self):
        report = _analyze(self._grid([0.04, 0.10, 0.05]))
        self.assertNotIn("column_imbalance", _diag_types(report))


class FrameMachineTests(unittest.TestCase):
    def test_empty_frame_is_error(self):
        objects = [_obj("s:0", visible_from=2),
                   _obj("s:1", frame=(0.09, 0.8, 0.8, 0.15), visible_from=2)]
        report = _analyze(_rec(objects=objects, page=3, frame_count=2))
        self.assertIn("empty_frame", _diag_types(report))
        self.assertTrue(report.has_error)

    def test_sparse_first_frame(self):
        objects = [_obj("s:0", frame=(0.09, 0.07, 0.1, 0.05), payload=(0.1, 0.08, 0.08, 0.03)),
                   _obj("s:1", frame=(0.09, 0.2, 0.8, 0.6), visible_from=2)]
        report = _analyze(_rec(objects=objects, page=3, frame_count=2))
        self.assertIn("sparse_frame", _diag_types(report))
        report = _analyze(_rec(objects=objects, page=3, frame_count=2), profile="agent")
        sparse = [d for d in report.diagnostics if d.type == "sparse_frame"]
        self.assertEqual(sparse[0].severity, "error")

    def test_missing_step_is_integrity_error(self):
        frames = [_frame("s", step=2, steps=2, page=3)]
        report = _analyze(_rec(page=3, frame_count=2), frames=frames)
        self.assertIn("frame_integrity", _diag_types(report))

    def test_no_frames_is_integrity_error(self):
        report = _analyze(_rec(), frames=[])
        self.assertIn("frame_integrity", _diag_types(report))

    def test_steps_field_must_match_frame_count(self):
        frames = [_frame("s", step=1, steps=3, page=2)]
        report = _analyze(_rec(frame_count=1), frames=frames)
        self.assertIn("frame_integrity", _diag_types(report))

    def test_duplicate_step_is_integrity_error(self):
        frames = [_frame("s", step=1, steps=2, page=2),
                  _frame("s", step=1, steps=2, page=3)]
        report = _analyze(_rec(page=3, frame_count=2), frames=frames)
        self.assertIn("frame_integrity", _diag_types(report))

    def test_nonconsecutive_pages_flagged(self):
        frames = [_frame("s", step=1, steps=2, page=2),
                  _frame("s", step=2, steps=2, page=5)]
        report = _analyze(_rec(page=5, frame_count=2), frames=frames)
        self.assertIn("frame_integrity", _diag_types(report))

    def test_record_page_must_be_final_frame_page(self):
        frames = [_frame("s", step=1, steps=1, page=4)]
        report = _analyze(_rec(page=2), frames=frames)
        self.assertIn("frame_integrity", _diag_types(report))

    def test_handout_final_frame_only(self):
        frames = [_frame("s", step=2, steps=2, page=3, handout=True)]
        report = _analyze(_rec(page=3, frame_count=2), frames=frames)
        self.assertNotIn("frame_integrity", _diag_types(report))
        frames = [_frame("s", step=1, steps=2, page=3, handout=True)]
        report = _analyze(_rec(page=3, frame_count=2), frames=frames)
        self.assertIn("frame_integrity", _diag_types(report))

    def test_unrelated_overlap_checked_per_step(self):
        objects = [
            _obj("s:0", frame=(0.09, 0.1, 0.8, 0.4)),
            _obj("s:1", frame=(0.09, 0.3, 0.8, 0.4), visible_from=2),
        ]
        report = _analyze(_rec(objects=objects, page=3, frame_count=2))
        self.assertIn("object_overlap", _diag_types(report))
        agent = _analyze(_rec(objects=objects, page=3, frame_count=2), profile="agent")
        overlap = [d for d in agent.diagnostics if d.type == "object_overlap"]
        self.assertEqual(overlap[0].severity, "error")


class StructureTests(unittest.TestCase):
    def test_orphan_frame_is_error(self):
        records = [sc.parse_record(_rec(rid="a"))]
        by_id, orphans, dups = sc.join_frames(
            records, [_frame("a"), _frame("ghost", page=5)])
        self.assertEqual(sorted(by_id), ["a"])
        report = sc.structure_report(orphans, dups, "human")
        self.assertIsNotNone(report)
        self.assertIn("orphan_frame", _diag_types(report))
        self.assertTrue(report.has_error)

    def test_duplicate_record_id_is_error(self):
        records = [sc.parse_record(_rec(rid="a")),
                   sc.parse_record(_rec(rid="a", page=4))]
        _, orphans, dups = sc.join_frames(records, [_frame("a")])
        report = sc.structure_report(orphans, dups, "human")
        self.assertIsNotNone(report)
        self.assertIn("duplicate_slide_id", _diag_types(report))

    def test_clean_join_reports_nothing(self):
        records = [sc.parse_record(_rec(rid="a"))]
        _, orphans, dups = sc.join_frames(records, [_frame("a")])
        self.assertIsNone(sc.structure_report(orphans, dups, "human"))


class TuningContractTests(unittest.TestCase):
    def test_tuning_used_severity_by_profile(self):
        rec = _rec(extra={"tuned": True})
        report = _analyze(rec)
        diag = [d for d in report.diagnostics if d.type == "tuning_used"]
        self.assertEqual(diag[0].severity, "warning")
        report = _analyze(rec, profile="agent")
        diag = [d for d in report.diagnostics if d.type == "tuning_used"]
        self.assertEqual(diag[0].severity, "error")


class CoverageTests(unittest.TestCase):
    def _pages(self, kinds):
        return [{"schema": sc.PAGE_SCHEMA, "kind": k, "page": i + 1} for i, k in enumerate(kinds)]

    def _cov(self, records, frames, pages, **kw):
        parsed_records = [sc.parse_record(r) for r in records]
        parsed_frames = [sc.parse_frame(f) for f in frames]
        return sc.coverage_report(parsed_records, parsed_frames, pages, **kw)

    def test_frames_drive_coverage_not_ranges(self):
        # Handout: the record sits on page 3 with frame_count 2, but only one
        # physical frame exists.  Page 2 (hand-written) must stay uncovered.
        records = [_rec(rid="rev", page=3, frame_count=2)]
        frames = [_frame("rev", step=2, steps=2, page=3, handout=True)]
        pages = self._pages(["section", "content", "content"])
        report = self._cov(records, frames, pages, page_count=3)
        self.assertEqual(report.metrics["missing_pages"], [2])
        self.assertIn("telemetry_gap", _diag_types(report))

    def test_multi_frame_pages_covered(self):
        records = [_rec(rid="rev", page=4, frame_count=2)]
        frames = [_frame("rev", step=s, steps=2, page=2 + s) for s in (1, 2)]
        pages = self._pages(["section", "content", "content", "content"])
        report = self._cov(records, frames, pages, page_count=4)
        self.assertEqual(report.metrics["missing_pages"], [2])

    def test_orphan_frames_do_not_buy_coverage(self):
        # An orphan frame's page must stay uncovered: coverage receives only
        # joined frames.
        records = [_rec(rid="a", page=2)]
        pages = self._pages(["content", "content"])
        parsed = [sc.parse_record(r) for r in records]
        _, orphans, _ = sc.join_frames(parsed, [_frame("ghost", page=1)])
        self.assertEqual(len(orphans), 1)
        report = sc.coverage_report(parsed, [], pages, page_count=2)
        self.assertEqual(report.metrics["missing_pages"], [1])

    def test_exempt_kinds(self):
        records = [_rec(page=2)]
        pages = self._pages(["title", "content", "image", "end"])
        report = self._cov(records, [], pages, page_count=4)
        self.assertEqual(report.metrics["missing_pages"], [])
        self.assertEqual(report.metrics["exempt_pages"], 3)

    def test_manifest_gap_with_page_count(self):
        records = [_rec(page=2)]
        pages = self._pages(["title", "content"])
        report = self._cov(records, [], pages, page_count=4)
        self.assertIn("manifest_gap", _diag_types(report))
        self.assertEqual(report.metrics["unmanifested_pages"], [3, 4])

    def test_page_count_unknown_flagged(self):
        records = [_rec(page=2)]
        pages = self._pages(["content", "content"])
        report = self._cov(records, [], pages)
        self.assertIn("page_count_unknown", _diag_types(report))
        report = self._cov(records, [], pages, profile="agent")
        self.assertTrue(report.has_error)

    def test_duplicate_manifest_is_error(self):
        records = [_rec(page=1)]
        pages = [{"schema": sc.PAGE_SCHEMA, "kind": "content", "page": 1},
                 {"schema": sc.PAGE_SCHEMA, "kind": "outline", "page": 1}]
        report = self._cov(records, [], pages, page_count=1)
        self.assertIn("manifest_duplicate", _diag_types(report))
        self.assertTrue(report.has_error)

    def test_agent_profile_escalates(self):
        records = [_rec(page=2)]
        pages = self._pages(["content", "content"])
        report = self._cov(records, [], pages, profile="agent", page_count=2)
        self.assertTrue(report.has_error)


class HeaderTests(unittest.TestCase):
    def _header(self, page, scale=1.0, fits=True, fits_v=True, height=12.0):
        return {"schema": sc.HEADER_SCHEMA, "page": page, "scale": scale,
                "fits": fits, "fits_v": fits_v, "height": height}

    def test_shrunk_and_overflow(self):
        headers = [
            self._header(2),
            self._header(3, scale=0.82),
            self._header(4, scale=0.65, fits=False),
        ]
        report = sc.header_report(headers)
        types = _diag_types(report)
        self.assertIn("header_shrunk", types)
        self.assertIn("header_overflow", types)
        self.assertTrue(report.has_error)

    def test_vertical_overflow(self):
        report = sc.header_report([self._header(2, fits_v=False, height=40.0)])
        self.assertIn("header_overflow", _diag_types(report))
        self.assertTrue(report.has_error)


class RulesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = pathlib.Path(temporary.name)

    def _rules(self, payload):
        path = self.tmp / "rules.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_unknown_rule_rejected(self):
        with self.assertRaises(sc.TelemetryError):
            sc._load_rules(self._rules({"ink_flor": {"duo": 0.1}}))

    def test_valid_override_merges(self):
        rules = sc._load_rules(self._rules({"ink_floor": {"duo": 0.05}}))
        self.assertEqual(rules["ink_floor"]["duo"], 0.05)
        self.assertEqual(rules["ink_floor"]["grid"], sc.DEFAULT_RULES["ink_floor"]["grid"])

    def test_list_leaf_rejected(self):
        # The review's crash case: a list where a number is expected must be
        # a clean rule error, not a TypeError traceback.
        with self.assertRaises(sc.TelemetryError):
            sc._load_rules(self._rules({"ink_floor": {"duo": [1, 2]}}))

    def test_bool_leaf_rejected(self):
        with self.assertRaises(sc.TelemetryError):
            sc._load_rules(self._rules({"ink_floor": {"duo": True}}))

    def test_reversed_range_rejected(self):
        with self.assertRaises(sc.TelemetryError):
            sc._load_rules(self._rules({"proximity_ranges": {"tight": [0.5, 0.1]}}))

    def test_range_length_enforced(self):
        with self.assertRaises(sc.TelemetryError):
            sc._load_rules(self._rules({"proximity_ranges": {"tight": [0.1]}}))

    def test_valid_range_merges(self):
        rules = sc._load_rules(self._rules({"proximity_ranges": {"tight": [0.02, 0.09]}}))
        self.assertEqual(rules["proximity_ranges"]["tight"], [0.02, 0.09])


class SplitRecordsTests(unittest.TestCase):
    def test_mixture_split_by_schema(self):
        values = [
            _rec(),
            {"schema": sc.PAGE_SCHEMA, "kind": "content", "page": 2},
            _frame(),
            {"schema": sc.HEADER_SCHEMA, "page": 2, "scale": 1.0, "fits": True,
             "fits_v": True, "height": 12.0},
            {"t": "pdfpc-unrelated"},
        ]
        buckets = sc.split_records(values)
        self.assertEqual([len(buckets[k]) for k in ("layout", "pages", "frames", "headers")],
                         [1, 1, 1, 1])


class CliExitCodeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = pathlib.Path(temporary.name)

    def _write_json(self, name, payload):
        path = self.tmp / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def _run(self, payload, *args):
        telemetry = self._write_json("telemetry.json", payload)
        return subprocess.run([sys.executable, str(CHECKER), telemetry, *args],
                              capture_output=True, text=True)

    def _payload(self, rec):
        return [rec] + _frames_for(rec)

    def test_error_exits_one(self):
        rec = _rec(fit=_fit("overflow", required=1.2, body_overflow=0.2))
        proc = self._run(self._payload(rec))
        self.assertEqual(proc.returncode, 1, msg=_process_output(proc))

    def test_clean_exits_zero(self):
        proc = self._run(self._payload(_rec()))
        self.assertEqual(proc.returncode, 0, msg=_process_output(proc))

    def test_strict_warning_exits_one(self):
        rec = _rec(fit=_fit("compressed", required=0.9, gap_ratio=0.5))
        normal = self._run(self._payload(rec))
        strict = self._run(self._payload(rec), "--strict")
        self.assertEqual(normal.returncode, 0, msg=_process_output(normal))
        self.assertEqual(strict.returncode, 1, msg=_process_output(strict))

    def test_advisory_always_zero(self):
        rec = _rec(fit=_fit("overflow", required=1.2, body_overflow=0.2))
        proc = self._run(self._payload(rec), "--advisory")
        self.assertEqual(proc.returncode, 0, msg=_process_output(proc))

    def test_empty_telemetry_exits_one(self):
        normal = self._run([])
        advisory = self._run([], "--advisory")
        self.assertEqual(normal.returncode, 1, msg=_process_output(normal))
        self.assertEqual(advisory.returncode, 0, msg=_process_output(advisory))

    def test_old_schema_exits_two(self):
        rec = _rec()
        rec["schema"] = "xwysyy-slide-layout/v3"
        proc = self._run([rec])
        self.assertEqual(proc.returncode, 2, msg=_process_output(proc))
        self.assertIn("expected", proc.stderr)

    def test_broken_rules_exit_two(self):
        rules = self._write_json("rules.json", {"nonsense": 1})
        proc = self._run(self._payload(_rec()), "--rules", rules)
        self.assertEqual(proc.returncode, 2, msg=_process_output(proc))
        self.assertIn("unknown rule", proc.stderr)

    def test_orphan_frame_exits_one(self):
        rec = _rec()
        proc = self._run(self._payload(rec) + [_frame("ghost", page=9)])
        self.assertEqual(proc.returncode, 1, msg=_process_output(proc))
        self.assertIn("orphan_frame", proc.stdout)


@unittest.skipUnless(HAS_TYPST, "typst not on PATH")
class TypstIntegrationTests(unittest.TestCase):
    """Compile the real decks and assert the end-to-end verdicts."""

    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _xcheck(self, deck, *args):
        return subprocess.run(
            [sys.executable, str(XCHECK), str(deck), "--input", "visual-ci=true",
             "--format", "json", *args],
            capture_output=True, text=True)

    def _slides(self, proc):
        self.assertTrue(proc.stdout, msg=proc.stderr)
        data = json.loads(proc.stdout)
        return {s["id"]: s for s in data["slides"]}

    def test_demo_good_pages_pass_and_bad_pages_flagged(self):
        proc = self._xcheck(REPO / "examples" / "layout-demo.typ")
        slides = self._slides(proc)
        good = [k for k in slides if k.startswith("good-")]
        self.assertEqual(len(good), 10)
        for k in good:
            self.assertEqual(slides[k]["diagnostics"], [], msg=f"{k}: {slides[k]['diagnostics']}")
        expected = {
            "bad-lowdensity": "low_density",
            "bad-smallfig": "low_density",
            "bad-imbalance": "column_imbalance",
            "bad-empty-card": "underfilled_card",
            "bad-overflow": "content_overflow",
            "bad-grid-overflow": "content_overflow",
        }
        for k, dtype in expected.items():
            types = [d["type"] for d in slides[k]["diagnostics"]]
            self.assertIn(dtype, types, msg=f"{k}: {types}")
        # deliberate mistakes include errors, so the run exits non-zero
        self.assertEqual(proc.returncode, 1, msg=_process_output(proc))
        # coverage: every content page carries telemetry
        self.assertEqual(slides["<deck>"]["metrics"]["missing_pages"], [])
        # archetypes survive the pipeline
        self.assertEqual(slides["good-stat"]["archetype"], "stat")
        self.assertEqual(slides["good-figure"]["archetype"], "figure")

    def test_fit_states(self):
        meta_path = pathlib.Path(self.tmp.name) / "fit-meta.json"
        proc = self._xcheck(FIXTURES / "layout-fit.typ", "--save-meta", str(meta_path))
        slides = self._slides(proc)
        types = {k: [d["type"] for d in s["diagnostics"]] for k, s in slides.items()}
        self.assertIn("margin_squeeze", types["sidebar-tight"])
        self.assertIn("content_overflow", types["duo-overflow-starved"])
        self.assertNotIn("invalid_fit_state", types["duo-overflow-starved"])
        self.assertIn("gap_compressed", types["duo-compressed"])
        # the raw fit states, from the saved metadata
        meta = json.loads(meta_path.read_text())
        states = {v["id"]: v["fit"]["state"] for v in meta
                  if isinstance(v, dict) and v.get("schema") == sc.SCHEMA}
        self.assertEqual(states["sidebar-tight"], "tight")
        self.assertEqual(states["duo-overflow-starved"], "overflow")
        self.assertEqual(states["duo-compressed"], "compressed")

    def test_handout_coverage_gap_not_masked(self):
        deck = FIXTURES / "layout-handout.typ"
        for extra in ([], ["--input", "handout=true"]):
            proc = self._xcheck(deck, "--profile", "agent", *extra)
            slides = self._slides(proc)
            self.assertIn(2, slides["<deck>"]["metrics"]["missing_pages"], msg=str(extra))
            self.assertEqual(proc.returncode, 1, msg=f"{extra}\n{_process_output(proc)}")

    def test_pixel_stage_catches_escape_and_edge(self):
        proc = self._xcheck(FIXTURES / "layout-pixel.typ", "--pixels", "--ppi", "54")
        slides = self._slides(proc)
        types = [d["type"] for d in slides["<pixels>"]["diagnostics"]]
        self.assertIn("render_telemetry_mismatch", types)
        self.assertIn("edge_ink", types)

    def test_adversarial_autoid_blank_frame_fails(self):
        # GPT review P0#1: without an explicit id the blank first reveal frame
        # used to detach from its record and pass green.
        proc = self._xcheck(FIXTURES / "adversarial" / "autoid-blank-frame.typ",
                            "--profile", "agent")
        slides = self._slides(proc)
        all_types = [d["type"] for s in slides.values() for d in s["diagnostics"]]
        self.assertIn("empty_frame", all_types)
        self.assertNotIn("orphan_frame", all_types)
        self.assertEqual(proc.returncode, 1, msg=_process_output(proc))

    def test_adversarial_empty_stretch_fails_pixels(self):
        # GPT review P0#2: an empty stretch visual claims a full-frame payload;
        # only the pixel stage can refute the claim.
        proc = self._xcheck(FIXTURES / "adversarial" / "empty-stretch.typ",
                            "--profile", "agent")
        slides = self._slides(proc)
        types = [d["type"] for d in slides["<pixels>"]["diagnostics"]]
        self.assertIn("hollow_object", types)
        self.assertEqual(proc.returncode, 1, msg=_process_output(proc))

    def test_panic_fixtures_fail_to_compile(self):
        expectations = {
            "required-slot.typ": "top is required",
            "empty-content.typ": "renders empty",
            "grid-single.typ": "at least 2 columns",
            "tuning-unknown.typ": "unknown tuning key",
            "tuning-range.typ": "outside",
            "reveal-from-bad.typ": "reveal-from",
            "stat-missing.typ": "metric",
            "slide-kind.typ": "kind is not a parameter",
            "visual-fit.typ": "fit must be",
            "spacer-card.typ": "no measurable width",
            "bare-rule.typ": "no measurable height",
            "focus-reveal.typ": "has no reveal steps",
            "takeaway-stretch.typ": "cannot be visual",
            "sidebar-typed.typ": "not typed items",
            "image-noimg.typ": "img is required",
            "role-bad.typ": "closed role set",
            "metric-empty.typ": "renders empty",
        }
        panic_dir = FIXTURES / "panic"
        fixtures = sorted(p.name for p in panic_dir.glob("*.typ"))
        self.assertEqual(fixtures, sorted(expectations))
        out = pathlib.Path(self.tmp.name) / "panic.pdf"
        for name, needle in expectations.items():
            proc = subprocess.run(
                ["typst", "compile", "--root", str(REPO), str(panic_dir / name), str(out)],
                capture_output=True, text=True)
            self.assertNotEqual(
                proc.returncode,
                0,
                msg=f"{name} compiled but must panic\n{_process_output(proc)}",
            )
            self.assertIn(needle, proc.stderr, msg=f"{name}: {proc.stderr[:400]}")

    def test_note_mode_panics_match_slides_mode(self):
        # The same authoring errors must fail the note build too (formerly the
        # note branch returned before validation).
        out = pathlib.Path(self.tmp.name) / "note.pdf"
        for name in ("spacer-card.typ", "role-bad.typ", "metric-empty.typ"):
            proc = subprocess.run(
                ["typst", "compile", "--root", str(REPO), "--input", "mode=note",
                 str(FIXTURES / "panic" / name), str(out)],
                capture_output=True, text=True)
            self.assertNotEqual(
                proc.returncode,
                0,
                msg=f"{name} note build must panic\n{_process_output(proc)}",
            )

    def test_header_shrink_telemetry(self):
        proc = self._xcheck(FIXTURES / "header-shrink.typ")
        self.assertTrue(proc.stdout, msg=proc.stderr)
        slides = {s["id"]: s for s in json.loads(proc.stdout)["slides"]}
        types = [d["type"] for d in slides["<headers>"]["diagnostics"]]
        self.assertIn("header_shrunk", types)


if __name__ == "__main__":
    unittest.main()
