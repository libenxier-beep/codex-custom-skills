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
