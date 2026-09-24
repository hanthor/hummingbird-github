# Contributing

Add source RPM names—not binary RPM names—to `config/bootstrap-packages.txt`.
Keep additions dependency-first. Pull requests validate configuration but cannot
publish packages, pages content, attestations, or image tags.

## Local Validation

Before submitting a pull request, run the configuration validation script locally to verify package specifications:

```bash
python3 tools/validate.py
```

Alternatively, if `just` is installed on your environment:

```bash
just validate
```

Validation ensures that:
- `config/bootstrap-packages.txt` is non-empty, contains no duplicates, and lists valid source RPM names (one per line, without spaces or slashes).
- Every imported package under `packages/*/` contains a valid `.hummingbird-upstream.json` file with all required provenance fields (`package`, `branch`, `remote`, `commit`, `tree`, `imported_at`).
- All package imports strictly target the `rawhide` branch.

## Importing Upstream Packages

To bring in an upstream source, use **Actions → Import Rawhide package**. It
imports Fedora dist-git rather than a binary RPM, records the exact Rawhide
commit, and proposes the result through a pull request. Do not modify
`.hummingbird-upstream.json` directly; re-import when upstream changes.
