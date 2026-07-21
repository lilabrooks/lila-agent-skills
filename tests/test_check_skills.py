from __future__ import annotations

import stat
from pathlib import Path

from conftest import SKILL_CHECK_SCRIPT, run_python


def create_skill_repository(root: Path) -> Path:
    skill = root / "skills" / "demo-skill"
    (skill / "agents").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "scripts").mkdir()
    (root / "README.md").write_text(
        "# Skills\n\n| Skill | Purpose |\n| --- | --- |\n"
        "| `demo-skill` | Test package. |\n",
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: demo-skill\n"
        "description: Validate a representative skill package.\n"
        "---\n\n"
        "Read [details](references/details.md).\n",
        encoding="utf-8",
    )
    (skill / "references" / "details.md").write_text("# Details\n", encoding="utf-8")
    script = skill / "scripts" / "tool.py"
    script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Demo Skill"\n'
        '  short_description: "Validate a representative skill package"\n'
        '  default_prompt: "Use $demo-skill to validate this package."\n',
        encoding="utf-8",
    )
    return skill


def test_valid_repository_passes(tmp_path: Path) -> None:
    create_skill_repository(tmp_path)

    result = run_python(SKILL_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 0
    assert "Skill validation passed: 1 packages." in result.stdout


def test_name_and_inventory_mismatches_fail(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    skill_file = skill / "SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8").replace(
            "name: demo-skill", "name: wrong-skill"
        ),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Empty inventory\n", encoding="utf-8")

    result = run_python(SKILL_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "does not match directory" in result.stderr
    assert "inventory is missing skills" in result.stderr


def test_missing_and_escaping_relative_references_fail(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: demo-skill\n"
        "description: Validate a representative skill package.\n"
        "---\n\n"
        "Read [missing](references/missing.md) and [outside](../../README.md).\n",
        encoding="utf-8",
    )

    result = run_python(SKILL_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "relative reference does not resolve" in result.stderr
    assert "relative reference escapes the skill package" in result.stderr


def test_openai_metadata_constraints_fail(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n"
        "  display_name: Demo\n"
        '  short_description: "Too short"\n'
        '  default_prompt: "Use the skill."\n',
        encoding="utf-8",
    )

    result = run_python(SKILL_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "must be quoted" in result.stderr
    assert "short_description must contain 25 to 64 characters" in result.stderr
    assert "must explicitly mention $demo-skill" in result.stderr


def test_non_executable_skill_script_fails(tmp_path: Path) -> None:
    skill = create_skill_repository(tmp_path)
    script = skill / "scripts" / "tool.py"
    script.chmod(stat.S_IRUSR | stat.S_IWUSR)

    result = run_python(SKILL_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "script must have an executable file mode" in result.stderr
