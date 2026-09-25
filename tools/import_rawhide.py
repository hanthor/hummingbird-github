#!/usr/bin/env python3
"""Import a Fedora dist-git Rawhide snapshot into this package factory."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# python3 tools/import_rawhide.py (how every workflow invokes this) puts
# tools/ itself on sys.path, not the repo root, so "tools" is not importable
# as a package without this. Must run before the tools.common import below.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.common import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", help="Fedora dist-git package name")
    parser.add_argument("--branch", default="rawhide")
    parser.add_argument("--remote-template", default="https://src.fedoraproject.org/rpms/{package}.git")
    parser.add_argument("--destination", type=Path, default=Path("packages"))
    args = parser.parse_args()

    if not args.package.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("package name must contain only letters, numbers, '_' or '-'")

    remote = args.remote_template.format(package=args.package)
    destination = args.destination / args.package
    if destination.exists():
        raise SystemExit(f"destination already exists: {destination}")

    with tempfile.TemporaryDirectory(prefix="rawhide-import-") as temporary:
        clone = Path(temporary) / "dist-git"
        subprocess.run(["git", "clone", "--filter=blob:none", "--branch", args.branch, remote, str(clone)], check=True)
        commit = run("git", "rev-parse", "HEAD", cwd=clone)
        tree = run("git", "rev-parse", "HEAD^{tree}", cwd=clone)
        destination.mkdir(parents=True)
        archive = subprocess.Popen(["git", "archive", args.branch], cwd=clone, stdout=subprocess.PIPE)
        try:
            subprocess.run(["tar", "-x", "-C", str(destination)], stdin=archive.stdout, check=True)
        finally:
            if archive.stdout:
                archive.stdout.close()
            archive.wait()

    provenance = {
        "package": args.package,
        "branch": args.branch,
        "remote": remote,
        "commit": commit,
        "tree": tree,
        "imported_at": datetime.now(UTC).isoformat(),
    }
    (destination / ".hummingbird-upstream.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
