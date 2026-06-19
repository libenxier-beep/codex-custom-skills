#!/usr/bin/env python3
"""Validate an autoresearch experiment contract JSON file."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


ALLOWED_DIRECTIONS = {"lower", "higher", "pass_fail", "threshold"}
ALLOWED_ISOLATION = {"branch", "worktree", "scratch-copy", "existing-branch"}


def fail(message: str) -> None:
    print(f"contract error: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_contract(path: pathlib.Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON: {exc}")
    if not isinstance(data, dict):
        fail("top-level contract must be a JSON object")
    return data


def require(data: dict[str, Any], path: str, expected: type) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            fail(f"missing required field: {path}")
        current = current[part]
    if not isinstance(current, expected):
        fail(f"{path} must be {expected.__name__}")
    if expected is str and not current.strip():
        fail(f"{path} must not be empty")
    if expected is list and not current:
        fail(f"{path} must not be empty")
    return current


def require_positive_int(data: dict[str, Any], path: str) -> int:
    value = require(data, path, int)
    if value <= 0:
        fail(f"{path} must be > 0")
    return value


def require_nonnegative_number(data: dict[str, Any], path: str) -> float:
    value = require(data, path, (int, float))
    if value < 0:
        fail(f"{path} must be >= 0")
    return float(value)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_contract.py CONTRACT.json")

    contract = load_contract(pathlib.Path(sys.argv[1]))

    require(contract, "goal", str)
    direction = require(contract, "direction", str)
    if direction not in ALLOWED_DIRECTIONS:
        fail(f"direction must be one of {sorted(ALLOWED_DIRECTIONS)}")

    editable = require(contract, "scope.editable_files", list)
    forbidden = require(contract, "scope.forbidden_files", list)
    if not all(isinstance(item, str) and item.strip() for item in editable):
        fail("scope.editable_files must contain non-empty strings")
    if not all(isinstance(item, str) and item.strip() for item in forbidden):
        fail("scope.forbidden_files must contain non-empty strings")
    overlap = set(editable).intersection(forbidden)
    if overlap:
        fail(f"files cannot be both editable and forbidden: {sorted(overlap)}")

    require(contract, "verify.command", str)
    require_positive_int(contract, "verify.timeout_seconds")
    require(contract, "verify.log_file", str)
    require(contract, "verify.metric_regex", str)

    require_positive_int(contract, "budget.max_iterations")
    require_positive_int(contract, "budget.max_wall_time_minutes")
    require(contract, "budget.resource_ceiling", str)
    require(contract, "budget.stop_condition", str)

    isolation = require(contract, "isolation.strategy", str)
    if isolation not in ALLOWED_ISOLATION:
        fail(f"isolation.strategy must be one of {sorted(ALLOWED_ISOLATION)}")
    if isolation in {"branch", "worktree"}:
        require(contract, "isolation.name", str)

    require(contract, "discard_permission", bool)
    require(contract, "evidence.results_file", str)
    require(contract, "evidence.logs_dir", str)

    require_nonnegative_number(contract, "metric_noise.min_delta")
    repeat_on_near_tie = require(contract, "metric_noise.repeat_on_near_tie", bool)
    if repeat_on_near_tie:
        repeat_count = contract.get("metric_noise", {}).get("repeat_count", 2)
        if not isinstance(repeat_count, int) or repeat_count < 2:
            fail("metric_noise.repeat_count must be an integer >= 2 when provided")

    print("contract ok")


if __name__ == "__main__":
    main()
