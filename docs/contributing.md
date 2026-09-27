# Contributing

Add source RPM names—not binary RPM names—to `config/bootstrap-packages.txt`.
Keep additions dependency-first. Pull requests validate configuration but cannot
publish packages, pages content, attestations, or image tags.

Before submitting changes, run local validation: see [Local Validation and Development](local-validation.md).

To bring in an upstream source, use **Actions → Import Rawhide package**. It
imports Fedora dist-git rather than a binary RPM, records the exact Rawhide
commit, and proposes the result through a pull request. Do not modify
`.hummingbird-upstream.json`; re-import when upstream changes.
