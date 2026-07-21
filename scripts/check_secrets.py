#!/usr/bin/env python3
"""Scan repository files for probable credentials against a reviewed baseline."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def repository_files(root: Path) -> list[str]:
    """Return tracked and non-ignored untracked files using Git's path rules."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(detail or "Git could not enumerate repository files")

    return [
        os.fsdecode(item)
        for item in result.stdout.split(b"\0")
        if item and os.fsdecode(item) != ".secrets.baseline"
    ]


def run_scan(root: Path, baseline: Path) -> int:
    """Run detect-secrets-hook and return its exit status."""
    executable = shutil.which("detect-secrets-hook")
    if executable is None:
        print(
            "ERROR: detect-secrets-hook is unavailable; run `make secrets`.",
            file=sys.stderr,
        )
        return 2

    try:
        filenames = repository_files(root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not filenames:
        print("Secret scan: no repository files to inspect.")
        return 0

    result = subprocess.run(
        [executable, "--baseline", str(baseline), *filenames],
        cwd=root,
        check=False,
    )
    if result.returncode == 0:
        print(f"Secret scan: {len(filenames)} files matched the reviewed baseline.")
    return result.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path(".secrets.baseline"),
        help="Baseline path relative to the repository root",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    baseline = args.baseline
    if not baseline.is_absolute():
        baseline = root / baseline

    if not (root / ".git").exists():
        print(f"ERROR: not a Git repository: {root}", file=sys.stderr)
        return 2
    if not baseline.is_file():
        print(f"ERROR: secret baseline is missing: {baseline}", file=sys.stderr)
        return 2
    return run_scan(root, baseline)


if __name__ == "__main__":
    raise SystemExit(main())
