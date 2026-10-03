"""Unit tests for dist_git module."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path so we can import dist_git
sys.path.insert(0, str(Path(__file__).parent.parent))
from dist_git import koji_complete, nvr_from_spec


class TestNvrFromSpec:
    """Tests for nvr_from_spec() function."""

    def test_valid_spec_with_basic_fields(self, tmp_path):
        """Extract NVR from a valid spec file with basic name, version, release."""
        spec_file = tmp_path / "test.spec"
        spec_file.write_text("""
Name:          test-package
Version:       1.0.0
Release:       1%{?dist}
Summary:       Test package
        """)
        
        result = nvr_from_spec(spec_file)
        assert result == "test-package-1.0.0-1"

    def test_nvr_with_complex_version_release(self, tmp_path):
        """Handle versions and releases with special characters."""
        spec_file = tmp_path / "complex.spec"
        spec_file.write_text("""
Name:          kernel
Version:       6.5.0
Release:       12.fc40%{?dist}
Summary:       Kernel
        """)
        
        result = nvr_from_spec(spec_file)
        assert result == "kernel-6.5.0-12.fc40"

    def test_nvr_strips_dist_suffix(self, tmp_path):
        """Strip %{?dist} suffix from release field."""
        spec_file = tmp_path / "dist.spec"
        spec_file.write_text("""
Name:          myapp
Version:       2.1
Release:       5%{?dist}
        """)
        
        result = nvr_from_spec(spec_file)
        assert result == "myapp-2.1-5"
        assert "%{?dist}" not in result

    def test_nvr_missing_name_field(self, tmp_path):
        """Raise ValueError when Name field is missing."""
        spec_file = tmp_path / "missing_name.spec"
        spec_file.write_text("""
Version:       1.0
Release:       1
        """)
        
        with pytest.raises(ValueError, match="missing spec fields.*name"):
            nvr_from_spec(spec_file)

    def test_nvr_missing_version_field(self, tmp_path):
        """Raise ValueError when Version field is missing."""
        spec_file = tmp_path / "missing_version.spec"
        spec_file.write_text("""
Name:          test
Release:       1
        """)
        
        with pytest.raises(ValueError, match="missing spec fields.*version"):
            nvr_from_spec(spec_file)

    def test_nvr_missing_release_field(self, tmp_path):
        """Raise ValueError when Release field is missing."""
        spec_file = tmp_path / "missing_release.spec"
        spec_file.write_text("""
Name:          test
Version:       1.0
        """)
        
        with pytest.raises(ValueError, match="missing spec fields.*release"):
            nvr_from_spec(spec_file)

    def test_nvr_multiple_missing_fields(self, tmp_path):
        """List all missing fields in error message."""
        spec_file = tmp_path / "empty.spec"
        spec_file.write_text("")
        
        with pytest.raises(ValueError, match="missing spec fields"):
            nvr_from_spec(spec_file)
        # Verify error mentions all three fields (exact order may vary)
        with pytest.raises(ValueError) as exc_info:
            nvr_from_spec(spec_file)
        error_msg = str(exc_info.value)
        assert "name" in error_msg
        assert "version" in error_msg
        assert "release" in error_msg

    def test_nvr_fields_case_insensitive(self, tmp_path):
        """Handle spec fields with different casing."""
        spec_file = tmp_path / "case.spec"
        spec_file.write_text("""
NAME:          app
VERSION:       1.0
RELEASE:       1
        """)
        
        # Should NOT work - spec fields are case-sensitive in practice
        # This test documents the current behavior
        with pytest.raises(ValueError):
            nvr_from_spec(spec_file)

    def test_nvr_with_whitespace_variations(self, tmp_path):
        """Handle variable whitespace around field values."""
        spec_file = tmp_path / "whitespace.spec"
        spec_file.write_text("""
Name:    padded-name
Version:           1.0.0
Release:  1%{?dist}
        """)
        
        result = nvr_from_spec(spec_file)
        assert result == "padded-name-1.0.0-1"

    def test_nvr_ignores_comments_and_metadata(self, tmp_path):
        """Ignore comments and metadata lines, extract only NVR fields."""
        spec_file = tmp_path / "full.spec"
        spec_file.write_text("""
%define myvar value

Name:          mypackage
Summary:       This is a test
Version:       2.0.0
License:       MIT
Release:       10%{?dist}
URL:           https://example.com
%description
A test package.
        """)
        
        result = nvr_from_spec(spec_file)
        assert result == "mypackage-2.0.0-10"

    def test_nvr_with_spec_macros_in_name(self, tmp_path):
        """Handle spec files where name contains valid characters."""
        spec_file = tmp_path / "macro.spec"
        spec_file.write_text("""
Name:          lib-c++
Version:       1.0
Release:       1%{?dist}
        """)
        
        result = nvr_from_spec(spec_file)
        assert result == "lib-c++-1.0-1"

    def test_nvr_handles_encoding_errors_gracefully(self, tmp_path):
        """Handle spec files with encoding errors by replacing invalid chars."""
        spec_file = tmp_path / "binary.spec"
        # Write some binary data that's not valid UTF-8
        spec_file.write_bytes(b"""
Name:          good-name
Version:       1.0
Release:       1\xff\xfe
        """)
        
        # Should not raise, uses errors='replace'
        result = nvr_from_spec(spec_file)
        assert "good-name" in result


class TestKojiComplete:
    """Tests for koji_complete() function."""

    @patch("dist_git.urllib.request.urlopen")
    def test_koji_complete_returns_true_for_completed_build(self, mock_urlopen):
        """Return True when Koji reports a completed build."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps({
            "result": {"state": 1}  # Koji BUILD_STATES[COMPLETE]
        }).encode()
        mock_urlopen.return_value = mock_response
        
        result = koji_complete("mypackage-1.0-1.fc40")
        assert result is True

    @patch("dist_git.urllib.request.urlopen")
    def test_koji_complete_returns_false_for_building(self, mock_urlopen):
        """Return False when Koji reports build is not completed."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps({
            "result": {"state": 0}  # Koji BUILD_STATES[BUILDING]
        }).encode()
        mock_urlopen.return_value = mock_response
        
        result = koji_complete("mypackage-1.0-1.fc40")
        assert result is False

    @patch("dist_git.urllib.request.urlopen")
    def test_koji_complete_returns_false_for_nonexistent_build(self, mock_urlopen):
        """Return False when build doesn't exist in Koji."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps({
            "result": None
        }).encode()
        mock_urlopen.return_value = mock_response
        
        result = koji_complete("nonexistent-1.0-1.fc40")
        assert result is False

    @patch("dist_git.urllib.request.urlopen")
    def test_koji_complete_uses_correct_endpoint(self, mock_urlopen):
        """Make request to correct Koji JSON-RPC endpoint."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps({
            "result": {"state": 1}
        }).encode()
        mock_urlopen.return_value = mock_response
        
        koji_complete("test-1.0-1")
        
        # Verify the endpoint was called
        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        # Check that the URL contains the Koji endpoint
        assert "koji.fedoraproject.org/kojihub" in str(call_args)

    @patch("dist_git.urllib.request.urlopen")
    def test_koji_complete_sends_correct_method(self, mock_urlopen):
        """Send correct JSON-RPC method name to Koji."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps({
            "result": {"state": 1}
        }).encode()
        mock_urlopen.return_value = mock_response
        
        koji_complete("test-1.0-1")
        
        # Get the request object that was passed
        request = mock_urlopen.call_args[0][0]
        data = json.loads(request.data.decode())
        assert data["method"] == "getBuild"
        assert data["params"] == ["test-1.0-1"]
