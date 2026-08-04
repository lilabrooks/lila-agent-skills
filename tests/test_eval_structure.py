from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from conftest import PROJECT_ROOT

EVALS_ROOT = PROJECT_ROOT / "evals"
REQUIRED_CASE_KEYS = {
    "version",
    "skill",
    "scenario",
    "hosts",
    "fixture",
    "prompt",
    "answers",
    "criteria",
    "forbidden_actions",
    "terminal_condition",
}
ALLOWED_ACTION_SCOPES = {"workspace", "host-state", "conversation", "external"}


def load_mapping(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), f"{path} must contain a mapping"
    return loaded


def non_empty_text(value: object, label: str) -> str:
    assert isinstance(value, str) and value.strip(), f"{label} must be non-empty text"
    return value


def mapping_list(value: object, label: str) -> list[dict[str, Any]]:
    assert isinstance(value, list) and value, f"{label} must be a non-empty list"
    assert all(isinstance(item, dict) for item in value), (
        f"{label} must contain mappings"
    )
    return value


def assert_unique_ids(items: list[dict[str, Any]], label: str) -> None:
    identifiers = [non_empty_text(item.get("id"), f"{label}.id") for item in items]
    assert len(identifiers) == len(set(identifiers)), f"{label} ids must be unique"


def validate_answers(case: dict[str, Any], label: str) -> None:
    answers = case["answers"]
    assert isinstance(answers, dict), f"{label}.answers must be a mapping"
    assert set(answers) == {"instructions", "facts"}
    non_empty_text(answers["instructions"], f"{label}.answers.instructions")
    facts = mapping_list(answers["facts"], f"{label}.answers.facts")
    assert_unique_ids(facts, f"{label}.answers.facts")
    for fact in facts:
        assert set(fact) == {"id", "disclose_when", "answer"}
        non_empty_text(fact["disclose_when"], f"{label}.fact.disclose_when")
        non_empty_text(fact["answer"], f"{label}.fact.answer")


def validate_criteria(case: dict[str, Any], label: str) -> None:
    criteria = mapping_list(case["criteria"], f"{label}.criteria")
    assert_unique_ids(criteria, f"{label}.criteria")
    for criterion in criteria:
        assert set(criterion) == {"id", "description", "applicability"}
        non_empty_text(criterion["description"], f"{label}.criterion.description")
        non_empty_text(criterion["applicability"], f"{label}.criterion.applicability")


def validate_forbidden_actions(case: dict[str, Any], label: str) -> None:
    actions = mapping_list(case["forbidden_actions"], f"{label}.forbidden_actions")
    assert_unique_ids(actions, f"{label}.forbidden_actions")
    for action in actions:
        assert set(action) == {"id", "scope", "description"}
        assert action["scope"] in ALLOWED_ACTION_SCOPES
        non_empty_text(action["description"], f"{label}.action.description")


def validate_case(
    path: Path,
    skill_name: str,
    scenario_name: str,
    known_hosts: set[str],
    scenario_entries: set[str],
) -> None:
    case = load_mapping(path)
    label = str(path.relative_to(PROJECT_ROOT))
    assert set(case) == REQUIRED_CASE_KEYS
    assert case["version"] == 1
    assert case["skill"] == skill_name
    assert case["scenario"] == scenario_name

    hosts = case["hosts"]
    assert isinstance(hosts, list) and hosts
    assert all(isinstance(host, str) for host in hosts)
    assert len(hosts) == len(set(hosts))
    assert set(hosts) <= known_hosts
    assert "{invocation}" in non_empty_text(case["prompt"], f"{label}.prompt")

    fixture = case["fixture"]
    assert fixture is None or isinstance(fixture, str)
    if isinstance(fixture, str):
        assert fixture == "fixture"
        assert "fixture" in scenario_entries
        fixture_path = (path.parent / fixture).resolve()
        assert fixture_path.is_dir()
        fixture_path.relative_to(path.parent.resolve())
    else:
        assert "fixture" not in scenario_entries

    validate_answers(case, label)
    validate_criteria(case, label)
    validate_forbidden_actions(case, label)

    terminal = case["terminal_condition"]
    assert isinstance(terminal, dict)
    assert set(terminal) == {"description", "requires_owner_confirmation"}
    non_empty_text(terminal["description"], f"{label}.terminal.description")
    assert isinstance(terminal["requires_owner_confirmation"], bool)


def test_live_eval_scenario_structure() -> None:
    hosts_document = load_mapping(EVALS_ROOT / "hosts.yaml")
    assert set(hosts_document) == {"version", "hosts"}
    assert hosts_document["version"] == 1
    hosts = hosts_document["hosts"]
    assert isinstance(hosts, dict) and hosts
    for host_name, host in hosts.items():
        assert isinstance(host_name, str) and host_name
        assert isinstance(host, dict)
        assert set(host) == {"label", "invocation_template"}
        non_empty_text(host["label"], f"host {host_name}.label")
        assert "{skill}" in non_empty_text(
            host["invocation_template"], f"host {host_name}.invocation_template"
        )

    root_entries = sorted(EVALS_ROOT.iterdir())
    skill_roots = [entry for entry in root_entries if entry.name != "hosts.yaml"]
    assert all(path.is_dir() for path in skill_roots)
    assert skill_roots

    known_skills = {path.name for path in (PROJECT_ROOT / "skills").iterdir()}
    for skill_root in skill_roots:
        assert skill_root.name in known_skills
        scenarios = sorted(skill_root.iterdir())
        assert scenarios and all(path.is_dir() for path in scenarios)
        for scenario in scenarios:
            entries = {path.name for path in scenario.iterdir()}
            assert "case.yaml" in entries
            assert entries <= {"case.yaml", "fixture"}
            validate_case(
                scenario / "case.yaml",
                skill_root.name,
                scenario.name,
                set(hosts),
                entries,
            )
