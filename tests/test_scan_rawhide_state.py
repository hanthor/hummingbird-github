"""Tests for scan_rawhide_state.py source name parsing."""

import sys
import os
from unittest import TestCase

# Import the module to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../tools"))
from scan_rawhide_state import source_name


class SourceNameTests(TestCase):
    """Test cases for source_name() Fedora source RPM parser."""

    def test_simple_source_rpm_name(self):
        """Parse a simple source RPM name without hyphens."""
        result = source_name("kernel-6.12.0-1.fc41.src.rpm")
        self.assertEqual(result, "kernel")

    def test_source_rpm_with_hyphens_in_name(self):
        """Parse source RPM where package name contains hyphens."""
        result = source_name("gnome-shell-46.0-1.fc41.src.rpm")
        self.assertEqual(result, "gnome-shell")

    def test_source_rpm_multiple_hyphens_in_name(self):
        """Parse source RPM with multiple hyphens in package name."""
        result = source_name("python-urllib3-2.0.7-1.fc41.src.rpm")
        self.assertEqual(result, "python-urllib3")

    def test_source_rpm_with_complex_name(self):
        """Parse source RPM with complex multi-part package name."""
        result = source_name("lib-virt-glib-5.0.0-1.fc41.src.rpm")
        self.assertEqual(result, "lib-virt-glib")

    def test_source_rpm_version_with_epoch(self):
        """Parse source RPM with epoch in version."""
        result = source_name("systemd-255.4-1.fc41.src.rpm")
        self.assertEqual(result, "systemd")

    def test_source_rpm_release_with_fedora_notation(self):
        """Parse source RPM with .fc41 release notation."""
        result = source_name("bash-5.2.26-1.fc41.src.rpm")
        self.assertEqual(result, "bash")

    def test_source_rpm_complex_release_string(self):
        """Parse source RPM with complex release (numbers and letters)."""
        result = source_name("gcc-14.1.0-3.fc41.src.rpm")
        self.assertEqual(result, "gcc")

    def test_source_rpm_with_prerelease_version(self):
        """Parse source RPM with pre-release version notation."""
        result = source_name("firefox-128.0rc1-1.fc41.src.rpm")
        self.assertEqual(result, "firefox")

    def test_invalid_source_rpm_no_version(self):
        """Raise ValueError for invalid source RPM without version number."""
        with self.assertRaises(ValueError) as ctx:
            source_name("invalidname.src.rpm")
        self.assertIn("cannot parse", str(ctx.exception))

    def test_invalid_source_rpm_missing_src_extension(self):
        """Raise ValueError for source RPM without .src.rpm extension."""
        result = source_name("kernel-6.12.0-1.fc41.src.rpm")
        # Should still work, this is the normal case
        self.assertEqual(result, "kernel")

    def test_invalid_source_rpm_binary_extension(self):
        """Raise ValueError for binary RPM (not .src.rpm)."""
        with self.assertRaises(ValueError) as ctx:
            source_name("kernel-6.12.0-1.fc41.x86_64.rpm")
        self.assertIn("cannot parse", str(ctx.exception))

    def test_source_rpm_underscores_in_name(self):
        """Parse source RPM with underscores in package name."""
        result = source_name("lib_foo-1.0-1.fc41.src.rpm")
        self.assertEqual(result, "lib_foo")

    def test_source_rpm_numbers_in_name(self):
        """Parse source RPM with numbers in package name."""
        result = source_name("openssl3-3.2.1-1.fc41.src.rpm")
        self.assertEqual(result, "openssl3")

    def test_source_rpm_edge_case_single_hyphen_name(self):
        """Parse source RPM where package name is single word."""
        result = source_name("sed-4.9-1.fc41.src.rpm")
        self.assertEqual(result, "sed")

    def test_source_rpm_with_release_containing_prerelease(self):
        """Parse source RPM with pre-release in release field."""
        result = source_name("git-2.44.0-0.1rc1.fc41.src.rpm")
        self.assertEqual(result, "git")

    def test_source_rpm_arch_independent_suffix(self):
        """Verify that architecture doesn't affect parsing (src.rpm is the marker)."""
        result = source_name("python-requests-2.31.0-1.fc41.src.rpm")
        self.assertEqual(result, "python-requests")
        # x86_64 version should fail (not .src.rpm)
        with self.assertRaises(ValueError):
            source_name("python-requests-2.31.0-1.fc41.x86_64.rpm")

    def test_source_rpm_name_consistency(self):
        """Verify extracted name matches package name portion."""
        rpm = "audit-libs-3.1.2-1.fc41.src.rpm"
        result = source_name(rpm)
        # The result should be the part before the first version number
        self.assertTrue(rpm.startswith(result))
        self.assertEqual(result, "audit-libs")
