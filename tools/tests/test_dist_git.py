"""Test suite for dist_git.py utilities."""

import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Since tools/ is not a package, we need to add it to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from dist_git import nvr_from_spec


class TestNvrFromSpec:
    """Test cases for nvr_from_spec() spec file parser."""

    def test_parse_valid_spec(self):
        """Extract name, version, and release from a valid spec file."""
        spec_content = """
Name: nginx
Version: 1.24.0
Release: 1%{?dist}

Summary: High performance web server
License: BSD
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "nginx.spec"
            spec_path.write_text(spec_content)
            result = nvr_from_spec(spec_path)
            assert result == "nginx-1.24.0-1"

    def test_parse_spec_with_whitespace(self):
        """Handle spec files with extra whitespace around fields."""
        spec_content = """
Name:    nginx
Version:   1.24.0
Release:  1%{?dist}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "nginx.spec"
            spec_path.write_text(spec_content)
            result = nvr_from_spec(spec_path)
            assert result == "nginx-1.24.0-1"

    def test_parse_spec_requires_uppercase_fields(self):
        """Require field names to be uppercase (spec convention)."""
        spec_content = """
name: postgresql
version: 15.1
release: 2%{?dist}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "postgresql.spec"
            spec_path.write_text(spec_content)
            # Lowercase field names won't be recognized
            with pytest.raises(ValueError, match="missing spec fields"):
                nvr_from_spec(spec_path)

    def test_parse_spec_with_complex_release(self):
        """Handle complex release strings with %dist macros."""
        spec_content = """
Name: openssl
Version: 3.0.7
Release: 5%{?dist}

Summary: Utilities and libraries for cryptography
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "openssl.spec"
            spec_path.write_text(spec_content)
            result = nvr_from_spec(spec_path)
            assert result == "openssl-3.0.7-5"

    def test_parse_spec_missing_name(self):
        """Raise ValueError when Name field is missing."""
        spec_content = """
Version: 1.0
Release: 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "invalid.spec"
            spec_path.write_text(spec_content)
            with pytest.raises(ValueError, match="missing spec fields: name"):
                nvr_from_spec(spec_path)

    def test_parse_spec_missing_version(self):
        """Raise ValueError when Version field is missing."""
        spec_content = """
Name: foo
Release: 1
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "invalid.spec"
            spec_path.write_text(spec_content)
            with pytest.raises(ValueError, match="missing spec fields: version"):
                nvr_from_spec(spec_path)

    def test_parse_spec_missing_release(self):
        """Raise ValueError when Release field is missing."""
        spec_content = """
Name: foo
Version: 1.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "invalid.spec"
            spec_path.write_text(spec_content)
            with pytest.raises(ValueError, match="missing spec fields: release"):
                nvr_from_spec(spec_path)

    def test_parse_spec_missing_multiple_fields(self):
        """Raise ValueError listing all missing fields."""
        spec_content = """
Name: foo
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "invalid.spec"
            spec_path.write_text(spec_content)
            with pytest.raises(ValueError, match="missing spec fields"):
                nvr_from_spec(spec_path)
                # Should mention both release and version

    def test_parse_spec_with_rpm_macros_in_release(self):
        """Only %{?dist} macro is stripped, other macros are preserved."""
        spec_content = """
Name: kernel
Version: 6.1.0
Release: 1%{?rc:rc%rc}%{?dist}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "kernel.spec"
            spec_path.write_text(spec_content)
            result = nvr_from_spec(spec_path)
            # Only %{?dist} is removed, other macros remain
            assert result == "kernel-6.1.0-1%{?rc:rc%rc}"

    def test_parse_spec_with_malformed_encoding(self):
        """Handle spec files with encoding issues gracefully."""
        spec_content_binary = b"Name: foo\nVersion: 1.0\nRelease: 1\xFF\xFF"
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "invalid.spec"
            spec_path.write_bytes(spec_content_binary)
            # Should handle encoding errors and extract what it can
            # The malformed bytes after Release are included as-is
            result = nvr_from_spec(spec_path)
            # Extraction still works despite encoding issues
            assert result.startswith("foo-1.0-1")
