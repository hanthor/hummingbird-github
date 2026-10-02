#!/usr/bin/env python3
"""Measure Bluefin's package contract against a Hummingbird image and repo."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from bluefin_manifest import contract_packages, load


def lines(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("config/bluefin-packages.toml"))
    parser.add_argument("--image-packages", type=Path, required=True)
    parser.add_argument("--repo-packages", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/hummingbird-gap.json"))
    parser.add_argument("--image", required=True)
    args = parser.parse_args()

    manifest = load(args.manifest)
    # Version-specific lists are intentionally included: this is the full
    # Bluefin contract, independent of whichever Fedora release consumes it.
    contract = set(contract_packages(manifest))
    image, repo = lines(args.image_packages), lines(args.repo_packages)
    available = image | repo
    report = {
        "measured_at": datetime.now(UTC).isoformat(),
        "image": args.image,
        "contract_binary_packages": sorted(contract),
        "available_from_image": sorted(contract & image),
        "available_from_repo_only": sorted((contract & repo) - image),
        "missing_from_hummingbird": sorted(contract - available),
        "counts": {
            "contract": len(contract),
            "image": len(contract & image),
            "repo_only": len((contract & repo) - image),
            "missing": len(contract - available),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
