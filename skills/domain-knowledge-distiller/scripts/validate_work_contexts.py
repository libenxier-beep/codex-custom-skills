#!/usr/bin/env python3
"""Validate a work_contexts root for routing, portability, and eval hygiene."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_CONTEXT_FIELDS = {
    "id",
    "path",
    "summary",
    "triggers",
    "non_triggers",
    "read_path",
    "eval_file",
    "risk_file",
    "status",
    "last_reviewed",
    "sync_targets",
    "depends_on",
}

ROUTER_CASE_FIELDS = [
    "id",
    "user_request",
    "should_load_context",
    "expected_first_file",
    "expected_deeper_files",
    "negative_reason",
]

ABSOLUTE_PATH_RE = re.compile(r"(/Users/[^\"'\s,)\]]+|/home/[^\"'\s,)\]]+|[A-Za-z]:\\\\[^\"'\s,)\]]+)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, f"{path}: invalid JSON: {exc.msg}")
    except OSError as exc:
        fail(errors, f"{path}: cannot read: {exc}")
    return None


def is_relative_path(value: str) -> bool:
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", value):
        return False
    parts = Path(value).parts
    return ".." not in parts


def path_exists(root: Path, rel: str) -> bool:
    rel = rel.rstrip("/")
    return bool(rel) and (root / rel).exists()


def validate_portable_path(root: Path, rel: str, where: str, errors: list[str], *, allow_directory: bool = True) -> None:
    if not isinstance(rel, str) or not rel.strip():
        fail(errors, f"{where}: missing path")
        return
    if not is_relative_path(rel):
        fail(errors, f"{where}: path must be repo-relative, got {rel!r}")
        return
    target = root / rel.rstrip("/")
    if not target.exists():
        fail(errors, f"{where}: path does not exist: {rel}")
        return
    if rel.endswith("/") and not target.is_dir() and allow_directory:
        fail(errors, f"{where}: expected directory path: {rel}")


def validate_router_cases(root: Path, rel: str, context_id: str, errors: list[str]) -> None:
    path = root / rel
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        fail(errors, f"{rel}: cannot read router cases: {exc}")
        return

    if not rows:
        fail(errors, f"{rel}: no router cases")
        return
    if list(rows[0].keys()) != ROUTER_CASE_FIELDS:
        fail(errors, f"{rel}: header must be {ROUTER_CASE_FIELDS}")
        return

    seen: set[str] = set()
    positives = 0
    negatives = 0
    for idx, row in enumerate(rows, start=2):
        case_id = row["id"].strip()
        if not case_id:
            fail(errors, f"{rel}:{idx}: missing id")
        elif case_id in seen:
            fail(errors, f"{rel}:{idx}: duplicate id {case_id!r}")
        seen.add(case_id)

        should_load = row["should_load_context"].strip().lower()
        if should_load not in {"yes", "no"}:
            fail(errors, f"{rel}:{idx}: should_load_context must be yes or no")
            continue

        if should_load == "yes":
            positives += 1
            first_file = row["expected_first_file"].strip()
            validate_portable_path(root, first_file, f"{rel}:{idx}.expected_first_file", errors, allow_directory=False)
            for deeper in [item.strip() for item in row["expected_deeper_files"].split(";") if item.strip()]:
                validate_portable_path(root, deeper, f"{rel}:{idx}.expected_deeper_files", errors)
        else:
            negatives += 1
            if not row["negative_reason"].strip():
                fail(errors, f"{rel}:{idx}: negative cases need negative_reason")
            if row["expected_first_file"].strip() or row["expected_deeper_files"].strip():
                fail(errors, f"{rel}:{idx}: negative cases should not include expected files")

    if positives < 1:
        fail(errors, f"{rel}: needs at least one positive router case for {context_id}")
    if negatives < 1:
        fail(errors, f"{rel}: needs at least one negative router case for {context_id}")


def extract_frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    return text[4:end]


def validate_risk_file(path: Path, rel: str, errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(errors, f"{rel}: cannot read risk file: {exc}")
        return
    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        fail(errors, f"{rel}: missing YAML frontmatter")
        return
    if "type: risk-register" not in frontmatter:
        fail(errors, f"{rel}: frontmatter should include type: risk-register")
    if "retrieval_keys:" not in frontmatter:
        fail(errors, f"{rel}: frontmatter should include retrieval_keys")


def validate_registry(root: Path, errors: list[str]) -> None:
    registry_path = root / "contexts.registry.json"
    if not registry_path.exists():
        fail(errors, "contexts.registry.json: missing top-level machine-readable registry")
        return

    registry = load_json(registry_path, errors)
    if not isinstance(registry, dict):
        fail(errors, "contexts.registry.json: expected object")
        return

    contexts = registry.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        fail(errors, "contexts.registry.json: contexts must be a non-empty array")
        return

    ids: set[str] = set()
    root_readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    for idx, context in enumerate(contexts):
        where = f"contexts.registry.json:contexts[{idx}]"
        if not isinstance(context, dict):
            fail(errors, f"{where}: expected object")
            continue
        missing = sorted(REQUIRED_CONTEXT_FIELDS - set(context))
        if missing:
            fail(errors, f"{where}: missing fields {missing}")
            continue

        context_id = context["id"]
        if not isinstance(context_id, str) or not context_id:
            fail(errors, f"{where}.id: missing id")
        elif context_id in ids:
            fail(errors, f"{where}.id: duplicate id {context_id!r}")
        ids.add(context_id)

        if context.get("status") not in {"active", "draft", "archived"}:
            fail(errors, f"{where}.status: expected active, draft, or archived")
        if not isinstance(context.get("last_reviewed"), str) or not DATE_RE.fullmatch(context["last_reviewed"]):
            fail(errors, f"{where}.last_reviewed: expected YYYY-MM-DD")

        for list_field in ["triggers", "non_triggers", "read_path", "depends_on"]:
            value = context.get(list_field)
            if not isinstance(value, list):
                fail(errors, f"{where}.{list_field}: expected array")
            elif list_field != "depends_on" and not value:
                fail(errors, f"{where}.{list_field}: expected at least one item")

        validate_portable_path(root, context["path"], f"{where}.path", errors, allow_directory=False)
        validate_portable_path(root, context["eval_file"], f"{where}.eval_file", errors, allow_directory=False)
        validate_portable_path(root, context["risk_file"], f"{where}.risk_file", errors, allow_directory=False)

        if path_exists(root, context["eval_file"]):
            validate_router_cases(root, context["eval_file"], str(context_id), errors)
        if path_exists(root, context["risk_file"]):
            validate_risk_file(root / context["risk_file"], context["risk_file"], errors)

        for read_idx, rel in enumerate(context.get("read_path", [])):
            validate_portable_path(root, rel, f"{where}.read_path[{read_idx}]", errors)
        for deep_idx, rel in enumerate(context.get("deeper_files", []) or []):
            validate_portable_path(root, rel, f"{where}.deeper_files[{deep_idx}]", errors)

        context_dir = str(context["path"]).split("/", 1)[0]
        if root_readme and context_dir not in root_readme:
            fail(errors, f"{where}: context directory {context_dir!r} is not mentioned in README.md")


def validate_json_files(root: Path, errors: list[str]) -> None:
    for path in sorted(root.rglob("*.json")):
        load_json(path, errors)


def validate_retrieval_indexes(root: Path, errors: list[str]) -> None:
    for index_path in sorted(root.glob("*/indexes/*.json")):
        data = load_json(index_path, errors)
        if data is None:
            continue
        rel_index = index_path.relative_to(root).as_posix()
        text = index_path.read_text(encoding="utf-8")
        if ABSOLUTE_PATH_RE.search(text):
            fail(errors, f"{rel_index}: retrieval index contains absolute local path")

        def walk(value: Any, where: str) -> None:
            if isinstance(value, dict):
                file_value = value.get("file")
                if isinstance(file_value, str):
                    validate_portable_path(root, file_value, f"{rel_index}:{where}.file", errors, allow_directory=False)
                for key, child in value.items():
                    walk(child, f"{where}.{key}")
            elif isinstance(value, list):
                for item_idx, item in enumerate(value):
                    walk(item, f"{where}[{item_idx}]")

        walk(data, "$")


def validate_canonical_pattern_indexes(root: Path, errors: list[str]) -> None:
    for index_path in sorted(root.glob("*/indexes/index.json")):
        data = load_json(index_path, errors)
        if not isinstance(data, dict):
            continue
        patterns = data.get("patterns")
        if not isinstance(patterns, list):
            continue

        names = [item.get("name") for item in patterns if isinstance(item, dict) and isinstance(item.get("name"), str)]
        duplicate_names = {name for name in names if names.count(name) > 1}
        if not duplicate_names:
            continue

        canonical_path = index_path.parent / "canonical_patterns.json"
        rel = canonical_path.relative_to(root).as_posix()
        if not canonical_path.exists():
            fail(errors, f"{rel}: missing; duplicate pattern names require a canonical grouping index")
            continue

        canonical = load_json(canonical_path, errors)
        if not isinstance(canonical, dict):
            continue
        if canonical.get("pattern_count") != len(patterns):
            fail(errors, f"{rel}: pattern_count does not match source index")
        if canonical.get("canonical_count") != len(set(names)):
            fail(errors, f"{rel}: canonical_count does not match unique pattern names")
        if canonical.get("duplicate_group_count", 0) < 1:
            fail(errors, f"{rel}: duplicate_group_count should reflect duplicate source patterns")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a work_contexts root.")
    parser.add_argument("path", help="Path to work_contexts root")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    errors: list[str] = []
    if not root.exists():
        fail(errors, f"path does not exist: {root}")
    elif not root.is_dir():
        fail(errors, f"path is not a directory: {root}")
    else:
        validate_registry(root, errors)
        validate_json_files(root, errors)
        validate_retrieval_indexes(root, errors)
        validate_canonical_pattern_indexes(root, errors)

    if errors:
        print("work contexts validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"work contexts validation passed: {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
