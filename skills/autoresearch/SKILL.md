---
name: autoresearch
description: Use when the user wants Codex to run, adapt, or audit a bounded metric-driven experiment loop in karpathy/autoresearch or a similarly small repo with a clear editable scope, validation command, metric, and keep/discard criterion.
---

# Autoresearch

Autoresearch is a controlled experiment loop for code or model improvements: define an objective metric, run a baseline, try one hypothesis at a time, verify, keep only proven improvements, and leave an audit trail.

This skill is inspired by Karpathy's `karpathy/autoresearch`, where `program.md` guides agents to edit `train.py`, run fixed-budget training, compare `val_bpb`, and keep or discard candidates. Treat the upstream project as the canonical special case, not the only possible use.

Source note: upstream repository `https://github.com/karpathy/autoresearch`, especially `README.md` and `program.md`.

## Use When

- The user names `autoresearch`, `Karpathy autoresearch`, overnight experiments, or autonomous metric-driven iteration.
- The task has a measurable objective such as lower loss, fewer failures, higher benchmark score, faster runtime, or a deterministic acceptance command.
- There is a bounded editable surface, ideally one file or a small explicit file set.
- Failed ideas can be safely discarded or isolated.
- The user is asking for experiment execution, experiment setup, or a review of an autoresearch-style loop.

## Do Not Use When

- There is no objective metric or verification command.
- The task is broad research, literature review, product strategy, or knowledge distillation with no executable experiment loop.
- The target is a production system, shared branch, user data store, deployment, finance/legal/medical workflow, or any environment where failed edits have side effects.
- The workspace has unrelated uncommitted changes and the user has not agreed how to isolate them.
- The user wants a one-off code fix, review, refactor, or explanation rather than repeated experiments.
- The only available validation is subjective taste unless the user first defines a rubric and iteration budget.

## Required Experiment Contract

Before changing files, establish and echo this contract:

| Field | Required decision |
| --- | --- |
| Goal | What metric or score should improve? |
| Direction | Lower is better, higher is better, pass/fail, or threshold target. |
| Scope | Editable files and forbidden files. |
| Verify | Exact command, timeout, log file, and metric extraction rule. |
| Budget | Max iterations, max wall time, resource ceiling, and stop condition. |
| Isolation | Branch, worktree, or scratch copy strategy. |
| Discard permission | Whether Codex may automatically revert its own failed candidate edits to scoped files. |
| Evidence | Where results, logs, and final summary will live. |

If any required field is missing, ask concise questions or propose conservative defaults. Do not begin the loop until the contract is explicit.

## Safety Rules

- Inspect `git status --short` before edits. If unrelated changes exist, do not touch them.
- Prefer a fresh branch or isolated worktree for long experiment loops.
- Edit only contract-approved files. In upstream `karpathy/autoresearch`, this normally means `train.py`; `prepare.py` and the evaluation harness are read-only.
- Do not install dependencies, alter datasets, change metric code, or edit the verification harness without explicit user approval.
- Do not use destructive git commands by default. If discarding requires destructive restore/reset, the contract must explicitly allow it and the status check must show only current experiment changes in approved files.
- Redirect long command output to logs. Do not stream training or benchmark logs into chat.
- Stop when budget is reached, validation becomes unreliable, repeated crashes show the setup is broken, or the next experiment would violate the contract.

## Procedure

1. Classify the run.
   - Upstream mode: repo is `karpathy/autoresearch` or has `prepare.py`, `train.py`, `program.md`, and `pyproject.toml`.
   - Adapted mode: another repo with an explicit metric, command, and scoped editable files.

2. Read the minimum context.
   - Upstream mode: read `README.md`, `program.md`, `prepare.py`, `train.py`, and `pyproject.toml`.
   - Adapted mode: read the files named in the contract plus the verification command docs if present.

3. Verify the environment.
   - Confirm required tools exist, such as `uv` for upstream mode.
   - Confirm data or fixtures exist. For upstream mode, check `~/.cache/autoresearch/`; if missing, tell the user to run or approve `uv run prepare.py`.
   - Run the verification command once only if this is part of the agreed setup.

4. Initialize tracking.
   - Create or reuse a results file outside committed source unless the user wants it versioned.
   - Recommended TSV columns:

```text
timestamp	base_commit	candidate_commit	metric	memory_gb	status	description
```

5. Establish the baseline.
   - Run the verification command without changing code.
   - Parse the metric using the contract's extraction rule.
   - Record baseline as `keep`.

6. Run bounded experiment iterations.
   - Choose one hypothesis.
   - Make the smallest scoped edit.
   - Run the verification command with a timeout and log redirection.
   - Parse metric, resource use, and crash state.
   - Compare against the current best and the complexity cost.
   - Keep only if it improves enough to justify complexity and stays within resource limits.
   - Discard failed or worse candidates only using the contract-approved discard method.
   - Record every candidate in the results file.

7. End with a handoff.
   - Report best metric, baseline metric, current branch or worktree, kept changes, discarded ideas, logs/results path, and remaining risks.
   - Leave the workspace in a clearly named state: best kept branch, clean scoped files, or explicit blocker.

## Upstream Karpathy Defaults

Use these only when the repo matches upstream `karpathy/autoresearch` and the user did not override them:

- Editable file: `train.py`.
- Read-only files: `prepare.py`, tokenizer/data utilities, and `evaluate_bpb` metric path.
- Setup command: `uv sync`, then `uv run prepare.py` if data is absent and the user approves.
- Verify command: `uv run train.py > run.log 2>&1`.
- Metric extraction: `grep "^val_bpb:\\|^peak_vram_mb:" run.log`.
- Direction: lower `val_bpb` is better.
- Timeout: treat a run over 10 minutes as failed unless the user set a different budget.
- Complexity rule: prefer simpler code when metrics are equal or nearly equal.

## Output Contract

Return:

- The agreed experiment contract or any missing fields that blocked execution.
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
- Edge case: dirty workspace or no verification command should stop at contract negotiation.
- Evidence check: results file exists, baseline is recorded, at least one log is captured, and changed files match scope.

## Common Mistakes

- Treating "autonomous" as permission to run forever. Use bounded budgets.
- Treating any research task as autoresearch. Require an executable metric.
- Keeping a candidate because it feels clever. Keep only measured improvements.
- Modifying the harness to make the metric better. The metric path is the judge.
- Resetting or restoring files without proving they are only current experiment changes.
- Letting logs flood context. Write logs to files and extract the metric.
