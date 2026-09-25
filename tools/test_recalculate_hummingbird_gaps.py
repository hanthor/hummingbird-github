#!/usr/bin/env python3
"""Unit tests for tools/recalculate_hummingbird_gaps.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "recalculate_hummingbird_gaps.py"

sys.path.insert(0, str(TOOL.parent))
import recalculate_hummingbird_gaps as tool_module  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, timeout=30,
    )


def write_lines(path: Path, values: list[str]) -> Path:
    path.write_text("\n".join(values) + "\n" if values else "")
    return path


def write_manifest(path: Path, sections: dict[str, list[str]]) -> Path:
    body = []
    for section, packages in sections.items():
        body.append(f"[{section}]")
        pkg_list = ", ".join(f'"{p}"' for p in packages)
        body.append(f"packages = [{pkg_list}]")
        body.append("")
    path.write_text("\n".join(body))
    return path


class LinesHelperTests(unittest.TestCase):
    def test_strips_blank_lines_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "pkgs.txt"
            f.write_text("foo\n\n# comment\nbar\n   \nbaz\n")
            self.assertEqual(tool_module.lines(f), {"foo", "bar", "baz"})

    def test_empty_file_returns_empty_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "empty.txt"
            f.write_text("")
            self.assertEqual(tool_module.lines(f), set())


class MainCliTests(unittest.TestCase):
    def test_all_contract_packages_available_reports_zero_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {
                "fedora": ["bash", "coreutils"],
                "excluded": ["should-not-count"],
            })
            image = write_lines(tmp_path / "image.txt", ["bash"])
            repo = write_lines(tmp_path / "repo.txt", ["coreutils"])
            output = tmp_path / "gap.json"

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output), "--image", "test:latest")
            self.assertEqual(result.returncode, 0, result.stderr)

            report = json.loads(output.read_text())
            self.assertEqual(report["counts"]["missing"], 0)
            self.assertEqual(report["missing_from_hummingbird"], [])
            self.assertEqual(report["contract_binary_packages"], ["bash", "coreutils"])

    def test_excluded_section_is_not_part_of_the_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {
                "fedora": ["bash"],
                "excluded": ["firefox-langpacks"],
            })
            image = write_lines(tmp_path / "image.txt", ["bash", "firefox-langpacks"])
            repo = write_lines(tmp_path / "repo.txt", [])
            output = tmp_path / "gap.json"

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output), "--image", "test:latest")
            self.assertEqual(result.returncode, 0, result.stderr)

            report = json.loads(output.read_text())
            self.assertNotIn("firefox-langpacks", report["contract_binary_packages"])

    def test_missing_package_is_reported_and_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {
                "fedora": ["bash", "coreutils", "gone-missing"],
            })
            image = write_lines(tmp_path / "image.txt", ["bash"])
            repo = write_lines(tmp_path / "repo.txt", ["coreutils"])
            output = tmp_path / "gap.json"

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output), "--image", "test:latest")
            self.assertEqual(result.returncode, 0, result.stderr)

            report = json.loads(output.read_text())
            self.assertEqual(report["missing_from_hummingbird"], ["gone-missing"])
            self.assertEqual(report["counts"]["missing"], 1)

    def test_repo_only_package_is_distinguished_from_image_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {
                "fedora": ["bash", "coreutils"],
            })
            image = write_lines(tmp_path / "image.txt", ["bash"])
            repo = write_lines(tmp_path / "repo.txt", ["bash", "coreutils"])
            output = tmp_path / "gap.json"

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output), "--image", "test:latest")
            self.assertEqual(result.returncode, 0, result.stderr)

            report = json.loads(output.read_text())
            self.assertEqual(report["available_from_image"], ["bash"])
            self.assertEqual(report["available_from_repo_only"], ["coreutils"])
            self.assertEqual(report["counts"]["image"], 1)
            self.assertEqual(report["counts"]["repo_only"], 1)

    def test_multiple_sections_are_unioned_into_one_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {
                "multimedia_overrides": ["mesa-libGL"],
                "fedora": ["bash"],
                "fedora_v42": ["some-v42-only-pkg"],
            })
            image = write_lines(tmp_path / "image.txt", ["bash", "mesa-libGL", "some-v42-only-pkg"])
            repo = write_lines(tmp_path / "repo.txt", [])
            output = tmp_path / "gap.json"

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output), "--image", "test:latest")
            self.assertEqual(result.returncode, 0, result.stderr)

            report = json.loads(output.read_text())
            self.assertEqual(set(report["contract_binary_packages"]), {"bash", "mesa-libGL", "some-v42-only-pkg"})
            self.assertEqual(report["counts"]["missing"], 0)

    def test_output_report_includes_image_argument_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {"fedora": ["bash"]})
            image = write_lines(tmp_path / "image.txt", ["bash"])
            repo = write_lines(tmp_path / "repo.txt", [])
            output = tmp_path / "gap.json"

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output),
                         "--image", "quay.io/example/os:latest")
            self.assertEqual(result.returncode, 0, result.stderr)

            report = json.loads(output.read_text())
            self.assertEqual(report["image"], "quay.io/example/os:latest")
            self.assertIn("measured_at", report)

    def test_output_directory_is_created_if_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {"fedora": ["bash"]})
            image = write_lines(tmp_path / "image.txt", ["bash"])
            repo = write_lines(tmp_path / "repo.txt", [])
            output = tmp_path / "nested" / "dir" / "gap.json"
            self.assertFalse(output.parent.exists())

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output), "--image", "test:latest")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())

    def test_stdout_prints_counts_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = write_manifest(tmp_path / "manifest.toml", {"fedora": ["bash", "missing-one"]})
            image = write_lines(tmp_path / "image.txt", ["bash"])
            repo = write_lines(tmp_path / "repo.txt", [])
            output = tmp_path / "gap.json"

            result = run("--manifest", str(manifest), "--image-packages", str(image),
                         "--repo-packages", str(repo), "--output", str(output), "--image", "test:latest")
            self.assertEqual(result.returncode, 0, result.stderr)

            counts = json.loads(result.stdout)
            self.assertEqual(counts, {"contract": 2, "image": 1, "repo_only": 0, "missing": 1})


if __name__ == "__main__":
    unittest.main()
