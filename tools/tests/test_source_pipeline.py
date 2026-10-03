"""Unit tests for source_pipeline module."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add parent directory to path so we can import source_pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))
from source_pipeline import digest, fetch


class TestDigest:
    """Tests for digest() function."""

    def test_digest_sha512_simple_file(self, tmp_path):
        """Calculate correct SHA-512 digest for a simple file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        
        result = digest(test_file, "sha512")
        
        # Verify it matches the expected SHA-512
        expected = hashlib.sha512(b"hello world").hexdigest()
        assert result == expected
        assert len(result) == 128  # SHA-512 hex is 128 chars

    def test_digest_sha256_file(self, tmp_path):
        """Calculate correct SHA-256 digest."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data")
        
        result = digest(test_file, "sha256")
        
        expected = hashlib.sha256(b"test data").hexdigest()
        assert result == expected
        assert len(result) == 64  # SHA-256 hex is 64 chars

    def test_digest_large_file_streaming(self, tmp_path):
        """Stream large files in chunks to avoid loading all in memory."""
        test_file = tmp_path / "large.bin"
        # Create a 5MB file
        chunk_size = 1024 * 1024
        chunks = [b"x" * chunk_size for _ in range(5)]
        test_file.write_bytes(b"".join(chunks))
        
        result = digest(test_file, "sha512")
        
        # Verify calculation is correct
        hasher = hashlib.sha512()
        for chunk in chunks:
            hasher.update(chunk)
        expected = hasher.hexdigest()
        assert result == expected

    def test_digest_empty_file(self, tmp_path):
        """Calculate digest of an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        result = digest(test_file, "sha512")
        
        expected = hashlib.sha512(b"").hexdigest()
        assert result == expected

    def test_digest_binary_file_with_null_bytes(self, tmp_path):
        """Handle binary files with null bytes."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        
        result = digest(test_file, "sha256")
        
        expected = hashlib.sha256(b"\x00\x01\x02\xff\xfe\xfd").hexdigest()
        assert result == expected

    def test_digest_returns_lowercase_hex(self, tmp_path):
        """Return digest as lowercase hexadecimal string."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("TEST")
        
        result = digest(test_file, "sha512")
        
        assert result == result.lower()
        assert all(c in "0123456789abcdef" for c in result)

    def test_digest_invalid_algorithm_raises_error(self, tmp_path):
        """Raise error for unsupported hash algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError):
            digest(test_file, "invalid_algorithm")

    def test_digest_nonexistent_file_raises_error(self, tmp_path):
        """Raise FileNotFoundError for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            digest(nonexistent, "sha512")

    def test_digest_md5_also_supported(self, tmp_path):
        """Support MD5 algorithm (though not recommended for security)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")
        
        result = digest(test_file, "md5")
        
        expected = hashlib.md5(b"data").hexdigest()
        assert result == expected
        assert len(result) == 32


class TestFetch:
    """Tests for fetch() function."""

    @patch("source_pipeline.urllib.request.urlopen")
    @patch("source_pipeline.shutil.copyfileobj")
    def test_fetch_downloads_url_to_file(self, mock_copy, mock_urlopen, tmp_path):
        """Download URL and save to destination file."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = MagicMock()
        mock_urlopen.return_value = mock_response
        
        destination = tmp_path / "download.tar.gz"
        fetch("https://example.com/file.tar.gz", destination)
        
        # Verify copyfileobj was called (file was written)
        assert mock_copy.called

    @patch("source_pipeline.urllib.request.urlopen")
    def test_fetch_sets_user_agent(self, mock_urlopen, tmp_path):
        """Set User-Agent header in request."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = MagicMock()
        mock_urlopen.return_value = mock_response
        
        destination = tmp_path / "file.tar.gz"
        fetch("https://example.com/file.tar.gz", destination)
        
        # Get the request object
        request = mock_urlopen.call_args[0][0]
        assert "hummingbird-github-source-pipeline" in request.get_header("User-agent")

    @patch("source_pipeline.urllib.request.urlopen")
    def test_fetch_uses_60s_timeout(self, mock_urlopen, tmp_path):
        """Use 60 second timeout for downloads."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = MagicMock()
        mock_urlopen.return_value = mock_response
        
        destination = tmp_path / "file.tar.gz"
        fetch("https://example.com/file.tar.gz", destination)
        
        # Check timeout argument
        timeout_arg = mock_urlopen.call_args[1].get("timeout")
        assert timeout_arg == 60

    @patch("source_pipeline.urllib.request.urlopen")
    def test_fetch_raises_on_http_error(self, mock_urlopen, tmp_path):
        """Raise exception on HTTP errors."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com/notfound",
            404,
            "Not Found",
            {},
            None
        )
        
        destination = tmp_path / "file.tar.gz"
        with pytest.raises(urllib.error.HTTPError):
            fetch("https://example.com/notfound", destination)

    @patch("source_pipeline.urllib.request.urlopen")
    def test_fetch_raises_on_timeout(self, mock_urlopen, tmp_path):
        """Raise exception on network timeout."""
        import socket
        mock_urlopen.side_effect = socket.timeout("connection timeout")
        
        destination = tmp_path / "file.tar.gz"
        with pytest.raises(socket.timeout):
            fetch("https://example.com/slowfile", destination)

    @patch("source_pipeline.urllib.request.urlopen")
    def test_fetch_creates_destination_file(self, mock_urlopen, tmp_path):
        """Create the destination file when downloading."""
        mock_response = MagicMock()
        mock_response.__enter__.return_value = MagicMock()
        mock_urlopen.return_value = mock_response
        
        destination = tmp_path / "newfile.tar.gz"
        assert not destination.exists()
        
        # Actually test the file open call happens
        with patch("builtins.open", mock_open()) as mock_file:
            fetch("https://example.com/file.tar.gz", destination)
            mock_file.assert_called()
