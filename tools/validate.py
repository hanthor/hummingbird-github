#!/usr/bin/env python3
"""Validate package-factory configuration."""
import json
from pathlib import Path

packages = [
    raw.strip()
    for raw in Path("config/bootstrap-packages.txt").read_text().splitlines()
    if raw.strip() and not raw.lstrip().startswith("#")
]

if not packages:
    raise SystemExit("bootstrap package set is empty")
if len(packages) != len(set(packages)):
    raise SystemExit("bootstrap package set contains duplicates")
if any(" " in package or "/" in package for package in packages):
    raise SystemExit("package names must be source RPM names, one per line")

# Check declared packages have recipes
declared_set = set(packages)
package_dirs = {path.name for path in Path("packages").iterdir() if path.is_dir()}

missing_recipes = sorted(declared_set - package_dirs)
if missing_recipes:
    raise SystemExit(
        f"declared in bootstrap-packages.txt with no packages/ recipe: {', '.join(missing_recipes)}"
    )

# Check all package directories have upstream provenance
for path in sorted(Path("packages").glob("*/.hummingbird-upstream.json")):
    data = json.loads(path.read_text())
    required = {"package", "branch", "remote", "commit", "tree", "imported_at"}
    if set(data) != required:
        raise SystemExit(f"invalid upstream provenance: {path}")
    if data["branch"] != "rawhide":
        raise SystemExit(f"only rawhide imports are supported: {path}")

for package_dir in sorted(package_dirs):
    provenance_file = Path("packages") / package_dir / ".hummingbird-upstream.json"
    if not provenance_file.is_file():
        raise SystemExit(
            f"package has no upstream provenance: packages/{package_dir}/.hummingbird-upstream.json"
        )

print(f"validated {len(declared_set)} declared, {len(package_dirs)} imported")
