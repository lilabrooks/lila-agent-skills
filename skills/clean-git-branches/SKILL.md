---
name: clean-git-branches
description: Audit and safely clean local and remote Git branches, especially after merged pull requests, squash merges, stale remote-tracking refs, or branch drift. Use when asked which branches are stale or safe to delete, to prune or delete merged branches, to reconcile local and remote branch pointers, or to confirm that the default branch and its upstream point to the same commit.
---

# Clean Git branches

Inspect before deleting, preserve recoverability, and finish with direct evidence that local and remote refs match the requested state.

## Boundaries

- Treat an audit or safety question as read-only apart from an authorized fetch and prune. Report candidates without deleting them.
- Treat an explicit cleanup request as authority to delete only branches already proven safe within that request. Ask before deleting any ambiguous branch.
- Preserve unrelated work, the index, untracked files, worktrees, Git configuration, tags, remotes, and repository policy.
- Never delete the default branch, a protected branch, a branch with an open pull request, or a branch checked out in another worktree.
- Never use `git reset --hard`, plain force push, wildcard deletion, or a guessed branch or remote name.
- Record every branch's full tip SHA before deletion so it can be recreated if its commit remains available.

## 1. Establish the repository state

1. Find the repository root and read applicable `AGENTS.md`, `CLAUDE.md`, contribution, release, and repository-specific instructions.
2. Capture the current state before any ref update:

   ```bash
   git status --short --branch
   git branch --show-current
   git remote -v
   git worktree list --porcelain
   git for-each-ref --format='%(refname) %(objectname)' refs/heads refs/remotes
   ```

3. Identify the selected remote and verify its URL belongs to the repository in scope. Prefer the branch's configured upstream remote; ask when multiple remotes make the target ambiguous.
4. Discover the remote's default branch from authenticated repository metadata, from `refs/remotes/<remote>/HEAD`, or, when that ref is absent, from a read-only `git ls-remote --symref <remote> HEAD` query. Do not assume it is `main`.
5. Stop destructive work when a merge, rebase, cherry-pick, revert, bisect, unresolved index, detached `HEAD`, or concurrent ref change makes the state unclear.

## 2. Refresh remote evidence

Fetch and prune the selected remote before classifying branches:

```bash
git fetch --prune <remote>
```

Report remote-tracking refs removed by pruning as refs that were already absent from the server. A pruned remote-tracking ref is not proof that a same-named local branch is safe to delete.

List current branches after the fetch:

```bash
git branch --all --verbose --no-abbrev
git for-each-ref --format='%(refname:short) %(objectname)' refs/heads refs/remotes/<remote>
```

Use GitHub or the relevant forge for pull-request state and exact head SHAs when available. Keep connector access, CLI authentication, and Git transport authentication as separate facts.

## 3. Classify each candidate

Protect the default branch and any branch with an open pull request. For every other candidate, record:

- local tip SHA, remote tip SHA, and upstream;
- ahead and behind counts against the remote default branch;
- worktrees using the branch;
- associated pull-request state, base branch, merged time, and recorded head SHA;
- commits or patches that are absent from the default branch.

Use ancestry as the strongest local proof:

```bash
git merge-base --is-ancestor <candidate> <remote>/<default>
git rev-list --left-right --count <remote>/<default>...<candidate>
git log --oneline <remote>/<default>..<candidate>
git cherry -v <remote>/<default> <candidate>
```

Classify a branch as safe when one of these cases is established:

1. **Ancestry merged:** its tip is an ancestor of the current remote default branch.
2. **Squash or rebase merged:** a merged pull request names the same base branch, its recorded head SHA exactly matches the candidate tip, and the branch has not gained commits since that merged head. Inspect `git cherry`, the pull-request patch, and relevant tree differences for contradictory evidence.
3. **Superseded merged branch:** the exact candidate tip was merged through a pull request and later default-branch changes intentionally replaced parts of its tree. Confirm the merged PR head SHA and inspect the differing paths before classifying it as safe.

Classify a branch as unsafe or ambiguous when it has an open pull request, unique commits without proven patch equivalents, a closed-unmerged pull request, post-merge commits, an unknown base, mismatched local and remote tips, or incomplete forge metadata. Preserve it and explain the missing proof.

Branch age and a deleted remote counterpart are weak signals. Never use either alone as a deletion reason.

## 4. Synchronize the default branch safely

Compare the local and remote default branch tips:

```bash
git rev-parse refs/heads/<default>
git rev-parse refs/remotes/<remote>/<default>
git rev-list --left-right --count <default>...<remote>/<default>
```

- If they match, leave them unchanged.
- If local is only behind and checked out, update with `git merge --ff-only <remote>/<default>` when the worktree state makes the merge safe.
- If local is only behind and not checked out, fast-forward it without switching branches using `git fetch <remote> <default>:<default>`. Git refuses this refspec for a checked-out branch, so a refusal means the branch is active in some worktree.
- If local is ahead, report the unpushed commits. Do not push unless the user asked.
- If they diverge, stop and report both tips and commit ranges. Do not reset, rebase, merge, or force push without a separate request.
- If the default branch is checked out in another worktree, use that worktree or ask for direction. Do not bypass worktree protections.

Do not switch branches over user-owned changes when Git cannot preserve them safely.

## 5. Delete proven branches

Recheck each tip immediately before deletion. Require it to equal the recorded SHA.

Delete the remote branch with a literal branch name, then confirm the server ref is absent:

```bash
git push <remote> --delete <candidate>
git ls-remote --heads <remote> refs/heads/<candidate>
```

Delete the local branch with Git's merged check first:

```bash
git branch -d <candidate>
```

`-d` verifies the merge against the current `HEAD` or the branch's configured upstream, not against the remote default branch. It therefore refuses every squash, rebase, or superseded merge, and it can refuse an ancestry-merged candidate while a branch that does not contain it is checked out. Use `git branch -D <candidate>` only when the user authorized deletion, the recorded SHA is unchanged, and the evidence in section 3 covers that exact tip. Explain why forced local deletion is required, and do not switch branches merely to satisfy `-d`. This force affects only the local branch ref.

If remote deletion succeeds and local deletion fails, report the partial result and preserve the local branch until its blocker is resolved.

## 6. Verify the final state

Refresh refs and verify the requested result:

```bash
git fetch --prune <remote>
git status --short --branch
git branch --all --verbose --no-abbrev
git for-each-ref --format='%(refname:short) %(objectname)' refs/heads refs/remotes/<remote>
git rev-parse refs/heads/<default>
git rev-parse refs/remotes/<remote>/<default>
```

Confirm explicitly:

- every requested branch is absent locally and remotely;
- local and remote default-branch SHAs are identical, or describe the remaining ahead, behind, or diverged state;
- the current branch and upstream are expected;
- the worktree and index are unchanged except for authorized operations;
- only intended refs were removed.

Report deleted branch names and recorded SHAs, pruned refs that were already gone remotely, the final default-branch SHA, and recovery guidance. A deleted branch can usually be recreated from its recorded SHA while that commit still exists locally or on the forge.
