#!/usr/bin/env python3
"""Import a Fedora dist-git Rawhide snapshot into this package factory."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def import_package(
    package: str,
    *,
    branch: str = "rawhide",
    remote_template: str = "https://src.fedoraproject.org/rpms/{package}.git",
    destination_root: Path = Path("packages"),
) -> dict[str, str]:
    """Clone a Fedora dist-git branch into destination_root/package and record its provenance.

    Raises ValueError for a malformed package name and FileExistsError when the
    destination already exists, so a caller driving many imports (see
    import_bluefin_rawhide.py) can catch and report per-package failures
    without a subprocess round-trip through this module's own CLI.
    """
    if not package.replace("-", "").replace("_", "").isalnum():
        raise ValueError("package name must contain only letters, numbers, '_' or '-'")

    remote = remote_template.format(package=package)
    destination = destination_root / package
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    with tempfile.TemporaryDirectory(prefix="rawhide-import-") as temporary:
        clone = Path(temporary) / "dist-git"
        subprocess.run(["git", "clone", "--filter=blob:none", "--branch", branch, remote, str(clone)], check=True)
        commit = run("git", "rev-parse", "HEAD", cwd=clone)
        tree = run("git", "rev-parse", "HEAD^{tree}", cwd=clone)
        destination.mkdir(parents=True)
        archive = subprocess.Popen(["git", "archive", branch], cwd=clone, stdout=subprocess.PIPE)
        try:
            subprocess.run(["tar", "-x", "-C", str(destination)], stdin=archive.stdout, check=True)
        finally:
            if archive.stdout:
                archive.stdout.close()
            archive.wait()

    provenance = {
        "package": package,
        "branch": branch,
        "remote": remote,
        "commit": commit,
        "tree": tree,
        "imported_at": datetime.now(UTC).isoformat(),
    }
    (destination / ".hummingbird-upstream.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", help="Fedora dist-git package name")
    parser.add_argument("--branch", default="rawhide")
    parser.add_argument("--remote-template", default="https://src.fedoraproject.org/rpms/{package}.git")
    parser.add_argument("--destination", type=Path, default=Path("packages"))
    args = parser.parse_args()

    try:
        provenance = import_package(
            args.package,
            branch=args.branch,
            remote_template=args.remote_template,
            destination_root=args.destination,
        )
    except (ValueError, FileExistsError) as error:
        raise SystemExit(str(error))

    print(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
