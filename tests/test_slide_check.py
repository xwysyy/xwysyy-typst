"""Tests for scripts/slide-check.py (telemetry schema v3) and scripts/xwysyy-check.

Unit tests build synthetic v3 records; integration tests (skipped when typst
is not on PATH) compile the demo and the fixtures and assert the real
end-to-end behaviour: good pages pass, deliberate mistakes are flagged,
panic fixtures fail to compile, and the pixel stage catches what geometry
cannot.
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


def _box(x, y, w, h):
    return {"x": x, "y": y, "w": w, "h": h}


def _obj(oid, kind="card", role="explanation", frame=(0.09, 0.07, 0.82, 0.7),
         payload=None, painted=True, sizing=("natural", "natural"),
         visible_from=1, preferred_h=None):
    fx, fy, fw, fh = frame
    if payload is None:
        payload = (fx + 0.05, fy + 0.05, fw - 0.1, fh - 0.1)
    return {
        "id": oid, "object_kind": kind, "semantic_role": role, "group": "g",
        "frame": _box(*frame),
        "preferred": {"w": fw, "h": preferred_h if preferred_h is not None else fh},
        "payload": _box(*payload),
        "paint": _box(*frame) if painted else None,
        "sizing": {"x": sizing[0], "y": sizing[1]},
        "visible_from": visible_from,
    }


def _fit(state="normal", required=0.5, gap_scale=1.0, margin_deficit=0.0, body_overflow=0.0):
    return {"state": state, "required_height_ratio": required, "gap_scale": gap_scale,
            "margin_deficit_ratio": margin_deficit, "body_overflow_ratio": body_overflow}


def _rec(rid="s", archetype="stack", objects=None, relations=None, fit=None,
         extra=None, page=2, frame_count=1):
    return {
        "schema": sc.SCHEMA, "id": rid, "archetype": archetype,
        "layout_engine": "column", "page": page, "frame_count": frame_count,
        "coordinate_system": "normalized-slide-body",
        "objects": objects if objects is not None else [_obj("s:0")],
        "relations": relations or [],
        "fit": fit or _fit(),
        "extra": extra or {},
    }


def _diag_types(report):
    return [d.type for d in report.diagnostics]


def _analyze(record, frames=None, profile="human", rules=None):
    return sc.analyze_slide(record, rules or sc._load_rules(None), frames, profile)


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


class StrictParsingTests(unittest.TestCase):
    def test_missing_bbox_key_is_error(self):
        obj = _obj("s:0")
        del obj["frame"]["h"]
        report = _analyze(_rec(objects=[obj]))
        self.assertIn("invalid_object", _diag_types(report))

    def test_paint_must_be_dict_or_null(self):
        obj = _obj("s:0")
        obj["paint"] = "false"
        report = _analyze(_rec(objects=[obj]))
        self.assertIn("invalid_object", _diag_types(report))

    def test_sizing_required(self):
        obj = _obj("s:0")
        obj["sizing"] = "natural"
        report = _analyze(_rec(objects=[obj]))
        self.assertIn("invalid_object", _diag_types(report))

    def test_visible_from_must_be_positive_int(self):
        obj = _obj("s:0")
        obj["visible_from"] = 0
        report = _analyze(_rec(objects=[obj]))
        self.assertIn("invalid_object", _diag_types(report))

    def test_schema_mismatch_skips_record(self):
        rec = _rec()
        rec["schema"] = "xwysyy-slide-layout/v2"
        report = _analyze(rec)
        self.assertIn("schema_mismatch", _diag_types(report))
        self.assertEqual(report.diagnostics[0].severity, "warning")
        report = _analyze(rec, profile="agent")
        self.assertEqual(report.diagnostics[0].severity, "error")

    def test_unknown_object_kind_warns(self):
        report = _analyze(_rec(objects=[_obj("s:0", kind="main-visual")]))
        self.assertIn("unknown_object_kind", _diag_types(report))


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
        report = _analyze(_rec(fit=_fit("compressed", required=0.88, gap_scale=0.4)))
        self.assertIn("gap_compressed", _diag_types(report))
        self.assertFalse(report.has_error)


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
        # The review's narrow-visual case: a 10%-wide payload must not be
        # reported as ~0.58 coverage just because its frame spans the body.
        objects = [_obj("s:0", kind="visual", role="main_visual", painted=False,
                        frame=(0.09, 0.07, 0.82, 0.84),
                        payload=(0.45, 0.07, 0.10, 0.84))]
        report = _analyze(_rec(archetype="focus", objects=objects))
        self.assertLess(report.metrics["visual_coverage"], 0.12)


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


class OutsideBodyTests(unittest.TestCase):
    def test_horizontal_escape_checked_in_every_state(self):
        objects = [_obj("s:0", frame=(0.5, 0.1, 0.6, 0.4), payload=(0.52, 0.12, 0.56, 0.36))]
        report = _analyze(_rec(objects=objects, fit=_fit("tight", margin_deficit=0.05)))
        self.assertIn("object_outside_body", _diag_types(report))

    def test_vertical_escape_suppressed_when_fit_reports_it(self):
        objects = [_obj("s:0", frame=(0.09, 0.5, 0.8, 0.6), payload=(0.1, 0.52, 0.7, 0.56))]
        report = _analyze(_rec(objects=objects, fit=_fit("tight", margin_deficit=0.05)))
        self.assertNotIn("object_outside_body", _diag_types(report))
        report = _analyze(_rec(objects=objects))
        self.assertIn("object_outside_body", _diag_types(report))


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
        # Axis overlap but horizontally disjoint: no collision error.
        rec = self._pair((0.05, 0.1, 0.3, 0.4), (0.6, 0.35, 0.3, 0.4))
        self.assertNotIn("object_overlap", _diag_types(_analyze(rec)))
        # True 2-D intersection: error.
        rec = self._pair((0.09, 0.1, 0.8, 0.4), (0.09, 0.35, 0.8, 0.4))
        self.assertIn("object_overlap", _diag_types(_analyze(rec)))

    def test_reversed_direction_warns(self):
        rec = self._pair((0.13, 0.60, 0.74, 0.25), (0.09, 0.07, 0.82, 0.4))
        self.assertIn("invalid_relation_direction", _diag_types(_analyze(rec)))

    def test_crowded_suppressed_when_not_normal(self):
        rec = self._pair((0.09, 0.07, 0.82, 0.4), (0.13, 0.48, 0.74, 0.25))
        self.assertIn("crowded_related_pair", _diag_types(_analyze(rec)))
        rec["fit"] = _fit("compressed", gap_scale=0.3)
        self.assertNotIn("crowded_related_pair", _diag_types(_analyze(rec)))

    def test_wide_gutter_and_alignment(self):
        rec = self._pair((0.0, 0.2, 0.3, 0.5), (0.65, 0.2, 0.3, 0.5),
                         axis="horizontal", proximity="gutter")
        self.assertIn("wide_gutter", _diag_types(_analyze(rec)))
        rec = self._pair((0.0, 0.1, 0.45, 0.3), (0.5, 0.45, 0.45, 0.3),
                         axis="horizontal", proximity="gutter")
        self.assertIn("weak_relation_alignment", _diag_types(_analyze(rec)))


class ColumnImbalanceTests(unittest.TestCase):
    def _grid(self, pref_hs):
        objects = []
        n = len(pref_hs)
        for i, ph in enumerate(pref_hs):
            x = 0.02 + i * (0.96 / n)
            objects.append(_obj(f"s:{i}", frame=(x, 0.2, 0.9 / n, 0.6),
                                payload=(x + 0.02, 0.22, 0.9 / n - 0.04, max(ph - 0.05, 0.05)),
                                preferred_h=ph))
        return _rec(archetype="grid", objects=objects,
                    extra={"natural_height_variance": max(pref_hs) - min(pref_hs)})

    def test_imbalance_flagged(self):
        report = _analyze(self._grid([0.08, 0.62, 0.10]))
        self.assertIn("column_imbalance", _diag_types(report))

    def test_small_absolute_spread_passes(self):
        report = _analyze(self._grid([0.04, 0.10, 0.05]))
        self.assertNotIn("column_imbalance", _diag_types(report))


class RevealFrameTests(unittest.TestCase):
    def test_empty_frame_is_error(self):
        objects = [_obj("s:0", visible_from=2),
                   _obj("s:1", frame=(0.09, 0.8, 0.8, 0.15), visible_from=2)]
        frames = [{"schema": sc.FRAME_SCHEMA, "id": "s", "step": 1, "steps": 2, "page": 2},
                  {"schema": sc.FRAME_SCHEMA, "id": "s", "step": 2, "steps": 2, "page": 3}]
        report = _analyze(_rec(objects=objects, frame_count=2), frames=frames)
        self.assertIn("empty_frame", _diag_types(report))

    def test_unrelated_overlap_checked_per_step(self):
        objects = [
            _obj("s:0", frame=(0.09, 0.1, 0.8, 0.4)),
            _obj("s:1", frame=(0.09, 0.3, 0.8, 0.4), visible_from=2),
        ]
        frames = [{"schema": sc.FRAME_SCHEMA, "id": "s", "step": s, "steps": 2, "page": 1 + s}
                  for s in (1, 2)]
        report = _analyze(_rec(objects=objects, frame_count=2), frames=frames)
        self.assertIn("object_overlap", _diag_types(report))


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

    def test_frames_drive_coverage_not_ranges(self):
        # Handout: the record sits on page 3 with frame_count 2, but only one
        # physical frame exists.  Page 2 (hand-written) must stay uncovered.
        records = [_rec(rid="rev", page=3, frame_count=2)]
        frames = [{"schema": sc.FRAME_SCHEMA, "id": "rev", "step": 2, "steps": 2, "page": 3}]
        pages = self._pages(["section", "content", "content"])
        report = sc.coverage_report(records, frames, pages)
        self.assertEqual(report.metrics["missing_pages"], [2])
        self.assertIn("telemetry_gap", _diag_types(report))

    def test_multi_frame_pages_covered(self):
        records = [_rec(rid="rev", page=4, frame_count=2)]
        frames = [{"schema": sc.FRAME_SCHEMA, "id": "rev", "step": s, "steps": 2, "page": 2 + s}
                  for s in (1, 2)]
        pages = self._pages(["section", "content", "content", "content"])
        report = sc.coverage_report(records, frames, pages)
        self.assertEqual(report.metrics["missing_pages"], [2])

    def test_exempt_kinds(self):
        records = [_rec(page=2)]
        pages = self._pages(["title", "content", "image", "end"])
        report = sc.coverage_report(records, [], pages)
        self.assertEqual(report.metrics["missing_pages"], [])
        self.assertEqual(report.metrics["exempt_pages"], 3)

    def test_manifest_gap_with_page_count(self):
        records = [_rec(page=2)]
        pages = self._pages(["title", "content"])
        report = sc.coverage_report(records, [], pages, page_count=4)
        self.assertIn("manifest_gap", _diag_types(report))
        self.assertEqual(report.metrics["unmanifested_pages"], [3, 4])

    def test_agent_profile_escalates(self):
        records = [_rec(page=2)]
        pages = self._pages(["content", "content"])
        report = sc.coverage_report(records, [], pages, profile="agent")
        self.assertTrue(report.has_error)


class HeaderTests(unittest.TestCase):
    def test_shrunk_and_overflow(self):
        headers = [
            {"schema": sc.HEADER_SCHEMA, "page": 2, "scale": 1.0, "fits": True},
            {"schema": sc.HEADER_SCHEMA, "page": 3, "scale": 0.82, "fits": True},
            {"schema": sc.HEADER_SCHEMA, "page": 4, "scale": 0.65, "fits": False},
        ]
        report = sc.header_report(headers)
        types = _diag_types(report)
        self.assertIn("header_shrunk", types)
        self.assertIn("header_overflow", types)
        self.assertTrue(report.has_error)


class RulesTests(unittest.TestCase):
    def test_unknown_rule_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"ink_flor": {"duo": 0.1}}, f)
        with self.assertRaises(sc.TelemetryError):
            sc._load_rules(f.name)

    def test_valid_override_merges(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"ink_floor": {"duo": 0.05}}, f)
        rules = sc._load_rules(f.name)
        self.assertEqual(rules["ink_floor"]["duo"], 0.05)
        self.assertEqual(rules["ink_floor"]["grid"], sc.DEFAULT_RULES["ink_floor"]["grid"])


class SplitRecordsTests(unittest.TestCase):
    def test_mixture_split_by_schema(self):
        values = [
            _rec(),
            {"schema": sc.PAGE_SCHEMA, "kind": "content", "page": 2},
            {"schema": sc.FRAME_SCHEMA, "id": "s", "step": 1, "steps": 1, "page": 2},
            {"schema": sc.HEADER_SCHEMA, "page": 2, "scale": 1.0, "fits": True},
            {"t": "pdfpc-unrelated"},
        ]
        buckets = sc.split_records(values)
        self.assertEqual([len(buckets[k]) for k in ("layout", "pages", "frames", "headers")],
                         [1, 1, 1, 1])


class CliExitCodeTests(unittest.TestCase):
    def _run(self, payload, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
        return subprocess.run([sys.executable, str(CHECKER), f.name, *args],
                              capture_output=True, text=True)

    def test_error_exits_one(self):
        rec = _rec(fit=_fit("overflow", required=1.2, body_overflow=0.2))
        self.assertEqual(self._run([rec]).returncode, 1)

    def test_clean_exits_zero(self):
        self.assertEqual(self._run([_rec()]).returncode, 0)

    def test_strict_warning_exits_one(self):
        rec = _rec(fit=_fit("compressed", gap_scale=0.5))
        self.assertEqual(self._run([rec]).returncode, 0)
        self.assertEqual(self._run([rec], "--strict").returncode, 1)

    def test_advisory_always_zero(self):
        rec = _rec(fit=_fit("overflow", required=1.2, body_overflow=0.2))
        self.assertEqual(self._run([rec], "--advisory").returncode, 0)

    def test_empty_telemetry_exits_one(self):
        self.assertEqual(self._run([]).returncode, 1)
        self.assertEqual(self._run([], "--advisory").returncode, 0)

    def test_broken_rules_exit_two(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"nonsense": 1}, f)
        proc = self._run([_rec()], "--rules", f.name)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown rule", proc.stderr)


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
        self.assertEqual(proc.returncode, 1)
        # coverage: every content page carries telemetry
        self.assertEqual(slides["<deck>"]["metrics"]["missing_pages"], [])
        # archetypes survive the pipeline
        self.assertEqual(slides["good-stat"]["archetype"], "stat")
        self.assertEqual(slides["good-figure"]["archetype"], "figure")

    def test_fit_states(self):
        meta_path = pathlib.Path(self.tmp.name) / "fit-meta.json"
        proc = self._xcheck(REPO / "tests" / "fixtures" / "layout-fit.typ",
                            "--save-meta", str(meta_path))
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
        deck = REPO / "tests" / "fixtures" / "layout-handout.typ"
        for extra in ([], ["--input", "handout=true"]):
            proc = self._xcheck(deck, "--profile", "agent", *extra)
            slides = self._slides(proc)
            self.assertIn(2, slides["<deck>"]["metrics"]["missing_pages"], msg=str(extra))
            self.assertEqual(proc.returncode, 1, msg=str(extra))

    def test_pixel_stage_catches_escape_and_edge(self):
        proc = self._xcheck(REPO / "tests" / "fixtures" / "layout-pixel.typ",
                            "--pixels", "--ppi", "54")
        slides = self._slides(proc)
        types = [d["type"] for d in slides["<pixels>"]["diagnostics"]]
        self.assertIn("render_telemetry_mismatch", types)
        self.assertIn("edge_ink", types)

    def test_panic_fixtures_fail_to_compile(self):
        expectations = {
            "required-slot.typ": "top is required",
            "empty-content.typ": "renders empty",
            "grid-single.typ": "at least 2 columns",
            "tuning-unknown.typ": "unknown tuning key",
            "tuning-range.typ": "outside",
            "reveal-from-bad.typ": "reveal-from",
            "stat-missing.typ": "value",
            "slide-kind.typ": "kind must be one of",
            "visual-fit.typ": "fit must be",
        }
        panic_dir = REPO / "tests" / "fixtures" / "panic"
        fixtures = sorted(p.name for p in panic_dir.glob("*.typ"))
        self.assertEqual(fixtures, sorted(expectations))
        out = pathlib.Path(self.tmp.name) / "panic.pdf"
        for name, needle in expectations.items():
            proc = subprocess.run(
                ["typst", "compile", "--root", str(REPO), str(panic_dir / name), str(out)],
                capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0, msg=f"{name} compiled but must panic")
            self.assertIn(needle, proc.stderr, msg=f"{name}: {proc.stderr[:400]}")

    def test_header_shrink_telemetry(self):
        deck = pathlib.Path(self.tmp.name) / "long-title.typ"
        deck.write_text(
            f'#import "{REPO}/xwysyy.typ": *\n'
            '#show: xwysyy-pre.with(aspect-ratio: "4-3", theme: "sky",\n'
            '  config-info(title: [T], author: " ", institution: " "))\n'
            "= S\n"
            "== A very long slide title that keeps going and wraps onto a second line in four by three\n"
            "Body.\n"
            "#stack-slide(items: ([*A.* one], [*B.* two]))\n",
            encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(XCHECK), str(deck), "--root", "/", "--format", "json"],
            capture_output=True, text=True)
        self.assertTrue(proc.stdout, msg=proc.stderr)
        slides = {s["id"]: s for s in json.loads(proc.stdout)["slides"]}
        types = [d["type"] for d in slides["<headers>"]["diagnostics"]]
        self.assertIn("header_shrunk", types)


if __name__ == "__main__":
    unittest.main()
