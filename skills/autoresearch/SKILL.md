---
name: autoresearch
description: Use when the user wants Codex to run, adapt, or audit a bounded metric-driven experiment loop in karpathy/autoresearch or a similarly small repo with a clear editable scope, validation command, metric, and keep/discard criterion.
---

# Autoresearch

Autoresearch is a controlled experiment loop for code or model improvements: define a metric, run a baseline, try one hypothesis at a time, verify, keep only proven improvements, and leave an audit trail.

This skill is inspired by Karpathy's `karpathy/autoresearch`, where `program.md` guides agents to edit `train.py`, commit candidates, run fixed-budget training, compare `val_bpb`, and reset worse candidates. Treat upstream as the canonical special case, not the only possible use.

Source note: upstream repository `https://github.com/karpathy/autoresearch`, especially `README.md` and `program.md`.

## Use When

- The user names `autoresearch`, `Karpathy autoresearch`, overnight experiments, autonomous metric-driven iteration, candidate commits, or keep/reset experiment loops.
- The task has a measurable objective such as lower loss, fewer failures, higher benchmark score, faster runtime, or a deterministic acceptance command.
- There is a bounded editable surface, ideally one file or a small explicit file set.
- Failed ideas can be safely discarded or isolated.
- The user asks for experiment execution, experiment setup, or review of an autoresearch-style loop.
- The workspace is dirty but the user still asks for autoresearch; load this skill to negotiate isolation, but do not start the experiment loop.

## Do Not Use When

- The user only wants a summary, literature review, product strategy, knowledge distillation, one-off code fix, review, refactor, or explanation.
- There is no objective metric or verification command, and the user will not define one.
- The target is a production system, shared branch, user data store, deployment, finance/legal/medical workflow, or any environment where failed edits have unsafe side effects.
- The only validation is subjective taste and the user has not defined a rubric, scorer, iteration budget, and stop condition.

## Do Not Start The Loop When

- The workspace has unrelated uncommitted changes and isolation is not agreed.
- Required contract fields are missing.
- The verification command, metric parser, dataset, or fixture is unreliable.
- The next candidate would touch files outside the approved scope.

In these cases, stop at contract negotiation or setup repair. Do not silently continue.

## Required Experiment Contract

Before changing files, establish and echo this contract. Prefer storing it as JSON and running `scripts/validate_contract.py CONTRACT.json`.

| Field | Required decision |
| --- | --- |
| Goal | What metric or score should improve? |
| Direction | `lower`, `higher`, `pass_fail`, or `threshold`. |
| Scope | Editable files and forbidden files. |
| Verify | Exact command, timeout, log file, and metric extraction regex. |
| Budget | Max iterations, max wall time, resource ceiling, and stop condition. |
| Isolation | Branch, worktree, scratch copy, or existing branch strategy. |
| Discard permission | Whether Codex may automatically discard its own failed candidate commits or edits. |
| Result schema | `upstream` TSV or `generic` TSV. |
| Metric noise | `min_delta`, repeat-on-near-tie rule, repeat count, and tie-break rule. |
| Evidence | Results file, logs directory, and final summary location. |

If any required field is missing, ask concise questions or propose conservative defaults. Do not begin the loop until the contract is explicit and validated.

## Helper Scripts

Use the packaged scripts for repeated mechanics instead of hand-rolling shell snippets:

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.codex/skills/autoresearch}"
python3 "$SKILL_DIR/scripts/validate_contract.py" CONTRACT.json
python3 "$SKILL_DIR/scripts/parse_result.py" --mode upstream --log logs/candidate.log
python3 "$SKILL_DIR/scripts/append_results.py" --schema upstream --results results.tsv \
  --commit "$commit" --metric "$val_bpb" --memory-gb "$memory_gb" \
  --status "$decision_status" --description "short note"
```

- `validate_contract.py` checks required fields, isolation strategy, scoped file overlap, metric noise fields, and evidence paths.
- `parse_result.py` parses upstream `val_bpb` and `peak_vram_mb` by default, or a generic metric regex when adapted.
- `append_results.py` owns TSV headers and row appends so long runs do not drift between schemas.
- `SKILL_DIR` must point to the installed skill directory, not the target repo. On this machine the default expands to the local Codex skill path; override it when testing a checkout copy.

## Result Schemas

Use the upstream schema when the repo is `karpathy/autoresearch` or follows its `program.md` loop:

```text
commit	val_bpb	memory_gb	status	description
```

Use the generic schema only for adapted repos:

```text
timestamp	base_commit	candidate_commit	metric_name	metric	memory_gb	status	description
```

Statuses are `baseline`, `keep`, `discard`, `crash`, or `blocked`.

## Metric Noise Rules

- `min_delta` is required. A lower-is-better candidate wins only when `best - candidate >= min_delta`; higher-is-better wins only when `candidate - best >= min_delta`.
- Differences inside `min_delta` are ties. Keep the incumbent by default.
- A tied candidate may replace the incumbent only when it is materially simpler, does not worsen memory/runtime, and the contract allows simplicity as a tie-break.
- If a result is within the near-tie band or the run is flaky, repeat the current best and candidate using the contract's repeat count, then compare medians.
- If repeated runs disagree on winner, mark `blocked` or `discard`; do not keep because the idea feels clever.
- Never change the dataset, metric path, or verification harness to reduce noise unless the user explicitly changes the contract.

## Safety Rules

- Inspect `git status --short` before edits. If unrelated changes exist, use this skill only to negotiate branch/worktree/scratch isolation.
- Prefer a fresh branch or isolated worktree for long experiment loops.
- Edit only contract-approved files. In upstream mode this normally means `train.py`; `prepare.py`, `program.md`, tokenizer/data utilities, and the `evaluate_bpb` metric path are read-only.
- Do not install dependencies, alter datasets, change metric code, or edit the verification harness without explicit user approval.
- Redirect long command output to logs. Do not stream training or benchmark logs into chat.
- Destructive rollback is allowed only when the contract grants discard permission and status checks prove the candidate commit contains only current experiment changes in approved files.
- Stop when budget is reached, validation becomes unreliable, repeated crashes show setup is broken, or the next experiment would violate the contract.

## Procedure

1. Classify the run.
   - Upstream mode: repo is `karpathy/autoresearch` or has `prepare.py`, `train.py`, `program.md`, and `pyproject.toml`.
   - Adapted mode: another repo with explicit metric, command, schema, and scoped editable files.

2. Read the minimum context.
   - Upstream mode: read `README.md`, `program.md`, `prepare.py`, `train.py`, and `pyproject.toml`.
   - Adapted mode: read the files named in the contract plus verification command docs if present.

3. Verify the environment.
   - Confirm required tools exist, such as `uv` for upstream mode.
   - Confirm data or fixtures exist. For upstream mode, check `~/.cache/autoresearch/`; if missing, tell the user to run or approve `uv run prepare.py`.
   - Run setup only when approved by contract or user.

4. Validate the contract and initialize tracking.
   - Set `SKILL_DIR="${SKILL_DIR:-$HOME/.codex/skills/autoresearch}"`.
   - Write or receive a contract JSON and run `$SKILL_DIR/scripts/validate_contract.py`.
   - Create the logs directory and results TSV location from the contract.
   - Keep logs/results outside committed source unless the user wants them versioned.

5. Establish the baseline.
   - Run the verification command without code changes.
   - Parse the log with `$SKILL_DIR/scripts/parse_result.py`.
   - Append a `baseline` row with `$SKILL_DIR/scripts/append_results.py`.
   - Record the baseline commit with `git rev-parse --short HEAD`.

6. Run one candidate at a time.
   - Choose one hypothesis.
   - Make the smallest scoped edit.
   - Inspect `git diff -- <approved files>`.
   - In upstream mode, commit the candidate before running it.
   - Run the verification command with timeout and log redirection.
   - Parse the metric and memory with `$SKILL_DIR/scripts/parse_result.py`.
   - Apply the metric noise rules.
   - Decide `keep`, `discard`, `crash`, or `blocked`.
   - Append the final status row with `$SKILL_DIR/scripts/append_results.py` before starting the next candidate.

7. End with a handoff.
   - Report contract, baseline, best result, iteration count, kept commits, discarded commits, crash count, changed files, logs/results paths, and remaining risks.
   - Leave the workspace in a clearly named state: best kept branch, clean scoped files, or explicit blocker.

## Upstream Strict Git Flow

Use this stricter loop for `karpathy/autoresearch` unless the user overrides it:

1. Start from a clean branch or worktree and record `base_commit`.
2. Edit only `train.py`.
3. Review the diff, then commit the candidate:

```bash
git add train.py
git commit -m "candidate: <short hypothesis>"
candidate_commit="$(git rev-parse --short HEAD)"
```

4. Run `uv run train.py > logs/$candidate_commit.log 2>&1` with the contract timeout.
5. Parse the run result. Do not append a TSV row yet:

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.codex/skills/autoresearch}"
python3 "$SKILL_DIR/scripts/parse_result.py" \
  --mode upstream \
  --log "logs/$candidate_commit.log" \
  > "logs/$candidate_commit.result.json"
```

6. Apply the metric noise rules against the current incumbent and set `decision_status` to `keep`, `discard`, `crash`, or `blocked`.
7. Append the decided status to upstream TSV:

```bash
python3 "$SKILL_DIR/scripts/append_results.py" --schema upstream --results results.tsv \
  --commit "$candidate_commit" --metric "$val_bpb" --memory-gb "$memory_gb" \
  --status "$decision_status" --description "<hypothesis>"
```

8. If `decision_status=keep`, keep the commit as the new incumbent.
9. If it is `discard` and discard permission is explicit, verify `git status --short -- train.py` is clean after the candidate commit, then remove the failed candidate with `git reset --hard HEAD~1`.
10. If discard permission is absent or state is not clean, do not reset; leave the candidate commit on the experiment branch and report the required manual discard.

Never reset across user work, uncommitted edits, harness changes, or logs/results that the user wanted versioned.

## Upstream Karpathy Defaults

Use these only when the repo matches upstream `karpathy/autoresearch` and the user did not override them:

- Editable file: `train.py`.
- Read-only files: `prepare.py`, `program.md`, tokenizer/data utilities, and `evaluate_bpb` metric path.
- Setup command: `uv sync`, then `uv run prepare.py` if data is absent and the user approves.
- Verify command: `uv run train.py > logs/$candidate_commit.log 2>&1`.
- Metric extraction: `$SKILL_DIR/scripts/parse_result.py --mode upstream --log logs/$candidate_commit.log`.
- Result schema: upstream TSV, `commit	val_bpb	memory_gb	status	description`.
- Direction: lower `val_bpb` is better.
- Timeout: treat a run over 10 minutes as failed unless the contract sets a different budget.
- Default noise rule: `min_delta = 0.001 val_bpb`; repeat current best and candidate twice when inside the near-tie band.
- Complexity rule: when metrics are tied inside `min_delta`, prefer the simpler incumbent unless the candidate is clearly simpler and does not increase memory/runtime.

## Output Contract

Return:

- The agreed experiment contract or missing fields that blocked execution.
- Baseline result and best result.
- Iteration count, kept candidates, discarded candidates, and crash count.
- Paths to `results.tsv` and logs.
- Exact files changed.
- Any command that failed and the relevant last lines of its log.

## Validation

Before calling an autoresearch run successful:

- Explicit trigger: "Use autoresearch on this repo for 8 iterations."
- Implicit trigger: "Let Codex try overnight experiments and keep only metric improvements."
- Negative control: "Review Karpathy autoresearch and summarize the idea" should not start an experiment loop.
- Edge case: dirty workspace should load this skill but stop at isolation negotiation.
- Evidence check: contract validates, baseline exists, at least one log is parsed, results TSV uses the selected schema, and changed files match scope.
- Script check: `validate_contract.py`, `parse_result.py`, and `append_results.py` run successfully on a small fixture.

## Common Mistakes

- Treating "autonomous" as permission to run forever. Use bounded budgets.
- Treating any research task as autoresearch. Require an executable metric.
- Leaving deterministic mechanics as prose. Use scripts for contract validation, log parsing, and result appends.
- Keeping a candidate because it feels clever. Keep only measured improvements beyond `min_delta`.
- Treating a dirty worktree as "do not load skill." Load the skill, negotiate isolation, and do not start the loop.
- Mixing upstream and generic TSV schemas in one run.
- Modifying the harness to make the metric better. The metric path is the judge.
- Resetting or restoring files without proving they are only current experiment changes.
- Letting logs flood context. Write logs to files and extract the metric.
