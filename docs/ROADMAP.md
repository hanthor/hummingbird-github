# Hummingbird GitHub factory roadmap

Updated 2026-10-04. This is the public adoption and delivery roadmap for the Hummingbird GitHub factory — a direct-upstream RPM rebuild and bootc image composition system designed to track Fedora faster, with verified supply-chain provenance.

## Current status

**Phase: Bootstrap and self-hosting foundation**

The factory has:
- ✓ Verified direct-upstream source fetching with SHA-512 validation and optional GPG verification
- ✓ GitHub Actions-based RPM rebuild pipeline with Mock and keyless Cosign signing
- ✓ Initial package set covering Fedora components blocking Bluefin: FUSE, NTFS, UDisks, GVFS, GNOME, Firefox, Distrobox, and dependencies
- ✓ bootc image composition from published overlay repository
- ✓ Hummingbird package-gap measurement (6-hour cadence) comparing base image, overlay, and Bluefin contract
- ✓ GitHub Pages-hosted repository with OIDC/Cosign-signed repodata

Open work:
- Expand package coverage beyond bootstrap set (see "Near-term" below)
- Self-host the build root (currently seeds from Rawhide/dist-git)
- Establish measurable adoption and integration benchmarks

**Supply-chain maturity**: Direct source verification for all published packages; GitHub OIDC keyless signing for repodata; Cosign-verifiable provenance. Rawhide dependency is temporary (bootstrap seed only).

**Adoption readiness**: Not yet published as a standalone product. Factory runs and publishes artifacts; external consumption and feedback are limited. Documentation is technical; user onboarding is absent.

## Near-term: October 2026–January 2027

### 1. Expand verified package coverage

**Goal**: Move beyond the initial bootstrap set toward a coherent, self-contained factory.

**Scope**:
- Document current package gaps vs Bluefin contract (automated via 6-hour measurement job)
- Prioritize gap packages by: (a) dependency density, (b) frequency of upstream updates, (c) existing Fedora maintenance burden
- Add 15–25 additional packages with direct-source policies to `upstream-sources.json`
- Test rebuilt packages in bootc image composition and Bluefin installation workflows

**Success criteria**:
- Gap report shows 50%+ coverage of named Bluefin contract packages
- No regression in existing package build reliability (maintain <5% build failure rate)
- All new packages pass local validation and image composition tests

### 2. Self-host the build root

**Goal**: Reduce Rawhide dependency; increase upstream independence and supply-chain closure.

**Scope**:
- Identify the minimal core package set required to build everything else (systemd, gcc, rpm, make, etc.)
- Separate "seed from Rawhide" phase from "build using factory packages" phase
- Add a gating step that refuses to publish if build root has unverified sources
- Document the dependency DAG and bootstrap sequence

**Success criteria**:
- Build root is reproducible from verified sources only
- Factory can detect (and fail closed on) Rawhide dependency drift
- Bootstrap and self-hosting phases are clearly separated in CI output

### 3. Establish measurable adoption signals

**Goal**: Understand how users discover and consume Hummingbird artifacts; identify barriers.

**Scope**:
- Publish a getting-started guide for consuming the overlay repository (dnf integration, bootc usage examples)
- Record artifact download statistics (GitHub Actions artifacts, Pages repository access logs)
- Collect issue reports and user feedback on: build reliability, package selection, documentation clarity, integration friction
- Define "adoption success" metrics (e.g., X external users running factory images, Y verified installs per week)

**Success criteria**:
- Getting-started guide is published and tested by at least one external user
- Download metrics are collected and reported monthly
- At least 3 reproducible external user feedback items are filed as issues

## Mid-term: January–April 2027

### 1. Establish Bluefin parity and integration testing

**Goal**: Validate that factory-built packages maintain Bluefin's release semantics and compatibility.

**Scope**:
- Run Bluefin's own test suite against factory-built images (where applicable)
- Compare package contents (binary size, symbol availability, runtime behavior) against Bluefin's corresponding images
- Document known differences and compatibility caveats
- Add regression guards to the CI (fail on unexpected binary changes, unaccounted symbol removals)

**Success criteria**:
- Factory images pass Bluefin's core smoke tests (boot, basic services, package management)
- Parity report documents intentional differences and their rationale
- No undocumented binary differences are merged

### 2. Multi-architecture support planning

**Goal**: Scope what it takes to extend beyond x86_64.

**Scope**:
- Audit GitHub Actions runner availability and cost for aarch64, ppc64le
- Identify architecture-specific package issues (esp. CUDA, GPU drivers, hardware support)
- Document hardware test matrix and CI strategy for multi-arch
- Do NOT begin builds yet; plan and cost first

**Success criteria**:
- Architecture support plan is published with estimated runner costs and timeline
- Known architecture-specific package issues are documented
- Plan approval from maintainers before CI expansion

### 3. Documentation expansion

**Goal**: Make the factory discoverable and usable by external contributors and users.

**Scope**:
- Publish contributor onboarding guide (how to add a new package, validate sources, write tests)
- Create architecture diagrams explaining the factory pipeline
- Document the supply-chain verification model and its guarantees/limits
- Add examples: how to integrate factory outputs into a downstream project, how to customize images

**Success criteria**:
- All architecture and supply-chain concepts are explained for new readers
- At least one external contributor uses the onboarding guide successfully
- Diagrams accurately represent current implementation

## Six to twelve months: April–October 2027

### Readiness gates for 1.0 release

A 1.0 release of Hummingbird GitHub requires:

1. **Supply-chain closure**: Build root is fully self-hosted (no Rawhide seed dependencies)
2. **Package coverage**: ≥80% of Bluefin contract packages have verified upstream sources and builds
3. **Integration validation**: Factory images pass Bluefin compatibility tests and at least one downstream (non-Bluefin) project integration test
4. **Adoption evidence**: ≥10 external contributors or active users with documented use cases
5. **Security and maintenance**: SECURITY.md published, vulnerability reporting process established, maintenance SLA documented
6. **Documentation**: All technical and user-facing documentation complete and verified by external readers

### Optional future work

- **Public extension API**: Allow external projects to define custom package overlays (out of scope for 1.0)
- **Image customization**: User-facing tools to create customized bootc images from factory packages (consider post-1.0)
- **Hardware support matrix**: Publish tested hardware configurations and known limitations (post-1.0, requires broader testing community)
- **Downstream packaging**: Support for RPM repository mirrors and offline deployment (future optimization)

## Known limitations

- **Rawhide bootstrap**: Currently seeds from Rawhide; self-hosting in progress
- **Architecture support**: x86_64 only; multi-arch planned but not costed or resourced
- **Test coverage**: Currently validates build success and basic image boot; comprehensive compatibility testing is limited
- **Adoption metrics**: No usage telemetry; feedback is volunteer-driven and anecdotal
- **Uptime SLA**: GitHub Actions runner availability and scheduling are best-effort, not guaranteed

## How contributors can help

- **Add verified packages**: Identify high-value packages with clear upstream URLs and contribute `upstream-sources.json` entries
- **Test on real hardware**: Report build-time and runtime issues on actual systems; document your hardware configuration
- **Integration testing**: Try factory images in your own workflows; report friction points and compatibility issues
- **Documentation feedback**: Review guides and architecture docs; identify unclear sections and suggest improvements
- **Supply-chain validation**: Verify that published signatures and checksums match your expectations; report discrepancies
- **Maintenance help**: Volunteer to maintain specific high-value packages (GNOME, Firefox, development tools)

See [architecture.md](architecture.md) and [contributing.md](contributing.md) for technical details.

## Release history

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 0.1.0 (factory foundation) | 2026-10-04 | In use | Bootstrap packages, direct-source verification, overlay repository |
| 1.0 (self-hosted production) | Planned Q4 2027 | Pending gates | Full supply-chain closure, ≥80% package coverage, external adoption validation |

---

*Last updated 2026-10-04 by strategist agent (ACMM L5 — hold-gated mode)*
