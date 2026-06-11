---
id: "{{domain_slug}}-open-risks"
title: "{{domain_title}} Open Risks"
summary: "Operational, source, routing, portability, and validation risks for the {{domain_title}} context."
scope: runtime
applies_to: codex
type: risk-register
stability: medium
status: active
last_reviewed: "{{YYYY-MM-DD}}"
retrieval_keys:
  - "{{primary_trigger}} risks"
---

# Open Risks

## Source Coverage

- risk: {{source_coverage_risk}}
- why_it_matters: {{source_coverage_impact}}
- mitigation: {{source_coverage_mitigation}}

## Over-Routing

- risk: {{over_routing_risk}}
- why_it_matters: {{over_routing_impact}}
- mitigation: Use `evals/router_cases.csv` negative cases before widening triggers.

## Portability

- risk: {{portability_risk}}
- why_it_matters: Portable agents and cloned repositories cannot rely on local-only paths or runtime assumptions.
- mitigation: Keep registry, indexes, and router evals repo-relative; put local-only details in operation notes.

## Validation Gap

- risk: {{validation_gap_risk}}
- why_it_matters: A readable knowledge base can still fail retrieval or application behavior.
- mitigation: Add router evals, retrieval pressure checks, source refs, and schema validation before calling the context complete.
