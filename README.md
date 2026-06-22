# EPIC Cache Router Lab

Reference harness for cache routing, continuity safety, and human-in-the-loop
generation workflows for long-form AI visual projects.

This is a sanitized public lab derived from a larger private workflow used for
a 120-page AI graphic novel project. It does not contain production code,
private prompts, proprietary character references, generated book assets, API
keys, model traces, or company-specific implementation details.

## Why This Exists

Long-form image generation is not only a prompt problem. Once a project spans
dozens of pages, the workflow becomes a routing problem:

- When can a previous result be reused exactly?
- When is a semantic match close enough to inspect but not safe to return?
- When should the system make a surgical edit instead of regenerating?
- When has an edit chain drifted far enough that a fresh render is safer?
- How should the system explain routing decisions to a human reviewer?

The goal of this repo is to make those tradeoffs concrete.

## Routing States

The demo router classifies each request into one of the following operations:

| Operation | Meaning |
|---|---|
| `return_cached` | Safe exact or high-confidence semantic reuse |
| `surgical_edit` | Small prop, expression, wardrobe, or lighting change |
| `camera_or_pose_change` | Camera/framing/action changed enough to avoid reuse |
| `identity_locked_regen` | Preserve character identity while regenerating the scene |
| `fresh_generation` | No safe prior result or too much continuity risk |
| `manual_review` | Candidate exists, but safety score is below threshold |

## What The Demo Shows

The lab uses synthetic fixtures under `fixtures/`:

- fictional characters with continuity constraints
- prior generated-panel metadata
- incoming panel requests
- expected routing outcomes

Run the demo:

```bash
python examples/demo_router.py
```

Run the eval:

```bash
python -m epic_cache_router_lab.evals fixtures/prior_panels.json fixtures/requests.json
```

Run tests:

```bash
python -m pytest
```

## Public-Safe Scope

This repo intentionally focuses on the product and systems shape:

- deterministic routing logic
- explainable decision output
- synthetic continuity metadata
- eval metrics for route accuracy, avoided generation, and unsafe reuse
- documentation of safety gates and failure modes

It intentionally excludes:

- private EPIC artwork, prompts, characters, and source assets
- production WorldFlow or EPIC code
- patent-sensitive implementation details
- customer data, vendor traces, API keys, or benchmark claims

## Repo Map

```text
src/epic_cache_router_lab/
  models.py        Typed records for requests, cached panels, and decisions
  router.py        Deterministic routing and safety scoring
  evals.py         Fixture-based evaluation runner
examples/
  demo_router.py   Small terminal demo
fixtures/
  prior_panels.json
  requests.json
docs/
  architecture.md
  routing_states.md
  safety_gates.md
  epic_case_study.md
tests/
```

## Case Study

See [docs/epic_case_study.md](docs/epic_case_study.md) for the public-safe
story behind the project: a cache-routing workflow built to manage continuity,
cost, and review discipline across a long-form AI graphic novel.

