#!/usr/bin/env python3
"""Parse an autoresearch run log and emit a compact JSON metric result."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


UPSTREAM_METRIC_RE = r"^val_bpb:\s*([0-9]+(?:\.[0-9]+)?)"
UPSTREAM_MEMORY_RE = r"^peak_vram_mb:\s*([0-9]+(?:\.[0-9]+)?)"


def parse_float(pattern: str, text: str, label: str) -> float:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        print(f"parse error: could not find {label} with regex {pattern!r}", file=sys.stderr)
        raise SystemExit(1)
    try:
        return float(match.group(1))
    except (IndexError, ValueError) as exc:
        print(f"parse error: {label} capture group must be numeric: {exc}", file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["upstream", "generic"], default="generic")
    parser.add_argument("--log", required=True, help="Path to the command log to parse.")
    parser.add_argument("--metric-regex", help="Regex with one numeric capture group.")
    parser.add_argument("--metric-name", help="Metric name for JSON output.")
    parser.add_argument("--memory-regex", help="Regex with one numeric memory capture group.")
    parser.add_argument(
        "--memory-unit",
        choices=["mb", "gb"],
        help="Unit for --memory-regex capture. Upstream default is mb.",
    )
    args = parser.parse_args()

    log_path = pathlib.Path(args.log)
    text = log_path.read_text(encoding="utf-8", errors="replace")

    if args.mode == "upstream":
        metric_regex = args.metric_regex or UPSTREAM_METRIC_RE
        metric_name = args.metric_name or "val_bpb"
        memory_regex = args.memory_regex or UPSTREAM_MEMORY_RE
        memory_unit = args.memory_unit or "mb"
    else:
        if not args.metric_regex:
            parser.error("--metric-regex is required in generic mode")
        metric_regex = args.metric_regex
        metric_name = args.metric_name or "metric"
        memory_regex = args.memory_regex
        memory_unit = args.memory_unit or "gb"

    metric = parse_float(metric_regex, text, metric_name)
    memory_gb = None
    if memory_regex:
        raw_memory = parse_float(memory_regex, text, "memory")
        memory_gb = raw_memory / 1024 if memory_unit == "mb" else raw_memory

    print(
        json.dumps(
            {
                "metric_name": metric_name,
                "metric": metric,
                "memory_gb": memory_gb,
                "log": str(log_path),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
