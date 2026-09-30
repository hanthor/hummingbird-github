# Security Policy

Hummingbird GitHub is a software supply-chain factory: it rebuilds RPMs from
verified upstream sources, publishes a signed repository, and composes a
signed bootc base image consumed by other systems. Vulnerabilities in this
pipeline can affect every consumer of its output, so please report them
responsibly rather than filing a public issue.

## Reporting a Vulnerability

Use GitHub's private vulnerability reporting for this repository:

1. Go to the [Security tab](https://github.com/hanthor/hummingbird-github/security).
2. Select **Report a vulnerability**.
3. Describe the issue, its impact, and reproduction steps if available.

This opens a private advisory visible only to the maintainer and does not
require an email address or third-party account.

## Scope

In scope for security reports:

- Bypass or weakening of `source_pipeline.py`'s checksum/signature
  verification gate
- Injection of an unverified or attacker-controlled source through
  `config/upstream-sources.json` or `config/bootstrap-packages.txt`
- Compromise or misuse of the Cosign keyless signing step in
  `.github/workflows/rebuild-rpms.yml`
- Tampering with published repository metadata (`repodata/`) that would not
  be caught by existing verification
- Any path by which a pull request could publish RPMs, images, attestations,
  or tags (the project's stated design intentionally forbids this)

Out of scope:

- The repository/image signing-trust gap already tracked in
  [#36](https://github.com/hanthor/hummingbird-github/issues/36) (the
  published `Containerfile` asserts `gpgcheck=1` with no `gpgkey=`, while the
  publisher signs `repomd.xml` with Cosign in a format `dnf` does not
  consult, and RPMs themselves are unsigned). That is a known architecture
  gap with an open tracking issue, not a new report — feel free to comment
  on #36 instead if you have additional findings specific to it.

## Response

This is a single-maintainer project. There is no guaranteed response time,
but reports are read promptly. Please allow time for a fix before any public
disclosure.
