#!/usr/bin/env python3
"""Tests for dist_git.py utilities, particularly nvr_from_spec()."""

import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from dist_git import nvr_from_spec


def test_nvr_from_spec_basic():
    """Parse a basic spec file with Name, Version, Release."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: test-package
Version: 1.0
Release: 1
Summary: A test package
License: MIT
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "test-package-1.0-1", f"expected 'test-package-1.0-1', got '{result}'"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_with_dist_macro():
    """Strip %{?dist} from Release field."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: my-package
Version: 2.1
Release: 5%{?dist}
Summary: Package with dist macro
License: GPL
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "my-package-2.1-5", f"expected 'my-package-2.1-5', got '{result}'"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_whitespace_handling():
    """Handle leading/trailing whitespace in spec fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name:   padded-name   
Version:  3.5  
Release:   2   
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "padded-name-3.5-2", f"expected 'padded-name-3.5-2', got '{result}'"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_hyphenated_names():
    """Handle package names with hyphens and numbers."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: lib-test-3-core
Version: 10.1.5
Release: 27
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "lib-test-3-core-10.1.5-27", f"expected 'lib-test-3-core-10.1.5-27', got '{result}'"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_version_with_dots():
    """Handle versions with multiple dots."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: complex-version
Version: 2023.10.15.1
Release: 1
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "complex-version-2023.10.15.1-1"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_release_with_date():
    """Handle Release field with date-based format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: time-release
Version: 1.0
Release: 20230928.1
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "time-release-1.0-20230928.1"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_missing_name():
    """Raise ValueError when Name is missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Version: 1.0
Release: 1
Summary: Missing name
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        try:
            nvr_from_spec(spec_path)
            assert False, "should have raised ValueError"
        except ValueError as e:
            assert "name" in str(e).lower(), f"error should mention missing 'name': {e}"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_missing_version():
    """Raise ValueError when Version is missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: test
Release: 1
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        try:
            nvr_from_spec(spec_path)
            assert False, "should have raised ValueError"
        except ValueError as e:
            assert "version" in str(e).lower(), f"error should mention missing 'version': {e}"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_missing_release():
    """Raise ValueError when Release is missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: test
Version: 1.0
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        try:
            nvr_from_spec(spec_path)
            assert False, "should have raised ValueError"
        except ValueError as e:
            assert "release" in str(e).lower(), f"error should mention missing 'release': {e}"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_comments_ignored():
    """Ignore lines that look like comments or are in comments."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
# This is a comment
Name: actual-name
# Version: 999.0
Version: 1.0
Release: 1
# Release: should-be-ignored
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "actual-name-1.0-1", f"expected 'actual-name-1.0-1', got '{result}'"
    finally:
        spec_path.unlink()


def test_nvr_from_spec_field_not_at_line_start():
    """Only match fields at the start of a line."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.spec', delete=False) as f:
        f.write("""
Name: correct-name
Version: 1.0
Release: 1
# This line has Version: 999.0 in a comment
Some text with Name: wrong-name
""")
        f.flush()
        spec_path = Path(f.name)
    
    try:
        result = nvr_from_spec(spec_path)
        assert result == "correct-name-1.0-1"
    finally:
        spec_path.unlink()




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
