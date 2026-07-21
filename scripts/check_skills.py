#!/usr/bin/env python3
"""Validate Agent Skills packages and repository-specific metadata."""

from __future__ import annotations

import argparse
import re
import stat
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INVENTORY_PATTERN = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
ALLOWED_FRONTMATTER = {"name", "description", "license", "allowed-tools", "metadata"}
ALLOWED_OPENAI_KEYS = {"interface", "dependencies", "policy"}
ALLOWED_POLICY_KEYS = {"allow_implicit_invocation"}
REQUIRED_INTERFACE_KEYS = {"display_name", "short_description", "default_prompt"}


class Findings:
    """Collect deterministic validation errors."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[str] = []

    def add(self, path: Path, message: str) -> None:
        try:
            label = path.relative_to(self.root)
        except ValueError:
            label = path
        self.errors.append(f"{label}: {message}")


def load_mapping(path: Path, findings: Findings) -> dict[str, Any] | None:
    try:
        loaded: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        findings.add(path, f"cannot parse YAML: {exc}")
        return None
    if not isinstance(loaded, dict):
        findings.add(path, "YAML content must be a mapping")
        return None
    return loaded


def frontmatter(path: Path, findings: Findings) -> dict[str, Any] | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        findings.add(path, f"cannot read file: {exc}")
        return None
    if not lines or lines[0] != "---":
        findings.add(path, "must begin with YAML frontmatter")
        return None
    try:
        closing = lines.index("---", 1)
    except ValueError:
        findings.add(path, "frontmatter is missing its closing delimiter")
        return None
    try:
        loaded: object = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        findings.add(path, f"cannot parse frontmatter: {exc}")
        return None
    if not isinstance(loaded, dict):
        findings.add(path, "frontmatter must be a mapping")
        return None
    return loaded


def string_value(
    mapping: dict[str, Any], key: str, path: Path, findings: Findings
) -> str | None:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        findings.add(path, f"{key!r} must be a non-empty string")
        return None
    return value


def link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0]


def validate_relative_links(
    skill_dir: Path, skill_file: Path, findings: Findings
) -> None:
    text = skill_file.read_text(encoding="utf-8")
    package_root = skill_dir.resolve()
    for raw_target in LINK_PATTERN.findall(text):
        target = link_target(raw_target)
        if (
            not target
            or target.startswith(("#", "/"))
            or ":" in target.split("/", 1)[0]
        ):
            continue
        resolved = (skill_file.parent / target.split("#", 1)[0]).resolve()
        try:
            resolved.relative_to(package_root)
        except ValueError:
            findings.add(
                skill_file, f"relative reference escapes the skill package: {target}"
            )
            continue
        if not resolved.exists():
            findings.add(skill_file, f"relative reference does not resolve: {target}")


def validate_frontmatter(skill_dir: Path, findings: Findings) -> None:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        findings.add(skill_file, "required file is missing")
        return
    metadata = frontmatter(skill_file, findings)
    if metadata is None:
        return

    unexpected = set(metadata) - ALLOWED_FRONTMATTER
    if unexpected:
        findings.add(skill_file, f"unsupported frontmatter keys: {sorted(unexpected)}")

    name = string_value(metadata, "name", skill_file, findings)
    if name is not None:
        if len(name) > 64 or NAME_PATTERN.fullmatch(name) is None:
            findings.add(
                skill_file,
                "name must be a kebab-case identifier of at most 64 characters",
            )
        if name != skill_dir.name:
            findings.add(
                skill_file, f"name {name!r} does not match directory {skill_dir.name!r}"
            )

    description = string_value(metadata, "description", skill_file, findings)
    if description is not None:
        if len(description) > 1024:
            findings.add(skill_file, "description exceeds 1,024 characters")
        if "<" in description or ">" in description:
            findings.add(skill_file, "description cannot contain angle brackets")

    validate_relative_links(skill_dir, skill_file, findings)


def validate_string_styles(node: Node, path: Path, findings: Findings) -> None:
    if isinstance(node, MappingNode):
        for _, value_node in node.value:
            validate_string_styles(value_node, path, findings)
        return
    if isinstance(node, SequenceNode):
        for item in node.value:
            validate_string_styles(item, path, findings)
        return
    if (
        isinstance(node, ScalarNode)
        and node.tag.endswith(":str")
        and node.style is None
    ):
        findings.add(
            path, f"string value on line {node.start_mark.line + 1} must be quoted"
        )


def mapping_value(
    mapping: dict[str, Any], key: str, path: Path, findings: Findings
) -> dict[str, Any] | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        findings.add(path, f"{key!r} must be a mapping")
        return None
    return value


def validate_interface(
    interface: dict[str, Any], skill_name: str, path: Path, findings: Findings
) -> None:
    missing = REQUIRED_INTERFACE_KEYS - set(interface)
    if missing:
        findings.add(path, f"interface is missing required keys: {sorted(missing)}")

    string_value(interface, "display_name", path, findings)
    short_description = string_value(interface, "short_description", path, findings)
    if short_description is not None and not 25 <= len(short_description) <= 64:
        findings.add(path, "short_description must contain 25 to 64 characters")
    prompt = string_value(interface, "default_prompt", path, findings)
    if prompt is not None and f"${skill_name}" not in prompt:
        findings.add(path, f"default_prompt must explicitly mention ${skill_name}")

    for key in ("icon_small", "icon_large"):
        icon = interface.get(key)
        if icon is None:
            continue
        if not isinstance(icon, str) or not icon:
            findings.add(path, f"{key!r} must be a non-empty relative path")
            continue
        icon_path = (path.parent.parent / icon).resolve()
        try:
            icon_path.relative_to(path.parent.parent.resolve())
        except ValueError:
            findings.add(path, f"{key!r} escapes the skill package")
            continue
        if not icon_path.is_file():
            findings.add(path, f"{key!r} does not resolve: {icon}")


def validate_policy(policy: dict[str, Any], path: Path, findings: Findings) -> None:
    unexpected = set(policy) - ALLOWED_POLICY_KEYS
    if unexpected:
        findings.add(path, f"unsupported policy keys: {sorted(unexpected)}")
    implicit = policy.get("allow_implicit_invocation")
    if implicit is not None and not isinstance(implicit, bool):
        findings.add(path, "'allow_implicit_invocation' must be a boolean")


def validate_openai_metadata(skill_dir: Path, findings: Findings) -> None:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.exists():
        return
    if not path.is_file():
        findings.add(path, "metadata path must be a file")
        return

    metadata = load_mapping(path, findings)
    if metadata is None:
        return
    unexpected = set(metadata) - ALLOWED_OPENAI_KEYS
    if unexpected:
        findings.add(path, f"unsupported top-level keys: {sorted(unexpected)}")

    try:
        node = yaml.compose(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        node = None
    if node is not None:
        validate_string_styles(node, path, findings)

    interface = mapping_value(metadata, "interface", path, findings)
    if interface is None:
        findings.add(path, "required 'interface' mapping is missing")
    else:
        validate_interface(interface, skill_dir.name, path, findings)

    policy = mapping_value(metadata, "policy", path, findings)
    if policy is not None:
        validate_policy(policy, path, findings)


def validate_script_modes(skill_dir: Path, findings: Findings) -> None:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return
    for path in sorted(scripts_dir.rglob("*")):
        if (
            path.is_file()
            and path.suffix in {".py", ".sh"}
            and path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) == 0
        ):
            findings.add(path, "script must have an executable file mode")


def skill_directories(root: Path, findings: Findings) -> list[Path]:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        findings.add(skills_root, "skills directory is missing")
        return []
    return sorted(
        path
        for path in skills_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )


def validate_inventory(
    root: Path, skill_names: Iterable[str], findings: Findings
) -> None:
    readme = root / "README.md"
    if not readme.is_file():
        findings.add(readme, "root inventory is missing")
        return
    listed = set(INVENTORY_PATTERN.findall(readme.read_text(encoding="utf-8")))
    actual = set(skill_names)
    if listed != actual:
        missing = sorted(actual - listed)
        extra = sorted(listed - actual)
        if missing:
            findings.add(readme, f"inventory is missing skills: {missing}")
        if extra:
            findings.add(readme, f"inventory lists unknown skills: {extra}")


def validate_repository(root: Path) -> list[str]:
    findings = Findings(root)
    directories = skill_directories(root, findings)
    for skill_dir in directories:
        validate_frontmatter(skill_dir, findings)
        validate_openai_metadata(skill_dir, findings)
        validate_script_modes(skill_dir, findings)
    validate_inventory(root, (path.name for path in directories), findings)
    return sorted(findings.errors)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to validate (default: current directory)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    errors = validate_repository(root)
    if errors:
        print(f"Skill validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"Skill validation passed: {len(skill_directories(root, Findings(root)))} packages."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
