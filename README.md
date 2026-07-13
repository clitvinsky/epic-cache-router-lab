# EPIC Cache Router Lab

[![CI](https://github.com/clitvinsky/epic-cache-router-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/clitvinsky/epic-cache-router-lab/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

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

Run the generation-plan demo:

```bash
python examples/demo_generation_plan.py
```

Run the eval:

```bash
python -m epic_cache_router_lab.evals fixtures/prior_panels.json fixtures/requests.json
```

Run tests:

```bash
python -m pytest
```

## Diffusion-Aware Routing Extension

Routing decides what should happen. The planning layer decides what would
execute: each `CacheDecision` maps to a `GenerationPlan` with a generation
mode, a starting point, estimated denoising steps, and a normalized cost.

| Route | Generation mode | Starting point | Model call | Cost units |
|---|---|---|---:|---:|
| `return_cached` | `cache` | `cached_asset` | no | 0.0 |
| `surgical_edit` | `latent_edit` | `prior_latent` | yes | 0.35 |
| `camera_or_pose_change` | `img2img` | `reference_image` | yes | 0.65 |
| `identity_locked_regen` | `identity_locked` | `reference_image` | yes | 0.85 |
| `fresh_generation` | `fresh_noise` | `noise` | yes | 1.0 |
| `manual_review` | `review_only` | `none` | no | 0.1 |

Each request is also scored against its matched prior panel with continuity
metrics: identity, prop, location, and prompt overlap plus a weighted drift
score. Direct reuse that fails those gates counts as unsafe reuse. The eval
report aggregates plans and metrics. On the bundled fixtures (24 requests
covering all six routes):

```text
total_requests: 24
route_accuracy: 1.0
unsafe_reuse_count: 0
review_rate: 0.25
avg_drift_score: 0.145
model_calls: 15
avoided_model_calls: 9
baseline_cost_units: 24.0
routed_cost_units: 10.85
estimated_savings_ratio: 0.548
```

Costs are normalized planning estimates, not vendor pricing; the numbers
demonstrate the harness, not production performance. Metric definitions,
thresholds, and known blind spots are in [docs/eval_card.md](docs/eval_card.md).
The full design, including the optional toy-backend phase, is in
[docs/diffusion_router_engineering_spec.md](docs/diffusion_router_engineering_spec.md).

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
  models.py              Typed records for requests, cached panels, decisions, and plans
  router.py              Deterministic routing and safety scoring
  execution_router.py    Maps routing decisions to generation execution plans
  cost_model.py          Cost-avoidance accounting over generation plans
  continuity_metrics.py  Identity, prop, location, prompt, and drift scoring
  evals.py               Fixture-based evaluation runner with cost and continuity reporting
examples/
  demo_router.py             Small terminal demo
  demo_generation_plan.py    Route -> execution plan and cost summary demo
fixtures/
  prior_panels.json
  requests.json
docs/
  architecture.md
  routing_states.md
  safety_gates.md
  epic_case_study.md
  diffusion_router_engineering_spec.md
  eval_card.md
tests/
```

## Used By

[compositional-caching-demo](https://github.com/clitvinsky/compositional-caching-demo)
imports this library as its decision layer: a visual reuse demo where every
request routes through `CacheRouter` and the UI shows the route, rationale,
drift, and cost per request.

## Case Study

See [docs/epic_case_study.md](docs/epic_case_study.md) for the public-safe
story behind the project: a cache-routing workflow built to manage continuity,
cost, and review discipline across a long-form AI graphic novel.

