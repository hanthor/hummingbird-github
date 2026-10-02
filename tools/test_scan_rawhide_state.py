#!/usr/bin/env python3
"""Tests for scan_rawhide_state.py utilities, particularly source_name()."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scan_rawhide_state import source_name


def test_source_name_basic():
    """Parse a basic Fedora source RPM filename."""
    result = source_name("grub2-1:2.06-92.fc40.src.rpm")
    assert result == "grub2", f"expected 'grub2', got '{result}'"


def test_source_name_with_dashes_in_package_name():
    """Handle package names containing dashes."""
    result = source_name("libfoo-bar-baz-1.0-1.fc40.src.rpm")
    assert result == "libfoo-bar-baz", f"expected 'libfoo-bar-baz', got '{result}'"


def test_source_name_with_epoch():
    """Handle version strings with epoch prefix."""
    result = source_name("bash-10:5.2.26-3.fc40.src.rpm")
    assert result == "bash", f"expected 'bash', got '{result}'"


def test_source_name_complex_version():
    """Parse complex version-release strings."""
    result = source_name("postgresql-15.5-1.fc40.src.rpm")
    assert result == "postgresql", f"expected 'postgresql', got '{result}'"


def test_source_name_with_multiple_dashes_in_name():
    """Handle names like lib-foo-bar-dev."""
    result = source_name("libcurl-devel-8.6.0-1.fc40.src.rpm")
    assert result == "libcurl-devel", f"expected 'libcurl-devel', got '{result}'"


def test_source_name_single_digit_release():
    """Handle single-digit release versions."""
    result = source_name("vim-9.0.1-1.fc40.src.rpm")
    assert result == "vim", f"expected 'vim', got '{result}'"


def test_source_name_prerelease_version():
    """Handle pre-release version strings (beta, rc, etc)."""
    result = source_name("gcc-14.0.0rc1-1.fc40.src.rpm")
    assert result == "gcc", f"expected 'gcc', got '{result}'"


def test_source_name_rawhide_dist():
    """Handle rawhide distribution tag."""
    result = source_name("grub2-1:2.06-1.rawhide.fc41.src.rpm")
    assert result == "grub2", f"expected 'grub2', got '{result}'"


def test_source_name_rejects_missing_epoch():
    """Accept versions without epoch prefix."""
    result = source_name("package-1.0-1.fc40.src.rpm")
    assert result == "package", f"expected 'package', got '{result}'"


def test_source_name_underscore_in_name():
    """Handle names with underscores (though uncommon in Fedora)."""
    result = source_name("lib_foo-1.0-1.fc40.src.rpm")
    assert result == "lib_foo", f"expected 'lib_foo', got '{result}'"


def test_source_name_rejects_invalid_version_start():
    """Reject source RPMs where version doesn't start with digit."""
    try:
        source_name("package-abc-1.fc40.src.rpm")
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert "cannot parse source RPM" in str(e)


def test_source_name_rejects_no_src_suffix():
    """Reject non-source RPMs."""
    try:
        source_name("package-1.0-1.fc40.x86_64.rpm")
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert "cannot parse source RPM" in str(e)


def test_source_name_rejects_wrong_extension():
    """Reject files without .rpm extension."""
    try:
        source_name("package-1.0-1.fc40.src.tar.gz")
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert "cannot parse source RPM" in str(e)


def test_source_name_rejects_missing_name():
    """Reject RPMs with only version-release."""
    try:
        source_name("1.0-1.fc40.src.rpm")
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert "cannot parse source RPM" in str(e)


def test_source_name_long_name():
    """Handle unusually long package names."""
    result = source_name("python-libxml2-xslt-module-extra-long-name-1.0-1.fc40.src.rpm")
    assert result == "python-libxml2-xslt-module-extra-long-name"


def test_source_name_numeric_suffix():
    """Handle names ending with numbers."""
    result = source_name("mysql57-5.7.42-1.fc40.src.rpm")
    assert result == "mysql57"


def test_source_name_numeric_prefix():
    """Handle names starting with numbers (unusual but possible)."""
    result = source_name("3-to-2-1.0-1.fc40.src.rpm")
    assert result == "3-to-2"


def test_source_name_fedora_versioning():
    """Parse Fedora-specific version strings."""
    test_cases = [
        ("bash-5.2.26-3.fc40.src.rpm", "bash"),
        ("kernel-6.6.23-1.fc40.src.rpm", "kernel"),
        ("systemd-254.12-1.fc40.src.rpm", "systemd"),
        ("glibc-2.38.1-14.fc40.src.rpm", "glibc"),
    ]
    for sourcerpm, expected in test_cases:
        result = source_name(sourcerpm)
        assert result == expected, f"for {sourcerpm}: expected '{expected}', got '{result}'"


def test_source_name_many_dashes():
    """Handle package names with many consecutive dashes (edge case)."""
    # While unusual, the regex should handle this
    result = source_name("lib-foo---bar-1.0-1.fc40.src.rpm")
    assert result == "lib-foo---bar"


def test_source_name_fedora_38_through_41():
    """Test across multiple Fedora versions."""
    versions = ["38", "39", "40", "41"]
    for version in versions:
        result = source_name(f"grub2-1:2.06-92.fc{version}.src.rpm")
        assert result == "grub2"


def test_source_name_rawhide_metadata():
    """Handle rawhide-specific metadata format."""
    result = source_name("package-1.0-1.rawhide.src.rpm")
    assert result == "package"


if __name__ == "__main__":
    # Run all tests
    import inspect
    module = sys.modules[__name__]
    tests = [
        (name, func) for name, func in inspect.getmembers(module)
        if name.startswith("test_") and callable(func)
    ]

    passed = 0
    failed = 0
    for name, func in tests:
        try:
            func()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {passed + failed} tests")
    sys.exit(0 if failed == 0 else 1)
