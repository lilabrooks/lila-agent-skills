from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from conftest import PROJECT_ROOT, git, init_repository, run, run_python
from test_check_secrets import create_empty_baseline
from test_check_skills import create_skill_repository

CHECK_SECRETS_SCRIPT = PROJECT_ROOT / "scripts/check_secrets.py"
CHECK_SKILLS_SCRIPT = PROJECT_ROOT / "scripts/check_skills.py"
AUDIT_SCRIPT = PROJECT_ROOT / "skills/verify-repository/scripts/repo_audit.py"


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


check_secrets = load_module(CHECK_SECRETS_SCRIPT, "quality_check_secrets")
check_skills = load_module(CHECK_SKILLS_SCRIPT, "quality_check_skills")
repo_audit = load_module(AUDIT_SCRIPT, "quality_repo_audit")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "must begin with YAML frontmatter"),
        ("---\nname: demo-skill\n", "frontmatter is missing its closing delimiter"),
        ("---\nname: [\n---\n", "cannot parse frontmatter"),
        ("---\n- demo-skill\n---\n", "frontmatter must be a mapping"),
    ],
)
def test_skill_frontmatter_structure_errors_fail(
    tmp_path: Path, content: str, message: str
) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "SKILL.md").write_text(content, encoding="utf-8")

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert message in result.stderr


def test_skill_frontmatter_rejects_invalid_utf8(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "SKILL.md").write_bytes(b"\xff\xfe")

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "cannot read file" in result.stderr


def test_skill_frontmatter_fields_and_link_forms_are_checked(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    description = "<" + ("x" * 1025) + ">"
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: Invalid_Name\n"
        f'description: "{description}"\n'
        "unsupported: true\n"
        "---\n\n"
        "[anchor](#section) [absolute](/tmp/file) [web](https://example.com) "
        '[empty]() [wrapped](<references/details.md> "title")\n',
        encoding="utf-8",
    )

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "unsupported frontmatter keys" in result.stderr
    assert "name must be a kebab-case identifier" in result.stderr
    assert "does not match directory" in result.stderr
    assert "description exceeds 1,024 characters" in result.stderr
    assert "description cannot contain angle brackets" in result.stderr
    assert "relative reference" not in result.stderr


def test_skill_frontmatter_requires_string_fields(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "SKILL.md").write_text(
        "---\nname: []\ndescription:\n---\n", encoding="utf-8"
    )

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "'name' must be a non-empty string" in result.stderr
    assert "'description' must be a non-empty string" in result.stderr


def test_skill_package_allows_optional_metadata_and_scripts(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    shutil.rmtree(skill / "agents")
    shutil.rmtree(skill / "scripts")

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 0


def test_skill_package_requires_skill_file(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "SKILL.md").unlink()

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "required file is missing" in result.stderr


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("interface: [", "cannot parse YAML"),
        ("- interface", "YAML content must be a mapping"),
        ("dependencies: {}\n", "required 'interface' mapping is missing"),
        (
            "unsupported: true\ninterface: []\n",
            "unsupported top-level keys",
        ),
    ],
)
def test_openai_metadata_structure_errors_fail(
    tmp_path: Path, content: str, message: str
) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "agents" / "openai.yaml").write_text(content, encoding="utf-8")

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert message in result.stderr


def test_openai_metadata_path_must_be_a_file(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    metadata = skill / "agents" / "openai.yaml"
    metadata.unlink()
    metadata.mkdir()

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "metadata path must be a file" in result.stderr


def test_openai_metadata_rejects_invalid_fields_and_icons(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n"
        "  display_name: []\n"
        '  short_description: ""\n'
        "  default_prompt: 3\n"
        "  icon_small: []\n"
        '  icon_large: "../../outside.svg"\n',
        encoding="utf-8",
    )

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "'display_name' must be a non-empty string" in result.stderr
    assert "'short_description' must be a non-empty string" in result.stderr
    assert "'default_prompt' must be a non-empty string" in result.stderr
    assert "'icon_small' must be a non-empty relative path" in result.stderr
    assert "'icon_large' escapes the skill package" in result.stderr


def test_openai_metadata_rejects_invalid_invocation_policy(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    metadata = skill / "agents" / "openai.yaml"
    metadata.write_text(
        metadata.read_text(encoding="utf-8")
        + "policy:\n"
        + '  allow_implicit_invocation: "no"\n'
        + "  unexpected: true\n",
        encoding="utf-8",
    )

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "'allow_implicit_invocation' must be a boolean" in result.stderr
    assert "unsupported policy keys: ['unexpected']" in result.stderr


def test_openai_metadata_checks_icon_resolution_and_sequences(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "icon.svg").write_text("<svg/>\n", encoding="utf-8")
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Demo Skill"\n'
        '  short_description: "Validate a representative skill package"\n'
        '  default_prompt: "Use $demo-skill to validate this package."\n'
        '  icon_small: "./missing.svg"\n'
        '  icon_large: "./icon.svg"\n'
        "dependencies:\n"
        "  tools:\n"
        "    - type: mcp\n"
        "      value: demo\n",
        encoding="utf-8",
    )

    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "icon_small' does not resolve" in result.stderr
    assert "string value" in result.stderr
    assert "must be quoted" in result.stderr


def test_repository_structure_and_inventory_errors_fail(tmp_path: Path) -> None:
    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)
    assert result.returncode == 1
    assert "skills directory is missing" in result.stderr
    assert "root inventory is missing" in result.stderr

    skill = create_skill_repository(tmp_path)
    (tmp_path / "README.md").write_text(
        "| `demo-skill` | Demo |\n| `ghost-skill` | Ghost |\n",
        encoding="utf-8",
    )
    result = run_python(CHECK_SKILLS_SCRIPT, "--root", tmp_path)
    assert result.returncode == 1
    assert "inventory lists unknown skills" in result.stderr
    assert skill.is_dir()


def test_findings_preserve_paths_outside_repository(tmp_path: Path) -> None:
    findings = check_skills.Findings(tmp_path)
    outside = tmp_path.parent / "outside.txt"

    findings.add(outside, "outside")

    assert findings.errors == [f"{outside}: outside"]


def test_secret_scan_reports_git_enumeration_failure(tmp_path: Path) -> None:
    root = tmp_path / "broken"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".secrets.baseline").write_text("{}\n", encoding="utf-8")

    result = run_python(CHECK_SECRETS_SCRIPT, "--root", root)

    assert result.returncode == 2
    assert "fatal: not a git repository" in result.stderr


def test_secret_scan_accepts_empty_repository_and_absolute_baseline(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    init_repository(root, commit=False)
    create_empty_baseline(root)
    baseline = (root / ".secrets.baseline").resolve()

    result = run_python(CHECK_SECRETS_SCRIPT, "--root", root, "--baseline", baseline)

    assert result.returncode == 0
    assert "no repository files to inspect" in result.stdout


def test_secret_scan_reports_missing_scanner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = tmp_path / ".secrets.baseline"
    baseline.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(check_secrets.shutil, "which", lambda _: None)

    result = check_secrets.run_scan(tmp_path, baseline)

    assert result == 2


def test_audit_reports_long_status_merged_and_gone_branches(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    init_repository(root)
    run(["git", "init", "--bare", "--quiet", str(remote)])
    git(root, "branch", "merged")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "--quiet", "--set-upstream", "origin", "main")
    run(["git", "--git-dir", str(remote), "update-ref", "-d", "refs/heads/main"])
    git(root, "fetch", "--quiet", "--prune", "origin")
    for index in range(21):
        (root / f"untracked-{index}.txt").write_text("draft\n", encoding="utf-8")

    result = run_python(AUDIT_SCRIPT, "--root", root)

    assert result.returncode == 0
    assert "and 1 more" in result.stdout
    assert "merged local branch candidate" in result.stdout
    assert "local branch(es) with gone upstream" in result.stdout


def test_audit_accepts_satisfied_ignore_expectations(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    (root / ".gitignore").write_text("*.cache\n", encoding="utf-8")

    result = run_python(
        AUDIT_SCRIPT,
        "--root",
        root,
        "--expect-ignored",
        "expected.cache",
        "--expect-trackable",
        "expected.txt",
    )

    assert result.returncode == 0


def test_audit_detects_hidden_pth_and_duplicate_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    init_repository(root)
    environment = root / ".venv"
    environment.mkdir()
    hidden_pth = environment / "hidden.pth"
    hidden_pth.write_text("import demo\n", encoding="utf-8")
    (environment / "cache 2").mkdir()
    (root / ".ruff_cache 2").mkdir()
    (root / ".venv.nosync").symlink_to(environment, target_is_directory=True)
    monkeypatch.setattr(repo_audit, "is_hidden", lambda path: path == hidden_pth)

    audit = repo_audit.Audit(root)
    repo_audit.check_local_artifacts(audit)

    assert any("hidden .pth" in error for error in audit.errors)
    assert any("sync-conflict duplicate" in error for error in audit.errors)


def test_audit_platform_hidden_flags_and_external_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(repo_audit.stat, "UF_HIDDEN", 1, raising=False)
    monkeypatch.setattr(repo_audit.stat, "FILE_ATTRIBUTE_HIDDEN", 2, raising=False)

    class FakePath:
        def __init__(self, flags: int, attributes: int) -> None:
            self.metadata = SimpleNamespace(
                st_flags=flags, st_file_attributes=attributes
            )

        def lstat(self) -> Any:
            return self.metadata

    assert repo_audit.is_hidden(FakePath(1, 0))
    assert repo_audit.is_hidden(FakePath(0, 2))
    assert not repo_audit.is_hidden(FakePath(0, 0))

    external = tmp_path.parent
    assert repo_audit.relative(external, tmp_path) == str(external)
