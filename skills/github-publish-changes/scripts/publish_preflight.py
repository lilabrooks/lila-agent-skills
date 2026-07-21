#!/usr/bin/env python3
"""Inspect Git state for github-publish-changes without mutating the repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal

OPERATION_PATHS = {
    "merge": "MERGE_HEAD",
    "cherry_pick": "CHERRY_PICK_HEAD",
    "revert": "REVERT_HEAD",
    "bisect": "BISECT_START",
    "rebase_merge": "rebase-merge",
    "rebase_apply": "rebase-apply",
    "sequencer": "sequencer",
}

OPERATIONS = ("inspect", "full-check", "commit", "push")
PushMode = Literal[
    "ordinary", "destination-absent", "rewritten-history-authorized", "invalid"
]

SUSPICIOUS_NAMES = {
    ".env",
    ".envrc",
    ".git-credentials",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "auth.json",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
    "kubeconfig",
    "secrets.json",
}

SUSPICIOUS_SUFFIXES = {".jks", ".key", ".keystore", ".p12", ".pfx", ".pem"}
SUSPICIOUS_PATH_SUFFIXES = {
    (".aws", "credentials"),
    (".docker", "config.json"),
    (".kube", "config"),
}
ARTIFACT_PARTS = {
    ".coverage",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "coverage",
    "coverage.xml",
    "dist",
    "htmlcov",
    "node_modules",
}
SYNC_DUPLICATE = re.compile(r" \d+(\.[^/ ]+)?$")


class GitError(RuntimeError):
    """A Git command failed."""


def run_git(
    root: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "-C", str(root), *args]
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        env=env,
    )
    if check and completed.returncode != 0:
        message = completed.stderr.decode("utf-8", "replace").strip()
        raise GitError(
            message or f"Git exited {completed.returncode}: {' '.join(args)}"
        )
    return completed


def text_or_none(completed: subprocess.CompletedProcess[bytes]) -> str | None:
    if completed.returncode != 0:
        return None
    value = completed.stdout.decode("utf-8", "replace").strip()
    return value or None


def nul_paths(completed: subprocess.CompletedProcess[bytes]) -> list[str]:
    if completed.returncode != 0 or not completed.stdout:
        return []
    return sorted(
        item.decode("utf-8", "surrogateescape")
        for item in completed.stdout.rstrip(b"\0").split(b"\0")
        if item
    )


def git_path(root: Path, name: str) -> Path:
    value = run_git(root, "rev-parse", "--git-path", name).stdout.decode().strip()
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_tree_from_index(
    root: Path, index_path: Path
) -> tuple[str | None, str | None]:
    """Compute the index tree with temporary index and object storage."""
    try:
        objects_path = git_path(root, "objects")
        with tempfile.TemporaryDirectory(
            prefix="github-publish-preflight-"
        ) as temp_name:
            temp_root = Path(temp_name)
            temp_index = temp_root / "index"
            temp_objects = temp_root / "objects"
            temp_objects.mkdir()

            if index_path.is_file():
                shutil.copy2(index_path, temp_index)
                shared = text_or_none(
                    run_git(root, "rev-parse", "--shared-index-path", check=False)
                )
                if shared:
                    shared_path = Path(shared)
                    if not shared_path.is_absolute():
                        shared_path = (root / shared_path).resolve()
                    if shared_path.is_file():
                        shutil.copy2(shared_path, temp_root / shared_path.name)

            env = os.environ.copy()
            env["GIT_INDEX_FILE"] = str(temp_index)
            env["GIT_OBJECT_DIRECTORY"] = str(temp_objects)
            alternates = [str(objects_path)]
            existing_alternates = env.get("GIT_ALTERNATE_OBJECT_DIRECTORIES")
            if existing_alternates:
                alternates.append(existing_alternates)
            env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.pathsep.join(alternates)

            if not temp_index.exists():
                run_git(root, "read-tree", "--empty", env=env)
            tree = run_git(root, "write-tree", env=env).stdout.decode().strip()
            return tree or None, None
    except (GitError, OSError) as error:
        return None, str(error)


def active_operations(root: Path) -> list[str]:
    active: list[str] = []
    for operation, relative_path in OPERATION_PATHS.items():
        if git_path(root, relative_path).exists():
            active.append(operation)
    return active


def unmerged_paths(root: Path) -> list[str]:
    completed = run_git(root, "ls-files", "--unmerged", "-z", check=False)
    paths: set[str] = set()
    for record in completed.stdout.rstrip(b"\0").split(b"\0"):
        if b"\t" in record:
            paths.add(record.split(b"\t", 1)[1].decode("utf-8", "surrogateescape"))
    return sorted(paths)


def git_failure(completed: subprocess.CompletedProcess[bytes], action: str) -> str:
    detail = completed.stderr.decode("utf-8", "replace").strip()
    return detail or f"Git exited {completed.returncode} while {action}"


def require_success(
    completed: subprocess.CompletedProcess[bytes], action: str
) -> subprocess.CompletedProcess[bytes]:
    if completed.returncode != 0:
        raise GitError(git_failure(completed, action))
    return completed


def checkout_paths(root: Path) -> tuple[set[str], set[str], dict[str, str]]:
    tracked_result = run_git(root, "ls-files", "--stage", "-z", check=False)
    require_success(tracked_result, "listing tracked paths")
    tracked: set[str] = set()
    gitlinks: dict[str, str] = {}
    for record in tracked_result.stdout.rstrip(b"\0").split(b"\0"):
        if not record or b"\t" not in record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        fields = metadata.split()
        if len(fields) != 3:
            raise GitError("Git returned an invalid staged path record")
        mode, object_id, stage = fields
        path = raw_path.decode("utf-8", "surrogateescape")
        tracked.add(path)
        if mode == b"160000" and stage == b"0":
            gitlinks[path] = object_id.decode("ascii")
    untracked_result = run_git(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        check=False,
    )
    require_success(untracked_result, "listing untracked paths")
    return tracked, set(nul_paths(untracked_result)), gitlinks


def checkout_fingerprint_once(root: Path) -> tuple[str | None, str | None]:
    """Hash tracked and nonignored untracked checkout content without Git writes."""
    try:
        tracked, untracked, gitlinks = checkout_paths(root)
        digest = hashlib.sha256()
        digest.update(b"github-publish-checkout-v1\0")
        for value in sorted(tracked | untracked):
            digest.update(os.fsencode(value))
            digest.update(b"\0")
            if value in gitlinks:
                digest.update(b"gitlink\0")
                digest.update(gitlinks[value].encode("ascii"))
                digest.update(b"\0")
                continue
            path = root / value
            try:
                details = path.lstat()
            except FileNotFoundError:
                if value in tracked:
                    digest.update(b"missing\0")
                    continue
                raise GitError(
                    f"untracked path disappeared while fingerprinting: {value}"
                ) from None
            except OSError as path_error:
                raise GitError(f"cannot inspect {value}: {path_error}") from path_error

            if stat.S_ISREG(details.st_mode):
                digest.update(b"file\0")
                digest.update(
                    b"executable\0" if details.st_mode & 0o111 else b"regular\0"
                )
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            elif stat.S_ISLNK(details.st_mode):
                digest.update(b"symlink\0")
                digest.update(os.fsencode(os.readlink(path)))
            else:
                raise GitError(f"unsupported checkout path type: {value}")
            digest.update(b"\0")
        return digest.hexdigest(), None
    except (GitError, OSError) as error:
        return None, str(error)


def checkout_fingerprint(root: Path) -> tuple[str | None, str | None]:
    first, error = checkout_fingerprint_once(root)
    if error:
        return None, error
    second, error = checkout_fingerprint_once(root)
    if error:
        return None, error
    if first != second:
        return None, "checkout changed while fingerprinting"
    return first, None


def outgoing_range(
    root: Path, compare_sha: str | None, head: str | None
) -> tuple[dict[str, int] | None, list[dict[str, str]], list[str], str | None]:
    if not compare_sha or not head:
        return None, [], [], "a commit comparison and HEAD are required"

    try:
        count_result = require_success(
            run_git(
                root,
                "rev-list",
                "--left-right",
                "--count",
                f"{compare_sha}...{head}",
                check=False,
            ),
            "counting the outgoing range",
        )
        values = count_result.stdout.decode().split()
        if len(values) != 2:
            raise GitError("Git returned an invalid ahead/behind count")
        try:
            behind, ahead = (int(value) for value in values)
        except ValueError as error:
            raise GitError("Git returned an invalid ahead/behind count") from error

        revisions = require_success(
            run_git(
                root,
                "rev-list",
                "--reverse",
                f"{compare_sha}..{head}",
                check=False,
            ),
            "listing outgoing commits",
        )
        commits: list[dict[str, str]] = []
        for sha in revisions.stdout.decode().splitlines():
            subject_result = require_success(
                run_git(root, "show", "-s", "--format=%s", sha, check=False),
                f"inspecting commit {sha}",
            )
            commits.append(
                {
                    "sha": sha,
                    "subject": subject_result.stdout.decode("utf-8", "replace").rstrip(
                        "\n"
                    ),
                }
            )

        paths_result = require_success(
            run_git(
                root,
                "diff",
                "--name-only",
                "-z",
                f"{compare_sha}..{head}",
                check=False,
            ),
            "listing outgoing paths",
        )
        return (
            {"behind": behind, "ahead": ahead},
            commits,
            nul_paths(paths_result),
            None,
        )
    except GitError as error:
        return None, [], [], str(error)


def suspicious_paths(paths: list[str]) -> list[str]:
    matches: list[str] = []
    for value in paths:
        path = Path(value)
        lower_parts = {part.lower() for part in path.parts}
        normalized_parts = {
            SYNC_DUPLICATE.sub(lambda match: match.group(1) or "", part)
            for part in lower_parts
        }
        lower_name = path.name.lower()
        lower_parts_tuple = tuple(part.lower() for part in path.parts)
        if (
            lower_name in SUSPICIOUS_NAMES
            or lower_name.startswith(".env.")
            or path.suffix.lower() in SUSPICIOUS_SUFFIXES
            or any(
                lower_parts_tuple[-len(suffix) :] == suffix
                for suffix in SUSPICIOUS_PATH_SUFFIXES
            )
            or normalized_parts.intersection(ARTIFACT_PARTS)
        ):
            matches.append(value)
    return sorted(set(matches))


def requested_push_mode(
    destination_branch_absent: bool, rewritten_history_authorized: bool
) -> PushMode:
    if destination_branch_absent and rewritten_history_authorized:
        return "invalid"
    if destination_branch_absent:
        return "destination-absent"
    if rewritten_history_authorized:
        return "rewritten-history-authorized"
    return "ordinary"


def collect(
    root: Path,
    compare_ref: str | None,
    selected_remote: str | None,
    operation: str,
    push_mode: PushMode,
) -> dict[str, Any]:
    destination_branch_absent = push_mode in {"destination-absent", "invalid"}
    rewritten_history_authorized = push_mode in {
        "rewritten-history-authorized",
        "invalid",
    }
    repository_root_text = (
        run_git(root, "rev-parse", "--show-toplevel").stdout.decode().strip()
    )
    repository_root = Path(repository_root_text).resolve()
    branch = text_or_none(
        run_git(
            repository_root,
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
            check=False,
        )
    )
    head = text_or_none(
        run_git(repository_root, "rev-parse", "--verify", "HEAD", check=False)
    )
    upstream = text_or_none(
        run_git(
            repository_root,
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
            check=False,
        )
    )
    upstream_sha = (
        text_or_none(
            run_git(repository_root, "rev-parse", "--verify", upstream, check=False)
        )
        if upstream
        else None
    )
    configured_upstream_remote = (
        text_or_none(
            run_git(
                repository_root,
                "config",
                "--get",
                f"branch.{branch}.remote",
                check=False,
            )
        )
        if branch
        else None
    )
    compare_sha = (
        text_or_none(
            run_git(
                repository_root,
                "rev-parse",
                "--verify",
                f"{compare_ref}^{{commit}}",
                check=False,
            )
        )
        if compare_ref
        else None
    )
    index_path = git_path(repository_root, "index")
    index_fingerprint = sha256_file(index_path)
    candidate_tree_requested = operation in {"inspect", "commit"}
    if candidate_tree_requested:
        candidate_tree, candidate_tree_error = candidate_tree_from_index(
            repository_root, index_path
        )
    else:
        candidate_tree, candidate_tree_error = None, None
    checkout_fingerprint_requested = operation == "full-check"
    if checkout_fingerprint_requested:
        checkout_fingerprint_sha256, checkout_fingerprint_error = checkout_fingerprint(
            repository_root
        )
    else:
        checkout_fingerprint_sha256, checkout_fingerprint_error = None, None

    staged = nul_paths(
        run_git(
            repository_root,
            "diff",
            "--cached",
            "--name-only",
            "-z",
            check=False,
        )
    )
    unstaged = nul_paths(
        run_git(repository_root, "diff", "--name-only", "-z", check=False)
    )
    untracked = nul_paths(
        run_git(
            repository_root,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            check=False,
        )
    )
    operations = active_operations(repository_root)
    unmerged = unmerged_paths(repository_root)
    remotes = sorted(
        run_git(repository_root, "remote", check=False).stdout.decode().splitlines()
    )
    remote = selected_remote
    remote_required = operation == "push"

    compare_ref_valid = compare_ref is None or compare_sha is not None
    comparison_required = operation == "push"
    selected_remote_exists = remote is None or remote in remotes
    safe_to_stage_or_commit = not operations and not unmerged
    range_requested = compare_ref is not None or comparison_required
    if range_requested:
        ahead_behind_value, commits, outgoing_paths, range_error = outgoing_range(
            repository_root, compare_sha, head
        )
    else:
        ahead_behind_value, commits, outgoing_paths, range_error = None, [], [], None
    outgoing_range_valid = range_error is None

    operation_identity_available = {
        "inspect": candidate_tree is not None,
        "full-check": checkout_fingerprint_sha256 is not None,
        "commit": candidate_tree is not None,
        "push": head is not None,
    }[operation]
    attached_branch_ready = operation != "commit" or branch is not None
    remote_ready = selected_remote_exists and (
        not remote_required or remote is not None
    )
    comparison_ready = compare_ref_valid and (
        not comparison_required or compare_ref is not None
    )
    push_options_valid = push_mode != "invalid" and (
        operation == "push" or push_mode == "ordinary"
    )
    push_relationship_ready = operation != "push" or (
        push_options_valid
        and ahead_behind_value is not None
        and (
            destination_branch_absent
            or rewritten_history_authorized
            or ahead_behind_value["behind"] == 0
        )
    )
    safe_for_requested_write = (
        safe_to_stage_or_commit
        and operation_identity_available
        and attached_branch_ready
        and remote_ready
        and comparison_ready
        and outgoing_range_valid
        and push_options_valid
        and push_relationship_ready
    )
    all_changed = sorted(set(staged + unstaged + untracked))
    result: dict[str, Any] = {
        "repository_root": str(repository_root),
        "operation": operation,
        "branch": branch,
        "detached_head": branch is None and head is not None,
        "unborn_branch": head is None and branch is not None,
        "head": head,
        "upstream": upstream,
        "upstream_sha": upstream_sha,
        "configured_upstream_remote": configured_upstream_remote,
        "selected_remote": remote,
        "remote_required": remote_required,
        "remotes": remotes,
        "compare_ref": compare_ref,
        "compare_sha": compare_sha,
        "compare_ref_valid": compare_ref_valid,
        "comparison_required": comparison_required,
        "push_mode": push_mode,
        "destination_branch_absent": destination_branch_absent,
        "rewritten_history_authorized": rewritten_history_authorized,
        "push_options_valid": push_options_valid,
        "push_relationship_ready": push_relationship_ready,
        "ahead_behind": ahead_behind_value,
        "outgoing_commits": commits,
        "outgoing_paths": outgoing_paths,
        "outgoing_range_valid": outgoing_range_valid,
        "outgoing_range_error": range_error,
        "active_operations": operations,
        "unmerged_paths": unmerged,
        "safe_to_stage_or_commit": safe_to_stage_or_commit,
        "safe_for_requested_write": safe_for_requested_write,
        "selected_remote_exists": selected_remote_exists,
        "attached_branch_ready": attached_branch_ready,
        "operation_identity_available": operation_identity_available,
        "index_fingerprint_sha256": index_fingerprint,
        "candidate_index_tree": candidate_tree,
        "candidate_index_tree_requested": candidate_tree_requested,
        "candidate_index_tree_available": candidate_tree is not None,
        "candidate_index_tree_error": candidate_tree_error,
        "checkout_fingerprint_sha256": checkout_fingerprint_sha256,
        "checkout_fingerprint_requested": checkout_fingerprint_requested,
        "checkout_fingerprint_available": checkout_fingerprint_sha256 is not None,
        "checkout_fingerprint_error": checkout_fingerprint_error,
        "staged_paths": staged,
        "unstaged_paths": unstaged,
        "untracked_paths": untracked,
        "suspicious_changed_paths": suspicious_paths(all_changed),
        "worktrees": run_git(
            repository_root, "worktree", "list", "--porcelain", check=False
        )
        .stdout.decode("utf-8", "replace")
        .splitlines(),
    }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Path inside the Git repository")
    parser.add_argument(
        "--compare-ref", help="Fetched ref used to inspect outgoing commits"
    )
    parser.add_argument("--remote", help="Selected push remote name")
    parser.add_argument(
        "--operation",
        choices=OPERATIONS,
        default="inspect",
        help="Operation whose authorization and evidence requirements are checked",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 when the requested operation lacks safe state or required evidence",
    )
    parser.add_argument(
        "--destination-branch-absent",
        action="store_true",
        help="Confirm the push destination does not exist; compare-ref names its reviewed base",
    )
    parser.add_argument(
        "--rewritten-history-authorized",
        action="store_true",
        help="Confirm explicit authority to replace an existing destination with an exact lease",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = collect(
            Path(args.root).resolve(),
            args.compare_ref,
            args.remote,
            args.operation,
            requested_push_mode(
                args.destination_branch_absent,
                args.rewritten_history_authorized,
            ),
        )
    except (GitError, OSError) as error:
        print(json.dumps({"error": str(error)}, indent=2))
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    if args.strict and not result["safe_for_requested_write"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
