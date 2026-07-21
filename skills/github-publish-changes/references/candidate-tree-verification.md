# Candidate-tree verification

Read this reference when the current checkout contains out-of-scope changes, push-only must
leave a dirty worktree alone, or the repository gate depends on Git metadata, submodules, or
Git LFS content.

## Choose the verification surface

1. Run preflight for the requested operation. Record the branch, `HEAD`, index fingerprint,
   staged paths, candidate index tree, and checkout fingerprint before creating a snapshot.
2. Use the current checkout only when its tracked contents equal the candidate tree and no
   out-of-scope untracked path can affect discovery, imports, builds, tests, or packaging.
3. Use an archive of an existing commit tree for source-only push gates. Extract it beneath a
   newly created temporary directory and run the documented setup and gate there.
4. Use a temporary Git checkout when the gate reads commit history, tags, `git describe`,
   submodules, Git LFS state, or repository-relative metadata. Ask an available repository-
   verification workflow to build the snapshot when it supports that operation.
5. Keep source-archive and Git-checkout results distinct. An archive omits `.git`, submodule
   working trees, ignored files, and expanded Git LFS objects unless setup reconstructs them.

## New-commit candidate

Stage the intended content first. Run `git diff --cached --check`, inspect the staged patch,
then run commit preflight. Treat its `candidate_index_tree` as the verification identity. The
helper computes that SHA with temporary index and object storage, so it does not add an object
to the user's repository.

When the current checkout does not match the index candidate, use a host or repository verifier
that can materialize the exact index in external temporary storage. If no such helper exists,
report that limitation and ask before creating a temporary clone, ref, commit, or worktree.
Keep temporary refs and commits outside the user's repository unless the user authorizes them.
Preserve the original index and worktree throughout.

After the gate, rerun commit preflight. Require the candidate tree and index fingerprint to
match their recorded values. After committing, require `HEAD^{tree}` to equal the verified tree.

## Standalone full-check candidate

Use `checkout_fingerprint_sha256` as the read-only identity for the tracked and nonignored
untracked checkout. The fingerprint covers paths, regular-file content, executable bits,
symlink targets, tracked deletions, and each staged submodule gitlink object ID. It excludes
ignored paths, Git metadata, checked-out submodule contents, and external state. Inspect those
inputs separately when they can affect the gate.
Rerun full-check preflight after the gate and require the same fingerprint before reusing the
result.

## Push-only candidate

Use the fetched remote branch and local `HEAD` to define the outgoing range. Verify the final
`HEAD` tree in an isolated snapshot whenever the checkout is dirty. Review every commit and the
cumulative diff in the range even when the final tree passes the gate.

For a new remote branch, select an explicit base branch. Ask the user when repository guidance,
the current branch point, and GitHub metadata do not identify one unambiguously.

## Failure handling

Report checkout failures, missing submodule content, absent Git LFS objects, unavailable
dependencies, and snapshot limitations separately from product failures. A clean isolated
result proves only the recorded candidate tree under the reported snapshot mode.
