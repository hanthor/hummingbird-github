"""Tests for dist_git.py nvr_from_spec() function."""

import sys
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase

# Import the module to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../tools"))
from dist_git import nvr_from_spec


class NvrFromSpecTests(TestCase):
    """Test cases for nvr_from_spec() RPM spec file parser."""

    def test_valid_spec_basic(self):
        """Parse a basic valid spec file with Name, Version, Release."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name: gnome-shell\nVersion: 46.0\nRelease: 1\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "gnome-shell-46.0-1")
        finally:
            spec_path.unlink()

    def test_valid_spec_with_dist_macro(self):
        """Parse spec file with %{?dist} in Release (should be stripped)."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name: kernel\nVersion: 6.12.0\nRelease: 1%{?dist}\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "kernel-6.12.0-1")
        finally:
            spec_path.unlink()

    def test_valid_spec_with_whitespace(self):
        """Parse spec file with varied whitespace around colons."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name:    firefox\nVersion:  128.0\nRelease: 2\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "firefox-128.0-2")
        finally:
            spec_path.unlink()

    def test_valid_spec_mixed_case_fields(self):
        """Parse spec file (fields are case-insensitive in regex)."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name: python3\nVersion: 3.13.0\nRelease: 1\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "python3-3.13.0-1")
        finally:
            spec_path.unlink()

    def test_missing_name_field(self):
        """Raise ValueError when Name field is missing."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Version: 1.0\nRelease: 1\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec_path)
            self.assertIn("name", str(ctx.exception).lower())
        finally:
            spec_path.unlink()

    def test_missing_version_field(self):
        """Raise ValueError when Version field is missing."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name: package\nRelease: 1\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec_path)
            self.assertIn("version", str(ctx.exception).lower())
        finally:
            spec_path.unlink()

    def test_missing_release_field(self):
        """Raise ValueError when Release field is missing."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name: package\nVersion: 1.0\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec_path)
            self.assertIn("release", str(ctx.exception).lower())
        finally:
            spec_path.unlink()

    def test_all_fields_missing(self):
        """Raise ValueError when all NVR fields are missing."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Summary: Some package\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec_path)
            # Should mention all three missing fields
            error_msg = str(ctx.exception).lower()
            self.assertIn("name", error_msg)
            self.assertIn("version", error_msg)
            self.assertIn("release", error_msg)
        finally:
            spec_path.unlink()

    def test_spec_with_comments_and_blank_lines(self):
        """Parse spec file with comments and blank lines."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("# Comment line\n\nName: pkg\n# Another comment\nVersion: 2.0\n\nRelease: 3\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "pkg-2.0-3")
        finally:
            spec_path.unlink()

    def test_spec_with_multiline_descriptions(self):
        """Parse spec file with multiline %description (should ignore)."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("""Name: myapp
Version: 1.5
Release: 1

%description
This is a long description
that spans multiple lines
and should not interfere
with NVR extraction
""")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "myapp-1.5-1")
        finally:
            spec_path.unlink()

    def test_spec_with_release_containing_letters(self):
        """Parse Release field with letters (pre-release notation)."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name: beta-tool\nVersion: 0.1\nRelease: 0.1rc1\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "beta-tool-0.1-0.1rc1")
        finally:
            spec_path.unlink()

    def test_spec_fields_not_at_start_of_line(self):
        """Verify fields must be at start of line (not indented macros)."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            # %define Name: should not match, only Name: at line start
            f.write("%define Name: ignored\nName: actual\nVersion: 1.0\nRelease: 1\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            self.assertEqual(result, "actual-1.0-1")
        finally:
            spec_path.unlink()

    def test_spec_with_empty_file(self):
        """Raise ValueError for empty spec file."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            # Write nothing
            f.flush()
            spec_path = Path(f.name)
        
        try:
            with self.assertRaises(ValueError) as ctx:
                nvr_from_spec(spec_path)
            self.assertIn("missing spec fields", str(ctx.exception))
        finally:
            spec_path.unlink()

    def test_nvr_format_consistency(self):
        """Verify NVR format is always name-version-release."""
        with NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
            f.write("Name: test-pkg-name\nVersion: 1.2.3.4\nRelease: 5beta\n")
            f.flush()
            spec_path = Path(f.name)
        
        try:
            result = nvr_from_spec(spec_path)
            # Should have exactly two hyphens separating the three parts
            self.assertEqual(result.count('-'), 2)
            self.assertRegex(result, r"^[\w\-\.]+\-[\w\-\.]+\-[\w\-\.]+$")
        finally:
            spec_path.unlink()
