#!/usr/bin/env python3
"""Unit tests for scan_rawhide_state.py's source_name() function."""

import unittest
from tools.scan_rawhide_state import source_name


class TestSourceName(unittest.TestCase):
    """Test source RPM name parsing."""

    def test_source_name_basic(self):
        """Test basic source RPM name extraction."""
        result = source_name("bash-5.2.26-1.fc40.src.rpm")
        self.assertEqual(result, "bash")

    def test_source_name_hyphenated_package(self):
        """Test package name with hyphens."""
        result = source_name("python3-requests-2.31.0-1.fc40.src.rpm")
        self.assertEqual(result, "python3-requests")

    def test_source_name_multiple_hyphens(self):
        """Test package name with multiple hyphens."""
        result = source_name("perl-YAML-Syck-1.34-2.fc40.src.rpm")
        self.assertEqual(result, "perl-YAML-Syck")

    def test_source_name_version_with_dots(self):
        """Test version string with multiple dots."""
        result = source_name("openssl-3.1.4-1.fc40.src.rpm")
        self.assertEqual(result, "openssl")

    def test_source_name_version_with_rc(self):
        """Test version with release candidate suffix."""
        result = source_name("gcc-13.2.1-3.fc40.src.rpm")
        self.assertEqual(result, "gcc")

    def test_source_name_complex_version(self):
        """Test complex version with multiple components."""
        result = source_name("glibc-2.38.1-13.fc40.src.rpm")
        self.assertEqual(result, "glibc")

    def test_source_name_date_based_version(self):
        """Test date-based version strings."""
        result = source_name("java-21.0.1-11.fc40.src.rpm")
        self.assertEqual(result, "java")

    def test_source_name_prerelease_version(self):
        """Test pre-release version strings."""
        result = source_name("kernel-6.6.0-1.fc40.src.rpm")
        self.assertEqual(result, "kernel")

    def test_source_name_epoch_version(self):
        """Test version with epoch prefix."""
        result = source_name("glibc-2:2.38.1-1.fc40.src.rpm")
        self.assertEqual(result, "glibc")

    def test_source_name_single_digit_release(self):
        """Test single-digit release number."""
        result = source_name("vim-9.0.1234-1.fc40.src.rpm")
        self.assertEqual(result, "vim")

    def test_source_name_high_release_number(self):
        """Test high release number."""
        result = source_name("httpd-2.4.57-99.fc40.src.rpm")
        self.assertEqual(result, "httpd")

    def test_source_name_dist_fc39(self):
        """Test different Fedora dist version."""
        result = source_name("sqlite-3.43.2-1.fc39.src.rpm")
        self.assertEqual(result, "sqlite")

    def test_source_name_dist_fc41(self):
        """Test Fedora 41 (future) dist version."""
        result = source_name("zsh-5.9-2.fc41.src.rpm")
        self.assertEqual(result, "zsh")

    def test_source_name_invalid_no_src_suffix(self):
        """Test error on non-source RPM."""
        with self.assertRaises(ValueError) as ctx:
            source_name("bash-5.2.26-1.fc40.x86_64.rpm")
        self.assertIn("cannot parse source RPM", str(ctx.exception))

    def test_source_name_invalid_missing_version(self):
        """Test error on missing version."""
        with self.assertRaises(ValueError) as ctx:
            source_name("bash.src.rpm")
        self.assertIn("cannot parse source RPM", str(ctx.exception))

    def test_source_name_invalid_no_release(self):
        """Test error on missing release number."""
        with self.assertRaises(ValueError) as ctx:
            source_name("bash-5.2.26.fc40.src.rpm")
        self.assertIn("cannot parse source RPM", str(ctx.exception))

    def test_source_name_invalid_version_starts_with_letter(self):
        """Test error when version starts with letter (not digit)."""
        with self.assertRaises(ValueError) as ctx:
            source_name("bash-v5.2.26-1.fc40.src.rpm")
        self.assertIn("cannot parse source RPM", str(ctx.exception))

    def test_source_name_invalid_empty_string(self):
        """Test error on empty string."""
        with self.assertRaises(ValueError) as ctx:
            source_name("")
        self.assertIn("cannot parse source RPM", str(ctx.exception))

    def test_source_name_invalid_malformed_name(self):
        """Test error on completely malformed input."""
        with self.assertRaises(ValueError) as ctx:
            source_name("not-a-valid-rpm-filename")
        self.assertIn("cannot parse source RPM", str(ctx.exception))

    def test_source_name_long_package_name(self):
        """Test long package name with many hyphens."""
        result = source_name("python3-dbus-common-bridge-1.2.3-4.fc40.src.rpm")
        self.assertEqual(result, "python3-dbus-common-bridge")

    def test_source_name_package_name_with_dots_in_number(self):
        """Test version with dots followed by release."""
        result = source_name("libreoffice-24.2.1.2-1.fc40.src.rpm")
        self.assertEqual(result, "libreoffice")


if __name__ == "__main__":
    unittest.main()
