"""Test suite for source_pipeline.py utilities."""

import hashlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from source_pipeline import digest, selected


class TestDigest:
    """Test cases for digest() file hashing utility."""

    def test_digest_sha512_small_file(self):
        """Calculate SHA-512 hash of a small file."""
        content = b"Hello, World!"
        expected = hashlib.sha512(content).hexdigest()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            filepath.write_bytes(content)
            result = digest(filepath, "sha512")
            assert result == expected

    def test_digest_sha256_small_file(self):
        """Calculate SHA-256 hash of a small file."""
        content = b"Test content"
        expected = hashlib.sha256(content).hexdigest()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            filepath.write_bytes(content)
            result = digest(filepath, "sha256")
            assert result == expected

    def test_digest_large_file(self):
        """Handle large files with chunked reading."""
        # Create a file larger than the 1MB chunk size
        content = b"x" * (2 * 1024 * 1024 + 500)
        expected = hashlib.sha512(content).hexdigest()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "large.bin"
            filepath.write_bytes(content)
            result = digest(filepath, "sha512")
            assert result == expected

    def test_digest_empty_file(self):
        """Handle empty files correctly."""
        content = b""
        expected = hashlib.sha512(content).hexdigest()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.txt"
            filepath.write_bytes(content)
            result = digest(filepath, "sha512")
            assert result == expected

    def test_digest_binary_file(self):
        """Calculate hash of binary file with various byte values."""
        content = bytes(range(256))
        expected = hashlib.sha512(content).hexdigest()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "binary.bin"
            filepath.write_bytes(content)
            result = digest(filepath, "sha512")
            assert result == expected

    def test_digest_different_algorithms(self):
        """Hash same content with different algorithms produces different results."""
        content = b"Test content for hashing"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            filepath.write_bytes(content)
            
            sha256_result = digest(filepath, "sha256")
            sha512_result = digest(filepath, "sha512")
            md5_result = digest(filepath, "md5")
            
            # All three should be different
            assert sha256_result != sha512_result
            assert sha256_result != md5_result
            assert sha512_result != md5_result
            
            # Verify they're valid hex strings
            assert len(sha256_result) == 64  # SHA-256 in hex is 64 chars
            assert len(sha512_result) == 128  # SHA-512 in hex is 128 chars
            assert len(md5_result) == 32  # MD5 in hex is 32 chars


class TestSelected:
    """Test cases for selected() config package selection."""

    def test_selected_all_packages_when_name_is_none(self):
        """Return all packages when name parameter is None."""
        config = {
            "packages": [
                {"name": "pkg1", "url": "http://example.com/pkg1"},
                {"name": "pkg2", "url": "http://example.com/pkg2"},
                {"name": "pkg3", "url": "http://example.com/pkg3"},
            ]
        }
        result = selected(config, None)
        assert len(result) == 3
        assert result == config["packages"]

    def test_selected_specific_package(self):
        """Return only the named package."""
        config = {
            "packages": [
                {"name": "pkg1", "url": "http://example.com/pkg1"},
                {"name": "pkg2", "url": "http://example.com/pkg2"},
                {"name": "pkg3", "url": "http://example.com/pkg3"},
            ]
        }
        result = selected(config, "pkg2")
        assert len(result) == 1
        assert result[0]["name"] == "pkg2"

    def test_selected_nonexistent_package_exits(self):
        """Raise SystemExit when named package not found."""
        config = {
            "packages": [
                {"name": "pkg1", "url": "http://example.com/pkg1"},
                {"name": "pkg2", "url": "http://example.com/pkg2"},
            ]
        }
        with pytest.raises(SystemExit):
            selected(config, "nonexistent")

    def test_selected_empty_config(self):
        """Handle config with no packages."""
        config = {}
        result = selected(config, None)
        assert result == []

    def test_selected_empty_packages_list_exits(self):
        """Raise SystemExit when packages list is empty and name given."""
        config = {"packages": []}
        with pytest.raises(SystemExit):
            selected(config, "any")

    def test_selected_case_sensitive(self):
        """Package selection is case-sensitive."""
        config = {
            "packages": [
                {"name": "Pkg1", "url": "http://example.com/pkg1"},
                {"name": "pkg1", "url": "http://example.com/pkg1-lower"},
            ]
        }
        result = selected(config, "pkg1")
        assert len(result) == 1
        assert result[0]["url"] == "http://example.com/pkg1-lower"
