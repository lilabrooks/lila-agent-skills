#!/usr/bin/env python3
"""Check deterministic contracts and calibrated outputs for repository skills."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

EXPECTED_VARIANTS = {
    "baseline": False,
    "treatment": True,
    "self_review": True,
    "mutation": False,
}
ALLOWED_GATES = {"authorization", "scope", "verification"}


class ConfigError(ValueError):
    """Report an invalid behavioral fixture."""


@dataclass(frozen=True)
class Evaluation:
    """Store independent-check results for one candidate output."""

    passed: int
    total: int
    failures: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.failures


def as_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ConfigError(f"{label} must be a mapping with string keys")
    return cast(dict[str, object], value)


def as_sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ConfigError(f"{label} must be a sequence")
    return cast(list[object], value)


def as_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{label} must be a non-empty string")
    return value


def as_strings(value: object, label: str) -> list[str]:
    values = as_sequence(value, label)
    if not all(isinstance(item, str) and item for item in values):
        raise ConfigError(f"{label} must contain non-empty strings")
    return cast(list[str], values)


def regex(pattern: str, label: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise ConfigError(
            f"{label} contains an invalid regular expression: {exc}"
        ) from exc


def contract_failures(text: str, contract: dict[str, object]) -> list[str]:
    failures = [
        f"missing required literal {literal!r}"
        for literal in as_strings(
            contract.get("required_literals"), "required_literals"
        )
        if literal not in text
    ]
    for index, raw_rule in enumerate(
        as_sequence(contract.get("forbidden"), "forbidden")
    ):
        rule = as_mapping(raw_rule, f"forbidden[{index}]")
        pattern = as_text(rule.get("pattern"), f"forbidden[{index}].pattern")
        if regex(pattern, f"forbidden[{index}].pattern").search(text):
            failures.append(f"matched forbidden pattern {pattern!r}")
    return failures


def content_check_detail(
    output: str, check: dict[str, object], check_id: str, kind: str
) -> list[str] | None:
    if kind == "contains_all":
        missing = [
            value
            for value in as_strings(check.get("values"), f"check {check_id}.values")
            if value not in output
        ]
        return [f"missing {missing!r}"] if missing else []
    if kind == "excludes_all":
        present = [
            value
            for value in as_strings(check.get("values"), f"check {check_id}.values")
            if value in output
        ]
        return [f"found {present!r}"] if present else []
    return None


def check_output(output: str, checks: list[object]) -> Evaluation:
    failures: list[str] = []
    failed_checks: set[str] = set()
    for index, raw_check in enumerate(checks):
        check = as_mapping(raw_check, f"checks[{index}]")
        check_id = as_text(check.get("id"), f"checks[{index}].id")
        gate = as_text(check.get("gate"), f"checks[{index}].gate")
        if gate not in ALLOWED_GATES:
            raise ConfigError(f"check {check_id!r} has unknown gate {gate!r}")
        kind = as_text(check.get("kind"), f"checks[{index}].kind")
        detail = content_check_detail(output, check, check_id, kind)
        if detail is None:
            raise ConfigError(f"check {check_id!r} has unknown kind {kind!r}")

        if detail:
            failed_checks.add(check_id)
            failures.extend(f"{gate}/{check_id}: {item}" for item in detail)
    return Evaluation(len(checks) - len(failed_checks), len(checks), tuple(failures))


def validate_contracts(root: Path, contracts: list[object]) -> tuple[list[str], int]:
    failures: list[str] = []
    mutation_count = 0
    root = root.resolve()
    for index, raw_contract in enumerate(contracts):
        contract = as_mapping(raw_contract, f"contracts[{index}]")
        contract_id = as_text(contract.get("id"), f"contracts[{index}].id")
        relative_path = Path(as_text(contract.get("path"), f"contracts[{index}].path"))
        path = (root / relative_path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ConfigError(
                f"contract {contract_id!r} path escapes the repository"
            ) from exc
        text = path.read_text(encoding="utf-8")
        failures.extend(
            f"{contract_id}: {failure}" for failure in contract_failures(text, contract)
        )

        required = as_strings(
            contract.get("required_literals"),
            f"contract {contract_id}.required_literals",
        )
        for literal in required:
            mutation_count += 1
            # This sentinel runs only if the contract evaluator itself regresses.
            if not contract_failures(
                text.replace(literal, ""), contract
            ):  # pragma: no cover
                failures.append(
                    f"{contract_id}: removing {literal!r} escaped mutation detection"
                )
        for rule_index, raw_rule in enumerate(
            as_sequence(contract.get("forbidden"), f"contract {contract_id}.forbidden")
        ):
            rule = as_mapping(
                raw_rule, f"contract {contract_id}.forbidden[{rule_index}]"
            )
            mutation = as_text(
                rule.get("mutation"),
                f"contract {contract_id}.forbidden[{rule_index}].mutation",
            )
            mutation_count += 1
            # This sentinel runs only if the contract evaluator itself regresses.
            if not contract_failures(
                f"{text}\n{mutation}\n", contract
            ):  # pragma: no cover
                failures.append(
                    f"{contract_id}: forbidden mutation {mutation!r} escaped detection"
                )
    return failures, mutation_count


def validate_scenarios(scenarios: list[object]) -> tuple[list[str], list[str], int]:
    failures: list[str] = []
    summaries: list[str] = []
    output_count = 0
    for index, raw_scenario in enumerate(scenarios):
        scenario = as_mapping(raw_scenario, f"scenarios[{index}]")
        scenario_id = as_text(scenario.get("id"), f"scenarios[{index}].id")
        as_text(scenario.get("prompt"), f"scenario {scenario_id}.prompt")
        checks = as_sequence(scenario.get("checks"), f"scenario {scenario_id}.checks")
        variants = as_mapping(
            scenario.get("variants"), f"scenario {scenario_id}.variants"
        )
        if set(variants) != set(EXPECTED_VARIANTS):
            raise ConfigError(
                f"scenario {scenario_id!r} must define {sorted(EXPECTED_VARIANTS)!r}"
            )

        results: dict[str, Evaluation] = {}
        for variant, expected in EXPECTED_VARIANTS.items():
            output = as_text(variants.get(variant), f"scenario {scenario_id}.{variant}")
            result = check_output(output, checks)
            results[variant] = result
            output_count += 1
            if result.ok != expected:
                failures.append(
                    f"{scenario_id}/{variant}: expected {'pass' if expected else 'fail'}; "
                    f"checks passed {result.passed}/{result.total}; "
                    f"failures={list(result.failures)!r}"
                )
        if results["treatment"].passed <= results["baseline"].passed:
            failures.append(f"{scenario_id}: treatment did not beat baseline")
        summaries.append(
            f"{scenario_id}: baseline {results['baseline'].passed}/{results['baseline'].total}, "
            f"treatment {results['treatment'].passed}/{results['treatment'].total}, "
            f"self-review {results['self_review'].passed}/{results['self_review'].total}, "
            f"mutation {results['mutation'].passed}/{results['mutation'].total}"
        )
    return failures, summaries, output_count


def load_fixture(path: Path) -> dict[str, object]:
    loaded: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    fixture = as_mapping(loaded, "fixture")
    if fixture.get("version") != 1:
        raise ConfigError("fixture.version must be 1")
    return fixture


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("tests/fixtures/skill_behavior.yaml"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    fixture_path = args.fixture
    if not fixture_path.is_absolute():
        fixture_path = root / fixture_path
    try:
        fixture = load_fixture(fixture_path)
        contracts = as_sequence(fixture.get("contracts"), "contracts")
        scenarios = as_sequence(fixture.get("scenarios"), "scenarios")
        contract_errors, mutation_count = validate_contracts(root, contracts)
        scenario_errors, summaries, output_count = validate_scenarios(scenarios)
    except (ConfigError, OSError, UnicodeError, yaml.YAMLError) as exc:
        print(f"Behavioral contract configuration failed: {exc}", file=sys.stderr)
        return 2

    failures = contract_errors + scenario_errors
    if failures:
        print(
            f"Behavioral contract check failed with {len(failures)} error(s):",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        f"Behavioral contract check passed: {len(contracts)} skills, "
        f"{len(scenarios)} scenarios, {output_count} calibrated outputs, "
        f"{mutation_count} contract mutations."
    )
    for summary in summaries:
        print(f"- {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
