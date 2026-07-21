---
name: github-merge-pull-request
description: Safely inspect and merge an identified GitHub pull request with an explicit merge method and an exact head-SHA guard. Use when asked to assess merge readiness, choose or perform squash, merge-commit, or rebase merging, enable auto-merge, enter a required merge queue, perform an explicitly approved administrator bypass, or handle separately authorized post-merge branch deletion. Preserve repository rules and require distinct authority for delayed merges, bypasses, branch updates, and cleanup.
---

# GitHub merge pull request

Inspect the exact pull-request candidate, respect repository policy, perform only the requested
merge outcome, and verify GitHub's resulting state.

## Boundaries

- A read-only mergeability or method question authorizes inspection only.
- A request to merge one identified pull request authorizes one policy-compliant merge attempt
  against its inspected head SHA.
- Do not infer auto-merge, merge-queue enrollment, administrator bypass, or branch deletion from
  a direct merge request. Require explicit intent for each one.
- Keep pull-request creation, branch updates, conflict resolution, reviews, check reruns, repository
  settings, releases, deployments, and local history changes outside this skill unless the user
  separately requests the relevant workflow.
- Treat an already merged or closed pull request as a terminal state. Report it without trying to
  recreate, reopen, or merge it.

Use an authenticated GitHub connector or app for metadata and merge operations when it can select
the method and bind the write to the expected head SHA. Use `gh` when the connector lacks either
capability. Keep connector access, `gh` authentication, and Git transport authentication as
separate facts, and never print credentials or credential-bearing URLs.

## 1. Identify the exact candidate

1. Read repository guidance, contribution rules, and merge policy.
2. Resolve the repository owner, repository name, and pull-request number. Use these explicit
   identifiers for every write; do not let the current branch select a pull request implicitly.
3. Query GitHub and record the pull-request URL, state, draft status, base branch, head repository,
   head branch, head SHA, author, mergeability, review decision, checks, merge queue requirement,
   current auto-merge state, and existing merge result.
4. Inspect the commits and complete pull-request patch. Flag submodules, Git LFS pointers,
   generated files, workflows, dependency or lockfile changes, and other content whose review
   status is unclear.
5. Ask for the target when multiple repositories or pull requests fit the request. Never guess a
   pull-request number, base branch, or repository.

## 2. Establish merge eligibility

1. Require the pull request to be open and out of draft state.
2. Inspect required reviews, unresolved review threads when available, required status checks,
   merge conflicts, rulesets, branch protection, allowed merge methods, and merge-queue policy.
3. Do not approve the pull request, dismiss reviews, resolve conversations, update its branch,
   rerun or bypass checks, or push conflict resolutions as part of merge preparation.
4. For a direct merge, require every enforceable requirement to be satisfied before invoking the
   merge tool. Some `gh pr merge` paths enable delayed merging when checks are pending, so do not
   invoke it early unless the user explicitly requested auto-merge or queue enrollment.
5. Requery the pull request immediately before the write. Require the repository, pull-request
   number, base branch, head repository, head branch, and head SHA to match the inspected candidate.
   Reinspect the patch and requirements when the head SHA or base branch changes.

Report a blocked merge with the failed or pending requirements. Preserve the pull request and its
branches unless the user separately asks to address a blocker.

## 3. Select the outcome and method

Distinguish these terminal actions:

- **Direct merge:** merge now after every requirement passes.
- **Auto-merge:** register a future merge after requirements pass. Require an explicit auto-merge
  request and confirm that the repository permits it.
- **Merge queue:** enqueue the pull request under the base branch's queue policy. Require explicit
  consent to queue when the original request asked for an immediate merge.
- **Administrator bypass:** merge despite named unmet requirements. Require explicit bypass intent
  after showing those requirements; ordinary merge permission is insufficient.

Choose the method with these rules:

1. Honor an explicit `squash`, `merge commit`, or `rebase` request when the repository and base
   branch allow it.
2. Use the repository's only allowed method when exactly one is available.
3. When several methods are available and the user did not choose one, ask before writing.
4. Stop when the requested method is disabled. Do not silently substitute another method.
5. Let a required merge queue control its merge method. Do not claim that a caller-selected method
   will override queue configuration.

Map a direct CLI merge to exactly one of `--squash`, `--merge`, or `--rebase`. Preserve the
repository's configured commit-message defaults unless the user supplied a subject or body. Show
any agent-proposed subject or body before the write, then pass only the approved text. Do not change
the merge author email without explicit instruction.

## 4. Execute against the inspected head

Prefer a connector write that accepts the pull-request identity, selected method, and expected head
SHA. Otherwise use a fully qualified, non-interactive CLI command:

```text
gh pr merge <number> --repo <owner/repository> --<merge|squash|rebase> --match-head-commit <head-sha>
```

Use the literal number, repository, method flag, and full inspected SHA. Add `--subject` or `--body`
only for user-approved text.

For explicitly authorized auto-merge, add `--auto` after verifying that delayed mutation is the
requested outcome. For a required merge queue, omit the strategy when GitHub says the queue owns it
and confirm that the user authorized queue enrollment. Add `--admin` only after explicit bypass
authorization tied to the currently reported unmet requirements.

Preserve head-mismatch, policy, permission, authentication, and mergeability failures as evidence.
Do not retry with a weaker guard, another method, auto-merge, or administrator privileges.

## 5. Handle branch deletion separately

Never pass `--delete-branch` as part of the merge command. Finish and verify the merge first.

When branch deletion was separately requested, apply a branch-cleanup workflow to the exact recorded
head SHA. Protect default and protected branches, forks outside the user's authority, branches used
by open pull requests, branches checked out in any worktree, and branches whose tips changed. Keep
the branch when safety cannot be proved, and report why. Treat merge success followed by cleanup
failure as a partial result.

## 6. Verify and report

Query GitHub after the write rather than relying on a command's exit status.

- For a direct merge, confirm the pull request is merged and record the merged time, resulting
  commit SHA, base branch, selected method, merged-by identity, and original head SHA.
- For auto-merge, confirm the request is enabled for the same head SHA and report its pending
  requirements. Do not claim the pull request is merged until GitHub reports it as merged.
- For a merge queue, confirm the queued or pending state and report available queue details. Do not
  claim completion while GitHub still reports a queued state.
- Confirm whether the source branch was retained. Report deletion only after separate remote and
  local verification.

Monitor a delayed merge only when the user asks to wait. Otherwise report the exact current state
and leave it pending. End after the requested merge outcome and verification.

## Safety rules

- Bind every merge write to the inspected full head SHA.
- Never use administrator bypass to recover from an ordinary merge rejection without new explicit
  authority.
- Never force-push, update, close, reopen, edit, approve, or delete the pull request as part of a
  merge request.
- Never alter repository merge settings, rulesets, branch protection, required checks, or merge
  queues to make a pull request mergeable.
- Preserve local branches, worktrees, the index, untracked files, remotes, Git configuration, and
  credentials.
