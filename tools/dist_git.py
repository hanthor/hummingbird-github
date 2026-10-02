#!/usr/bin/env python3
"""Koji-gated Fedora dist-git snapshot checker.

The Fedora lookaside ``sources`` file describes sources, while Koji is the
build authority.  A dist-git commit is a candidate only if Koji reports the
same name-version-release as a completed build.  This tool reports candidates;
the workflow turns them into reviewable update branches.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

# python3 tools/dist_git.py (how every workflow invokes this) puts tools/
# itself on sys.path, not the repo root, so "tools" is not importable as a
# package without this. Must run before the tools.common import below.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from tools.common import nvr_from_spec, run


def koji_complete(nvr: str) -> bool:
    # Koji's public JSON-RPC endpoint is stable and needs no secret.  Query
    # getBuild so a package is never promoted solely because dist-git advanced.
    request = urllib.request.Request(
        "https://koji.fedoraproject.org/kojihub",
        data=json.dumps({"method": "getBuild", "params": [nvr], "id": 1}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "hummingbird-github-distgit/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        build = json.load(response).get("result")
    return bool(build and build.get("state") == 1)  # Koji BUILD_STATES[COMPLETE]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("--branch", default="rawhide")
    parser.add_argument("--remote-template", default="https://src.fedoraproject.org/rpms/{package}.git")
    args = parser.parse_args()
    remote = args.remote_template.format(package=args.package)
    with tempfile.TemporaryDirectory(prefix="distgit-") as temporary:
        checkout = Path(temporary) / args.package
        subprocess.run(["git", "clone", "--depth=1", "--branch", args.branch, remote, str(checkout)], check=True)
        specs = list(checkout.glob("*.spec"))
        if len(specs) != 1:
            raise SystemExit(f"expected exactly one spec file, found {len(specs)}")
        nvr = nvr_from_spec(specs[0])
        result = {"package": args.package, "remote": remote, "branch": args.branch,
                  "commit": run("git", "rev-parse", "HEAD", cwd=checkout), "nvr": nvr,
                  "koji_complete": koji_complete(nvr)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["koji_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
