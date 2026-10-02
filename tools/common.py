"""Shared helper functions for hummingbird-github tools."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def run(*args: str, cwd: Path | None = None) -> str:
    """Run a subprocess command and return trimmed stdout."""
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def parse_source_name(sourcerpm: str) -> str:
    """Extract source package name from a source RPM filename or candidate string."""
    match = re.match(r"^(.+)-[0-9][^-]*-.*\.src\.rpm$", sourcerpm)
    if not match:
        raise ValueError(f"cannot parse source RPM: {sourcerpm}")
    return match.group(1)


def nvr_from_spec(spec: Path) -> str:
    """Extract NVR (Name-Version-Release) from a spec file."""
    fields: dict[str, str] = {}
    for line in spec.read_text(errors="replace").splitlines():
        match = re.match(r"^(Name|Version|Release):\s*(\S+)", line)
        if match:
            fields[match.group(1).lower()] = match.group(2).replace("%{?dist}", "")
    missing = {"name", "version", "release"} - fields.keys()
    if missing:
        raise ValueError(f"missing spec fields: {', '.join(sorted(missing))}")
    return "{name}-{version}-{release}".format(**fields)
