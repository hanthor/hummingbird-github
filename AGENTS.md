# Agent Guidelines

Authoritative quick-reference for agents working in this repository. Mirrors
the convention Hummingbird uses in `redhat/hummingbird/rpms`.

## Read these first

| Document | Why |
| --- | --- |
| [`docs/targeting-hummingbird.md`](docs/targeting-hummingbird.md) | What "build targeting Hummingbird" means: what we fork, the build root, ABI, conventions, and what is still open |
| [`docs/architecture.md`](docs/architecture.md) | Pipeline shape |
| [`docs/contributing.md`](docs/contributing.md) | How to add a package |

**Hummingbird's own documentation is authoritative** over anything in this
repository. When the two disagree, theirs wins and this repository is the bug.

- Docs: <https://hummingbird-project.io/docs/>
- Source: <https://gitlab.com/redhat/hummingbird>
- Buildroot: `redhat/hummingbird/containers` → `mock/mock.cfg`, `yum-repos/`,
  `images/variables.yml`
- Packages and their agent tooling: `redhat/hummingbird/rpms` → `AGENTS.md`,
  `.agents/skills/`

## Skills

Real content lives in `.agents/skills/`; `.claude/skills/` symlinks to it, so
one copy serves every agent.

| Skill | Use when |
| --- | --- |
| `build-failure-triage` | A rebuild job failed and you need to know whose bug it is — ours, Fedora's, or the container's |
| `hummingbird` | Querying Hummingbird's image catalog: available images, tags, CVEs, SBOMs |

The `hummingbird` skill is vendored from
<https://gitlab.com/redhat/hummingbird/skills> (Apache-2.0, Red Hat). It
queries a live API, so refresh it rather than editing it:

```sh
curl -sS https://gitlab.com/api/v4/projects/redhat%2Fhummingbird%2Fskills/repository/files/SKILL.md/raw?ref=main \
  -o .agents/skills/hummingbird/SKILL.md
```

Upstream also publishes `upstream-diff` (classifying local spec changes as
upstreamable) and `analyze-failures` (Konflux pipelines in GitLab MRs). Neither
is vendored here: both drive Hummingbird's own tooling — `ci/upstream_diff.py`,
Konflux, GitLab — which this repository does not have. Port them if that
tooling arrives; do not copy them as-is.

## Conventions worth not rediscovering

- Sources come from **upstream releases**, verified and SHA-512 locked. Fedora
  dist-git supplies the **recipe only**, pinned by commit in
  `.hummingbird-upstream.json`.
- Packages that BuildRequire each other need a `stage` in
  `config/upstream-sources.json`. Stage N resolves against stages `< N`.
- Hummingbird's disttag is `hum1`, and it bumps `Release` with a `.N` suffix
  immediately before `%{?dist}` so a rebuild sorts above the Fedora build it
  derives from. **This repository does not do that yet** — its RPMs still carry
  Fedora's disttag.
- Never skip a test, or push an empty commit, to get a build green.
