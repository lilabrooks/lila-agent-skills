from __future__ import annotations

import shutil
from pathlib import Path
from typing import TypeAlias

import pytest
import yaml
from conftest import BEHAVIOR_CHECK_SCRIPT, PROJECT_ROOT, run_python

FIXTURE = PROJECT_ROOT / "tests/fixtures/skill_behavior.yaml"
FixturePath: TypeAlias = tuple[str | int, ...]


def copy_behavior_repository(root: Path) -> Path:
    for name in (
        "github-publish-changes",
        "github-merge-pull-request",
        "prepare-agent-compatible-repository",
        "clean-git-branches",
        "verify-repository",
    ):
        destination = root / "skills" / name
        destination.mkdir(parents=True)
        shutil.copy(PROJECT_ROOT / "skills" / name / "SKILL.md", destination)
    fixture = root / "tests/fixtures/skill_behavior.yaml"
    fixture.parent.mkdir(parents=True)
    shutil.copy(FIXTURE, fixture)
    return fixture


def load_fixture(path: Path) -> dict[str, object]:
    loaded: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def write_fixture(path: Path, fixture: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(fixture, sort_keys=False), encoding="utf-8")


def replace_fixture_value(
    fixture: dict[str, object], path: FixturePath, value: object
) -> None:
    current: object = fixture
    for key in path[:-1]:
        if isinstance(key, int):
            assert isinstance(current, list)
            current = current[key]
        else:
            assert isinstance(current, dict)
            current = current[key]
    final = path[-1]
    if isinstance(final, int):
        assert isinstance(current, list)
        current[final] = value
    else:
        assert isinstance(current, dict)
        current[final] = value


def run_with_fixture_value(
    tmp_path: Path, path: FixturePath, value: object
) -> tuple[int, str]:
    fixture_path = copy_behavior_repository(tmp_path)
    fixture = load_fixture(fixture_path)
    replace_fixture_value(fixture, path, value)
    write_fixture(fixture_path, fixture)
    result = run_python(
        BEHAVIOR_CHECK_SCRIPT,
        "--root",
        tmp_path,
        "--fixture",
        fixture_path,
    )
    return result.returncode, result.stderr


def test_repository_behavioral_contracts_pass() -> None:
    result = run_python(BEHAVIOR_CHECK_SCRIPT, "--root", PROJECT_ROOT)

    assert result.returncode == 0, result.stderr
    assert "Behavioral contract check passed: 5 skills, 12 scenarios" in result.stdout
    assert "standard-commit-boundary: baseline" in result.stdout


def test_behavioral_contract_inventory_covers_every_skill() -> None:
    fixture = load_fixture(FIXTURE)
    contracts = fixture["contracts"]
    assert isinstance(contracts, list)
    contract_ids = {
        contract["id"] for contract in contracts if isinstance(contract, dict)
    }
    skill_ids = {
        path.name
        for path in (PROJECT_ROOT / "skills").iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }

    assert contract_ids == skill_ids


def test_removed_compatibility_rule_fails_contract(tmp_path: Path) -> None:
    copy_behavior_repository(tmp_path)
    skill = tmp_path / "skills/prepare-agent-compatible-repository/SKILL.md"
    required = "Do not turn instructions into enforcement claims."
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(required, ""),
        encoding="utf-8",
    )

    result = run_python(BEHAVIOR_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert f"missing required literal {required!r}" in result.stderr


def test_removed_publish_authorization_rule_fails_contract(tmp_path: Path) -> None:
    copy_behavior_repository(tmp_path)
    skill = tmp_path / "skills/github-publish-changes/SKILL.md"
    required = "End after the requested push."
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(required, ""), encoding="utf-8"
    )

    result = run_python(BEHAVIOR_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert f"missing required literal {required!r}" in result.stderr


def test_calibration_rejects_passing_mutation(tmp_path: Path) -> None:
    fixture_path = copy_behavior_repository(tmp_path)
    fixture = load_fixture(fixture_path)
    scenarios = fixture["scenarios"]
    assert isinstance(scenarios, list)
    scenario = scenarios[0]
    assert isinstance(scenario, dict)
    variants = scenario["variants"]
    assert isinstance(variants, dict)
    variants["mutation"] = variants["treatment"]
    write_fixture(fixture_path, fixture)

    result = run_python(BEHAVIOR_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "standard-commit-boundary/mutation: expected fail" in result.stderr


def test_invalid_fixture_reports_configuration_error(tmp_path: Path) -> None:
    fixture_path = copy_behavior_repository(tmp_path)
    fixture = load_fixture(fixture_path)
    scenarios = fixture["scenarios"]
    assert isinstance(scenarios, list)
    scenario = scenarios[0]
    assert isinstance(scenario, dict)
    checks = scenario["checks"]
    assert isinstance(checks, list)
    check = checks[0]
    assert isinstance(check, dict)
    check["kind"] = "subjective_model_grade"
    write_fixture(fixture_path, fixture)

    result = run_python(BEHAVIOR_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 2
    assert "unknown kind 'subjective_model_grade'" in result.stderr


@pytest.mark.parametrize(
    ("path", "value", "expected"),
    [
        (("version",), 2, "fixture.version must be 1"),
        (("contracts",), {}, "contracts must be a sequence"),
        (("scenarios", 0, "id"), "", "must be a non-empty string"),
        (
            ("contracts", 0, "required_literals"),
            [""],
            "must contain non-empty strings",
        ),
        (("scenarios", 0, "checks", 0, "gate"), "unknown-gate", "unknown gate"),
        (("scenarios", 0, "variants"), {"treatment": "x"}, "must define"),
    ],
)
def test_malformed_fixture_values_fail_cleanly(
    tmp_path: Path, path: FixturePath, value: object, expected: str
) -> None:
    returncode, stderr = run_with_fixture_value(tmp_path, path, value)

    assert returncode == 2
    assert expected in stderr


def test_contract_path_cannot_escape_repository(tmp_path: Path) -> None:
    returncode, stderr = run_with_fixture_value(
        tmp_path,
        ("contracts", 0, "path"),
        "../outside/SKILL.md",
    )

    assert returncode == 2
    assert "path escapes the repository" in stderr


def test_treatment_must_beat_baseline(tmp_path: Path) -> None:
    fixture_path = copy_behavior_repository(tmp_path)
    fixture = load_fixture(fixture_path)
    scenarios = fixture["scenarios"]
    assert isinstance(scenarios, list)
    scenario = scenarios[0]
    assert isinstance(scenario, dict)
    variants = scenario["variants"]
    assert isinstance(variants, dict)
    variants["baseline"] = variants["treatment"]
    write_fixture(fixture_path, fixture)

    result = run_python(BEHAVIOR_CHECK_SCRIPT, "--root", tmp_path)

    assert result.returncode == 1
    assert "treatment did not beat baseline" in result.stderr
