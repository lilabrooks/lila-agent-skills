from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = (
    PROJECT_ROOT / "skills/github-publish-changes/scripts/publish_preflight.py"
)
AUDIT_SCRIPT = PROJECT_ROOT / "skills/verify-repository/scripts/repo_audit.py"
SKILL_CHECK_SCRIPT = PROJECT_ROOT / "scripts/check_skills.py"
SECRET_CHECK_SCRIPT = PROJECT_ROOT / "scripts/check_secrets.py"
BEHAVIOR_CHECK_SCRIPT = PROJECT_ROOT / "scripts/check_skill_behavior.py"


def pytest_configure() -> None:
    """Isolate every test process from user and system Git configuration."""
    os.environ.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0",
    )


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        env=env,
    )


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(root), *args], check=check)


def init_repository(root: Path, *, commit: bool = True) -> None:
    root.mkdir()
    run(["git", "init", "--quiet", "--initial-branch=main", str(root)])
    git(root, "config", "user.name", "Skill Tests")
    git(root, "config", "user.email", "skills@example.invalid")
    if commit:
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        git(root, "add", "tracked.txt")
        git(root, "commit", "--quiet", "-m", "base")


def run_python(
    script: Path, *args: Any, check: bool = False
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            str(script),
            *(str(value) for value in args),
        ],
        check=check,
    )
