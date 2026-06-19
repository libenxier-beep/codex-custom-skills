#!/usr/bin/env python3
"""Append one autoresearch candidate result to a TSV file."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import pathlib
import sys


UPSTREAM_HEADER = ["commit", "val_bpb", "memory_gb", "status", "description"]
GENERIC_HEADER = [
    "timestamp",
    "base_commit",
    "candidate_commit",
    "metric_name",
    "metric",
    "memory_gb",
    "status",
    "description",
]
STATUSES = {"baseline", "keep", "discard", "crash", "blocked"}


def clean(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def ensure_header(path: pathlib.Path, header: list[str]) -> None:
    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f, delimiter="\t").writerow(header)
        return

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        existing = next(reader, None)
    if existing != header:
        print(
            f"results schema mismatch in {path}: expected {header}, found {existing}",
            file=sys.stderr,
        )
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", choices=["upstream", "generic"], required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--commit", help="Commit used by upstream schema.")
    parser.add_argument("--base-commit", help="Base commit used by generic schema.")
    parser.add_argument("--candidate-commit", help="Candidate commit used by generic schema.")
    parser.add_argument("--metric", required=True)
    parser.add_argument("--metric-name", default="metric")
    parser.add_argument("--memory-gb", default="")
    parser.add_argument("--status", required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()

    if args.status not in STATUSES:
        parser.error(f"--status must be one of {sorted(STATUSES)}")

    path = pathlib.Path(args.results)
    if args.schema == "upstream":
        if not args.commit:
            parser.error("--commit is required for --schema upstream")
        header = UPSTREAM_HEADER
        row = [
            clean(args.commit),
            clean(args.metric),
            clean(args.memory_gb),
            clean(args.status),
            clean(args.description),
        ]
    else:
        if not args.base_commit or not args.candidate_commit:
            parser.error("--base-commit and --candidate-commit are required for generic schema")
        header = GENERIC_HEADER
        row = [
            dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
            clean(args.base_commit),
            clean(args.candidate_commit),
            clean(args.metric_name),
            clean(args.metric),
            clean(args.memory_gb),
            clean(args.status),
            clean(args.description),
        ]

    ensure_header(path, header)
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter="\t").writerow(row)


if __name__ == "__main__":
    main()
