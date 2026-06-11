---
name: domain-knowledge-distiller
description: Use when a user asks to absorb, distill, internalize, deconstruct, or abstract articles, architectures, quotes, cases, or other high-value sources into reusable domain knowledge for future agent use; triggers include 吸收, 沉淀, 内化, 抽象成原则, 以后能用, work_contexts.
---

# Domain Knowledge Distiller

## Use When

- The user wants high-value resources transformed into reusable domain knowledge, not just summarized.
- The target output is a durable `work_contexts/<domain_slug>/` mini wiki.
- The work needs first-principles analysis, reusable principles, patterns, case mechanisms, architecture, micro tactics, or future retrieval metadata.
- The user explicitly asks for future agent use, efficient recall, knowledge routing, or a Karpathy-style LLM wiki.

## Do Not Use When

- The user only asks for a normal summary, translation, rewrite, excerpt, or temporary reading note.
- The source is low-value and the user has not asked to preserve it.
- The task is only factual verification, citation collection, or web research without durable distillation.
- The knowledge belongs in a repo-local `AGENTS.md`, a one-off prompt, or a deterministic script instead of a reusable domain context.

## Procedure

1. Identify the target domain and source set.
   - If the domain is unclear and cannot be inferred from the task, ask one concise question.
   - Treat explicit requests like "save", "put into work_contexts", or "make this reusable later" as authorization to update that domain context.
2. Assess source quality and fit.
   - For external or current sources, verify with web access when needed and keep source links.
   - Read `references/source-quality-rubric.md` when source credibility, conflict, or copyright handling matters.
3. Distill by mechanism, not by surface summary.
   - Read `references/first-principles-distillation.md` for deep decomposition.
   - Extract goals, constraints, causal mechanisms, invariants, tradeoffs, failure boundaries, and transfer limits.
4. Encode for future agent use.
   - Read `references/agent-learning-loop.md` when building durable knowledge cards.
   - Each important item needs future-use metadata: use cases, non-use cases, retrieval keys, source refs, confidence, and last reviewed date.
5. Route into a domain mini wiki.
   - Resolve the domain context path in this order:
     1. User-provided target path.
     2. `$CODEX_MEMORY_ROOT/work_contexts/<domain_slug>/`.
     3. `$CODEX_HOME/memories/work_contexts/<domain_slug>/`.
     4. `~/.codex/memories/work_contexts/<domain_slug>/`.
   - Read `references/retrieval-routing.md` before creating or restructuring the domain mini wiki.
   - Read `references/work-context-root-maintenance.md` when the target lives under a shared `work_contexts/` root, when adding or reactivating a context, or when changing root-level routing, generated indexes, sync state, router evals, or duplicate source-derived cards.
   - Use templates from `templates/` when creating new pages or cards.
6. Validate the result.
   - Run `python3 scripts/lint_domain_context.py <domain_context_path>` when files are created or edited.
   - Run `python3 scripts/validate_work_contexts.py <work_contexts_root>` when adding contexts, editing routing files, changing generated indexes, or publishing a shared work-context repository.
   - Run `python3 scripts/run_static_evals.py` before publishing skill changes.
   - Perform one retrieval pressure check: given a future task prompt, verify that `README.md -> index.md/retrieval.md -> target page` finds the relevant knowledge.

## Read Only If Needed

- `references/first-principles-distillation.md`: Use for deep decomposition and abstraction quality.
- `references/agent-learning-loop.md`: Use when converting sources into future-callable knowledge cards.
- `references/retrieval-routing.md`: Use when creating or maintaining the pages inside one `work_contexts/<domain_slug>/`.
- `references/work-context-root-maintenance.md`: Use when maintaining a shared `work_contexts/` root, registry, router evals, open risks, portability, or canonical grouping.
- `references/source-quality-rubric.md`: Use when judging source quality, provenance, conflicts, or copyright boundaries.
- `templates/`: Use when creating a new domain context or adding structured knowledge cards.
- `schemas/`: Use when checking structured fields, source manifest entries, or frontmatter.
- `evals/prompts.csv`: Use when testing trigger behavior and retrieval quality.
- `scripts/lint_domain_context.py`: Run after writing or modifying a domain context.
- `scripts/validate_work_contexts.py`: Run after modifying a shared `work_contexts/` root, top-level registry, router evals, generated indexes, or canonical grouping indexes.
- `scripts/run_static_evals.py`: Run when changing the skill, linter, templates, schemas, or eval fixtures.

## Output Contract

Return:

- Target domain and source set.
- What was absorbed, what was rejected or deferred, and why.
- New or updated reusable knowledge: principles, patterns, architecture, micro tactics, cases, open questions.
- Future-use routing: likely user triggers, non-triggers, retrieval keys, first page to read, registry updates, and pages updated.
- Risk and validation surface: router eval cases, open risks, canonical grouping if needed, and portability decisions.
- Evidence: changed files, lint result, work-context root validation when applicable, and one retrieval pressure check.

## Validation

- Explicit trigger: "Use domain-knowledge-distiller to absorb this article into work_contexts."
- Implicit trigger: "This failure case is valuable; turn it into principles I can use later."
- Negative control: "Summarize this article in 300 words."
- Evidence check: The output includes source provenance, knowledge cards, retrieval keys, updated index/retrieval pages, and successful lint/static eval runs.
- Root-system check: When a shared `work_contexts/` root is touched, follow `references/work-context-root-maintenance.md` and run `scripts/validate_work_contexts.py`.

## Common Mistakes

- Producing a polished summary but no reusable mechanism, boundary, or retrieval metadata.
- Copying whole articles into memory instead of storing compact source cards, links, short excerpts, and derived knowledge.
- Putting every domain into one large wiki instead of one `work_contexts/<domain_slug>/` per domain.
- Hardcoding a personal absolute path in reusable skill instructions; resolve memory roots from user input or environment variables.
- Making `README.md` a tutorial; keep it an entry point with shortest read paths.
- Writing principles without non-use cases, source refs, or confidence.
- Adding or moving a shared-root context but skipping `references/work-context-root-maintenance.md`.
- Calling the knowledge base complete because domain pages lint, while root-level routing and portability checks were never run.
