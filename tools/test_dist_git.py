#!/usr/bin/env python3
"""Unit tests for dist_git.py's pure spec-parsing logic.

Deliberately excludes koji_complete() (network), command() (subprocess), and
the main() CLI (git clone + network): those touch live infrastructure and are
out of scope for a fixture-based unit test.
"""
import tempfile
import unittest
from pathlib import Path

from dist_git import nvr_from_spec


class NvrFromSpecTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.spec_path = Path(self._tmp.name) / "package.spec"

    def _write(self, content: str) -> Path:
        self.spec_path.write_text(content)
        return self.spec_path

    def test_extracts_name_version_release(self):
        spec = self._write(
            "Name: pipewire\n"
            "Version: 1.2.7\n"
            "Release: 1%{?dist}\n"
            "Summary: A low-latency audio/video router\n"
        )
        self.assertEqual(nvr_from_spec(spec), "pipewire-1.2.7-1")

    def test_strips_dist_macro_from_release(self):
        spec = self._write(
            "Name: gnome-shell\n"
            "Version: 46.2\n"
            "Release: 3%{?dist}\n"
        )
        self.assertEqual(nvr_from_spec(spec), "gnome-shell-46.2-3")

    def test_release_without_dist_macro(self):
        spec = self._write(
            "Name: foo\n"
            "Version: 1.0\n"
            "Release: 2\n"
        )
        self.assertEqual(nvr_from_spec(spec), "foo-1.0-2")

    def test_fields_can_appear_in_any_order(self):
        spec = self._write(
            "Release: 1%{?dist}\n"
            "Name: foo\n"
            "Summary: irrelevant\n"
            "Version: 1.0\n"
        )
        self.assertEqual(nvr_from_spec(spec), "foo-1.0-1")

    def test_missing_release_raises_with_field_name(self):
        spec = self._write(
            "Name: foo\n"
            "Version: 1.0\n"
        )
        with self.assertRaises(ValueError) as ctx:
            nvr_from_spec(spec)
        self.assertIn("release", str(ctx.exception))

    def test_missing_all_fields_raises_with_all_names(self):
        spec = self._write("Summary: nothing useful here\n")
        with self.assertRaises(ValueError) as ctx:
            nvr_from_spec(spec)
        message = str(ctx.exception)
        self.assertIn("name", message)
        self.assertIn("version", message)
        self.assertIn("release", message)

    def test_ignores_unrelated_fields(self):
        spec = self._write(
            "Name: foo\n"
            "Version: 1.0\n"
            "Release: 1\n"
            "License: MIT\n"
            "URL: https://example.invalid/foo\n"
        )
        self.assertEqual(nvr_from_spec(spec), "foo-1.0-1")

    def test_non_utf8_bytes_do_not_crash(self):
        # errors="replace" is load-bearing: some Fedora specs carry latin-1
        # changelog entries. A byte sequence that is invalid UTF-8 must not
        # raise UnicodeDecodeError.
        spec = self.spec_path
        spec.write_bytes(
            b"Name: foo\nVersion: 1.0\nRelease: 1\n"
            b"# changelog note with a stray byte: \xe9\n"
        )
        self.assertEqual(nvr_from_spec(spec), "foo-1.0-1")


if __name__ == "__main__":
    unittest.main()
