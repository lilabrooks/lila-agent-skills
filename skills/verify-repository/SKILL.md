---
name: verify-repository
description: Perform evidence-based repository readiness and final-QA audits. Use when the agent is asked to assess whether a repository is ready for agent or production use, run final QA, verify nothing broke, audit before a commit or release, inspect coverage and quality gates, validate git and ignore hygiene, check generated-project workflows, or clean verification artifacts.
---

# Verify Repository

Use the repository's own commands as the source of truth, then add checks that
its normal gate does not cover. Preserve user work and distinguish product
failures from local-environment damage.

## Rules

- Read all applicable `AGENTS.md` and override instructions before acting.
- Capture `git status --short --branch` before running tools.
- Treat existing tracked and untracked changes as user-owned unless their
  origin is known. Do not edit, delete, stage, or commit them implicitly.
- Keep staging, committing, pushing, and pull-request creation outside this
  skill. When the user combines verification with publishing, complete the
  verification boundary and hand the tested state to the GitHub publishing
  skill.
- Prefer read-only inspection for an assessment request. Implement repairs only
  when the user asks for changes or the active request clearly includes them.
- Run repository-owned gates instead of recreating their lint, test, typing,
  coverage, build, or documentation logic in this skill.
- Never promise that a repository has no bugs. Report that no failures were
  found within the tested scope and list that scope.
- Request approval when a meaningful check needs network access, external
  writes, destructive cleanup, or credentials.

## Workflow

### 1. Establish the baseline

1. Locate the repository root and applicable agent instructions.
2. Inspect the current branch, worktree state, remotes, recent commit, manifests,
   lockfiles, CI workflows, release configuration, and documented commands.
3. Identify unrelated changes before selecting checks.
4. Run the bundled read-only audit:

   ```bash
   python3 /path/to/verify-repository/scripts/repo_audit.py --root .
   ```

   Add repository-specific expectations when evidence supports them:

   ```bash
   python3 /path/to/verify-repository/scripts/repo_audit.py --root . \
     --expect-ignored .venv \
     --expect-trackable uv.lock
   ```

### 2. Discover the authoritative gate

Check `AGENTS.md`, README setup instructions, Makefiles or task runners,
dependency manifests, test configuration, and CI. Select the smallest command
that represents the repository's normal handoff gate. Examples include
`make check`, `uv run make check`, `npm test`, `cargo test`, or a documented
equivalent.

Verify that local commands and CI agree on:

- supported runtimes;
- dependency groups and lockfile policy;
- lint, formatting, typing, test, and documentation checks;
- coverage mode and threshold;
- build, packaging, and installed-entry-point checks.

### 3. Run checks in increasing cost order

1. Validate diffs, syntax, formatting, and configuration parsing.
2. Run focused tests for changed behavior.
3. Run the authoritative repository gate.
4. Run build, package installation, and installed-entry-point smoke tests when
   applicable.
5. Exercise generators or templates in a temporary directory. Include spaces
   or brackets in paths when the interface accepts arbitrary targets. Avoid
   `#` in Python virtual-environment paths unless support is explicit because
   console-script shebang handling is not portable there.
6. Choose the temporary snapshot mode deliberately when workflows depend on
   Git. Use a source archive without `.git` to verify graceful skips or clear
   unsupported-mode errors. Initialize and commit the same snapshot before
   exercising generators that read `HEAD`, call `git archive`, or otherwise
   require a checkout. Report the two results separately.
7. Run every declared runtime version when the change is runtime-sensitive or
   the user requests final release confidence.
8. Validate workflow YAML, shell syntax, and ShellCheck when those files change
   and the relevant tools are already available.

Use network-enabled setup phases for dependency installation in sandboxed cloud
agent environments. Agent-phase internet access may be unavailable. Keep offline
checks independent from optional external providers and credentials.

### 4. Audit agent and repository hygiene

Confirm, when applicable:

- `AGENTS.md` contains current setup, verification, and safety instructions;
- dependency installation is placed in the environment setup phase when it
  requires network access;
- `.gitignore` covers demonstrated local artifacts without hiding lockfiles,
  examples, agent instructions, hooks, or repository configuration;
- tracked files do not match ignore rules;
- coverage and build outputs are absent from the final worktree;
- branch and remote state match the requested handoff;
- generated projects inherit valid configuration after token replacement or
  renaming;
- changelog comparison links use a real canonical remote rather than a guessed
  URL;
- macOS hidden flags, sync-conflict copies, or `.icloud` placeholders are not
  breaking virtual environments or tool state.

Use `git check-ignore --no-index -v PATH` with concrete examples. Avoid adding
ignore entries for undocumented conventions merely because a filename sounds
tool-specific.

### 5. Handle failures without masking them

Classify each failure as one of:

- repository defect;
- changed behavior needing a regression test;
- missing dependency or unavailable network;
- damaged local environment;
- unrelated user-owned file interfering with a broad gate;
- expected skip or unsupported platform.

When sync-conflict copies appear during verification:

1. Record the affected paths before cleanup.
2. Remove only known disposable caches such as `.mypy_cache`, `.pytest_cache`,
   and `.ruff_cache`, and only when the task authorizes cleanup.
3. Rerun the affected check once.
4. Run the audit utility immediately after the rerun.
5. If conflict copies reappear, stop the cleanup loop and classify the checkout
   as under active sync churn. Report final QA as blocked by the environment and
   recommend moving the checkout outside the synced folder.
6. Do not automatically delete conflict copies in source, tests, `.git`, other
   non-cache paths, or virtual environments.

Preserve the failing evidence. If an unrelated file blocks the broad gate,
leave it untouched, test the intended tracked state in a temporary copy, and
report both results. A clean temporary result does not make the raw worktree
clean.

### 6. Hand off publishing requests

When the same user request also includes a commit, push, branch publication, or
pull request:

1. Finish verification and authorized artifact cleanup first.
2. Record the verified HEAD, intended changed paths, verification command,
   result, and final `git status --short --branch`.
3. Hand ordinary publishing requests to a host-native GitHub publishing workflow
   when one is available. Use `$github-publish-changes` only when the user selected
   it or its specialized basic-commit, exact-identity, mixed-worktree, fork,
   force-lease, or CI-monitoring behavior is required. Use the installed GitHub
   publisher when no host-native workflow is available.
4. Leave all staging, commit, push, and pull-request actions to that publishing
   skill. Do not duplicate them here.
5. Require the publishing skill to rerun affected checks when hooks, generated
   files, conflict copies, or any other change makes the tree differ from the
   verified state.

### 7. Clean and report

Remove only artifacts created by the verification run, and only when cleanup is
requested or clearly part of the task. Preserve virtual environments unless the
user authorizes recreation. Re-run `git status` after cleanup without invoking
tools that regenerate caches.

Report:

- the authoritative gate and its result;
- test counts, skips, coverage, runtime versions, and smoke-test outcomes;
- repairs made and regression tests added;
- remaining blockers, unrelated files, and untested surfaces;
- current branch, commit, and worktree state.

Keep the final result concise and lead with readiness or the blocking finding.

## Bundled utility

`scripts/repo_audit.py` is read-only. It reports git/worktree hygiene, tracked
files matching ignore rules, local branch state, generated build or coverage
outputs, hidden `.pth` files, sync-conflict copies, and iCloud placeholders.
Routine ignored test caches do not produce findings. The utility accepts repeated
`--expect-ignored` and `--expect-trackable` arguments for project-specific
ignore-policy checks. Treat its warnings as evidence to assess, not universal
policy violations.
