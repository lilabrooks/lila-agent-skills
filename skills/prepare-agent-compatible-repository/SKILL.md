---
name: prepare-agent-compatible-repository
description: Audit, create, and reconcile repository instructions and agent-facing configuration so a project works consistently with Codex and Claude Code. Use when asked to add or review AGENTS.md, AGENTS.override.md, CLAUDE.md, CLAUDE.local.md, .claude rules or settings, .codex project configuration, shared Agent Skills packages, nested instruction scope, setup and verification commands, or cross-agent repository readiness. Keep shared rules in one place, preserve intentional host differences, and distinguish behavioral guidance from enforced controls.
---

# Prepare an agent-compatible repository

Create a compact shared instruction layer, add the smallest host adapters needed by Codex and
Claude Code, and verify that both agents receive equivalent repository facts and commands.

## Boundaries

- Treat an audit or compatibility question as read-only. Report findings without editing files.
- Treat an explicit setup, repair, or reconciliation request as authority to change only the
  repository instruction and agent-configuration files within the requested scope.
- Preserve unrelated work, local preferences, personal memory, credentials, generated state,
  global configuration, and files outside the repository.
- Inspect existing instruction files before editing. Ask for direction when conflicting rules
  require a product, policy, or workflow choice that repository evidence cannot resolve.
- Do not install either agent, sign in, change global settings, enable network access, or add an
  external integration unless the user requests that separate action.
- Consult current official Codex and Claude Code documentation before encoding host-specific
  loading, settings, hook, permission, or skill behavior when documentation access is available.
  Mark an unverified host assumption instead of presenting it as current fact.

## 1. Establish the repository baseline

1. Locate the repository root and capture the branch and worktree state.
2. Read every instruction file that applies to the current scope before acting, including root and
   nested `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, and `CLAUDE.local.md` files.
3. Inspect `.claude/rules/`, `.claude/settings.json`, `.claude/settings.local.json`, project
   `.codex/config.toml`, repository skills, hooks, MCP configuration, CI workflows, contribution
   guides, task runners, manifests, and lockfiles when present.
4. Discover imports, symlinks, nested scopes, ignored local files, and instruction files that are
   accidentally untracked or excluded.
5. Identify the repository's actual setup, lint, format, typecheck, test, build, and handoff commands
   from executable configuration and CI. Record contradictions with prose documentation.
6. Classify each rule as shared repository guidance, Codex-specific behavior, Claude-specific
   behavior, personal local preference, or mechanically enforced policy.

Do not infer that a missing file is defective before checking whether the repository intentionally
supports only one host or stores equivalent guidance elsewhere.

## 2. Use one shared instruction source

Keep `AGENTS.md` as the shared repository instruction source. Put facts and rules needed by both
agents there: repository layout, setup, commands, code conventions, verification, safety boundaries,
generated-file policy, and Git expectations.

Create a project `CLAUDE.md` that imports `@AGENTS.md`:

```markdown
@AGENTS.md

## Claude Code

<!-- Claude-specific instructions only, when needed. -->
```

Do not copy shared instructions into both files. Preserve one editable copy and keep the adapter
small. Prefer the import over a symlink for repositories used across operating systems and tooling
that may not preserve symlinks.

Apply the same pattern to nested scopes:

- Let a nested `AGENTS.md` own shared instructions for its directory tree.
- Add a same-directory `CLAUDE.md` importing `@AGENTS.md` when Claude needs the same scoped rules.
- Keep nested adapters free of parent instructions that each host already loads.
- Check import paths relative to the importing file and reject missing targets or import cycles.
- Treat `AGENTS.override.md` as a Codex-specific override surface. Provide explicit Claude-side
  guidance only when that override expresses behavior Claude also needs.

Preserve an intentional standalone `CLAUDE.md` when it contains genuinely Claude-specific guidance.
Reconcile duplicated shared content only after comparing meaning, scope, and precedence.

## 3. Write useful shared guidance

Include only information an agent cannot safely or quickly infer from the repository. Prefer exact
commands and paths over general advice.

Cover the applicable parts of this checklist:

- repository purpose, important directories, and architectural boundaries;
- supported runtimes, package manager, dependency setup, and lockfile policy;
- authoritative focused and full verification commands;
- formatting, linting, typing, testing, build, and generated-file expectations;
- allowed scope inference, user-owned changes, secrets, network, and destructive-action rules;
- branch, commit, push, pull-request, release, and deployment authority boundaries;
- platform constraints, unavailable services, and known environment quirks;
- nested instruction locations and when they apply.

Keep instructions concise, concrete, current, and internally consistent. Remove discovered facts
that merely restate obvious source code. Move lengthy task procedures into skills or repository
documentation, then link them from the instruction file when agents need them.

## 4. Preserve host-specific controls

Keep host adapters explicit:

- Store Codex project settings and hooks in their documented Codex surfaces.
- Store Claude Code settings, permissions, hooks, subagents, and path-scoped rules in their
  documented Claude surfaces.
- Keep the core `SKILL.md` of a shared Agent Skills package useful without optional host metadata.
- Preserve host-specific metadata in optional adapter files rather than embedding it into the
  shared workflow unless the workflow truly depends on that host.
- Record a compatibility gap when one host has no equivalent feature. Do not fabricate a mapping.

Instructions guide agent behavior; they are not an enforcement guarantee. Use repository tests,
CI, hooks, sandbox or permission settings, and branch policy for controls that must execute or block
an action. Do not turn instructions into enforcement claims.

## 5. Audit compatibility

Check and report:

1. **Discovery:** each host can discover its root and nested instruction files in the intended
   working directories.
2. **Shared content:** `CLAUDE.md` imports the applicable `AGENTS.md`, with no stale duplicated
   shared rules.
3. **Scope:** nested rules reach the same files, and host-specific overrides do not silently change
   shared policy.
4. **Commands:** documented setup and verification commands exist, are non-interactive where
   automation requires it, and agree with CI and lockfiles.
5. **References:** imported files, paths, scripts, skills, hooks, and configuration references
   resolve inside the intended scope.
6. **Controls:** permissions, hooks, sandbox rules, and CI are described according to what they
   actually enforce.
7. **Hygiene:** local instruction files, caches, credentials, and agent state are ignored when they
   should remain personal; shared guidance and configuration remain trackable.
8. **Portability:** platform-specific commands, symlinks, shells, and required network phases are
   disclosed and have a supported path for each target environment.

Classify each result as compatible, blocking gap, warning, intentional host difference, or
unverified current-host behavior. A static file audit cannot prove that a future model will follow
every instruction.

## 6. Reconcile safely

1. Make the smallest edits that establish the shared-source pattern and preserve existing meaning.
2. Keep repository-wide rules in the root `AGENTS.md`; move host-only content to the corresponding
   adapter without widening its scope.
3. Add nested adapters only where nested shared instructions exist or a host-specific rule needs
   that scope.
4. Preserve comments, local conventions, and valid settings. Do not replace an entire instruction
   file merely to normalize formatting.
5. Leave hooks, permission rules, CI, dependency files, and global configuration unchanged unless
   the user included them in the repair request.
6. Reinspect the complete diff and verify that no shared rule was lost or weakened.

## 7. Validate and report

Validate relative imports, symlink targets, nested scope, configuration syntax, referenced commands,
and ignore behavior. Run the repository's documented checks when the request includes repair or
readiness verification. Request authorization before checks that need network access, credentials,
external writes, or destructive cleanup.

When either host is already available, use its read-only diagnostics to confirm loaded instruction
sources when that can be done without changing configuration or consuming unapproved external
resources. Otherwise report static verification only.

Report the files inspected and changed, the shared-source arrangement, host-specific differences,
commands verified, remaining gaps, documentation freshness, and final worktree state. Hand a final
repository-readiness request to `$verify-repository` when available; keep staging, commits, pushes,
and pull requests in their publication workflow.
