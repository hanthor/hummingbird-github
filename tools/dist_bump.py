#!/usr/bin/env python3
"""Print the .N suffix for a package's disttag, or nothing.

Our disttag follows AlmaLinux: Fedora's release and dist, then .bfin, then a
counter when we rebuild the same Fedora build more than once -- their dnf is
4.14.0-34.el9_8.alma.1 against Red Hat's 34.el9_8, and both .alma and .alma.N
appear in their repositories.

The counter is per package, so it lives beside the package's source entry as
"dist_bump": 1. Most packages never need one: it is only for the case where the
Fedora release we derive from has not moved but our own build of it has to.
"""
import json
import sys
from pathlib import Path

config = Path(__file__).resolve().parent.parent / "config" / "upstream-sources.json"
name = sys.argv[1]
for entry in json.loads(config.read_text())["packages"]:
    if entry.get("name") == name:
        bump = entry.get("dist_bump")
        if bump is not None:
            print(f".{bump}")
        break
