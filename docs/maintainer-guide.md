# Hummingbird Package Maintainer Guide

This guide explains how to maintain packages in the Hummingbird-GitHub overlay, understand verification gates, and contribute new packages responsibly.

## Overview

Hummingbird-GitHub builds an RPM overlay by:
1. Importing initial RPM recipes from Fedora dist-git
2. Fetching package sources directly from upstream (not Fedora/Rawhide)
3. Verifying checksums and signatures against configured policies
4. Building in Mock with reproducible source locks
5. Publishing signed RPM repodata to GitHub Pages and bootc images to GHCR

Each package in `config/upstream-sources.json` has an explicit source verification policy. Packages without a source policy are not eligible for builds or publication.

## Package Maintenance Tiers

### Tier 1: Verified Direct Source (Production)

**Requirements:**
- Upstream release URL is publicly available and immutable
- SHA-512 or release signature is configured and verified
- Renovate datasource is configured for automated version proposals
- Package has passed build and integration tests
- Maintainer commits to review version updates within SLA

**SLA:**
- Security patches: reviewed within 24 hours
- Version updates: reviewed within 1 week
- Maintenance: indefinite (unless explicitly deprecated)

**Visibility:** Listed in `config/upstream-sources.json`, published in stable overlay

### Tier 2: Rawhide Fallback (Transitional)

**Requirements:**
- Package is not yet in upstream-sources.json
- Fedora Rawhide recipe exists and builds successfully
- Used only as a bootstrap for new packages or gap-fillers for dependencies

**SLA:**
- No explicit SLA; best-effort updates from Rawhide only
- Eligible for automatic deprecation if Tier 1 policy not established

**Visibility:** Not in stable overlay; testing only

### Tier 3: Archived (Deprecated)

**Requirements:**
- Package no longer needed in Hummingbird
- Removal announced 2 weeks prior
- All dependents migrated to alternatives

**SLA:** None; no updates

**Visibility:** Removed from overlay and publishing

## Adding a New Package

### Step 1: Establish Upstream Source Policy

Before opening a pull request, determine the package's direct-source policy:

**Example 1: Release archive with checksum**
```json
{
  "name": "libfoo",
  "version": "1.2.3",
  "url_template": "https://example.com/releases/libfoo-{version}.tar.gz",
  "checksum_sha512": "abc123...",
  "renovate": {
    "datasource": "github-releases",
    "depName": "example/libfoo"
  }
}
```

**Example 2: Signed git tag**
```json
{
  "name": "bar",
  "version": "2.0.0",
  "url_template": "https://github.com/example/bar/archive/refs/tags/v{version}.tar.gz",
  "signature_url": "https://github.com/example/bar/releases/download/v{version}/v{version}.tar.gz.asc",
  "gpg_key": "ABCD1234...",
  "renovate": {
    "datasource": "github-tags",
    "depName": "example/bar"
  }
}
```

### Step 2: Import Fedora Recipe

If a Fedora dist-git package exists:

```bash
./scripts/import-rawhide-package.py <package-name>
```

This creates `packages/<name>/` with the Rawhide spec and patches, recorded in `.hummingbird-upstream.json`.

### Step 3: Verify the Source Policy

Run the verification pipeline locally:

```bash
./tools/source_pipeline.py \
  --config config/upstream-sources.json \
  --package <name> \
  --output-report verification-report.json
```

Ensure:
- Checksum matches upstream release
- Signature verifies (if applicable)
- Source archive is pristine

### Step 4: Build and Test

Add the package to `config/bootstrap-packages.txt` and trigger a test build:

```bash
# Creates a PR for review before publication
gh workflow run build-test-matrix.yml --ref strategy/<name>-new
```

Wait for CI to complete:
- ✅ Mock build succeeds on all architectures
- ✅ RPM passes basic linting (version, dependencies, etc.)
- ✅ Integration tests pass (if any)

### Step 5: Add to `upstream-sources.json`

Edit `config/upstream-sources.json` and add your package entry:

```json
{
  "name": "<package-name>",
  "version": "X.Y.Z",
  "url_template": "https://...",
  "checksum_sha512": "...",
  "renovate": { ... }
}
```

### Step 6: Open Pull Request

Title: `Add <package-name> package with direct-source verification`

Body should include:
- Upstream URL and verification method (checksum / signature / policy)
- Rationale for inclusion (what does this unblock in Hummingbird?)
- Build artifacts link (CI job number or screenshots)
- Maintenance tier (Tier 1 direct-source assumed)

## Updating an Existing Package

### Version Update (Renovate Bot)

Renovate opens PRs for new upstream versions automatically. As maintainer:

1. Review the version bump and changelog
2. Verify the CI pipeline:
   - `source_pipeline.py` passes (new checksum verified)
   - Mock builds complete on all architectures
   - `upstream-source` PR has merged (checksum recorded)
3. Approve and merge the update PR

**Timeline:** Review within 1 week of PR opening

### Security Patch

If a security update is released:

1. Bump version in `config/upstream-sources.json`
2. Verify checksum locally: `./tools/source_pipeline.py --package <name>`
3. Trigger rebuild: Push to a branch or manually run GitHub Actions workflow
4. Merge when CI passes

**Timeline:** Review within 24 hours of security notice

### Recipe or Patch Update

If you need to modify the RPM spec or patches:

1. Edit `packages/<name>/` files (spec, patches)
2. Ensure the package still sources from upstream (do not inline or vendor source)
3. Trigger a test build (same as Step 4 above)
4. Open a PR explaining the change

## Understanding the Verification Gate

The `source_pipeline.py` tool enforces strict supply-chain requirements:

### Checksum Verification

```
$ ./tools/source_pipeline.py --package libfoo
Fetching https://example.com/releases/libfoo-1.2.3.tar.gz
SHA-512: abc123...
Expected: abc123...
✓ Checksum matches
```

If checksum does not match, the build fails immediately. The previous source is not updated.

### Signature Verification

```
$ ./tools/source_pipeline.py --package bar
Fetching signature from https://...
GPG key: ABCD1234...
Verifying signature...
✓ Signature valid (key ABCD1234 trusted)
```

If signature verification fails, the build fails. This prevents man-in-the-middle attacks.

### Policy Enforcement

Packages without an entry in `config/upstream-sources.json`:
- Cannot be published from this factory
- Can build from Rawhide for testing only
- Are not installed in consumer bootc images

## Deprecating a Package

If a package is no longer needed:

1. Announce deprecation in the GitHub issue tracker (2-week notice)
2. Remove from `config/upstream-sources.json`
3. Remove from `config/bootstrap-packages.txt`
4. Keep `packages/<name>/` directory (historical record)
5. Merge to main; package is removed from next build

Consumers should have alternative package or mitigation plan before removal.

## Maintenance SLA and Rotation

### Current Model

Each package maintained by contributor who added it. No formal rotation yet.

### Escalation

If a package maintainer becomes unavailable:
1. Issue is opened and labeled `needs-maintainer`
2. Other contributors can volunteer or reassign
3. If no volunteer within 2 weeks, package moves to Tier 2 (Rawhide fallback)

## Troubleshooting

### Build Fails in Mock

Check CI logs for:
- Missing BuildRequires (may be in Hummingbird overlay, not Rawhide)
- Spec syntax errors
- Patching failures

Solution: Adjust spec or patches in `packages/<name>/` and push again.

### Checksum Mismatch

Upstream release changed without version bump. Solutions:
1. Contact upstream maintainer (report problem)
2. If upstream deleted old release, pin to a working mirror
3. If checksum is wrong in config, verify manually and correct

### Signature Verification Fails

GPG key is missing or outdated. Solutions:
1. Fetch key directly from upstream: `gpg --recv-key <key-id>`
2. Update `gpg_key` in `config/upstream-sources.json`
3. Re-verify with new key

## Questions?

- Architecture questions: See `docs/architecture.md`
- Specific package issue: Check package's GitHub issue tracker
- Process feedback: Open an issue on this repository
