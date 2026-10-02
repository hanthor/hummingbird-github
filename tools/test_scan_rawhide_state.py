#!/usr/bin/env python3
"""Unit tests for scan_rawhide_state.py's pure parsing/diffing logic.

Deliberately excludes query() (subprocess/dnf) and the main() CLI: those
touch live infrastructure and are out of scope for a fixture-based unit test.
"""
import unittest

from scan_rawhide_state import source_name


class SourceNameTests(unittest.TestCase):
    def test_simple_package_name(self):
        self.assertEqual(
            source_name("pipewire-1.2.7-1.fc42.src.rpm"),
            "pipewire",
        )

    def test_hyphenated_package_name(self):
        # Package names may contain '-'; only the version segment starts
        # with a digit, which is what disambiguates the split.
        self.assertEqual(
            source_name("gnome-shell-46.2-1.fc42.src.rpm"),
            "gnome-shell",
        )

    def test_mixed_case_package_name(self):
        self.assertEqual(
            source_name("NetworkManager-1.48.10-1.fc42.src.rpm"),
            "NetworkManager",
        )

    def test_multiple_hyphens_in_name_and_release(self):
        self.assertEqual(
            source_name("libwayland-egl-1.23.0-2.fc42.src.rpm"),
            "libwayland-egl",
        )

    def test_unparseable_input_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            source_name("not-an-rpm")
        self.assertIn("not-an-rpm", str(ctx.exception))

    def test_missing_src_rpm_suffix_raises(self):
        with self.assertRaises(ValueError):
            source_name("pipewire-1.2.7-1.fc42.rpm")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            source_name("")


if __name__ == "__main__":
    unittest.main()
