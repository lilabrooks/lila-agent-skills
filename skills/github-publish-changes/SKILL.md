---
name: github-publish-changes
description: Safely check, commit, and push intended local Git changes to GitHub when the user explicitly invokes this skill, requests its basic or quick commit tier, asks for exact candidate identity, or needs its handling for partial staging, dirty push-only worktrees, forks, exact force leases, or CI monitoring. Leave ordinary commit, push, and pull-request requests to a host-native publisher when one is available unless the user selects this skill. Stop at the requested boundary, preserve unrelated work, verify the exact candidate, and require separate authority for pull requests, tags, releases, deployments, bypasses, and rewritten history.
---

# GitHub publish changes

## Scope

Carry out the terminal action the user requested:

- **Full-check:** run the repository's full gate against the intended tree and stop.
- **Commit only:** run the full gate by default, then stage and commit locally.
- **Basic commit:** stage, inspect, run the repository's basic staged-tree gate, and commit
  locally. Use this tier only when the user explicitly asks for it.
- **Push only:** inspect and push existing commits; leave the index and worktree alone.
- **Commit and push:** stage, verify, commit, and push.
- **Publish a branch:** push the named or current branch and set its upstream when needed.

Use this skill when it was explicitly selected or its specialized basic-commit, exact-identity,
mixed-worktree, fork, force-lease, or CI-monitoring behavior is needed. Let a host-native GitHub
publisher own ordinary commit, push, and pull-request requests when that workflow is available.
Let a repository-verification workflow own a standalone readiness or final-QA audit unless this
skill's exact publication candidate is the object being verified.

Treat each requested terminal action as its authority boundary. Full-check permits verification
and its ordinary temporary outputs. Commit permits intentional staging and one local commit; it
does not permit a push. Both commit-only and combined commit-and-push requests also permit the
narrowly proven fast-forward of a topic branch created for the current request when its base
advances before the commit. Follow the remote edge-case reference and ask before moving any
pre-existing or ambiguously owned branch.
Push permits inspection, a narrowly targeted fetch of the destination, and one normal push of
existing commits; it does not permit staging or committing. A combined commit-and-push request
permits both phases in order. Branch publication permits creation of the named remote branch and
its upstream association.
None of these actions permits a pull request, tag, release, deployment, policy bypass, force push,
destructive cleanup, or any other persistent configuration change unless the user grants that
authority separately.

Send any request that also creates a pull request to the host's pull-request workflow when
one exists. End at the requested commit or push boundary when the host has no such workflow.
Require explicit user intent for tags, GitHub Releases, packages, deployments, and hosting.

Use local `git` for repository inspection and Git writes. Prefer an authenticated GitHub
connector or app for repository metadata and remote confirmation. Check `gh` authentication
only when a connector gap requires the CLI. Select tools by capability when hosts use
different tool names.

## Bundled resources

- Run `scripts/publish_preflight.py` before each Git write. Select `full-check`, `commit`, or
  `push` as the operation. It applies only that operation's remote, comparison, branch, and
  identity requirements without changing repository refs, objects, the index, or the worktree.
  An ordinary push rejects a destination that is ahead or divergent. Pass
  `--destination-branch-absent` only after confirming a new destination is absent, or
  `--rewritten-history-authorized` only after explicit force-push authorization. Never combine
  those modes.
- Read [candidate-tree-verification.md](references/candidate-tree-verification.md) when the
  worktree is mixed or dirty, the request is push-only, or the repository gate needs Git
  metadata, submodules, or Git LFS content.
- Read [remote-and-ci-edge-cases.md](references/remote-and-ci-edge-cases.md) when the request
  involves a fork, default-branch policy, a base branch that advanced during preparation,
  rewritten history, a remotely deleted branch, administrator bypass, or CI monitoring.

## 1. Establish authority, state, and scope

1. Read applicable host and repository guidance, including `AGENTS.md`, `CLAUDE.md`, local
   overrides, `CONTRIBUTING.md`, `SECURITY.md`, release instructions, and equivalents.
   Treat absent community files as normal.
2. Find the repository root and run:

   ```bash
   python3 <skill-dir>/scripts/publish_preflight.py \
     --root <repository> --operation <full-check|commit|push> --strict
   ```

   For push, also pass `--remote <remote>` and `--compare-ref <fetched-commit-ref>`. The
   comparison must resolve to a commit. For a confirmed new destination, compare with the
   reviewed base and pass `--destination-branch-absent`. For an explicitly authorized rewrite,
   compare with the fetched destination and pass `--rewritten-history-authorized`. Never pass
   both. Record the branch, `HEAD`, upstream, operation state, unmerged paths, index fingerprint,
   the requested operation identity, staged paths, unstaged paths, untracked paths, worktrees,
   and outgoing range.
3. Stop before staging when an unresolved merge, rebase, cherry-pick, revert, bisect, or
   unmerged index is present. Continue such an operation only when the user explicitly asked
   for that operation's continuation.
4. Accept null `HEAD`, upstream, remote, recent history, and policy values in a new repository.
   An unborn attached branch supports commit-only work. Ask for a target branch before
   committing from detached `HEAD`.
5. Inspect the complete intended content. For a new commit, review staged, unstaged, and
   untracked changes. For push-only, review every outgoing commit and their cumulative diff.
   Treat all existing changes and staging boundaries as user-owned.
6. Infer scope only when every included path and hunk clearly belongs to the request. Ask for
   direction when a same-file hunk, pre-staged path, generated file, deletion, rename, binary,
   submodule, or Git LFS change has uncertain ownership.
7. Before each Git write, rerun the preflight for that operation and compare the branch, `HEAD`,
   upstream SHA, operation state, operation identity, index fingerprint, and path sets with the
   prior checkpoint. Inspect any changed state before proceeding.

## 2. Choose the branch and remote

1. For ordinary commit-only work on an attached branch when no base advancement is known, keep
   the current branch and skip fetches, GitHub policy queries, and remote selection. When a
   request-created topic branch's base is known to have advanced, fetch only that selected base
   and follow the remote edge-case reference.
2. Honor an explicit user branch or remote. Validate a branch once with Git and pass the
   resolved branch and ref as literal arguments to later commands.
3. When branch creation is authorized, choose its prefix from user instructions, repository
   instructions, then host configuration. Use a concise descriptive name when none applies.
4. For a push, identify the push repository, remote, local branch, remote branch, upstream,
   and base branch as separate values. Confirm the push URL belongs to the intended GitHub
   repository without printing embedded credentials.
5. Fetch the selected remote when network access and authorization permit. Resolve the exact
   remote branch SHA and compare it with local `HEAD`. Stop on unexpected divergence. When a
   request-created topic branch's base advanced before commit, follow the remote edge-case
   reference before moving the branch.
6. Inspect the full outgoing range after the fetch: commit list, subjects, authors, signatures
   when policy requires them, name-status, cumulative patch, submodules, and Git LFS pointers.
   Ask for a base branch when a new branch has no unambiguous comparison ref.
7. Query repository rules and legacy branch protection only for a flow that will push. When
   default-branch policy is unavailable, report the uncertainty and request the route unless
   the user already named that branch. An explicit default-branch push authorizes one normal
   attempt after the warning. Require separate approval for administrator bypass.
8. Load the remote edge-case reference when any condition listed there applies.

## 3. Stage intentionally

Skip this section for push-only and full-check requests.

1. Preserve the initial index. When it contains out-of-scope entries, ask whether to include
   them or use a separate commit strategy. Leave them staged until the user authorizes a
   staging change.
2. Use patch staging for mixed-purpose hunks in one file. Ask for direction when a safe hunk
   split is uncertain. Path staging is suitable only when the entire path belongs in scope.
3. Recapture the checkpoint, then stage explicit paths or hunks. Use whole-worktree staging
   only after confirming every change belongs in the commit.
4. Inspect `git diff --cached --stat`, `git diff --cached --name-status`, and the full staged
   patch. Confirm file modes, deletions, renames, generated files, binaries, submodules, and
   Git LFS pointer changes.
5. Run `git diff --cached --check`. Resolve every error before committing.
6. Check staged path names for environment files, private keys, credentials, coverage data,
   caches, and build output without printing secret contents. Use a repository-native secret
   scanner when one is already configured. A filename scan alone cannot establish safety.
7. Stop on an empty staged set unless the user explicitly requested an empty commit.

## 4. Verify the exact candidate tree

1. For a new commit, record `candidate_index_tree` from the commit preflight after staged-patch
   review. The helper computes it with temporary index and object storage. For standalone
   full-check, record `checkout_fingerprint_sha256`. For push-only, record `HEAD^{tree}` and the
   complete outgoing commit range.
2. Select the verification tier from explicit user intent:
   - Run the repository's full handoff gate for `full-check`, a standard commit, and commit and
     push. Reuse a result only when it identifies the same operation identity and the surrounding
     state has stayed fixed.
   - For an explicit `basic commit` or `quick commit`, use the repository's documented basic
     staged-tree gate. When no basic gate exists, run `git diff --cached --check` and any
     configured secret scanner. Stop when repository policy requires the full gate.
   - For push-only, reuse a prior full result when it identifies the exact commit. Inspect the
     outgoing range and follow any push-time checks required by repository policy.
3. Treat an unqualified `commit` as the full tier. Never infer the basic tier from urgency,
   change size, or a request to move quickly.
4. Run a full gate in the current checkout only when tracked files match the candidate tree and
   out-of-scope untracked files cannot affect it. Use an isolated snapshot for every mixed or
   dirty worktree. Do not create repository objects, refs, or worktrees merely to obtain an
   identity. Follow the candidate-tree reference for snapshot selection and authorization.
5. Inspect in-scope configuration, documentation, lockfiles, generated files, submodules, and
   Git LFS behavior. Preserve evidence from missing tools or dependencies. Request permission
   before network installation or changes to manifests, lockfiles, environments, or system
   state.
6. Recapture the checkpoint after verification. Require the same candidate tree, branch,
   `HEAD`, index fingerprint, and operation state. Invalidate the earlier verification result after any movement of `HEAD`.
   Include a safe fast-forward to a newer base. Restage, review, record the new candidate identity,
   and rerun the selected gate. Review verification artifacts separately and remove only artifacts
   created by the check when cleanup is authorized.

## 5. Commit

1. Use a user-supplied message when provided. Otherwise derive it from the full staged diff
   and follow the repository's recent style and documented conventions.
2. Confirm Git author identity is usable. Keep repository and global identity unchanged unless
   the user explicitly requests a configuration change.
3. Recapture the checkpoint immediately before committing. Require the reviewed candidate tree
   and staging boundary to remain fixed.
4. Run normal commit hooks. Bypass hooks only after the user sees the failure and explicitly
   authorizes `--no-verify`.
5. Capture the commit SHA and compare `HEAD^{tree}` with the verified candidate tree. A mismatch
   means hooks or concurrent activity changed the commit; stop and inspect it.
6. Inspect the commit's name-status and run status immediately. Review hook-created tracked or
   untracked changes before any push. Amend or add a follow-up commit only with authorization.
7. End here for commit-only requests.

## 6. Push

1. Confirm the remote is accessible and points to the intended GitHub repository. Track
   connector access, `gh` authentication, and Git transport authentication independently.
   Report the channel that failed and leave credentials unchanged.
2. Fetch immediately before pushing. For an existing destination, record its observed SHA and
   rerun ordinary push preflight with the selected remote and that comparison ref. Stop when the
   destination is ahead or divergent. For a destination confirmed absent, use the reviewed base
   as the comparison and pass `--destination-branch-absent`. For explicitly authorized rewritten
   history, compare with the observed destination SHA and pass
   `--rewritten-history-authorized`. Never combine those modes. Inspect the outgoing commit list
   and cumulative patch again. Require local `HEAD` and the intended refspec to remain fixed.
3. Push a literal source-to-destination branch refspec. Set upstream for a new branch. Avoid
   implicit `push.default`, matching refspecs, tags, and extra configured destinations.
4. Use normal fast-forward push behavior by default. For explicitly authorized rewritten
   history, use an exact lease:

   ```text
   --force-with-lease=refs/heads/<branch>:<observed-remote-sha>
   ```

   Pass the resolved ref and observed SHA as literal arguments. Never use plain `--force`.
5. Preserve non-fast-forward, policy, permission, and authentication failures as evidence.
   Leave branches, history, remotes, and credentials unchanged after a rejected push unless
   the user authorizes a separate recovery action.
6. After success, confirm the exact remote branch ref equals local `HEAD` with a branch-ref
   connector or `git ls-remote <remote> refs/heads/<branch>`. Confirm upstream and final status.
7. End after the requested push.

## 7. Report and monitor

Report the completed boundary with the branch, upstream, commit SHA, remote repository, staged
scope, commit message, verified tree SHA, verification command and result, outgoing commit
range, remote-SHA confirmation, final worktree state, and deliberately uncommitted files. For a
basic commit, state that the full suite was skipped and name the checks that ran.

When the user asks to wait for CI, read the CI section of the remote edge-case reference and
monitor until a terminal state. Report unrequested CI as pending or unverified.

## Safety rules

- Preserve unrelated changes, partial staging, and existing worktrees.
- Keep commits, pushes, branch creation, pull requests, tags, releases, and cleanup within the
  user's stated boundary.
- Keep Git configuration, remotes, repository policy, credentials, and local refs unchanged
  without explicit authority.
- Keep release preparation, version changes, tags, GitHub Releases, packages, deployments, and
  hosting in their separately requested workflows.
