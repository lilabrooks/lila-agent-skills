# Changelog

Record user-visible workflow and safety changes to `github-publish-changes` here. Add new entries
at the top with the change date.

## 2026-07-20

### Added

- Added a narrow fast-forward recovery when a request-created topic branch's default-branch base
  advances before commit.
- Added behavioral coverage for ancestry proof, incoming-path review, fast-forward-only recovery,
  and verification invalidation after the base moves.
- Added explicit strict-preflight modes for confirmed new destinations and authorized rewritten
  history.
- Added stable checkout fingerprinting for staged submodule gitlink object IDs without reading
  checked-out submodule contents.

### Changed

- Required a fresh candidate identity and verification run after any movement of `HEAD`, including
  a safe base fast-forward.
- Required ordinary push preflight to reject destinations that are ahead or divergent.

## 2026-07-19

### Added

- Added explicit full-check, standard-commit, and basic-commit verification tiers.
- Added reporting requirements when a basic commit skips the full repository suite.
- Added detection for sync-numbered coverage database copies in preflight path review.
- Added operation-specific preflight modes for full-check, commit, push, and inspection.
- Added a stable read-only checkout fingerprint for full-check result identity.
- Added commit-type comparison validation and explicit outgoing-range error evidence.
- Added suspicious-path coverage for common package, cloud, container, and keystore credentials.

### Changed

- Reused one full-suite result across commit and push when the candidate tree stays fixed.
- Kept unqualified commit requests on the full verification tier.
- Limited remote inference and remote requirements to push operations.
- Limited candidate-tree and checkout-fingerprint work to operations that use those identities.
- Required push preflight to name a remote and a commit comparison explicitly.
- Blocked detached-head commits until a target branch is selected.
- Narrowed implicit activation so host-native publication and repository-audit workflows retain
  their ordinary requests.
- Replaced repository-local `git write-tree` guidance with temporary preflight identity and an
  authorization checkpoint before creating snapshot refs, commits, clones, or worktrees.
- Defined the exact implied authority for verification, commit, push, and branch publication,
  including the local metadata a narrow destination fetch may update.

## 2026-07-18

### Added

- Added a read-only preflight utility that records branch, operation, index, worktree, remote,
  and outgoing-range state.
- Added conditional references for candidate-tree verification and remote or CI edge cases.
- Added explicit support for unborn repositories, branch publication, dirty push-only worktrees,
  partial staging, and exact candidate-tree identity.

### Changed

- Conformed the read-only preflight utility to the repository's Python quality gate.
- Moved full verification after intentional staging and required cached whitespace checks.
- Required inspection of every outgoing commit and cumulative diff before pushing.
- Limited remote-policy checks to push flows and required authorization for local branch recovery.
- Pinned rewritten-history pushes to the observed remote SHA with an exact force lease.
- Expanded interface metadata to cover commit-only, push-only, branch-publication, and combined
  commit-and-push requests.

### Removed

- Removed a generated Finder metadata file from the skill package.
