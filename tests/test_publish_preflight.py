from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from conftest import PREFLIGHT_SCRIPT, git, init_repository, run_python


def preflight(root: Path, *args: str) -> tuple[int, dict[str, Any]]:
    result = run_python(PREFLIGHT_SCRIPT, "--root", root, *args)
    return result.returncode, json.loads(result.stdout)


def resolved_git_path(root: Path, name: str) -> Path:
    value = git(root, "rev-parse", "--git-path", name).stdout.strip()
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def file_fingerprint(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def directory_fingerprint(path: Path) -> tuple[tuple[str, str], ...]:
    if not path.is_dir():
        return ()
    return tuple(
        (str(item.relative_to(path)), hashlib.sha256(item.read_bytes()).hexdigest())
        for item in sorted(path.rglob("*"))
        if item.is_file()
    )


def repository_snapshot(root: Path) -> dict[str, object]:
    head_result = git(root, "rev-parse", "--verify", "HEAD", check=False)
    head = head_result.stdout.strip() if head_result.returncode == 0 else None
    return {
        "status": git(root, "status", "--porcelain=v1", "-z").stdout,
        "head": head,
        "index": file_fingerprint(resolved_git_path(root, "index")),
        "refs": git(root, "for-each-ref", "--format=%(refname) %(objectname)").stdout,
        "config": git(
            root, "config", "--local", "--list", "--show-origin", "-z"
        ).stdout,
        "fetch_head": file_fingerprint(resolved_git_path(root, "FETCH_HEAD")),
        "orig_head": file_fingerprint(resolved_git_path(root, "ORIG_HEAD")),
        "objects": directory_fingerprint(resolved_git_path(root, "objects")),
        "worktrees": git(root, "worktree", "list", "--porcelain").stdout,
    }


def test_unborn_repository_uses_an_empty_candidate_tree(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root, commit=False)
    (root / "untracked.txt").write_text("draft\n", encoding="utf-8")
    before = repository_snapshot(root)

    returncode, payload = preflight(root, "--strict")

    assert returncode == 0
    assert payload["unborn_branch"] is True
    assert payload["head"] is None
    assert payload["candidate_index_tree_available"] is True
    assert payload["untracked_paths"] == ["untracked.txt"]
    assert repository_snapshot(root) == before


def test_reports_outgoing_and_mixed_worktree_state_without_mutation(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    (root / "outgoing.txt").write_text("published\n", encoding="utf-8")
    git(root, "add", "outgoing.txt")
    git(root, "commit", "--quiet", "-m", "outgoing")
    (root / "staged.txt").write_text("staged\n", encoding="utf-8")
    git(root, "add", "staged.txt")
    (root / "tracked.txt").write_text("unstaged\n", encoding="utf-8")
    (root / ".env.local").write_text("example=true\n", encoding="utf-8")
    (root / ".coverage 2").write_text("generated\n", encoding="utf-8")
    git(root, "update-index", "--split-index")
    before = repository_snapshot(root)

    returncode, payload = preflight(root, "--compare-ref", base, "--strict")

    assert returncode == 0
    assert payload["ahead_behind"] == {"ahead": 1, "behind": 0}
    assert [item["subject"] for item in payload["outgoing_commits"]] == ["outgoing"]
    assert payload["staged_paths"] == ["staged.txt"]
    assert payload["unstaged_paths"] == ["tracked.txt"]
    assert payload["untracked_paths"] == [".coverage 2", ".env.local"]
    assert payload["suspicious_changed_paths"] == [".coverage 2", ".env.local"]
    assert payload["safe_for_requested_write"] is True
    assert repository_snapshot(root) == before


def test_strict_mode_rejects_an_invalid_compare_ref(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)

    returncode, payload = preflight(root, "--compare-ref", "missing/ref", "--strict")

    assert returncode == 2
    assert payload["compare_ref_valid"] is False
    assert payload["safe_for_requested_write"] is False


def test_strict_mode_rejects_an_unknown_remote(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)

    returncode, payload = preflight(
        root,
        "--operation",
        "push",
        "--remote",
        "missing",
        "--compare-ref",
        "HEAD",
        "--strict",
    )

    assert returncode == 2
    assert payload["selected_remote_exists"] is False
    assert payload["safe_for_requested_write"] is False


def test_commit_preflight_ignores_a_stale_configured_remote(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    git(root, "config", "branch.main.remote", "ghost")
    before = repository_snapshot(root)

    returncode, payload = preflight(root, "--operation", "commit", "--strict")

    assert returncode == 0
    assert payload["configured_upstream_remote"] == "ghost"
    assert payload["selected_remote"] is None
    assert payload["remote_required"] is False
    assert payload["candidate_index_tree_requested"] is True
    assert payload["checkout_fingerprint_requested"] is False
    assert payload["safe_for_requested_write"] is True
    assert repository_snapshot(root) == before


def test_compare_ref_must_resolve_to_a_commit(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    blob = git(root, "hash-object", "-w", "tracked.txt").stdout.strip()
    before = repository_snapshot(root)

    returncode, payload = preflight(root, "--compare-ref", blob, "--strict")

    assert returncode == 2
    assert payload["compare_ref_valid"] is False
    assert payload["compare_sha"] is None
    assert payload["outgoing_range_valid"] is False
    assert payload["outgoing_range_error"]
    assert repository_snapshot(root) == before


def test_push_requires_an_explicit_commit_comparison(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    git(root, "remote", "add", "origin", str(tmp_path / "remote.git"))

    returncode, payload = preflight(
        root, "--operation", "push", "--remote", "origin", "--strict"
    )

    assert returncode == 2
    assert payload["comparison_required"] is True
    assert payload["outgoing_range_valid"] is False
    assert payload["safe_for_requested_write"] is False


def test_push_requires_an_explicit_remote_even_with_branch_configuration(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    git(root, "remote", "add", "origin", str(tmp_path / "remote.git"))
    git(root, "config", "branch.main.remote", "origin")

    returncode, payload = preflight(
        root, "--operation", "push", "--compare-ref", "HEAD", "--strict"
    )

    assert returncode == 2
    assert payload["configured_upstream_remote"] == "origin"
    assert payload["selected_remote"] is None
    assert payload["remote_required"] is True
    assert payload["safe_for_requested_write"] is False


def test_push_preflight_accepts_an_explicit_remote_and_commit_range(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    git(root, "remote", "add", "origin", str(tmp_path / "remote.git"))

    returncode, payload = preflight(
        root,
        "--operation",
        "push",
        "--remote",
        "origin",
        "--compare-ref",
        "HEAD",
        "--strict",
    )

    assert returncode == 0
    assert payload["outgoing_range_valid"] is True
    assert payload["ahead_behind"] == {"ahead": 0, "behind": 0}
    assert payload["candidate_index_tree_requested"] is False
    assert payload["checkout_fingerprint_requested"] is False
    assert payload["safe_for_requested_write"] is True


def test_push_preflight_rejects_behind_and_divergent_history(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "commit", "--quiet", "--allow-empty", "-m", "remote ahead")
    destination = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "switch", "--quiet", "-c", "topic", base)
    git(root, "remote", "add", "origin", str(tmp_path / "remote.git"))

    returncode, behind = preflight(
        root,
        "--operation",
        "push",
        "--remote",
        "origin",
        "--compare-ref",
        destination,
        "--strict",
    )

    assert returncode == 2
    assert behind["ahead_behind"] == {"ahead": 0, "behind": 1}
    assert behind["push_relationship_ready"] is False
    assert behind["safe_for_requested_write"] is False

    git(root, "commit", "--quiet", "--allow-empty", "-m", "local ahead")
    returncode, divergent = preflight(
        root,
        "--operation",
        "push",
        "--remote",
        "origin",
        "--compare-ref",
        destination,
        "--strict",
    )

    assert returncode == 2
    assert divergent["ahead_behind"] == {"ahead": 1, "behind": 1}
    assert divergent["push_relationship_ready"] is False
    assert divergent["safe_for_requested_write"] is False


def test_push_preflight_requires_explicit_exception_modes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "commit", "--quiet", "--allow-empty", "-m", "remote ahead")
    destination = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "switch", "--quiet", "-c", "topic", base)
    git(root, "commit", "--quiet", "--allow-empty", "-m", "local ahead")
    git(root, "remote", "add", "origin", str(tmp_path / "remote.git"))

    expected_modes = {
        "--destination-branch-absent": "destination-absent",
        "--rewritten-history-authorized": "rewritten-history-authorized",
    }
    for option, expected_mode in expected_modes.items():
        returncode, payload = preflight(
            root,
            "--operation",
            "push",
            "--remote",
            "origin",
            "--compare-ref",
            destination,
            option,
            "--strict",
        )

        assert returncode == 0
        assert payload["push_mode"] == expected_mode
        assert payload["push_relationship_ready"] is True
        assert payload["safe_for_requested_write"] is True

    returncode, incompatible = preflight(
        root,
        "--operation",
        "push",
        "--remote",
        "origin",
        "--compare-ref",
        destination,
        "--destination-branch-absent",
        "--rewritten-history-authorized",
        "--strict",
    )

    assert returncode == 2
    assert incompatible["push_options_valid"] is False
    assert incompatible["safe_for_requested_write"] is False

    returncode, wrong_operation = preflight(
        root,
        "--operation",
        "commit",
        "--destination-branch-absent",
        "--strict",
    )

    assert returncode == 2
    assert wrong_operation["push_options_valid"] is False
    assert wrong_operation["safe_for_requested_write"] is False


def test_flags_common_credential_and_keystore_paths(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    paths = [
        ".aws/credentials",
        ".docker/config.json",
        ".kube/config",
        ".npmrc",
        "certificates/signing.jks",
    ]
    for value in paths:
        path = root / value
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")

    returncode, payload = preflight(root, "--strict")

    assert returncode == 0
    assert payload["suspicious_changed_paths"] == paths


def test_full_check_fingerprint_tracks_checkout_content_and_mode(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    before_repository = repository_snapshot(root)

    returncode, initial = preflight(root, "--operation", "full-check", "--strict")
    assert returncode == 0
    assert initial["checkout_fingerprint_available"] is True
    assert initial["checkout_fingerprint_requested"] is True
    assert initial["candidate_index_tree_requested"] is False
    assert repository_snapshot(root) == before_repository

    (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
    _, content_changed = preflight(root, "--operation", "full-check", "--strict")
    assert (
        content_changed["checkout_fingerprint_sha256"]
        != initial["checkout_fingerprint_sha256"]
    )

    (root / "tracked.txt").chmod(0o755)
    _, mode_changed = preflight(root, "--operation", "full-check", "--strict")
    assert (
        mode_changed["checkout_fingerprint_sha256"]
        != content_changed["checkout_fingerprint_sha256"]
    )

    (root / "draft-link").symlink_to("tracked.txt")
    _, link_added = preflight(root, "--operation", "full-check", "--strict")
    assert (
        link_added["checkout_fingerprint_sha256"]
        != mode_changed["checkout_fingerprint_sha256"]
    )


def test_full_check_fingerprints_gitlink_without_submodule_contents(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    dependency = tmp_path / "dependency"
    init_repository(root)
    init_repository(dependency)
    git(
        root,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "--quiet",
        str(dependency),
        "dependency",
    )

    returncode, initial = preflight(root, "--operation", "full-check", "--strict")

    assert returncode == 0
    assert initial["checkout_fingerprint_available"] is True
    assert initial["safe_for_requested_write"] is True

    submodule = root / "dependency"
    git(submodule, "config", "user.name", "Skill Tests")
    git(submodule, "config", "user.email", "skills@example.invalid")
    git(submodule, "commit", "--quiet", "--allow-empty", "-m", "new dependency")
    _, unstaged_gitlink = preflight(root, "--operation", "full-check", "--strict")
    assert (
        unstaged_gitlink["checkout_fingerprint_sha256"]
        == initial["checkout_fingerprint_sha256"]
    )

    git(root, "add", "dependency")
    _, staged_gitlink = preflight(root, "--operation", "full-check", "--strict")
    assert (
        staged_gitlink["checkout_fingerprint_sha256"]
        != initial["checkout_fingerprint_sha256"]
    )


def test_detached_head_commit_requires_branch_selection(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    git(root, "switch", "--quiet", "--detach")

    returncode, payload = preflight(root, "--operation", "commit", "--strict")

    assert returncode == 2
    assert payload["detached_head"] is True
    assert payload["attached_branch_ready"] is False
    assert payload["safe_for_requested_write"] is False


def test_linked_worktree_preflight_is_read_only(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    linked = tmp_path / "linked"
    init_repository(root)
    git(root, "worktree", "add", "--quiet", "-b", "linked", str(linked))
    (linked / "tracked.txt").write_text("linked edit\n", encoding="utf-8")
    before = repository_snapshot(linked)

    returncode, payload = preflight(linked, "--operation", "full-check", "--strict")

    assert returncode == 0
    assert payload["repository_root"] == str(linked.resolve())
    assert payload["checkout_fingerprint_available"] is True
    assert repository_snapshot(linked) == before


def test_strict_mode_rejects_merge_conflicts(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    git(root, "switch", "--quiet", "-c", "other")
    (root / "tracked.txt").write_text("other\n", encoding="utf-8")
    git(root, "commit", "--quiet", "-am", "other")
    git(root, "switch", "--quiet", "main")
    (root / "tracked.txt").write_text("main\n", encoding="utf-8")
    git(root, "commit", "--quiet", "-am", "main")
    merge = git(root, "merge", "other", check=False)
    assert merge.returncode != 0

    returncode, payload = preflight(root, "--strict")

    assert returncode == 2
    assert "merge" in payload["active_operations"]
    assert payload["unmerged_paths"] == ["tracked.txt"]
    assert payload["safe_to_stage_or_commit"] is False


def test_non_repository_reports_a_machine_readable_error(tmp_path: Path) -> None:
    returncode, payload = preflight(tmp_path, "--strict")

    assert returncode == 1
    assert "not a git repository" in payload["error"]
