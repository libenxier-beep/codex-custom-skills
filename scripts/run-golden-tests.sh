#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

expect_fail() {
  if "$@" >/tmp/codex-skills-negative.out 2>/tmp/codex-skills-negative.err; then
    echo "expected failure but command passed: $*" >&2
    cat /tmp/codex-skills-negative.out >&2
    cat /tmp/codex-skills-negative.err >&2
    exit 1
  fi
}

python3 "$ROOT/skills/scripts/khub-validate.py" line-endings "$ROOT/skills"
python3 "$ROOT/skills/domain-knowledge-distiller/scripts/run_static_evals.py"

for script in validate_contract.py parse_result.py append_results.py; do
  test -x "$ROOT/skills/autoresearch/scripts/$script"
done

if grep -n 'python3 scripts/' "$ROOT/skills/autoresearch/SKILL.md"; then
  echo "autoresearch SKILL.md must call helper scripts via SKILL_DIR, not target-repo scripts/" >&2
  exit 1
fi
grep -q 'SKILL_DIR=' "$ROOT/skills/autoresearch/SKILL.md"

if grep -n -- '--status keep --description "<hypothesis>"' "$ROOT/skills/autoresearch/SKILL.md"; then
  echo "autoresearch strict flow must decide status before appending results" >&2
  exit 1
fi
grep -q '\$decision_status' "$ROOT/skills/autoresearch/SKILL.md"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT HUP INT TERM

cat >"$tmpdir/autoresearch-contract.json" <<'JSON'
{
  "goal": "lower validation bpb",
  "direction": "lower",
  "scope": {
    "editable_files": ["train.py"],
    "forbidden_files": ["prepare.py", "program.md"]
  },
  "verify": {
    "command": "uv run train.py > logs/candidate.log 2>&1",
    "timeout_seconds": 600,
    "log_file": "logs/candidate.log",
    "metric_regex": "^val_bpb:\\s*([0-9.]+)"
  },
  "budget": {
    "max_iterations": 3,
    "max_wall_time_minutes": 60,
    "resource_ceiling": "peak_vram_mb <= 24000",
    "stop_condition": "no candidate beats current best by min_delta"
  },
  "isolation": {
    "strategy": "branch",
    "name": "autoresearch/test"
  },
  "discard_permission": true,
  "evidence": {
    "results_file": "results.tsv",
    "logs_dir": "logs"
  },
  "metric_noise": {
    "min_delta": 0.001,
    "repeat_on_near_tie": true
  }
}
JSON

python3 "$ROOT/skills/autoresearch/scripts/validate_contract.py" \
  "$tmpdir/autoresearch-contract.json"

python3 - <<'PY' "$tmpdir/autoresearch-contract.json" "$tmpdir/bad-min-delta.json"
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
data["metric_noise"]["min_delta"] = "tiny"
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(data, f)
PY

if python3 "$ROOT/skills/autoresearch/scripts/validate_contract.py" \
  "$tmpdir/bad-min-delta.json" >"$tmpdir/bad.out" 2>"$tmpdir/bad.err"; then
  echo "expected bad min_delta contract to fail" >&2
  exit 1
fi
if grep -q Traceback "$tmpdir/bad.err"; then
  echo "bad min_delta should produce a contract error, not a Python traceback" >&2
  cat "$tmpdir/bad.err" >&2
  exit 1
fi
grep -q 'contract error: metric_noise.min_delta must be int or float' "$tmpdir/bad.err"

cat >"$tmpdir/run.log" <<'LOG'
epoch: 1
val_bpb: 1.2345
peak_vram_mb: 4096
LOG

python3 "$ROOT/skills/autoresearch/scripts/parse_result.py" \
  --mode upstream \
  --log "$tmpdir/run.log" >"$tmpdir/parsed.json"

python3 - <<'PY' "$tmpdir/parsed.json"
import json
import math
import sys

data = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert data["metric_name"] == "val_bpb"
assert math.isclose(data["metric"], 1.2345)
assert math.isclose(data["memory_gb"], 4.0)
PY

python3 "$ROOT/skills/autoresearch/scripts/append_results.py" \
  --schema upstream \
  --results "$tmpdir/results.tsv" \
  --commit abc1234 \
  --metric 1.2345 \
  --memory-gb 4.0 \
  --status keep \
  --description baseline

python3 - <<'PY' "$tmpdir/results.tsv"
import csv
import sys

with open(sys.argv[1], newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))
assert rows[0] == {
    "commit": "abc1234",
    "val_bpb": "1.2345",
    "memory_gb": "4.0",
    "status": "keep",
    "description": "baseline",
}
PY

bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/output-route-plan.create.yaml"
bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/output-route-plan.append.yaml"
bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/output-decision-report.no-fit.md"
bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/output-decision-report.needs-human.md"
bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/output-decision-report.skip-duplicate.yaml"

bash "$ROOT/skills/khub-deposition-update/scripts/validate-note-payload.sh" \
  "$ROOT/skills/khub-deposition-update/examples/note-payload.seed.yaml"
bash "$ROOT/skills/khub-deposition-update/scripts/validate-execution-report.sh" \
  "$ROOT/skills/khub-deposition-update/examples/create-seed.md"
bash "$ROOT/skills/khub-deposition-update/scripts/validate-execution-report.sh" \
  "$ROOT/skills/khub-deposition-update/examples/blocked-report.md"
bash "$ROOT/skills/khub-deposition-update/scripts/validate-execution-report.sh" \
  "$ROOT/skills/khub-deposition-update/examples/conflict-report.md"

expect_fail bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/invalid/route-plan.bad-confidence.yaml"
expect_fail bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/invalid/route-plan.skip-duplicate.yaml"
expect_fail bash "$ROOT/skills/khub-classifier-router/scripts/validate-route-plan.sh" \
  "$ROOT/skills/khub-classifier-router/examples/invalid/decision-report.write-unblocked.yaml"
expect_fail bash "$ROOT/skills/khub-deposition-update/scripts/validate-note-payload.sh" \
  "$ROOT/skills/khub-deposition-update/examples/invalid/note-payload.missing-source-id.yaml"
expect_fail bash "$ROOT/skills/khub-deposition-update/scripts/validate-execution-report.sh" \
  "$ROOT/skills/khub-deposition-update/examples/invalid/execution-report.blocked-write-attempted.yaml"
expect_fail bash "$ROOT/skills/khub-deposition-update/scripts/validate-execution-report.sh" \
  "$ROOT/skills/khub-deposition-update/examples/invalid/execution-report.missing-source-trace.yaml"

python3 - <<'PY' "$ROOT"
import csv
import pathlib
import re
import sys
import yaml

root = pathlib.Path(sys.argv[1])
errors = []
for csv_path in root.glob("skills/*/evals/trigger-prompts.csv"):
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or list(rows[0].keys()) != ["id", "should_trigger", "prompt", "expected_evidence"]:
        errors.append(f"{csv_path}: bad trigger eval header")
    for row in rows:
        if row.get("should_trigger") not in {"true", "false"}:
            errors.append(f"{csv_path}: invalid should_trigger in {row.get('id')}")

for csv_path in root.glob("skills/*/evals/golden-prompts.csv"):
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    expected_header = ["id", "mode", "prompt_ref", "expected_read", "expected_output", "rubric_focus"]
    if not rows or list(rows[0].keys()) != expected_header:
        errors.append(f"{csv_path}: bad golden prompt header")
    for row in rows:
        if not row.get("prompt_ref") or not row.get("expected_output"):
            errors.append(f"{csv_path}: incomplete golden prompt row {row.get('id')}")
        prompt_ref = row.get("prompt_ref", "").strip()
        if prompt_ref and not (csv_path.parents[1] / prompt_ref).exists():
            errors.append(f"{csv_path}: missing prompt_ref target {prompt_ref} in {row.get('id')}")
        for rel in row.get("expected_read", "").split(";"):
            rel = rel.strip()
            if rel and not (csv_path.parents[1] / rel).exists():
                errors.append(f"{csv_path}: missing expected_read target {rel} in {row.get('id')}")

for md in [root / "README.md"] + list(root.glob("skills/*/SKILL.md")) + list(root.glob("skills/*/README.md")) + list(root.glob("skills/*/examples/*.md")):
    text = md.read_text(encoding="utf-8")
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in link or link.startswith("#"):
            continue
        if not (md.parent / link).resolve().exists():
            errors.append(f"{md}: broken link {link}")

for image_path in root.glob("skills/bluegrid-xhs-illustrations/examples/images/[0-9][0-9]-*.png"):
    data = image_path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        errors.append(f"{image_path}: not a PNG file")
        continue
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if (width, height) != (1080, 1350):
        errors.append(f"{image_path}: expected 1080x1350, got {width}x{height}")

for image_path in root.glob("skills/bluegrid-xhs-illustrations/assets/style-anchors/*.png"):
    data = image_path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        errors.append(f"{image_path}: not a PNG file")
        continue
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width < 900 or height < 1200:
        errors.append(f"{image_path}: style anchor too small: {width}x{height}")

line_limited = [
    root / "scripts/run-golden-tests.sh",
    *root.glob("skills/bluegrid-xhs-illustrations/evals/*.csv"),
    *root.glob("skills/bluegrid-xhs-illustrations/agents/*.yaml"),
]
for path in line_limited:
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if len(line) > 200:
            errors.append(f"{path}: line {lineno} exceeds 200 chars")

for schema_path in root.glob("skills/*/templates/*.schema.yaml"):
    with schema_path.open(encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    if not isinstance(schema, dict) or schema.get("type") != "object":
        errors.append(f"{schema_path}: schema must be an object schema")
    if "required" not in schema or "properties" not in schema:
        errors.append(f"{schema_path}: schema must define required and properties")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print("trigger evals and markdown links ok")
PY

echo "negative validator checks ok"
echo "golden tests ok"
