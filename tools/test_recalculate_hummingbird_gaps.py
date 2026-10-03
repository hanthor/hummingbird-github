#!/usr/bin/env python3
"""Unit tests for recalculate_hummingbird_gaps.py"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.recalculate_hummingbird_gaps import lines


class TestLines(unittest.TestCase):
    """Test the lines() helper function."""

    def test_lines_empty_file(self) -> None:
        """lines() returns empty set for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('')
            path = Path(f.name)
        try:
            result = lines(path)
            self.assertEqual(result, set())
        finally:
            path.unlink()

    def test_lines_strips_comments(self) -> None:
        """lines() filters out comment lines."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("package1\n# comment\npackage2\n")
            path = Path(f.name)
        try:
            result = lines(path)
            self.assertEqual(result, {"package1", "package2"})
        finally:
            path.unlink()

    def test_lines_strips_blank_lines(self) -> None:
        """lines() filters out blank and whitespace-only lines."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("package1\n\n   \npackage2\n")
            path = Path(f.name)
        try:
            result = lines(path)
            self.assertEqual(result, {"package1", "package2"})
        finally:
            path.unlink()

    def test_lines_strips_whitespace(self) -> None:
        """lines() strips leading/trailing whitespace from entries."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("  package1  \n package2 \n")
            path = Path(f.name)
        try:
            result = lines(path)
            self.assertEqual(result, {"package1", "package2"})
        finally:
            path.unlink()


class TestMainCLI(unittest.TestCase):
    """Test the main() CLI via subprocess (integration-style tests)."""

    def setUp(self) -> None:
        """Set up temporary directory for test artifacts."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _create_manifest(self, excluded: list[str] | None = None, 
                        packages_by_section: dict[str, list[str]] | None = None) -> Path:
        """Create a test manifest TOML file."""
        manifest_dir = self.temp_path / "config"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "bluefin-packages.toml"

        lines = []
        if excluded:
            lines.append("[excluded]\n")
            lines.append(f"packages = {excluded}\n")

        if packages_by_section:
            for section, packages in packages_by_section.items():
                lines.append(f"\n[{section}]\n")
                lines.append(f"packages = {packages}\n")

        manifest_path.write_text("".join(lines))
        return manifest_path

    def _run_main(self, manifest: Path, image_packages: Path, 
                  repo_packages: Path, output: Path, image: str) -> int:
        """Run recalculate_hummingbird_gaps.py via subprocess."""
        result = subprocess.run([
            sys.executable, '-m', 'tools.recalculate_hummingbird_gaps',
            '--manifest', str(manifest),
            '--image-packages', str(image_packages),
            '--repo-packages', str(repo_packages),
            '--output', str(output),
            '--image', image
        ], cwd=Path(__file__).parent.parent)
        return result.returncode

    def test_main_simple_contract(self) -> None:
        """main() correctly computes contract from manifest."""
        manifest_path = self._create_manifest(
            excluded=["excluded-pkg"],
            packages_by_section={"base": ["pkg1", "pkg2"], "extra": ["pkg3"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\npkg2\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("")
        output = self.temp_path / "reports" / "output.json"

        exit_code = self._run_main(manifest_path, image_packages, repo_packages, output, "test-image:v1")

        self.assertEqual(exit_code, 0)
        self.assertTrue(output.exists())
        report = json.loads(output.read_text())
        self.assertEqual(report["contract_binary_packages"], ["pkg1", "pkg2", "pkg3"])
        self.assertEqual(report["available_from_image"], ["pkg1", "pkg2"])
        self.assertEqual(report["available_from_repo_only"], [])
        self.assertEqual(report["missing_from_hummingbird"], ["pkg3"])

    def test_main_excluded_section_not_in_contract(self) -> None:
        """main() excludes packages from [excluded] section."""
        manifest_path = self._create_manifest(
            excluded=["excluded-pkg"],
            packages_by_section={"base": ["pkg1", "excluded-pkg"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\nexcluded-pkg\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("")
        output = self.temp_path / "reports" / "output.json"

        self._run_main(manifest_path, image_packages, repo_packages, output, "test-image")

        report = json.loads(output.read_text())
        self.assertNotIn("excluded-pkg", report["contract_binary_packages"])

    def test_main_repo_only_availability(self) -> None:
        """main() tracks packages available only from repo."""
        manifest_path = self._create_manifest(
            packages_by_section={"base": ["pkg1", "pkg2", "pkg3"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("pkg2\npkg3\n")
        output = self.temp_path / "reports" / "output.json"

        self._run_main(manifest_path, image_packages, repo_packages, output, "test-image")

        report = json.loads(output.read_text())
        self.assertEqual(sorted(report["available_from_repo_only"]), ["pkg2", "pkg3"])
        self.assertEqual(report["available_from_image"], ["pkg1"])

    def test_main_missing_packages(self) -> None:
        """main() identifies missing packages."""
        manifest_path = self._create_manifest(
            packages_by_section={"base": ["pkg1", "pkg2", "pkg3"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("pkg2\n")
        output = self.temp_path / "reports" / "output.json"

        self._run_main(manifest_path, image_packages, repo_packages, output, "test-image")

        report = json.loads(output.read_text())
        self.assertEqual(report["missing_from_hummingbird"], ["pkg3"])
        self.assertEqual(report["counts"]["missing"], 1)

    def test_main_counts(self) -> None:
        """main() produces correct count summary."""
        manifest_path = self._create_manifest(
            packages_by_section={"base": ["pkg1", "pkg2", "pkg3", "pkg4"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\npkg2\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("pkg3\n")
        output = self.temp_path / "reports" / "output.json"

        self._run_main(manifest_path, image_packages, repo_packages, output, "test-image")

        report = json.loads(output.read_text())
        self.assertEqual(report["counts"]["contract"], 4)
        self.assertEqual(report["counts"]["image"], 2)
        self.assertEqual(report["counts"]["repo_only"], 1)
        self.assertEqual(report["counts"]["missing"], 1)

    def test_main_creates_output_directory(self) -> None:
        """main() creates output directory if it doesn't exist."""
        manifest_path = self._create_manifest(
            packages_by_section={"base": ["pkg1"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("")
        output = self.temp_path / "deep" / "nested" / "reports" / "output.json"

        self._run_main(manifest_path, image_packages, repo_packages, output, "test-image")

        self.assertTrue(output.exists())

    def test_main_output_has_measured_at_timestamp(self) -> None:
        """main() includes ISO timestamp in report."""
        manifest_path = self._create_manifest(
            packages_by_section={"base": ["pkg1"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("")
        output = self.temp_path / "reports" / "output.json"

        self._run_main(manifest_path, image_packages, repo_packages, output, "test-image")

        report = json.loads(output.read_text())
        self.assertIn("measured_at", report)
        # Should be valid ISO format
        from datetime import datetime
        datetime.fromisoformat(report["measured_at"])

    def test_main_output_json_structure(self) -> None:
        """main() produces correctly structured JSON."""
        manifest_path = self._create_manifest(
            packages_by_section={"base": ["pkg1"]}
        )
        image_packages = self.temp_path / "image.txt"
        image_packages.write_text("pkg1\n")
        repo_packages = self.temp_path / "repo.txt"
        repo_packages.write_text("")
        output = self.temp_path / "reports" / "output.json"

        self._run_main(manifest_path, image_packages, repo_packages, output, "test-image:v1")

        report = json.loads(output.read_text())
        required_keys = {"measured_at", "image", "contract_binary_packages",
                        "available_from_image", "available_from_repo_only",
                        "missing_from_hummingbird", "counts"}
        self.assertEqual(set(report.keys()), required_keys)
        self.assertEqual(report["image"], "test-image:v1")


if __name__ == "__main__":
    unittest.main()
