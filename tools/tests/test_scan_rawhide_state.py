"""Test suite for scan_rawhide_state.py utilities."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scan_rawhide_state import source_name


class TestSourceName:
    """Test cases for source_name() Fedora source RPM parser."""

    def test_parse_valid_source_rpm(self):
        """Extract source package name from valid source RPM filename."""
        assert source_name("nginx-1.24.0-1.fc39.src.rpm") == "nginx"

    def test_parse_source_rpm_with_dash_in_name(self):
        """Handle package names containing dashes."""
        assert source_name("perl-IO-Socket-SSL-2.083-1.fc39.src.rpm") == "perl-IO-Socket-SSL"
        assert source_name("python-setuptools-scm-7.1.0-1.fc39.src.rpm") == "python-setuptools-scm"

    def test_parse_source_rpm_with_epoch(self):
        """Handle source RPMs with epoch numbers."""
        assert source_name("perl-5.10:5.38.0-1.fc39.src.rpm") == "perl"

    def test_parse_source_rpm_complex_version(self):
        """Handle complex Fedora version strings."""
        assert source_name("glibc-2.37.20230825-1.fc40.src.rpm") == "glibc"
        assert source_name("gcc-13.2.1-1.fc39.src.rpm") == "gcc"

    def test_parse_source_rpm_with_rc_or_beta(self):
        """Handle pre-release version strings."""
        assert source_name("kernel-6.5.0-0.rc1.1.fc40.src.rpm") == "kernel"
        assert source_name("firefox-120.0-0.1.beta.1.fc39.src.rpm") == "firefox"

    def test_parse_source_rpm_single_name(self):
        """Handle single-word package names."""
        assert source_name("vim-9.0.1234-1.fc39.src.rpm") == "vim"
        assert source_name("git-2.42.0-1.fc39.src.rpm") == "git"

    def test_parse_invalid_source_rpm_missing_src(self):
        """Raise ValueError for filenames not ending in .src.rpm."""
        with pytest.raises(ValueError, match="cannot parse source RPM"):
            source_name("nginx-1.24.0-1.fc39.rpm")

    def test_parse_invalid_source_rpm_wrong_format(self):
        """Raise ValueError for files not matching source RPM pattern."""
        with pytest.raises(ValueError, match="cannot parse source RPM"):
            source_name("nginx.src.rpm")

    def test_parse_invalid_source_rpm_no_version_digit(self):
        """Raise ValueError when version doesn't start with digit."""
        with pytest.raises(ValueError, match="cannot parse source RPM"):
            source_name("nginx-ver-1.fc39.src.rpm")

    def test_parse_invalid_source_rpm_too_few_dashes(self):
        """Raise ValueError when format doesn't match NVR-R pattern."""
        with pytest.raises(ValueError, match="cannot parse source RPM"):
            source_name("nginx-1.src.rpm")

    def test_parse_real_fedora_examples(self):
        """Test with real Fedora package names."""
        real_examples = [
            ("util-linux-2.38.1-1.fc39.src.rpm", "util-linux"),
            ("bash-5.2.15-4.fc39.src.rpm", "bash"),
            ("openssh-9.3-1.fc39.src.rpm", "openssh"),
            ("bind-9.16.44-3.fc39.src.rpm", "bind"),
            ("libreoffice-7.6.2.1-1.fc39.src.rpm", "libreoffice"),
            ("bind-dynamic-db-1.0-1.fc39.src.rpm", "bind-dynamic-db"),
        ]
        for sourcerpm, expected_name in real_examples:
            assert source_name(sourcerpm) == expected_name
