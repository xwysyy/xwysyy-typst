from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "render-visuals"


FAKE_TYPST = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import os
    import pathlib
    import sys

    counter = pathlib.Path(os.environ["FAKE_TYPST_COUNTER"])
    call = int(counter.read_text(encoding="utf-8")) + 1 if counter.exists() else 1
    counter.write_text(str(call), encoding="utf-8")
    if call == int(os.environ.get("FAKE_TYPST_FAIL_AT", "0")):
        raise SystemExit(17)
    if call == int(os.environ.get("FAKE_TYPST_SKIP_AT", "0")):
        raise SystemExit(0)

    target = pathlib.Path(sys.argv[-1].replace("{p}", "1"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"render {call}\\n", encoding="utf-8")
    """
)


def process_output(proc: subprocess.CompletedProcess[str]) -> str:
    return f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


class RenderVisualsTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = pathlib.Path(temporary.name)
        self.output = self.base / "visuals"
        self.output.mkdir()
        (self.output / "slides-sky-99.png").write_text("old", encoding="utf-8")
        (self.output / "keep.png").write_text("keep png", encoding="utf-8")
        (self.output / "keep.txt").write_text("keep", encoding="utf-8")

        fake_bin = self.base / "bin"
        fake_bin.mkdir()
        typst = fake_bin / "typst"
        typst.write_text(FAKE_TYPST, encoding="utf-8")
        typst.chmod(0o755)

        self.env = os.environ.copy()
        self.env["PATH"] = os.pathsep.join((str(fake_bin), self.env["PATH"]))
        self.env["FAKE_TYPST_COUNTER"] = str(self.base / "counter")

    def render(
        self,
        *,
        fail_at: int | None = None,
        skip_at: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        if fail_at is not None:
            env["FAKE_TYPST_FAIL_AT"] = str(fail_at)
        if skip_at is not None:
            env["FAKE_TYPST_SKIP_AT"] = str(skip_at)
        return subprocess.run(
            [str(RENDERER), str(self.output)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_success_replaces_the_complete_png_set(self) -> None:
        proc = self.render()

        self.assertEqual(proc.returncode, 0, process_output(proc))
        names = {path.name for path in self.output.glob("*.png")}
        self.assertEqual(
            names,
            {
                "dual-source-note-1.png",
                "dual-source-slides-1.png",
                "layout-demo-1.png",
                "note-1.png",
                "slides-sky-1.png",
                "slides-sunset-1.png",
                "theme-forest-1.png",
                "theme-graphite-1.png",
                "theme-midnight-1.png",
                "theme-sky-1.png",
                "theme-sunset-1.png",
                "theme-violet-1.png",
                "keep.png",
            },
        )
        self.assertEqual((self.output / "keep.png").read_text(encoding="utf-8"), "keep png")
        self.assertEqual((self.output / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_missing_render_is_reported_without_publishing(self) -> None:
        proc = self.render(skip_at=2)

        self.assertEqual(proc.returncode, 1, process_output(proc))
        self.assertIn("render produced no pages for: slides-sunset-{p}.png", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        names = {path.name for path in self.output.glob("*.png")}
        self.assertEqual(names, {"slides-sky-99.png", "keep.png"})

    def test_failed_render_preserves_the_previous_png_set(self) -> None:
        proc = self.render(fail_at=2)

        self.assertEqual(proc.returncode, 17, process_output(proc))
        names = {path.name for path in self.output.glob("*.png")}
        self.assertEqual(names, {"slides-sky-99.png", "keep.png"})
        self.assertEqual(
            (self.output / "slides-sky-99.png").read_text(encoding="utf-8"),
            "old",
        )
        self.assertEqual((self.output / "keep.png").read_text(encoding="utf-8"), "keep png")
        self.assertEqual((self.output / "keep.txt").read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
