#!/usr/bin/env python3
"""Unit tests for recalculate_hummingbird_gaps.py's lines() function."""

import unittest
import tempfile
from pathlib import Path
from tools.recalculate_hummingbird_gaps import lines


class TestLines(unittest.TestCase):
    """Test line reading and filtering from package files."""

    def _write_file(self, content: str) -> Path:
        """Helper: write content to a temporary file."""
        fd, path = tempfile.mkstemp(text=True)
        try:
            Path(path).write_text(content)
        finally:
            import os
            os.close(fd)
        return Path(path)

    def test_lines_basic(self):
        """Test basic line reading."""
        file = self._write_file("package1\npackage2\npackage3\n")
        try:
            result = lines(file)
            self.assertEqual(result, {"package1", "package2", "package3"})
        finally:
            file.unlink()

    def test_lines_with_comments(self):
        """Test that lines starting with # are filtered out."""
        file = self._write_file("""package1
# This is a comment
package2
#Another comment
package3
""")
        try:
            result = lines(file)
            self.assertEqual(result, {"package1", "package2", "package3"})
        finally:
            file.unlink()

    def test_lines_with_empty_lines(self):
        """Test that empty lines are filtered out."""
        file = self._write_file("""package1

package2

package3
""")
        try:
            result = lines(file)
            self.assertEqual(result, {"package1", "package2", "package3"})
        finally:
            file.unlink()

    def test_lines_with_whitespace_trimming(self):
        """Test that leading/trailing whitespace is trimmed."""
        file = self._write_file("""  package1  
    package2
package3    
""")
        try:
            result = lines(file)
            self.assertEqual(result, {"package1", "package2", "package3"})
        finally:
            file.unlink()

    def test_lines_mixed_content(self):
        """Test file with mix of packages, comments, and whitespace."""
        file = self._write_file("""# Fedora packages
bash
  coreutils  

# Development tools
gcc
  python3  
# Build system
make

""")
        try:
            result = lines(file)
            self.assertEqual(result, {"bash", "coreutils", "gcc", "python3", "make"})
        finally:
            file.unlink()

    def test_lines_empty_file(self):
        """Test that an empty file returns empty set."""
        file = self._write_file("")
        try:
            result = lines(file)
            self.assertEqual(result, set())
        finally:
            file.unlink()

    def test_lines_only_comments(self):
        """Test file with only comments returns empty set."""
        file = self._write_file("""# Comment 1
# Comment 2
# Comment 3
""")
        try:
            result = lines(file)
            self.assertEqual(result, set())
        finally:
            file.unlink()

    def test_lines_only_whitespace(self):
        """Test file with only whitespace returns empty set."""
        file = self._write_file("""

  
	
""")
        try:
            result = lines(file)
            self.assertEqual(result, set())
        finally:
            file.unlink()

    def test_lines_package_names_with_hyphens(self):
        """Test package names containing hyphens."""
        file = self._write_file("""python3-requests
python3-dbus
perl-YAML-Syck
""")
        try:
            result = lines(file)
            self.assertEqual(result, {"python3-requests", "python3-dbus", "perl-YAML-Syck"})
        finally:
            file.unlink()

    def test_lines_package_names_with_numbers(self):
        """Test package names containing numbers."""
        file = self._write_file("""gcc13
python311
perl5
""")
        try:
            result = lines(file)
            self.assertEqual(result, {"gcc13", "python311", "perl5"})
        finally:
            file.unlink()

    def test_lines_duplicates_deduplicated(self):
        """Test that duplicate packages are deduplicated (set behavior)."""
        file = self._write_file("""bash
coreutils
bash
python3
coreutils
""")
        try:
            result = lines(file)
            self.assertEqual(result, {"bash", "coreutils", "python3"})
        finally:
            file.unlink()

    def test_lines_tab_separated_content(self):
        """Test lines with tabs are preserved."""
        file = self._write_file("""package1\t# with comment
package2	# tab-separated
""")
        try:
            result = lines(file)
            # Tabs are preserved in the package name, not stripped
            self.assertEqual(len(result), 2)
            # At least one package should have a tab
            self.assertTrue(any('\t' in pkg for pkg in result))
        finally:
            file.unlink()

    def test_lines_inline_comments_not_stripped(self):
        """Test that inline comments (not at line start) are not stripped."""
        file = self._write_file("""package1  # this is not stripped
package2
""")
        try:
            result = lines(file)
            # The line gets trimmed, so "package1  # this is not stripped" becomes that
            # But the function only strips whitespace, not inline comments
            self.assertIn("package2", result)
            # One entry should have the comment text
            has_comment = any('#' in pkg for pkg in result)
            self.assertTrue(has_comment)
        finally:
            file.unlink()

    def test_lines_very_long_package_name(self):
        """Test handling of very long package names."""
        long_name = "a" * 1000
        file = self._write_file(f"{long_name}\n")
        try:
            result = lines(file)
            self.assertEqual(result, {long_name})
        finally:
            file.unlink()

    def test_lines_special_characters_in_names(self):
        """Test package names with special characters (allowed in package names)."""
        file = self._write_file("""lib++-devtools
python-dateutil
perl-DBI-DBD
""")
        try:
            result = lines(file)
            self.assertEqual(result, {"lib++-devtools", "python-dateutil", "perl-DBI-DBD"})
        finally:
            file.unlink()


if __name__ == "__main__":
    unittest.main()
