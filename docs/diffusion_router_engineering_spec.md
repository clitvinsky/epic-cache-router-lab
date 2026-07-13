# EPIC Diffusion Router Engineering Spec

Status: Phases 1 (model-aware planning), 2 (continuity evals), and 4 (review
report) implemented. Phase 3 (toy diffusion backend) is deliberately skipped
for now; the differentiator is routing and evaluation, not sample quality.

## 1. Purpose

Extend `epic-cache-router-lab` from a deterministic metadata router into a
small, inspectable generative-media systems lab.

The goal is not to compete with frontier image or video models. The goal is to
show how diffusion-style generation can be wrapped in routing, reuse, edit,
review, and evaluation infrastructure similar to what production generative
media systems need.

The finished artifact should demonstrate:

- basic diffusion or flow-matching model literacy
- routing decisions across reuse, edit, regeneration, and review
- continuity-aware evaluation for long-form visual workflows
- cost, latency, and avoided-generation accounting
- honest documentation of model limits and workflow tradeoffs

## 2. Audience

- engineers evaluating whether the project is a credible systems artifact
- product and research leaders interested in controllable generation,
  continuity, cost, and review loops

## 3. Positioning

> EPIC Diffusion Router Lab is a reference harness for routing, evaluating, and
> controlling diffusion-style generative media workflows across reuse, edit,
> regeneration, and human review.

Avoid claiming:

- frontier model research
- production quality image generation
- proprietary implementation details from private systems
- private benchmark or customer results

## 4. Non-Goals

This project will not:

- train a large text-to-image, text-to-video, or multimodal foundation model
- require paid GPU infrastructure
- publish private creative assets, production code, API traces, or customer data
- optimize for photorealistic samples
- depend on hosted model APIs for core tests

## 5. System Overview

```text
panel request
  |
  v
metadata extraction / structured request
  |
  v
candidate lookup
  |
  +-- no candidate ----------------------------> fresh_generation
  |
  v
continuity + reuse scoring
  |
  +-- safe exact match ------------------------> return_cached
  +-- localized change ------------------------> latent_edit
  +-- camera/action change --------------------> controlled_regen
  +-- identity drift or edit-depth limit ------> identity_locked_regen
  +-- ambiguous -------------------------------> manual_review
  +-- no safe path ----------------------------> fresh_generation
```

The existing router remains the core decision layer. The extension adds model
execution metadata, lightweight generation artifacts, and eval reporting around
that router.

## 6. Routing States

Keep existing routes:

- `return_cached`
- `surgical_edit`
- `camera_or_pose_change`
- `identity_locked_regen`
- `fresh_generation`
- `manual_review`

Add model-aware execution hints through a `GenerationPlan` produced from each
`CacheDecision`, rather than replacing the route taxonomy:

- `generation_mode`: `cache`, `latent_edit`, `img2img`, `fresh_noise`,
  `identity_locked`, `review_only`
- `starting_point`: `cached_asset`, `prior_latent`, `reference_image`, `noise`,
  `none`
- `estimated_steps`: integer denoising or flow steps
- `estimated_cost_units`: synthetic normalized cost estimate
- `estimated_latency_ms`: synthetic or measured latency

This keeps the public API stable while making the router diffusion-aware.

## 7. Package Layout

```text
src/epic_cache_router_lab/
  models.py                  Request, prior panel, decision, and plan models
  router.py                  Deterministic continuity router
  evals.py                   Fixture evaluator with cost reporting
  execution_router.py        Maps CacheDecision to a generation execution plan
  cost_model.py              Avoided generation, latency, and cost accounting
  continuity_metrics.py      Drift, prompt, identity, and prop metrics (Phase 2)
  diffusion_toy.py           Optional tiny DDPM or flow-matching model (Phase 3)

examples/
  demo_router.py             Terminal routing demo
  demo_generation_plan.py    Shows route -> execution plan and cost summary
  train_toy_diffusion.py     Optional small training entrypoint (Phase 3)
  sample_toy_diffusion.py    Optional sample-grid generation (Phase 3)

fixtures/
  prior_panels.json          Synthetic prior metadata
  requests.json              Synthetic incoming requests

docs/
  diffusion_router_engineering_spec.md
  eval_card.md               (Phase 2)
  model_card.md              (Phase 3)
  generation_workflow.md     (Phase 4)

tests/
  test_router.py
  test_evals.py
  test_execution_router.py
  test_cost_model.py
  test_continuity_metrics.py (Phase 2)
```

## 8. Data Model Additions

### `GenerationPlan`

Purpose: describe what the system should do after routing.

Fields:

- `request_id: str`
- `route: str`
- `generation_mode: str`
- `starting_point: str`
- `matched_panel_id: str | None`
- `requires_model_call: bool`
- `requires_review: bool`
- `estimated_steps: int`
- `estimated_cost_units: float`
- `estimated_latency_ms: int`
- `risk_flags: tuple[str, ...]`
- `rationale: str`

### `ContinuityMetricResult` (Phase 2)

Purpose: make eval outputs explicit and testable.

Fields:

- `request_id: str`
- `identity_score: float`
- `prop_score: float`
- `location_score: float`
- `prompt_score: float`
- `drift_score: float`
- `passed: bool`
- `failure_reasons: tuple[str, ...]`

## 9. Generation Backends

### Phase 1: Planning Only

No backend. The execution router converts a `CacheDecision` into a
deterministic `GenerationPlan` with estimated step count, latency, and cost by
route. No ML dependency, no image files. This proves the systems architecture
independent of sample quality and keeps the repo easy to run.

### Phase 3: Toy Diffusion Backend (future)

Options:

- small DDPM on MNIST or Fashion-MNIST
- tiny flow-matching model on synthetic 2D shapes

Recommended default:

- `torch` optional dependency under `ml`
- image size `28x28` or `32x32`
- CPU-compatible sampling for a small number of examples
- committed sample grids, not committed model checkpoints unless tiny

If a real latent edit path is too heavy, keep it simulated. The differentiator
is routing and evaluation, not image quality.

## 10. Execution Router Rules

Map `CacheDecision` to `GenerationPlan`:

| Route | Generation mode | Starting point | Model call | Review |
|---|---|---|---:|---:|
| `return_cached` | `cache` | `cached_asset` | no | no |
| `surgical_edit` | `latent_edit` | `prior_latent` | yes | no |
| `camera_or_pose_change` | `img2img` | `reference_image` | yes | no |
| `identity_locked_regen` | `identity_locked` | `reference_image` | yes | if risk flags |
| `fresh_generation` | `fresh_noise` | `noise` | yes | no |
| `manual_review` | `review_only` | `none` | no | yes |

Cost assumptions for the planning layer:

- cache return: `0.0` cost units
- manual review only: `0.1` cost units
- latent edit: `0.35` cost units
- img2img or camera/pose change: `0.65` cost units
- identity-locked regeneration: `0.85` cost units
- fresh generation: `1.0` cost units

These are normalized estimates, not vendor pricing.

## 11. Continuity Metrics (Phase 2)

Implement simple, inspectable metrics first:

- `identity_score`: character set overlap
- `prop_score`: prop set overlap
- `location_score`: exact or normalized location match
- `prompt_score`: token overlap between request and selected prior/generated
  description
- `drift_score`: weighted penalty from changed characters, props, location,
  camera, action, style tags, and edit depth

Pass/fail rule:

```text
passed =
  identity_score >= 0.95
  and location_score >= 0.90
  and drift_score <= 0.25
```

Later optional metrics (kept behind extras so the base repo stays lightweight):

- CLIP image/text similarity
- perceptual hash distance
- frame-to-frame consistency for toy video sequences

## 12. Eval Report

The eval runner should output:

- total requests
- route distribution
- expected-route accuracy
- avoided model calls
- estimated cost without router
- estimated cost with router
- estimated cost savings
- review rate
- unsafe reuse count (Phase 2)
- average safety score
- average drift score (Phase 2)

## 13. CLI Commands

```bash
python examples/demo_router.py
python examples/demo_generation_plan.py
python -m epic_cache_router_lab.evals fixtures/prior_panels.json fixtures/requests.json
python -m epic_cache_router_lab.report fixtures/prior_panels.json fixtures/requests.json
python -m pytest
```

## 14. Testing Strategy

Required tests:

- existing router tests continue to pass unchanged
- `return_cached` maps to no model call and zero cost
- `manual_review` maps to no model call and review required
- `fresh_generation` maps to fresh noise and full cost
- cost model reports savings when model calls are avoided
- unsafe reuse count increments only when direct reuse fails continuity gates
  (Phase 2)
- continuity metrics are deterministic over fixture inputs (Phase 2)

Optional ML tests (Phase 3):

- import test for the optional diffusion backend when `torch` is installed
- smoke test for one sampling pass with a tiny random model
- no test should require a downloaded dataset by default

## 15. Implementation Phases

### Phase 1: Model-Aware Planning (implemented)

- `GenerationPlan`
- `execution_router.py`
- `cost_model.py`
- `demo_generation_plan.py`
- tests
- README and doc updates

Success criteria: no new heavy dependencies, existing tests pass, eval report
includes cost and avoided-call metrics.

### Phase 2: Continuity Evals (implemented)

- `continuity_metrics.py`
- unsafe reuse accounting
- drift scoring
- `docs/eval_card.md`
- tests

Success criteria: each route has interpretable continuity metrics; eval output
demonstrates why direct reuse is sometimes unsafe.

### Phase 3: Toy Diffusion Or Flow Backend (future)

- optional `ml` dependency group
- `diffusion_toy.py` or `flow_toy.py`
- training and sampling scripts
- sample grid artifact
- `docs/model_card.md`

Success criteria: base tests do not require ML dependencies; documentation is
honest about scope.

### Phase 4: Review Report (implemented)

- Markdown review report rendered from eval output (`report.py`)
- route distribution summary, per-request rationale, review reasons
- cost and safety summary
- committed sample (`docs/sample_eval_report.md`) kept current by a test

Success criteria: report is readable by a technical reviewer and traceable to
fixture decisions and tests.

## 16. Quality Bar

The project is successful if a reviewer can answer:

- What decision did the router make?
- Why did it make that decision?
- What generation path would execute?
- What cost or latency was avoided?
- What continuity risk remains?
- What would require human review?
- Which parts are toy model code versus production architecture concepts?

## 17. Risks And Mitigations

Risk: weak toy model samples make the repo look unserious.

Mitigation: lead with routing and evals. Put toy samples behind the systems
story, not at the top of the README.

Risk: heavy ML dependencies make the repo hard to run.

Mitigation: keep the default install dependency-free. Use optional `ml` extras.

Risk: overclaiming research depth.

Mitigation: use precise language: "toy diffusion backend",
"diffusion-aware routing", "reference harness", and "simulated cost model".

Risk: project drifts into a large unfinished platform.

Mitigation: ship phases independently. Phase 1 and Phase 2 are valuable without
Phase 3.
