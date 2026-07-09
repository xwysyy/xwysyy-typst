#!/usr/bin/env python3
"""Tests for scripts/slide-check.py.

Two layers:

* unit tests run the checker against a fixture captured from real telemetry
  (fast, no Typst needed);
* an integration test compiles ``examples/layout-demo.typ`` with the real
  ``typst`` binary, queries the telemetry, and asserts the checker verdicts.
  The integration test is what guards against a Typst module that queries
  cleanly by hand but does not actually compile — the gap that let an earlier
  prototype ship a parse error.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "slide-check.py"
FIXTURE = ROOT / "tests" / "fixtures" / "layout-telemetry-sample.json"
DEMO = ROOT / "examples" / "layout-demo.typ"

_loader = importlib.machinery.SourceFileLoader("slide_check", str(SCRIPT))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
assert _spec is not None
checker = importlib.util.module_from_spec(_spec)
sys.modules[_loader.name] = checker
_loader.exec_module(checker)


def _analyze(records):
    return {r["id"]: checker.analyze_slide(r, checker.DEFAULT_RULES) for r in records}


class UnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.reports = _analyze(checker._records(raw))

    def _types(self, sid):
        return {d.type for d in self.reports[sid].diagnostics}

    def test_good_duo_passes(self):
        self.assertEqual(self._types("good-duo"), set())

    def test_good_grid_passes(self):
        self.assertEqual(self._types("good-grid"), set())

    def test_good_compare_passes(self):
        self.assertEqual(self._types("good-compare"), set())

    def test_low_density_is_flagged(self):
        self.assertIn("low_density", self._types("bad-lowdensity"))

    def test_column_imbalance_is_flagged(self):
        self.assertIn("column_imbalance", self._types("bad-imbalance"))

    def test_grid_overflow_is_error(self):
        # A grid/compare column taller than the body must raise the same
        # content_overflow error duo/stack do (regression: earlier the exported
        # height was clamped to 1.0 so grid/compare overflow passed silently).
        report = self.reports["bad-grid-overflow"]
        self.assertIn("content_overflow", {d.type for d in report.diagnostics})
        self.assertTrue(report.has_error)

    def test_trapped_whitespace_between_unrelated_blocks(self):
        # Two stacked content blocks with no declared relation, far apart.
        rec = {"schema": "xwysyy-slide-layout/v1", "id": "trap", "archetype": "custom",
               "objects": [
                   {"id": "a", "role": "figure", "x": 0.1, "y": 0.02, "w": 0.6, "h": 0.2},
                   {"id": "b", "role": "text", "x": 0.1, "y": 0.75, "w": 0.6, "h": 0.15},
               ],
               "relations": [], "extra": {}}
        report = checker.analyze_slide(rec, checker.DEFAULT_RULES)
        self.assertIn("trapped_whitespace", {d.type for d in report.diagnostics})

    def test_overflow_is_error(self):
        report = self.reports["bad-overflow"]
        by_type = {d.type: d for d in report.diagnostics}
        self.assertIn("content_overflow", by_type)
        self.assertEqual(by_type["content_overflow"].severity, "error")
        self.assertTrue(report.has_error)

    def test_cli_json_output(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURE), "--format", "json"],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn("xwysyy-slide-layout-check/v1", out)

    def test_sidebar_forced_height_not_over_dense(self):
        # A sidebar's equal-height cards can ink most of the body without being
        # "too dense" — over_dense must be suppressed for the sidebar archetype.
        rec = {"schema": "xwysyy-slide-layout/v1", "id": "sb", "archetype": "sidebar",
               "objects": [{"id": "sb:label", "role": "label", "x": 0.0, "y": 0.1, "w": 0.26, "h": 0.8},
                           {"id": "sb:body", "role": "content", "x": 0.3, "y": 0.1, "w": 0.7, "h": 0.8}],
               "relations": [], "extra": {}}
        report = checker.analyze_slide(rec, checker.DEFAULT_RULES)
        self.assertNotIn("over_dense", {d.type for d in report.diagnostics})

    def test_wide_gutter_is_warning_not_error(self):
        # A wide horizontal gutter is a nudge, not a broken semantic pair.
        rec = {"schema": "xwysyy-slide-layout/v1", "id": "cmp", "archetype": "compare",
               "objects": [{"id": "l", "role": "option", "x": 0.0, "y": 0.3, "w": 0.35, "h": 0.3},
                           {"id": "r", "role": "option", "x": 0.65, "y": 0.3, "w": 0.35, "h": 0.3}],
               "relations": [{"from": "l", "to": "r", "axis": "horizontal", "desired_proximity": "gutter"}],
               "extra": {}}
        report = checker.analyze_slide(rec, checker.DEFAULT_RULES)
        types = {d.type for d in report.diagnostics}
        self.assertIn("wide_gutter", types)
        self.assertNotIn("semantic_pair_split", types)
        self.assertFalse(report.has_error)

    def test_focus_overflow_flag_is_error(self):
        rec = {"schema": "xwysyy-slide-layout/v1", "id": "f", "archetype": "focus",
               "objects": [{"id": "f:focus", "role": "main_visual", "x": 0.12, "y": 0.0, "w": 0.76, "h": 0.99}],
               "relations": [], "extra": {"overflow": True}}
        report = checker.analyze_slide(rec, checker.DEFAULT_RULES)
        self.assertTrue(report.has_error)
        self.assertIn("content_overflow", {d.type for d in report.diagnostics})

    def test_malformed_bbox_is_reported_not_crash(self):
        bad = {"schema": "xwysyy-slide-layout/v1", "id": "x", "archetype": "custom",
               "objects": [{"id": "o", "role": "text", "x": 0.1, "y": 0.1, "w": "nan", "h": 0.2}],
               "relations": [], "extra": {}}
        report = checker.analyze_slide(bad, checker.DEFAULT_RULES)
        self.assertTrue(any(d.type == "invalid_bbox" for d in report.diagnostics))


@unittest.skipIf(shutil.which("typst") is None, "typst binary not on PATH")
class TypstIntegrationTests(unittest.TestCase):
    """Compile the demo for real, then check the exported telemetry."""

    @classmethod
    def setUpClass(cls):
        env = dict(os.environ)
        subprocess.run(
            ["typst", "compile", "--root", str(ROOT), str(DEMO), "/tmp/slide-check-it.pdf"],
            check=True, capture_output=True, text=True, env=env,
        )
        out = subprocess.run(
            ["typst", "query", "--root", str(ROOT), str(DEMO),
             "<xwysyy-slide-layout>", "--field", "value"],
            check=True, capture_output=True, text=True, env=env,
        ).stdout
        cls.reports = _analyze(checker._records(json.loads(out)))

    def test_all_good_slides_pass(self):
        for sid in ("good-duo", "good-focus", "good-grid", "good-compare", "good-stack",
                    "good-stat", "good-figure", "good-sidebar"):
            with self.subTest(slide=sid):
                self.assertFalse(self.reports[sid].has_problem,
                                 msg=[d.type for d in self.reports[sid].diagnostics])

    def test_bad_slides_are_flagged(self):
        self.assertIn("low_density", {d.type for d in self.reports["bad-lowdensity"].diagnostics})
        self.assertIn("column_imbalance", {d.type for d in self.reports["bad-imbalance"].diagnostics})
        self.assertTrue(self.reports["bad-overflow"].has_error)
        self.assertTrue(self.reports["bad-grid-overflow"].has_error)


if __name__ == "__main__":
    unittest.main()
