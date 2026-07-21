from __future__ import annotations

from pathlib import Path

from conftest import AUDIT_SCRIPT, git, init_repository, run_python


def test_non_repository_returns_usage_error(tmp_path: Path) -> None:
    result = run_python(AUDIT_SCRIPT, "--root", tmp_path)

    assert result.returncode == 2
    assert "not a git repository" in result.stderr


def test_clean_repository_has_no_findings(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)

    result = run_python(AUDIT_SCRIPT, "--root", root)

    assert result.returncode == 0
    assert "worktree is clean" in result.stdout
    assert "Errors (0)" in result.stdout


def test_tracked_ignored_file_is_an_error(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    (root / "ignored.tmp").write_text("tracked\n", encoding="utf-8")
    git(root, "add", "ignored.tmp")
    git(root, "commit", "--quiet", "-m", "track ignored candidate")
    (root / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
    git(root, "add", ".gitignore")
    git(root, "commit", "--quiet", "-m", "ignore tmp")

    result = run_python(AUDIT_SCRIPT, "--root", root)

    assert result.returncode == 1
    assert "tracked file(s) match ignore rules" in result.stdout
    assert "ignored.tmp" in result.stdout


def test_ignore_expectations_are_enforced(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    (root / ".gitignore").write_text("*.cache\n", encoding="utf-8")
    git(root, "add", ".gitignore")
    git(root, "commit", "--quiet", "-m", "ignore cache")

    result = run_python(
        AUDIT_SCRIPT,
        "--root",
        root,
        "--expect-ignored",
        "expected.txt",
        "--expect-trackable",
        "unexpected.cache",
    )

    assert result.returncode == 1
    assert "expected ignored path is trackable: expected.txt" in result.stdout
    assert "expected trackable path is ignored: unexpected.cache" in result.stdout


def test_default_branch_is_not_a_merged_cleanup_candidate(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    git(root, "branch", "merged-topic")
    git(root, "remote", "add", "origin", str(tmp_path / "remote.git"))
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "update-ref", "refs/remotes/origin/main", head)
    git(
        root,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
    )
    git(root, "switch", "--quiet", "-c", "active-topic")

    result = run_python(AUDIT_SCRIPT, "--root", root)

    assert result.returncode == 0
    assert "remote default local branch(es): ['main']" in result.stdout
    assert "merged local branch candidate(s): ['merged-topic']" in result.stdout


def test_local_artifacts_report_warnings_and_errors(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    cache = root / ".ruff_cache"
    cache.mkdir()
    (cache / "artifact 2.json").write_text("{}\n", encoding="utf-8")
    (root / "dist").mkdir()
    (root / ".coverage 2").write_text("generated\n", encoding="utf-8")
    (root / ".missing.icloud").write_text("placeholder\n", encoding="utf-8")

    result = run_python(AUDIT_SCRIPT, "--root", root)

    assert result.returncode == 1
    assert "generated build/coverage output(s) present: ['dist']" in result.stdout
    assert "sync-conflict duplicate(s)" in result.stdout
    assert "iCloud placeholder(s)" in result.stdout


def test_routine_ignored_caches_are_silent(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    (root / ".gitignore").write_text(
        ".coverage\n.mypy_cache/\n.pytest_cache/\n.ruff_cache/\n",
        encoding="utf-8",
    )
    git(root, "add", ".gitignore")
    git(root, "commit", "--quiet", "-m", "ignore routine caches")
    (root / ".coverage").write_text("generated\n", encoding="utf-8")
    for name in (".mypy_cache", ".pytest_cache", ".ruff_cache"):
        (root / name).mkdir()

    result = run_python(AUDIT_SCRIPT, "--root", root)

    assert result.returncode == 0
    assert "Warnings (0)" in result.stdout
    assert "generated build/coverage output(s)" not in result.stdout
