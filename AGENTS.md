# Repository instructions

## Purpose

This repository stores Lila Brooks's personal Agent Skills. Each direct child of
`skills/` must remain a valid, independently installable skill package.

## Change rules

- Keep the directory name and `SKILL.md` frontmatter `name` identical.
- Preserve the complete skill package, including `agents/`, `references/`,
  `scripts/`, and executable file modes.
- Keep repository-level documentation at the root. Do not add README, changelog,
  or installation files inside an individual skill unless its workflow requires
  that resource.
- Treat `agents/openai.yaml` as optional Codex metadata. Keep the core `SKILL.md`
  useful to other Agent Skills-compatible hosts when the workflow permits it.
- Never copy bundled system skills, plugin caches, credentials, environment files,
  test caches, or generated validation artifacts into this repository.
- Update `skills/github-publish-changes/CHANGELOG.md` whenever that skill changes.
- Update the root inventory whenever the skill set changes.
- Keep repository quality decisions and exceptions current in `QUALITY.md`.
- Update `uv.lock` whenever development dependencies change.

## Verification

Use the verification tier named by the user:

- For documentation-only copy edits during active iteration, run
  `git diff --check`. Run the full gate before a standard commit, commit and
  push, or an explicit `full-check` request.
- Run `make check` for `full-check`, a standard commit, or commit and push. It
  validates all skill packages and relative references, checks the skill
  behavioral contracts, formats and checks Python, validates YAML, runs tests,
  scans for probable credentials, and checks the working diff.
- For an explicit `basic commit` or `quick commit`, stage and inspect the exact
  intended tree, then run `make basic-commit-check`. This tier scans for probable
  credentials and checks the cached diff for whitespace errors. Keep normal
  commit hooks and report that the full suite was skipped.

Also use any Agent Skills validator supplied by the active host during a full
check and run shell syntax checks when shell scripts change.
