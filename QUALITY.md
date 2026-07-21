# Quality design

`make check` is the repository's canonical full quality gate. Standard commits,
commit-and-push requests, explicit `full-check` requests, and GitHub Actions use
it. An explicit `basic commit` or `quick commit` uses the smaller staged-tree
gate described below.

## Verification tiers

### Full gate

Run `make check` for `full-check`, a standard commit, or commit and push. Run it
once for an unchanged candidate tree; the push phase can reuse that result. A
push-only request can reuse a prior full result when it identifies the exact
commit being pushed.

The full gate runs these checks in order:

1. Ruff formatting and lint checks for repository Python.
2. Strict mypy analysis for maintained Python utilities.
3. Yamllint for skill metadata, Dependabot configuration, and GitHub Actions
   workflows.
4. Repository-specific semantic validation for Agent Skills packages.
5. Deterministic behavioral contracts for the repository workflow skills.
6. Pytest regression and edge-case tests.
7. A reviewed-baseline scan for probable credentials.
8. Git's whitespace-error check for the working diff.

### Basic commit gate

Use this tier only when the user explicitly asks for a `basic commit`, `quick
commit`, or clearly asks to skip the full suite. Stage and inspect the intended
tree first, then run `make basic-commit-check`. It performs the reviewed-baseline
credential scan and `git diff --cached --check`. Normal commit hooks still run.

This tier omits Ruff, mypy, Yamllint, semantic skill validation, pytest, and
coverage. Report those omissions with the resulting commit. CI still runs the
full gate after publication.

The repository audit is a separate contextual readiness check rather than part
of either deterministic gate. It reports environment, branch, generated-output,
and hygiene findings that may be useful during final QA without making those
contextual warnings failures of `make check`. Routine ignored test caches stay
silent.

Dependencies are declared in `pyproject.toml` and resolved in `uv.lock`. The
repository is a tooling project rather than an installable Python package, so uv
runs it with `package = false`. Its cache stays in the ignored `.uv-cache/`
directory so restricted agent environments do not need access to a home-directory
cache. Every uv-backed Make target uses `uv run --locked`, which prepares the
managed environment on demand and fails if `uv.lock` needs to change. Make places
that environment in uv's standard `.venv/` directory, so direct `uv run` and
Make invocations share one project environment. The lockfile supports repository
maintenance and CI; installed skill packages do not use it. Python 3.10 is the
compatibility floor because the maintained scripts use modern type syntax
introduced in that release. CI tests both 3.10 and 3.14 to cover the supported
floor and current runtime.

## Design decisions

### Canonical skill source

The version-controlled packages under `skills/` are canonical. Personal live
installs use symlinks under `~/.agents/skills/` so the installed behavior is the
same content covered by repository validation and behavioral contracts.
Independent copies under `~/.codex/skills/` are unsupported because they can
drift silently. Preserve and compare any legacy copy before replacing it with a
link.

### Python style and correctness

Ruff is both formatter and linter, which avoids conflicting formatters. The rule
set covers syntax errors, imports, modernization, common bugs, security patterns,
simplifications, Pylint-style structural issues, and Ruff-specific checks. The
per-file security exceptions cover pytest assertions and reviewed argument-vector
subprocess calls; shell execution remains prohibited. Line-length linting is
disabled because the scripts emit Markdown-rich diagnostic commands whose
readability is harmed by mechanical wrapping. Magic-number warnings are also
disabled because exit codes and small protocol limits are clearer next to their
use. Ruff's formatter still uses an 88-column target where it can wrap code
safely.

Mypy runs in strict mode against maintained utility code. Tests are exercised by
pytest and Ruff but are excluded from the strict typing boundary so fixtures and
subprocess assertions do not dilute the signal from production code.

### YAML structure and semantics

Yamllint enforces parsing, indentation, duplicate-key, trailing-space, and
newline rules across skill metadata and repository automation configuration.
Document-start and line-length requirements are disabled: the optional
`agents/openai.yaml` convention does not require `---`, and quoted default
prompts are intentionally readable as single scalar values.

`scripts/check_skills.py` adds checks that a generic YAML linter cannot provide.
It verifies package naming and frontmatter, relative references, executable
script modes, optional OpenAI metadata and implicit-invocation policy constraints,
and exact agreement between the root inventory and the skill directories.

### Tests and coverage

Pytest covers clean, dirty, unborn, conflicted, detached, linked-worktree,
malformed, invalid-object, stale-remote, and incomplete-push states for the
publishing preflight; repository audit findings and exit behavior; scanner
failures; malformed skill packages and metadata; and defensive parsing paths.
The tests use temporary repositories and isolated Git configuration so they
cannot modify this checkout or depend on a user's Git settings. Preflight
read-only assertions cover status, index, refs, configuration, fetch metadata,
objects, and worktree administration.

Coverage measures statements and branches across the subprocess boundaries used
by the command-line tests. The combined result must remain at or above 95 percent
and reports missing lines and partial branches. The suite reaches that floor
through behavior cases for invalid skill packages, scanner failures, Git state,
local-environment damage, and defensive parsing. Keep assertions on observable
results; do not add implementation-coupled tests solely to execute a line.

The threshold applies to the combined maintained utilities rather than imposing a
per-file quota. This keeps small platform adapters and exceptional defensive paths
from forcing artificial tests while preserving a hard repository-wide gate.
Review the per-file report and add regression cases when a module drops materially.

### Skill behavioral contracts

`scripts/check_skill_behavior.py` is an evaluator that does not load the checked
skills as instructions. It checks machine-readable contracts and calibrated
outputs in `tests/fixtures/skill_behavior.yaml`. Each complex scenario contains
four variants: an unguarded baseline, a treatment, a same-skill self-review, and
an intentionally weakened mutation. The treatment must pass every independent
hard check and beat the baseline. Baseline and mutation variants must fail. The
self-review is diagnostic evidence and cannot rescue a failing treatment.

The fixture covers every current repository skill. It checks verification tier
selection, exact refspecs and force leases, strict push exception modes,
pull-request merge-method selection, exact head-SHA guards, merge-state
verification, shared agent-instruction imports, nested scope,
audit-versus-repair boundaries, repository-readiness uncertainty, read-only
branch and repository audits, recorded-SHA deletion evidence, and commit, push,
merge, bypass, delayed-merge, repair, or branch-deletion authorization
boundaries. Authorization and verification checks are hard gates in their
scenarios. Contract mutation
checks remove required instructions and inject forbidden weakening language;
every mutation must be detected.

This suite proves the checked instructions remain present and that the evaluator
detects its calibrated regressions. Model behavior is stochastic, so deterministic
CI cannot prove every future response will comply. Required CI does not call a
hosted model because credentials, cost, model updates, and sampling variance
would make repository verification less repeatable. Use isolated live-model
evaluations as periodic evidence, with human-scored calibration data and no skill
instructions loaded into the evaluator.

### Credential and privacy checks

`scripts/check_secrets.py` scans tracked and non-ignored untracked files with
detect-secrets and compares findings with `.secrets.baseline`. New probable
credentials fail the gate. Any baseline update must be reviewed in plain text
before it is accepted.

Credential scanning does not detect all personal information. Review personal
skill content manually before the repository is made public or shared as an
archive.

### Continuous integration

GitHub Actions invokes the same `make check` target used locally. The workflow
has read-only repository permissions. The official uv setup action is pinned to
an immutable commit, as is the official checkout action. Review and update those
pins when either action publishes a security or maintenance release.

### Dependency updates

`.github/dependabot.yml` checks the root uv project and GitHub Actions monthly.
It groups updates within each ecosystem, caps open version-update pull requests
at 2 per ecosystem, and uses the `chore(deps)` commit prefix. Dependabot does
not auto-merge changes; every update remains subject to review and the Quality
workflow.

Dependabot alerts and security updates are controlled through GitHub repository
settings. GitHub can raise version-update pull requests for SHA-pinned actions.
Dependabot alerts require semantic-version action references, so SHA references
need separate advisory review. Review the exact uv runtime requirement in
`pyproject.toml` separately during dependency maintenance.

## Deliberate deferrals

- Markdownlint is deferred because the skill documents intentionally mix long
  prompts, examples, and host-specific syntax. Add it only with a small,
  documented rule set after reviewing every existing document.
- Bandit is deferred because these scripts intentionally invoke Git and other
  local tools through argument-vector subprocess calls. Ruff's security rules
  already cover the relevant Python patterns with less duplicate noise. Revisit
  this if a script begins handling network input, credentials, or a service
  boundary.
- Pre-commit is deferred because `make check` and CI already provide one source
  of truth. Add a thin pre-commit wrapper only if contributors repeatedly forget
  to run the gate; it should call existing targets rather than duplicate tool
  configuration.
- Actionlint is deferred because the repository has one small workflow and no
  local Go toolchain. Yamllint catches YAML defects and GitHub validates workflow
  semantics on publication. Add actionlint when workflow logic expands.

## Updating the gate

Use `uv lock --upgrade` deliberately, inspect dependency changes, and run
`make check`. Update a secret baseline only after reviewing every finding; run
`make secrets-baseline`, inspect the diff, and prefer removing or narrowly
allowlisting false positives over accepting them.
Update this document whenever a rule, supported Python version, tool, exception,
or deferral changes. Generated caches and validation artifacts must remain
untracked.
