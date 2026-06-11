# Work Context Root Maintenance

Use this only when a domain context lives inside a shared `work_contexts/` root or when root-level routing, sync, generated indexes, or portability are touched.

This file owns the system layer around domain contexts. It does not own source distillation quality, knowledge-card structure, or page-level retrieval design; those stay in `first-principles-distillation.md`, `agent-learning-loop.md`, and `retrieval-routing.md`.

## Responsibility Boundary

| File | Owns | Does Not Own |
| --- | --- | --- |
| `SKILL.md` | Trigger boundary, shortest workflow, validation entry points, output contract. | Full root maintenance rules. |
| `references/retrieval-routing.md` | One domain mini-wiki layout, page roles, retrieval keys, retrieval pressure check. | Shared root registry, sync, canonical grouping, portability policy. |
| `references/work-context-root-maintenance.md` | Root README, `contexts.registry.json`, router evals, open risks, path portability, duplicate evidence grouping, root validation. | Domain mechanism distillation or source credibility scoring. |
| `scripts/validate_work_contexts.py` | Deterministic checks for the root maintenance contract. | Judging knowledge quality. |

## Shared Root Files

Maintain these files when adding, reactivating, renaming, moving, or publishing a context:

```text
work_contexts/
  README.md
  contexts.registry.json
```

The root `README.md` should list active contexts and explain the human-readable routing rule.

`contexts.registry.json` is the machine-readable router. Each active context should include:

- `id`
- `path`
- `summary`
- `triggers`
- `non_triggers`
- `read_path`
- `eval_file`
- `risk_file`
- `status`
- `last_reviewed`
- `sync_targets`
- `depends_on`

All paths in registry and portable retrieval indexes must be repo-relative.

## Per-Context System Files

Each shared-root context should have:

```text
work_contexts/<domain_slug>/
  open_risks.md
  evals/
    router_cases.csv
```

`open_risks.md` records source limits, portability limits, stale assumptions, over-routing risk, validation gaps, and any context-specific uncertainty that should not be promoted into stable principles.

`evals/router_cases.csv` uses this header:

```csv
id,user_request,should_load_context,expected_first_file,expected_deeper_files,negative_reason
```

Rules:

- Include at least one positive case and one negative case.
- Positive cases name the first file and any deeper files needed for the task.
- Negative cases leave file columns blank and explain why the context should not load.
- Use real user-language cases, not only abstract labels.

## Portability Rules

- Do not put personal absolute paths such as `/Users/...`, `/home/...`, or drive-letter paths in registry files, generated indexes, router evals, or portable retrieval metadata.
- Local paths belong only in operation notes or source provenance when the local-only boundary is explicit.
- Generated JSON used for retrieval should remain parseable with `python3 -m json.tool`.
- A cloned repository should be able to route from `contexts.registry.json` without relying on the user's local Ring 0 or `core/router` files.

## Canonical Grouping

If many source items produce near-duplicate cards or patterns, create a canonical grouping index before treating each source-derived item as a separate retrieval result.

Use canonical grouping when:

- Several records share the same conceptual `name`.
- Only source repo, article, or evidence sample changes.
- Retrieval would over-count the same mechanism.

The canonical index should let agents retrieve the mechanism first and then choose evidence samples only when needed.

## Validation

Run:

```bash
python3 scripts/validate_work_contexts.py <work_contexts_root>
```

Run it when:

- Adding, renaming, moving, archiving, or reactivating a context.
- Editing `contexts.registry.json`, root `README.md`, `evals/router_cases.csv`, or `open_risks.md`.
- Changing generated retrieval indexes.
- Publishing or syncing a shared `work_contexts/` repository.
- Adding canonical grouping for duplicate source-derived evidence.

Do not call a shared root complete only because individual domain pages pass `lint_domain_context.py`.
