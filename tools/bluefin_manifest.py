#!/usr/bin/env python3
"""Single reader for the vendored Bluefin package manifest.

Provides a unified interface for consuming config/bluefin-packages.toml across
multiple tools, eliminating divergent parsing and enforcing the manifest schema.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# Sections expected in the manifest that contribute to the buildroot
BUILDROOT_SECTIONS = ("fedora", "multimedia_overrides")


def load(manifest_path: Path) -> dict:
    """Load and validate the Bluefin manifest.
    
    Args:
        manifest_path: Path to config/bluefin-packages.toml
        
    Returns:
        Parsed manifest dictionary
        
    Raises:
        SystemExit: If required sections are missing
    """
    data = tomllib.loads(manifest_path.read_text())
    missing = [name for name in BUILDROOT_SECTIONS if name not in data]
    if missing:
        raise SystemExit(
            f"{manifest_path}: manifest is missing required tables: {', '.join(missing)}"
        )
    return data


def importable_packages(data: dict) -> list[str]:
    """Binary packages this factory resolves and imports from Rawhide.
    
    These are the packages that appear in the buildroot sections and are
    actually imported by the factory. Version-specific tables (fedora_v42, etc.)
    are deliberately excluded: they describe Fedora releases this factory does
    not currently build against.
    
    Args:
        data: Manifest dictionary from load()
        
    Returns:
        Sorted list of importable binary package names
    """
    names: set[str] = set()
    for section in BUILDROOT_SECTIONS:
        names.update(data.get(section, {}).get("packages", []))
    return sorted(names)


def contract_packages(data: dict) -> list[str]:
    """Every binary package Bluefin expects, across all Fedora releases.
    
    This includes version-specific packages from tables like fedora_v42, which
    describe the full contract even if they're not imported in the current build.
    The "excluded" table is deliberately omitted.
    
    Args:
        data: Manifest dictionary from load()
        
    Returns:
        Sorted list of all contract binary package names
    """
    names: set[str] = set()
    for section, values in data.items():
        if section != "excluded" and isinstance(values, dict):
            names.update(values.get("packages", []))
    return sorted(names)
