# Remote and CI edge cases

Read only the section that matches the active request.

## Push authority

A push request covers the narrow metadata reads, destination-branch fetch, and normal literal
refspec push needed to publish the existing commits. Fetch only the selected destination when
practical; a fetch can update `FETCH_HEAD` and remote-tracking refs. Do not change remote URLs,
fetch specifications, branch configuration, credentials, unrelated refs, or other worktrees as
incidental recovery. Branch creation, rewritten history, administrator bypass, and local branch
repair require the authority stated in their matching workflow sections.

Run ordinary strict push preflight against the fetched destination for an existing branch. It
must reject an ahead or divergent destination. After confirming a new destination is absent,
compare with its reviewed base and pass `--destination-branch-absent`. Never use that flag for an
existing or uncertain destination.

## Forks

Record the push repository, push remote, head branch, target repository, base branch, and remote
branch independently. Confirm which repository receives the branch before pushing. Keep a fork's
push target separate from the pull request's base repository.

## Default-branch policy

Inspect GitHub rulesets and legacy branch protection before a default-branch push. General
repository metadata cannot prove that direct pushes are accepted. When policy data is missing,
report that uncertainty and ask which route to use unless the user explicitly named the default
branch. An explicit request authorizes one normal push attempt after the warning. Administrator
bypass requires separate approval.

When GitHub accepts a push through an administrator or ruleset bypass, report the bypass and the
named rules as a policy exception.

## Default branch advanced before commit

Use this recovery only for a topic branch created for the current request that has no unique
commits. Record the old `HEAD`, fetch the selected remote default branch, and prove the old `HEAD`
is its ancestor with `git merge-base --is-ancestor <old-head> <remote-default>`. Confirm the topic
branch still points to that old base. Ask before moving a pre-existing branch, an ambiguously owned
branch, or a branch with unique commits.

Inspect `git diff --name-status <old-head>..<remote-default>` alongside the staged, unstaged, and
untracked path sets. Continue only when the incoming base changes and the intended local changes
are separate and their ownership is clear. Stop when paths overlap, ancestry is unexpected, an
operation is already in progress, or the worktree state changed after inspection.

Advance the current topic branch with `git merge --ff-only <remote-default>`. Avoid reset, rebase,
and force operations for this recovery. Rerun commit preflight immediately afterward and inspect
the worktree and index. Treat the new `HEAD` as a new candidate base: stage and review the intended
patch again, record its new candidate identity, and rerun the selected verification gate. Never
reuse a result from before the fast-forward, even when the intended patch is byte-for-byte equal.

## Remotely merged and deleted topic branch

Fetch with pruning. Confirm that the remote default branch contains local `HEAD`, the current
tree equals the remote-default tree, and any local default branch can fast-forward. Report that
the topic branch is already merged and absent remotely.

Ask permission before updating the local default ref, switching branches, or removing any local
branch. Leave refs and the worktree alone when ancestry, tree identity, or authorization is
uncertain. Avoid recreating the deleted remote branch as incidental recovery.

## Rewritten history

Fetch the destination branch and record its exact SHA. Review every incoming remote commit and
the rewritten outgoing range. After explicit authorization, run strict push preflight against
the fetched destination with `--rewritten-history-authorized`, then use
`--force-with-lease=refs/heads/<branch>:<observed-remote-sha>` with literal values. A background
fetch cannot weaken that explicit lease. Use plain `--force` under no circumstance.

## CI monitoring

Monitor CI only when requested. Distinguish legacy commit statuses, Checks API runs, and GitHub
Actions workflow runs. An empty combined-status response establishes only that GitHub returned
no legacy statuses. Query commit-specific push runs when pull-request-only tooling omits direct
branch pushes.

Wait for every required run to reach a terminal state. Report each conclusion from the matching
check surface. A successful push establishes transport success; report CI separately.
