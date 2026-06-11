---
name: github-engineering-pattern-knowledge
description: Use when building, running, auditing, or extending a local Work Contexts knowledge base that learns transferable engineering patterns from GitHub repositories.
---

# GitHub Engineering Pattern Knowledge

Use this skill to operate the `github-pattern-knowledge` tool and keep its outputs suitable for agent reuse. The durable artifact is the Work Contexts knowledge base, not the dashboard.

## Use When

- A user wants to learn from GitHub repositories into a local engineering-pattern knowledge base.
- A seed list, daily extraction run, archive/skip registry, or dashboard needs to be created or maintained.
- Pattern notes need retrieval tags, progressive disclosure, source evidence, indexes, or harness validation.
- A GitHub token, rate-limit behavior, or already-learned repository archive affects ingestion.

## Do Not Use When

- The task is ordinary GitHub repository triage, PR review, or CI debugging.
- The user only wants a one-off summary of a single repository with no durable knowledge write.
- The target is long-term personal memory rather than a Work Contexts engineering knowledge base.

## Project Contract

- Tool repo: `github-pattern-knowledge`.
- Default knowledge root: `$CODEX_HOME/memories/work_contexts/github_engineering_patterns`.
- Generated knowledge directories: `patterns/`, `indexes/`, `cards/`, `registry/`, `sources/`, `runs/`, `rejected/`, and `schemas/`.
- Learned archive: `registry/learned_repos.json`.
- Seed archive: `registry/seed_repos.json`.
- Public tool repository: `https://github.com/libenxier-beep/github-pattern-knowledge`.

Keep secrets in `.env.local` or the shell environment. Never commit `GITHUB_TOKEN`, `.env`, `.env.local`, `node_modules`, `dist`, or generated private knowledge data unless the user explicitly asks for a public export.

## Operating Flow

1. Inspect the current repo and knowledge root before changing anything.
2. Load `.env.local` or require `GITHUB_TOKEN` only when GitHub rate limits block ingestion.
3. For seed work, update or read `registry/seed_repos.json`, then run `npm run seed -- --limit N` or `npm run seed -- --repos owner/name`.
4. For daily work, run `npm run daily`; it should prefer pending seed repos unless `--skip-seeds` is used.
5. Before selecting a repo, check `registry/learned_repos.json`; learned repos must be skipped.
6. After accepted writes, regenerate indexes and cards, then run the harness.
7. For legacy notes or any run that predates evidence tables, run `npm run evidence`, regenerate indexes, and run the harness again.
8. For dashboard changes, verify both API output and the UI.

## Pattern Note Standard

Accepted pattern notes must be Markdown with YAML frontmatter and must include source traceability:

- `source_repos[].repo`, `source_repos[].url`, concrete `source_repos[].commit`, and 2-4 `reference_files`
- retrieval fields such as engineering problem, project type, pattern type, transfer targets, complexity, and quality score
- body sections for engineering problem, core judgment, use/avoid conditions, design forces, boundary decisions, failure modes, alternatives, transfer guidance, implementation hint, evidence table, and source evidence

The evidence table is not decorative. Each row must name one reference file, describe the observed structure, list concrete functions/classes/tests/modules/config keys, and explain why that evidence supports the pattern. Prefer fewer patterns over weak evidence.

When ingestion records a commit SHA, subsequent tree, README, and selected file fetches must use that commit SHA as the ref. Do not fetch evidence from a moving branch after recording a concrete commit.

Each note should support progressive disclosure:

- frontmatter and retrieval tags for fast filtering
- a short summary and core judgment for first read
- boundary decisions and failure modes for implementation judgment
- source evidence for audit

## Commands

```bash
npm install
npm run seed -- --list
npm run seed -- --limit 3
npm run daily
npm run evidence
npm run index
npm run harness
npm test
npm run typecheck
npm run build
npm run dev
```

## Validation Gate

Before claiming the knowledge base or website is ready, run the relevant checks:

- `npm test`
- `npm run typecheck`
- `npm run build`
- `npm run evidence` when legacy notes, commit traceability, or evidence tables were changed
- `npm run harness`
- API check for `/api/knowledge/summary` or `/api/knowledge/archive` when archive/dashboard behavior changed

Report exact counts for learned repos, pending repos, checked files, and failures.

## Common Mistakes

- Treating human-facing cards as the agent-readable source of truth.
- Re-learning repos already recorded in `learned_repos.json`.
- Adding tags without regenerating indexes.
- Publishing local secrets or generated private Work Contexts data.
- Claiming completion without harness and dashboard/API verification.
