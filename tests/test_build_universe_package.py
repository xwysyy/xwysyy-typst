from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build-universe-package"

VALID_MANIFEST = """\
[package]
name = "xwysyy"
version = "0.4.0"
entrypoint = "xwysyy.typ"

[template]
path = "template"
entrypoint = "main.typ"
thumbnail = "thumbnail.png"
"""

VALID_README = """\
# xwysyy

```typst
#import "@preview/xwysyy:0.4.0": *
#import "@preview/xwysyy:0.4.0/xwysyy-extras.typ": *
```
"""


class BuildUniversePackageTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = pathlib.Path(temporary.name)
        self.repo = self.base / "repo"
        self.output = self.base / "package"

        files: dict[str, str | bytes] = {
            "LICENSE": "MIT\n",
            "README.md": VALID_README,
            "typst.toml": VALID_MANIFEST,
            "thumbnail.png": b"PNG",
            "xwysyy.typ": "",
            "xwysyy-extras.typ": "",
            "src/main.typ": "",
            "template/main.typ": '#import "@preview/xwysyy:0.4.0": *\n',
            "docs/LAYOUT.md": "# Layout\n",
            "scripts/compare-png": "#!/bin/sh\n",
            "scripts/slide-check.py": "#!/usr/bin/env python3\n",
            "scripts/xwysyy-check": "#!/bin/sh\n",
        }
        for relative, content in files.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")

        target = self.repo / "scripts" / BUILDER.name
        shutil.copy2(BUILDER, target)
        for name in ("compare-png", "slide-check.py", "xwysyy-check", BUILDER.name):
            (self.repo / "scripts" / name).chmod(0o755)

        self.git("init", "--quiet")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Release Test",
            "-c",
            "user.email=release-test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "fixture",
        )

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def commit_file(self, relative: str, content: str) -> None:
        (self.repo / relative).write_text(content, encoding="utf-8")
        self.git("add", relative)
        self.git(
            "-c",
            "user.name=Release Test",
            "-c",
            "user.email=release-test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            f"change {relative}",
        )

    def build(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.repo / "scripts" / BUILDER.name), str(self.output)],
            capture_output=True,
            text=True,
        )

    def test_valid_package_is_published_after_verification(self) -> None:
        result = self.build()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("built @preview/xwysyy:0.4.0", result.stdout)
        self.assertIn("tree-sha256:", result.stdout)
        self.assertTrue((self.output / "xwysyy.typ").is_file())
        self.assertTrue((self.output / "xwysyy-extras.typ").is_file())
        checker_mode = (self.output / "scripts" / "xwysyy-check").stat().st_mode
        self.assertTrue(checker_mode & 0o111)
        self.assertEqual(list(self.base.glob(".package.staging-*")), [])

    def test_invalid_manifest_table_is_reported_without_traceback(self) -> None:
        self.commit_file(
            "typst.toml",
            textwrap.dedent(
                """\
                package = "invalid"

                [template]
                path = "template"
                entrypoint = "main.typ"
                thumbnail = "thumbnail.png"
                """
            ),
        )

        result = self.build()

        self.assertEqual(result.returncode, 2)
        self.assertIn("[package] must be a table", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.output.exists())

    def test_manifest_paths_cannot_escape_package_directory(self) -> None:
        self.commit_file(
            "typst.toml",
            VALID_MANIFEST.replace('entrypoint = "xwysyy.typ"', 'entrypoint = "/etc/passwd"'),
        )

        result = self.build()

        self.assertEqual(result.returncode, 2)
        self.assertIn("package.entrypoint must be a relative package path", result.stderr)
        self.assertFalse(self.output.exists())

    def test_failed_verification_leaves_no_partial_output(self) -> None:
        self.commit_file("README.md", VALID_README + "typst compile examples/demo.typ\n")

        result = self.build()

        self.assertEqual(result.returncode, 2)
        self.assertIn("repo-only example command", result.stderr)
        self.assertFalse(self.output.exists())

    def test_indented_repo_only_readme_command_is_rejected(self) -> None:
        self.commit_file("README.md", VALID_README + "  typst compile examples/demo.typ\n")

        result = self.build()

        self.assertEqual(result.returncode, 2)
        self.assertIn("repo-only example command", result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
