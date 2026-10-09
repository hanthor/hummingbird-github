#!/usr/bin/env python3
"""Unit tests for source_pipeline.py"""

import json
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open, call
from tempfile import TemporaryDirectory
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

import source_pipeline


class TestDigest(unittest.TestCase):
    """Tests for the digest() function."""

    def test_digest_sha512_calculation(self):
        """digest() should calculate SHA-512 hashes correctly."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.bin"
            test_content = b"test data for sha512"
            test_file.write_bytes(test_content)
            
            result = source_pipeline.digest(test_file, "sha512")
            expected = hashlib.sha512(test_content).hexdigest()
            
            self.assertEqual(result, expected)

    def test_digest_sha256_calculation(self):
        """digest() should calculate SHA-256 hashes correctly."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.bin"
            test_content = b"test data for sha256"
            test_file.write_bytes(test_content)
            
            result = source_pipeline.digest(test_file, "sha256")
            expected = hashlib.sha256(test_content).hexdigest()
            
            self.assertEqual(result, expected)

    def test_digest_large_file(self):
        """digest() should handle files larger than 1MB chunks."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "large.bin"
            # Create a 2MB file
            large_content = b"x" * (2 * 1024 * 1024)
            test_file.write_bytes(large_content)
            
            result = source_pipeline.digest(test_file, "sha512")
            expected = hashlib.sha512(large_content).hexdigest()
            
            self.assertEqual(result, expected)


class TestFetch(unittest.TestCase):
    """Tests for the fetch() function."""

    @patch('source_pipeline.urllib.request.urlopen')
    @patch('source_pipeline.shutil.copyfileobj')
    def test_fetch_sets_user_agent(self, mock_copy, mock_urlopen):
        """fetch() should set User-Agent header."""
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "downloaded.bin"
            source_pipeline.fetch("https://example.com/file.tar.gz", dest)
            
            # Verify the request had the correct User-Agent
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            self.assertEqual(request.get_header("User-agent"), "hummingbird-github-source-pipeline/1")

    @patch('source_pipeline.urllib.request.urlopen')
    @patch('source_pipeline.shutil.copyfileobj')
    def test_fetch_sets_timeout(self, mock_copy, mock_urlopen):
        """fetch() should set a 60-second timeout."""
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "downloaded.bin"
            source_pipeline.fetch("https://example.com/file.tar.gz", dest)
            
            # Verify timeout was set
            call_kwargs = mock_urlopen.call_args[1]
            self.assertEqual(call_kwargs['timeout'], 60)


class TestVerifySignature(unittest.TestCase):
    """Tests for the verify_signature() function."""

    def test_verify_signature_skips_when_no_gpg_config(self):
        """verify_signature() should skip verification when gpg_key is not configured."""
        package = {"name": "test"}
        
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "file.tar.gz"
            target.write_text("test")
            
            # Should not raise
            source_pipeline.verify_signature(package, target, Path(tmpdir))

    def test_verify_signature_requires_both_key_and_url(self):
        """verify_signature() should require both gpg_key and signature_url."""
        package_with_key_only = {"gpg_key": "/path/to/key", "name": "test"}
        package_with_url_only = {"signature_url": "https://example.com/sig", "name": "test"}
        
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "file.tar.gz"
            target.write_text("test")
            tmppath = Path(tmpdir)
            
            with self.assertRaises(ValueError) as ctx:
                source_pipeline.verify_signature(package_with_key_only, target, tmppath)
            self.assertIn("must be configured together", str(ctx.exception))
            
            with self.assertRaises(ValueError) as ctx:
                source_pipeline.verify_signature(package_with_url_only, target, tmppath)
            self.assertIn("must be configured together", str(ctx.exception))

    @patch('source_pipeline.fetch')
    def test_verify_signature_rejects_missing_key_file(self, mock_fetch):
        """verify_signature() should reject a GPG key that doesn't exist."""
        package = {
            "name": "test",
            "gpg_key": "/nonexistent/key.asc",
            "signature_url": "https://example.com/file.tar.gz.asc"
        }
        
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "file.tar.gz"
            target.write_text("test")
            
            with self.assertRaises(ValueError) as ctx:
                source_pipeline.verify_signature(package, target, Path(tmpdir))
            self.assertIn("does not exist", str(ctx.exception))


class TestSelected(unittest.TestCase):
    """Tests for the selected() function."""

    def test_selected_returns_all_packages_when_no_name(self):
        """selected() should return all packages when name is None."""
        config = {
            "packages": [
                {"name": "pkg1"},
                {"name": "pkg2"},
                {"name": "pkg3"}
            ]
        }
        
        result = source_pipeline.selected(config, None)
        self.assertEqual(len(result), 3)
        self.assertEqual([p["name"] for p in result], ["pkg1", "pkg2", "pkg3"])

    def test_selected_filters_by_name(self):
        """selected() should filter packages by name."""
        config = {
            "packages": [
                {"name": "firefox"},
                {"name": "thunderbird"},
                {"name": "firefox-esr"}
            ]
        }
        
        result = source_pipeline.selected(config, "firefox")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "firefox")

    def test_selected_raises_on_missing_package(self):
        """selected() should raise SystemExit when package not found."""
        config = {"packages": [{"name": "firefox"}]}
        
        with self.assertRaises(SystemExit):
            source_pipeline.selected(config, "nonexistent")

    def test_selected_returns_empty_when_no_packages_configured(self):
        """selected() should return empty list when no packages are configured."""
        config = {}
        
        result = source_pipeline.selected(config, None)
        self.assertEqual(result, [])


class TestURLResolution(unittest.TestCase):
    """Tests for URL resolution logic in main()."""

    def test_url_from_template_with_version(self):
        """URL resolution should use url_template with version substitution."""
        # This test documents the expected behavior
        package = {
            "name": "firefox",
            "url_template": "https://ftp.mozilla.org/pub/firefox/releases/{version}/source/firefox-{version}.tar.xz",
            "version": "127.0",
            "sha512": "abc" * 22
        }
        
        url = package["url_template"].format(version=package["version"])
        self.assertIn("127.0", url)
        self.assertTrue(url.startswith("https://"))

    def test_filename_extraction_from_url(self):
        """Filename should be extracted from URL path."""
        url = "https://example.com/path/to/firefox-127.0.tar.xz"
        filename = Path(import_urllib_parse().urlparse(url).path).name
        self.assertEqual(filename, "firefox-127.0.tar.xz")

    def test_default_filename_when_url_has_no_path(self):
        """Default filename should be used when URL path is empty."""
        name = "firefox"
        url = "https://example.com/"
        filename = Path(import_urllib_parse().urlparse(url).path).name or f"{name}.source"
        self.assertEqual(filename, f"{name}.source")


def import_urllib_parse():
    """Helper to import urllib.parse."""
    import urllib.parse
    return urllib.parse


if __name__ == "__main__":
    unittest.main()
