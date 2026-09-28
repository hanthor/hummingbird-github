#!/usr/bin/env python3
"""Validate package-factory configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROVENANCE_FIELDS = {"package", "branch", "remote", "commit", "tree", "imported_at"}


def bootstrap_packages(path: Path) -> list[str]:
    return [
        raw.strip()
        for raw in path.read_text().splitlines()
        if raw.strip() and not raw.lstrip().startswith("#")
    ]


def check_provenance(packages: Path) -> None:
    for path in packages.glob("*/.hummingbird-upstream.json"):
        data = json.loads(path.read_text())
        if set(data) != PROVENANCE_FIELDS:
            raise SystemExit(f"invalid upstream provenance: {path}")
        if data["branch"] != "rawhide":
            raise SystemExit(f"only rawhide imports are supported: {path}")


def check_bootstrap_set(packages: list[str]) -> None:
    if not packages:
        raise SystemExit("bootstrap package set is empty")
    if len(packages) != len(set(packages)):
        raise SystemExit("bootstrap package set contains duplicates")
    if any(" " in package or "/" in package for package in packages):
        raise SystemExit("package names must be source RPM names, one per line")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="repository root the configuration paths resolve against",
    )
    args = parser.parse_args()

    bootstrap_path = args.root / "config/bootstrap-packages.txt"
    if not bootstrap_path.is_file():
        raise SystemExit(f"bootstrap package set not found: {bootstrap_path}")

    packages = bootstrap_packages(bootstrap_path)
    check_provenance(args.root / "packages")
    check_bootstrap_set(packages)
    print(f"validated {len(packages)} source RPMs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
