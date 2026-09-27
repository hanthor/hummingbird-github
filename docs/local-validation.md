# Local Validation and Development

Before submitting changes to package configuration or bootstrap packages, validate your changes locally.

## Prerequisites

- Python 3.10 or later
- Bash
- `just` command runner (installed via package manager or from https://github.com/casey/just)

## Running the validator

The `validate.py` script checks configuration consistency, package names, and provenance metadata:

```bash
just validate
```

This verifies:
- `config/bootstrap-packages.txt` contains no duplicates or invalid characters
- All imported packages have valid `.hummingbird-upstream.json` metadata (exact Rawhide branch, remote, commit, tree ID, and timestamp)
- Bootstrap package set is not empty

### Interpreter output

Successful validation:
```
validated 19 source RPMs
```

Common errors and fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| `bootstrap package set is empty` | `bootstrap-packages.txt` is blank or only comments | Add source RPM names |
| `bootstrap package set contains duplicates` | Same package listed twice | Remove duplicate line |
| `package names must be source RPM names, one per line` | Invalid characters or spaces in names | Source RPM format: `name` only, no version or `/` |
| `invalid upstream provenance: packages/<name>/.hummingbird-upstream.json` | Missing required fields or wrong Rawhide branch | Re-import package using Actions → Import Rawhide package |

## Workflow for adding a package

1. **Import the Rawhide source** — Go to **Actions** → **Import Rawhide package**, enter the package name, and submit. This creates a pull request with the Fedora spec and patches.
2. **Review the import PR** — The `.hummingbird-upstream.json` file records the exact Rawhide commit and tree ID. Verify the package is what you intended.
3. **Add to bootstrap set** — Merge the import PR. Then, in a new PR, add the package name to `config/bootstrap-packages.txt` in dependency order (dependencies before packages that depend on them).
4. **Validate locally** — Run `just validate` to ensure no typos or duplicates.
5. **Configure upstream source** (optional) — If this package should track a direct upstream instead of Rawhide, edit `config/upstream-sources.json` to add a release-tracking entry with URL, checksum, and optional GPG signature.

## Why local validation matters

The GitHub Actions CI pipeline runs validation on every pull request. Catching errors locally before pushing saves CI resources and makes reviews faster. The validator is strict by design: it fails if:
- Package names are malformed
- Required metadata is missing or incorrect
- Configuration is internally inconsistent

All these can be fixed locally and tested before opening a PR.
