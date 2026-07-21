# Personal agent skills

[![Quality](https://github.com/lilabrooks/lila-agent-skills/actions/workflows/quality.yml/badge.svg?branch=main&event=push)](https://github.com/lilabrooks/lila-agent-skills/actions/workflows/quality.yml?query=branch%3Amain+event%3Apush)
[![Coverage gate](https://img.shields.io/badge/coverage-%E2%89%A595%25-brightgreen)](QUALITY.md#tests-and-coverage)
[![License: All rights reserved](https://img.shields.io/badge/license-all_rights_reserved-blue)](LICENSE)

This repository is the version-controlled source for Lila Brooks's reusable
Agent Skills packages. Every direct child of `skills/` is independently
installable and contains a required `SKILL.md` plus any supporting metadata,
references, or scripts.

## Skill inventory

| Skill | Purpose | Notes |
| --- | --- | --- |
| `clean-git-branches` | Audits and safely cleans local and remote Git branches while checking that default-branch refs stay synchronized. | Handles squash-merged branches, pruning, exact-SHA checks, and verified deletion. |
| `github-merge-pull-request` | Inspects and merges an exact GitHub pull-request candidate. | Covers merge, squash, and rebase methods; head-SHA guards; queues; bypasses; and separate cleanup authority. |
| `github-publish-changes` | Commits and pushes intended Git changes while preserving unrelated work. | Includes read-only preflight, exact-tree checks, edge-case references, and a changelog. |
| `prepare-agent-compatible-repository` | Audits and reconciles repository guidance for Codex and Claude Code. | Uses shared `AGENTS.md` rules, small `CLAUDE.md` adapters, scope checks, and explicit host differences. |
| `verify-repository` | Runs evidence-based repository readiness, QA, coverage, and hygiene audits. | Includes a read-only repository audit script. |

## Agent compatibility

The core workflow for each package lives in `SKILL.md`. Optional
`agents/openai.yaml` files add Codex interface metadata and can be ignored by
other Agent Skills-compatible hosts. A skill may still name a specific host
when its workflow depends on that host's tools or conventions.

This repository keeps shared agent instructions in [AGENTS.md](AGENTS.md). The
root [CLAUDE.md](CLAUDE.md) imports those instructions for Claude Code.

## Install a skill

Use symlinks so installed skills always read the package tracked in this
repository. Codex uses `~/.agents/skills/`; Claude Code uses
`~/.claude/skills/`.

For example, from the repository root:

```bash
skill_name=github-publish-changes

mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s "$PWD/skills/$skill_name" "$HOME/.agents/skills/$skill_name"
ln -s "$PWD/skills/$skill_name" "$HOME/.claude/skills/$skill_name"
```

Check each destination before creating a link. Preserve or remove an existing
installation deliberately so unique work is not overwritten. Legacy standalone
copies under `~/.codex/skills/` are unsupported because they can drift from the
packages checked in this repository.

## Repository checks

Run the full quality gate after changing a skill or repository tooling:

```bash
make check
```

Git hooks are optional. Use `make check` before a standard commit; GitHub
Actions runs the same target.

The full gate checks formatting, lint, types, YAML, package structure,
behavioral contracts, tests, coverage, probable credentials, and Git whitespace.
GitHub Actions runs the same target.

The behavioral contract check covers every current skill and tests the documented
authority boundaries between verification, publishing, pull-request merging,
branch cleanup, and agent compatibility.

An explicit `basic commit` or `quick commit` uses the smaller staged-tree gate:

```bash
make basic-commit-check
```

That gate checks probable credentials and staged whitespace only. See
[QUALITY.md](QUALITY.md) for supported Python versions, coverage policy, tool
exceptions, and the full verification design.

Development dependencies are declared in `pyproject.toml` and locked in
`uv.lock`. Each uv-backed Make target prepares its tools on demand. Installed
skill packages do not use the repository's Python environment.

## Maintenance rules

- Keep one skill per directory under `skills/`.
- Keep each directory name equal to the `name` in its `SKILL.md` frontmatter.
- Preserve supporting files and executable modes.
- Update this inventory when adding, renaming, or removing a skill.
- Keep bundled system skills, plugin caches, credentials, and generated
  validation artifacts out of this repository.
- Use any Agent Skills validator supplied by the active host alongside
  `make check`.

## Copyright

Copyright © 2026 Lila Brooks. All rights reserved. See [LICENSE](LICENSE).
