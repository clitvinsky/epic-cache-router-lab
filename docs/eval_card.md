# Eval Card

What the fixture-based eval measures, how the fixtures were built, and how to
read the output honestly.

## Evaluated Behaviors

- **Route accuracy.** Every fixture request is labeled with an expected route;
  the eval reports the match rate.
- **Route distribution.** How requests spread across the six routing states.
- **Cost avoidance.** Baseline cost (every request generated fresh) versus
  routed cost, in normalized cost units, plus avoided model calls.
- **Review rate.** Share of requests that require a human before proceeding.
- **Continuity metrics.** Per-request identity, prop, location, prompt, and
  drift scores against the matched prior panel.
- **Unsafe reuse.** Count of `return_cached` decisions whose continuity gates
  fail. This is a tripwire metric: it should be zero while the router is
  working and increments only if routing regresses.

## Fixture Construction

- 8 synthetic prior panels across 6 fictional scenes, including two panels
  with `edit_depth` 1 to exercise the edit-chain limit.
- 24 labeled requests covering all six routes: 6 `return_cached`,
  4 `surgical_edit`, 4 `camera_or_pose_change`, 3 `identity_locked_regen`,
  3 `manual_review`, 4 `fresh_generation`.
- All content is synthetic. Fictional characters, no real project assets, no
  production prompts.

## Pass/Fail Thresholds

A request passes the continuity gates when:

```text
identity_score >= 0.95
location_score >= 0.90
drift_score   <= 0.25
```

Drift accumulates weighted penalties for changed continuity dimensions:
characters 0.30, location 0.20, camera 0.12, action 0.12, props 0.10,
style tags 0.08, plus 0.04 per level of prior edit depth (capped at 0.08).
Set-valued dimensions are penalized in proportion to how much of the set
changed.

## Current Output

```text
total_requests: 24
route_accuracy: 1.0
unsafe_reuse_count: 0
review_rate: 0.25
avg_drift_score: 0.145
baseline_cost_units: 24.0
routed_cost_units: 10.85
estimated_savings_ratio: 0.548
```

## Known Blind Spots

- **No image-space signal.** All metrics are set and token comparisons over
  metadata. They cannot see visual similarity; a production system would add
  CLIP similarity, perceptual hashing, or caption-embedding distance.
- **Word overlap is not intent overlap.** `prompt_score` treats shared tokens
  as shared meaning; paraphrases score low. This is why the `manual_review`
  fixtures pass every metadata gate yet still route to a human: the metadata
  matches, but the prompt has drifted in ways the system cannot judge.
- **Fixtures are authored to be separable.** Each request has a clear nearest
  panel. Real workloads have ambiguous neighbors and noisier metadata.
- **These are harness numbers, not production numbers.** The eval demonstrates
  that the decision layer behaves as specified over synthetic fixtures. It
  makes no claim about hit rates, savings, or safety on real traffic.

## Interpretation Guidance

- A drop in `route_accuracy` means routing behavior changed; check router
  thresholds and fixture expectations before anything else.
- Any nonzero `unsafe_reuse_count` is a regression: the router returned a
  cached result that fails continuity gates.
- Rising `avg_drift_score` with stable routing means matched panels are
  getting further from requests; consider whether fixtures or thresholds
  moved.
- `estimated_savings_ratio` follows the route mix mechanically. It is a
  planning estimate driven by the normalized cost table, not a measured
  saving.
