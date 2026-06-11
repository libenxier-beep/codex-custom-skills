# Codex Custom Skills

Public collection of custom-built Codex skills and reusable agent workflows.

## Skills

- `bluegrid-xhs-illustrations`: generate clean 小蓝格 headphone-IP Xiaohongshu illustrations and Chinese article visuals.
- `domain-knowledge-distiller`: distill high-value sources into durable `work_contexts/<domain_slug>/` knowledge bases with provenance, routing, evals, and portability checks.
- `flomo-daily-intake`: collect raw Flomo notes for a specific day or time range before routing or deposition.
- `github-engineering-pattern-knowledge`: operate the local GitHub engineering-pattern knowledge base and dashboard.
- `khub-classifier-router`: classify intake material and produce a route plan before writing KHub notes.
- `khub-deposition-update`: create or append Obsidian KHub notes from validated route plans.

Shared workflow guidance lives in `skills/workflow-principles.md`.

## Layout

```text
skills/
  bluegrid-xhs-illustrations/
  domain-knowledge-distiller/
  flomo-daily-intake/
  github-engineering-pattern-knowledge/
  khub-classifier-router/
  khub-deposition-update/
  workflow-principles.md
```

Each skill directory contains a `SKILL.md` entry point. Some skills also include contracts, templates, examples, references, validation scripts, and trigger evals.

## Install

Copy the desired skill directories into your Codex skills directory:

```bash
mkdir -p "$CODEX_HOME/skills"
cp -R skills/bluegrid-xhs-illustrations "$CODEX_HOME/skills/"
cp -R skills/domain-knowledge-distiller "$CODEX_HOME/skills/"
cp -R skills/flomo-daily-intake "$CODEX_HOME/skills/"
cp -R skills/github-engineering-pattern-knowledge "$CODEX_HOME/skills/"
cp -R skills/khub-classifier-router "$CODEX_HOME/skills/"
cp -R skills/khub-deposition-update "$CODEX_HOME/skills/"
```

Set `CODEX_HOME` to your local Codex configuration directory if it is not already defined.

## Validation

Run the full package check:

```bash
bash scripts/run-golden-tests.sh
```

This command validates positive examples, negative examples, schema parseability, shell entrypoints, line endings, trigger eval CSVs, and Markdown links.

Or run individual validators:

```bash
bash skills/khub-classifier-router/scripts/validate-route-plan.sh \
  skills/khub-classifier-router/examples/output-route-plan.create.yaml

bash skills/khub-deposition-update/scripts/validate-note-payload.sh \
  skills/khub-deposition-update/examples/note-payload.seed.yaml

bash skills/khub-deposition-update/scripts/validate-execution-report.sh \
  skills/khub-deposition-update/examples/create-seed.md
```

Review `skills/*/evals/trigger-prompts.csv` when changing skill names, descriptions, or activation boundaries.

## Sanitization

This repository should not contain private local paths, tokens, credentials, personal identifiers, or private project details. Use placeholders such as `$CODEX_HOME`, `PROJECT_ROOT`, and `OBSIDIAN_VAULT`.

## Attribution

See [NOTICE](NOTICE) for inspiration and attribution notes.
