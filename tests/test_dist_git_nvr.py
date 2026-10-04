#!/usr/bin/env python3
"""Unit tests for dist_git.py's nvr_from_spec() function."""

import unittest
import tempfile
from pathlib import Path
from tools.dist_git import nvr_from_spec


class TestNvrFromSpec(unittest.TestCase):
    """Test NVR extraction from spec files."""

    def _write_spec(self, content: str) -> Path:
        """Helper: write spec content to a temporary file."""
        fd, path = tempfile.mkstemp(suffix=".spec", text=True)
        try:
            Path(path).write_text(content)
        finally:
            import os
            os.close(fd)
        return Path(path)

    def test_nvr_from_spec_basic(self):
        """Test basic NVR extraction from a simple spec file."""
        spec = self._write_spec("""Name: mypackage
Version: 1.0
Release: 1
Summary: Test package
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "mypackage-1.0-1")
        finally:
            spec.unlink()

    def test_nvr_from_spec_with_dist_macro(self):
        """Test that %{?dist} macro is removed from Release."""
        spec = self._write_spec("""Name: mypackage
Version: 2.5
Release: 3%{?dist}
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "mypackage-2.5-3")
        finally:
            spec.unlink()

    def test_nvr_from_spec_whitespace_handling(self):
        """Test whitespace normalization in field values."""
        spec = self._write_spec("""Name:   mypackage   
Version:  1.5   
Release:  2  
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "mypackage-1.5-2")
        finally:
            spec.unlink()

    def test_nvr_from_spec_hyphenated_names(self):
        """Test package names with hyphens."""
        spec = self._write_spec("""Name: my-cool-package
Version: 3.0
Release: 1
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "my-cool-package-3.0-1")
        finally:
            spec.unlink()

    def test_nvr_from_spec_version_with_dots(self):
        """Test version strings with multiple dots."""
        spec = self._write_spec("""Name: package
Version: 1.2.3.4
Release: 5
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "package-1.2.3.4-5")
        finally:
            spec.unlink()

    def test_nvr_from_spec_release_with_date(self):
        """Test release strings with date-based versions."""
        spec = self._write_spec("""Name: package
Version: 20231201
Release: 1.fc39
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "package-20231201-1.fc39")
        finally:
            spec.unlink()

    def test_nvr_from_spec_missing_name(self):
        """Test error handling when Name field is missing."""
        spec = self._write_spec("""Version: 1.0
Release: 1
""")
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec)
            self.assertIn("missing spec fields", str(ctx.exception))
            self.assertIn("name", str(ctx.exception))
        finally:
            spec.unlink()

    def test_nvr_from_spec_missing_version(self):
        """Test error handling when Version field is missing."""
        spec = self._write_spec("""Name: mypackage
Release: 1
""")
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec)
            self.assertIn("missing spec fields", str(ctx.exception))
            self.assertIn("version", str(ctx.exception))
        finally:
            spec.unlink()

    def test_nvr_from_spec_missing_release(self):
        """Test error handling when Release field is missing."""
        spec = self._write_spec("""Name: mypackage
Version: 1.0
""")
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec)
            self.assertIn("missing spec fields", str(ctx.exception))
            self.assertIn("release", str(ctx.exception))
        finally:
            spec.unlink()

    def test_nvr_from_spec_comments_ignored(self):
        """Test that commented lines are ignored."""
        spec = self._write_spec("""# Name: wrong
Name: mypackage
# Version: 0.5
Version: 1.0
Release: 1
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "mypackage-1.0-1")
        finally:
            spec.unlink()

    def test_nvr_from_spec_field_not_at_line_start(self):
        """Test that fields must start at the beginning of the line."""
        spec = self._write_spec("""Name: mypackage
Version: 1.0
   Release: 1
Summary: Release should not be indented
Release: 2
""")
        try:
            result = nvr_from_spec(spec)
            # Should use Release: 2 (the one at line start), not indented Release: 1
            self.assertEqual(result, "mypackage-1.0-2")
        finally:
            spec.unlink()

    def test_nvr_from_spec_case_insensitive_field_names(self):
        """Test field names are case-insensitive (spec stores as lowercase)."""
        spec = self._write_spec("""NAME: mypackage
VERSION: 1.0
RELEASE: 1
""")
        try:
            # The regex uses \1 which captures the field name, but uppercase fields
            # won't match the pattern "^(Name|Version|Release):"
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec)
            self.assertIn("missing spec fields", str(ctx.exception))
        finally:
            spec.unlink()

    def test_nvr_from_spec_multiple_values_uses_last(self):
        """Test that when a field appears twice, the last occurrence is used."""
        spec = self._write_spec("""Name: package1
Version: 1.0
Release: 1
Name: package2
Version: 2.0
Release: 2
""")
        try:
            result = nvr_from_spec(spec)
            # Should use the last occurrence of each field
            self.assertEqual(result, "package2-2.0-2")
        finally:
            spec.unlink()

    def test_nvr_from_spec_with_epoch(self):
        """Test version with epoch prefix in Release field."""
        spec = self._write_spec("""Name: mypackage
Version: 1.0
Release: 1:2
""")
        try:
            result = nvr_from_spec(spec)
            self.assertEqual(result, "mypackage-1.0-1:2")
        finally:
            spec.unlink()


if __name__ == "__main__":
    unittest.main()
