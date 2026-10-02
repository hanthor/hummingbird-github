#!/usr/bin/env python3
"""Unit tests for recalculate_hummingbird_gaps.py"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from recalculate_hummingbird_gaps import lines, main


class TestLines(unittest.TestCase):
    """Test the lines() helper function."""

    def test_lines_strips_whitespace(self):
        """Test that lines() strips leading/trailing whitespace."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("  package1  \n")
            f.write("  package2  \n")
            f.flush()
            result = lines(Path(f.name))
            Path(f.name).unlink()
            self.assertEqual(result, {"package1", "package2"})

    def test_lines_filters_comments(self):
        """Test that lines() skips comment lines."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("package1\n")
            f.write("# This is a comment\n")
            f.write("package2\n")
            f.flush()
            result = lines(Path(f.name))
            Path(f.name).unlink()
            self.assertEqual(result, {"package1", "package2"})

    def test_lines_filters_blank_lines(self):
        """Test that lines() skips blank lines."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("package1\n")
            f.write("\n")
            f.write("package2\n")
            f.flush()
            result = lines(Path(f.name))
            Path(f.name).unlink()
            self.assertEqual(result, {"package1", "package2"})

    def test_lines_empty_file(self):
        """Test that lines() handles empty files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.flush()
            result = lines(Path(f.name))
            Path(f.name).unlink()
            self.assertEqual(result, set())

    def test_lines_only_comments(self):
        """Test that lines() returns empty set for comment-only files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("# Comment 1\n")
            f.write("# Comment 2\n")
            f.flush()
            result = lines(Path(f.name))
            Path(f.name).unlink()
            self.assertEqual(result, set())


class TestMainLogic(unittest.TestCase):
    """Test the main() function and contract logic."""

    def setUp(self):
        """Set up temp directory and files for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temp directory."""
        self.temp_dir.cleanup()

    def test_excluded_section_not_in_contract(self):
        """Test that [excluded] section is not included in contract."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[excluded]
packages = ["excluded-pkg"]

[fedora]
packages = ["fedora-pkg"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("fedora-pkg\nexcluded-pkg\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        report = json.loads(output_path.read_text())
        self.assertIn("fedora-pkg", report["contract_binary_packages"])
        self.assertNotIn("excluded-pkg", report["contract_binary_packages"])

    def test_multiple_sections_unioned(self):
        """Test that packages from multiple sections are unioned."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["pkg1"]

[multimedia]
packages = ["pkg2"]

[fedora_v42]
packages = ["pkg3"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("pkg1\npkg2\npkg3\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        report = json.loads(output_path.read_text())
        contract = set(report["contract_binary_packages"])
        self.assertEqual(contract, {"pkg1", "pkg2", "pkg3"})

    def test_image_vs_repo_only_distinction(self):
        """Test distinction between image, repo-only, and missing packages."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["image-pkg", "repo-only-pkg", "missing-pkg"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("image-pkg\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("repo-only-pkg\n")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        report = json.loads(output_path.read_text())
        self.assertIn("image-pkg", report["available_from_image"])
        self.assertIn("repo-only-pkg", report["available_from_repo_only"])
        self.assertIn("missing-pkg", report["missing_from_hummingbird"])

    def test_missing_package_detection(self):
        """Test detection of missing packages."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["missing1", "missing2"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        report = json.loads(output_path.read_text())
        missing = set(report["missing_from_hummingbird"])
        self.assertEqual(missing, {"missing1", "missing2"})
        self.assertEqual(report["counts"]["missing"], 2)

    def test_output_json_structure(self):
        """Test that output JSON has required structure."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["pkg1", "pkg2"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("pkg1\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("pkg2\n")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "hummingbird-test:v1.0",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        report = json.loads(output_path.read_text())

        # Check required fields
        self.assertIn("measured_at", report)
        self.assertIn("image", report)
        self.assertIn("contract_binary_packages", report)
        self.assertIn("available_from_image", report)
        self.assertIn("available_from_repo_only", report)
        self.assertIn("missing_from_hummingbird", report)
        self.assertIn("counts", report)

        # Check measured_at is ISO format
        try:
            datetime.fromisoformat(report["measured_at"])
        except ValueError:
            self.fail("measured_at is not valid ISO format")

        # Check image name
        self.assertEqual(report["image"], "hummingbird-test:v1.0")

        # Check counts structure
        counts = report["counts"]
        self.assertIn("contract", counts)
        self.assertIn("image", counts)
        self.assertIn("repo_only", counts)
        self.assertIn("missing", counts)

    def test_output_directory_creation(self):
        """Test that output directory is auto-created."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["pkg1"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("pkg1\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("")

        # Specify nested output directory that doesn't exist yet
        output_path = self.temp_path / "nested" / "dirs" / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        self.assertTrue(output_path.exists())
        self.assertTrue(output_path.is_file())

    def test_counts_calculation(self):
        """Test that counts are calculated correctly."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["a", "b", "c", "d"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("a\nb\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("c\n")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        report = json.loads(output_path.read_text())
        counts = report["counts"]
        self.assertEqual(counts["contract"], 4)  # a, b, c, d
        self.assertEqual(counts["image"], 2)  # a, b
        self.assertEqual(counts["repo_only"], 1)  # c
        self.assertEqual(counts["missing"], 1)  # d

    def test_stdout_counts_format(self):
        """Test that counts are printed to stdout in JSON format."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["pkg1", "pkg2"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("pkg1\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("pkg2\n")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            with mock.patch("builtins.print") as mock_print:
                result = main()

        self.assertEqual(result, 0)
        mock_print.assert_called_once()
        printed = mock_print.call_args[0][0]
        # Parse the printed output as JSON
        counts_printed = json.loads(printed)
        self.assertIn("contract", counts_printed)
        self.assertIn("image", counts_printed)

    def test_sorted_output(self):
        """Test that output lists are sorted."""
        manifest_path = self.temp_path / "manifest.toml"
        manifest_path.write_text("""
[fedora]
packages = ["z", "a", "m"]
""")

        image_path = self.temp_path / "image.txt"
        image_path.write_text("z\na\nm\n")

        repo_path = self.temp_path / "repo.txt"
        repo_path.write_text("")

        output_path = self.temp_path / "report.json"

        with mock.patch(
            "sys.argv",
            [
                "recalculate_hummingbird_gaps.py",
                "--manifest",
                str(manifest_path),
                "--image-packages",
                str(image_path),
                "--repo-packages",
                str(repo_path),
                "--output",
                str(output_path),
                "--image",
                "test-image:latest",
            ],
        ):
            result = main()

        self.assertEqual(result, 0)
        report = json.loads(output_path.read_text())
        self.assertEqual(report["contract_binary_packages"], ["a", "m", "z"])
        self.assertEqual(report["available_from_image"], ["a", "m", "z"])


if __name__ == "__main__":
    unittest.main()
