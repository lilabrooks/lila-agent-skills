from __future__ import annotations

from pathlib import Path

from conftest import SECRET_CHECK_SCRIPT, init_repository, run, run_python


def test_non_repository_returns_usage_error(tmp_path: Path) -> None:
    result = run_python(SECRET_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 2
    assert "not a Git repository" in result.stderr


def test_missing_baseline_returns_usage_error(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)

    result = run_python(SECRET_CHECK_SCRIPT, "--root", root)

    assert result.returncode == 2
    assert "secret baseline is missing" in result.stderr


def create_empty_baseline(root: Path) -> None:
    result = run(["detect-secrets", "scan"], cwd=root)
    (root / ".secrets.baseline").write_text(result.stdout, encoding="utf-8")


def test_reviewed_repository_passes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    create_empty_baseline(root)

    result = run_python(SECRET_CHECK_SCRIPT, "--root", root)

    assert result.returncode == 0
    assert "files matched the reviewed baseline" in result.stdout


def test_untracked_probable_secret_fails(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    create_empty_baseline(root)
    password = "-".join(("correct", "horse", "battery", "staple"))
    (root / "credentials.txt").write_text(
        f'password = "{password}"\n', encoding="utf-8"
    )

    result = run_python(SECRET_CHECK_SCRIPT, "--root", root)

    assert result.returncode == 1
    assert "credentials.txt" in result.stdout
