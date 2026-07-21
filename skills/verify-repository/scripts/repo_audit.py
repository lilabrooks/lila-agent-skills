#!/usr/bin/env python3
"""Read-only repository and local-environment audit for final QA."""

from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SYNC_DUPLICATE = re.compile(r" \d+(\.[^/ ]+)?$")
ROUTINE_CACHE_PATHS = (
    ".coverage",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
)
GENERATED_OUTPUT_PATHS = (
    "build",
    "coverage.xml",
    "dist",
    "htmlcov",
)
SYNC_SENSITIVE_PATHS = ROUTINE_CACHE_PATHS + GENERATED_OUTPUT_PATHS
TOOL_DIRS = (".venv", ".venv.nosync", ".mypy_cache", ".pytest_cache", ".ruff_cache")


@dataclass
class Audit:
    root: Path
    info: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def report(self) -> int:
        lines = [f"Repository: {self.root}"]
        for label, entries in (
            ("Info", self.info),
            ("Warnings", self.warnings),
            ("Errors", self.errors),
        ):
            lines.append(f"\n{label} ({len(entries)}):")
            if entries:
                lines.extend(f"- {entry}" for entry in entries)
            else:
                lines.append("- none")
        sys.stdout.write("\n".join(lines) + "\n")
        return 1 if self.errors else 0


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def find_root(value: str) -> Path:
    candidate = Path(value).expanduser().resolve()
    result = git(candidate, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        raise ValueError(f"not a git repository: {candidate}")
    return Path(result.stdout.strip()).resolve()


def is_hidden(path: Path) -> bool:
    metadata = path.lstat()
    unix_hidden = getattr(metadata, "st_flags", 0) & getattr(stat, "UF_HIDDEN", 0)
    windows_hidden = getattr(metadata, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_HIDDEN", 0
    )
    return bool(unix_hidden or windows_hidden)


def is_tool_directory_copy(path: Path) -> bool:
    if not path.is_dir():
        return False
    return any(re.fullmatch(rf"{re.escape(name)} \d+", path.name) for name in TOOL_DIRS)


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def canonical_sync_name(name: str) -> str | None:
    match = SYNC_DUPLICATE.search(name)
    if match is None:
        return None
    return name[: match.start()] + (match.group(1) or "")


def remote_default_local_branches(root: Path, remotes: list[str]) -> set[str]:
    defaults: set[str] = set()
    for remote in remotes:
        result = git(
            root,
            "symbolic-ref",
            "--quiet",
            "--short",
            f"refs/remotes/{remote}/HEAD",
            check=False,
        )
        target = result.stdout.strip()
        prefix = f"{remote}/"
        if result.returncode == 0 and target.startswith(prefix):
            defaults.add(target.removeprefix(prefix))
    return defaults


def check_git(audit: Audit) -> None:
    branch = git(audit.root, "branch", "--show-current").stdout.strip()
    head_result = git(
        audit.root,
        "log",
        "-1",
        "--oneline",
        "--decorate",
        check=False,
    )
    head = head_result.stdout.strip() if head_result.returncode == 0 else "(no commits)"
    audit.info.append(f"branch: {branch or '(detached HEAD)'}")
    audit.info.append(f"HEAD: {head}")

    remotes = git(audit.root, "remote").stdout.splitlines()
    audit.info.append(f"remotes: {len(remotes)}")
    default_branches = remote_default_local_branches(audit.root, remotes)
    if default_branches:
        audit.info.append(
            f"remote default local branch(es): {sorted(default_branches)}"
        )

    status = git(audit.root, "status", "--short").stdout.splitlines()
    if status:
        audit.warnings.append(
            f"worktree has {len(status)} changed or untracked path(s)"
        )
        audit.info.extend(f"status: {line}" for line in status[:20])
        if len(status) > 20:
            audit.info.append(f"status: ... and {len(status) - 20} more")
    else:
        audit.info.append("worktree is clean")

    ignored = git(
        audit.root,
        "ls-files",
        "-i",
        "-c",
        "--exclude-standard",
        check=False,
    ).stdout.splitlines()
    if ignored:
        audit.errors.append(
            f"{len(ignored)} tracked file(s) match ignore rules: {ignored[:10]}"
        )

    merged = git(
        audit.root,
        "branch",
        "--merged",
        "HEAD",
        "--format=%(refname:short)",
        check=False,
    ).stdout
    merged_names = [
        name
        for name in merged.splitlines()
        if name and name != branch and name not in default_branches
    ]
    if merged_names:
        audit.warnings.append(f"merged local branch candidate(s): {merged_names}")

    gone = [
        line.strip()
        for line in git(audit.root, "branch", "-vv").stdout.splitlines()
        if ": gone]" in line
    ]
    if gone:
        audit.warnings.append(f"local branch(es) with gone upstream: {gone}")


def check_ignore_expectations(
    audit: Audit,
    expect_ignored: list[str],
    expect_trackable: list[str],
) -> None:
    for path in expect_ignored:
        result = git(
            audit.root, "check-ignore", "--no-index", "--quiet", "--", path, check=False
        )
        if result.returncode != 0:
            audit.errors.append(f"expected ignored path is trackable: {path}")
    for path in expect_trackable:
        result = git(
            audit.root, "check-ignore", "--no-index", "--quiet", "--", path, check=False
        )
        if result.returncode == 0:
            audit.errors.append(f"expected trackable path is ignored: {path}")


def check_local_artifacts(audit: Audit) -> None:  # noqa: PLR0912
    generated_outputs = [
        name for name in GENERATED_OUTPUT_PATHS if (audit.root / name).exists()
    ]
    if generated_outputs:
        audit.warnings.append(
            f"generated build/coverage output(s) present: {generated_outputs}"
        )

    hidden_pth: list[str] = []
    duplicates = [
        relative(path, audit.root)
        for path in sorted(audit.root.iterdir())
        if path.is_file() and canonical_sync_name(path.name) in SYNC_SENSITIVE_PATHS
    ]
    duplicates.extend(
        [
            relative(path, audit.root)
            for path in sorted(audit.root.iterdir())
            if is_tool_directory_copy(path)
        ]
    )
    visited_directories: set[Path] = set()
    directories = [
        audit.root / name for name in TOOL_DIRS if (audit.root / name).is_dir()
    ]
    directories.sort(key=lambda path: path.is_symlink())
    for directory in directories:
        resolved_directory = directory.resolve()
        if resolved_directory in visited_directories:
            continue
        visited_directories.add(resolved_directory)
        for current, dirnames, filenames in os.walk(directory):
            current_path = Path(current)
            for filename in filenames:
                path = current_path / filename
                if path.suffix == ".pth" and is_hidden(path):
                    hidden_pth.append(relative(path, audit.root))
                if SYNC_DUPLICATE.search(filename):
                    duplicates.append(relative(path, audit.root))
            for dirname in tuple(dirnames):
                path = current_path / dirname
                if SYNC_DUPLICATE.search(dirname):
                    duplicates.append(relative(path, audit.root))
                    dirnames.remove(dirname)

    if hidden_pth:
        audit.errors.append(
            f"hidden .pth file(s) can break editable installs: {hidden_pth[:10]}"
        )
    if duplicates:
        audit.errors.append(
            f"sync-conflict duplicate(s) in tool directories: {duplicates[:10]}"
        )

    placeholders: list[str] = []
    for current, dirnames, filenames in os.walk(audit.root):
        dirnames[:] = [
            name for name in dirnames if name not in {".git", ".venv", ".venv.nosync"}
        ]
        for filename in filenames:
            if filename.startswith(".") and filename.endswith(".icloud"):
                placeholders.append(relative(Path(current) / filename, audit.root))
    if placeholders:
        audit.errors.append(
            f"iCloud placeholder(s) have no local contents: {placeholders[:10]}"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="path inside the repository")
    parser.add_argument("--expect-ignored", action="append", default=[], metavar="PATH")
    parser.add_argument(
        "--expect-trackable", action="append", default=[], metavar="PATH"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = find_root(args.root)
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    audit = Audit(root)
    check_git(audit)
    check_ignore_expectations(audit, args.expect_ignored, args.expect_trackable)
    check_local_artifacts(audit)
    return audit.report()


if __name__ == "__main__":
    raise SystemExit(main())
