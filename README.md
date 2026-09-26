# Hummingbird GitHub

A GitHub-hosted RPM and bootc image factory inspired by Hummingbird's goals:
fast upstream tracking, minimal images, reproducible build roots, and verifiable
supply-chain metadata.

It does **not** make consumer images install Fedora Rawhide directly. It uses
Fedora dist-git only to seed RPM recipes and patches, then rebuilds verified
direct-upstream sources on GitHub-hosted runners, publishes a coherent overlay
repository, and composes images from that repository.

## Using this repository

The factory produces an RPM overlay repository and a bootc base image. To use them:

### RPM overlay repository

Add this dnf config to your `Containerfile` or system:

```
[hummingbird-github]
name=Hummingbird GitHub RPM overlay
baseurl=https://hanthor.github.io/hummingbird-github/
enabled=1
gpgcheck=1
```

### Published base image

For direct use or as a build-from reference:

```
ghcr.io/hanthor/hummingbird-github-base:rawhide
```

Example:
```dockerfile
FROM ghcr.io/hanthor/hummingbird-github-base:rawhide
RUN dnf install -y <your-packages>
```

**Note**: `gpgcheck=1` is configured above but the factory does not yet sign RPMs (tracked in issue #36). Treat this as integrity checking only until signing is implemented.

## Initial scope

`config/bootstrap-packages.txt` is a dependency-first recipe-seeding set
covering the Fedora components that blocked Utah: FUSE, NTFS, device-mapper
persistent data, UDisks, librsvg, glycin, GVFS, GNOME, Firefox, and Distrobox.

The RPM workflow locks source RPM checksums, rebuilds them in Mock, creates
repodata, keylessly signs `repomd.xml` using GitHub OIDC/Cosign, and deploys it
to GitHub Pages. Pull requests never publish RPMs or images.

## Hummingbird-compatible freshness model

Rawhide and Fedora dist-git can be behind upstream: a maintainer may not have
pushed a spec change yet, or its build may not have completed. This factory
therefore follows Hummingbird's direct-source model for **every RPM it builds**:

1. The Fedora spec and patches are a bootstrap seed, never the release-update
   feed.
2. `source_pipeline.py` fetches each configured release archive or signed git
   tag directly from its upstream URL. It records SHA-512, verifies a configured
   checksum/signature, writes a report, and fails closed before the source is
   allowed into a build.
3. A package lacking a direct-source policy is not eligible for builds or
   publication. Fedora Rawhide is retained solely as a compatibility build root
   while the factory becomes self-hosting.

The source watcher runs at a best-effort cadence; GitHub does not guarantee
execution time for scheduled jobs. A source candidate is built, tested, and only
then published. Failed verification leaves the previous source unchanged.

## Import and fork upstream packages

`Import Rawhide package` imports a Fedora dist-git's `rawhide` branch into
`packages/<name>/`, recording its remote, immutable commit, tree ID, and import
time in `.hummingbird-upstream.json`. It is the initial spec/patch seed only;
the direct source pipeline owns all later source updates. The workflow opens a
pull request so downstream patches are explicit and reviewable before the
package enters a rebuild set.

`config/upstream-sources.json` is the allow-list for packages that need to lead
Fedora. Each entry supplies its release URL, immutable SHA-512, and, whenever
the upstream offers it, a release-signature URL plus pinned GPG key. It
deliberately contains no entries until each package has an agreed source URL
and verification policy; that is a deliberate admission gate, not a Rawhide
fallback.

Each release-tracked entry uses `version` plus `url_template` (with
`{version}`), and a `renovate` object containing its `datasource` and `depName`.
Renovate therefore proposes updates from the real upstream. Its
`upstream-source` PRs can automerge only after the verified RPM build gate; the
pipeline refuses publication until the PR also records the newly downloaded
source digest (and signature result, when configured).

This is an in-factory fork with upstream provenance. Mirroring each source into
an independent GitHub repository is intentionally optional: GitHub Actions'
`GITHUB_TOKEN` cannot create repositories. It can be added later with a
dedicated, narrowly scoped repository-creation credential.

See [architecture](docs/architecture.md) and [contributing](docs/contributing.md).

## Hummingbird availability measurement

`Recalculate Hummingbird package gaps` runs every six hours. It pulls the
Hummingbird bootc image to inspect its installed RPM database, queries the live
Hummingbird repository separately, and compares their union to Bluefin's
package contract. Its artifact distinguishes packages already installed in the
base image, packages newly available from the repository, and genuine gaps.

## Rawhide bootstrap policy

Fedora Rawhide is permitted only inside an isolated buildroot: it supplies the
compiler, build macros, and bootstrap BuildRequires needed to introduce a
Hummingbird gap. Package source archives still come directly from their
upstreams and are verified before build; the resulting repository, not Rawhide,
is used by consumer images and subsequent cross-package builds.
