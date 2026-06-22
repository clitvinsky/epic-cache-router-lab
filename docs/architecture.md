# Architecture

The lab models a cache router as a decision layer between a human creative
workflow and an expensive generation backend.

```text
panel request
  |
  v
metadata extraction
  |
  v
candidate lookup  --->  no candidate  --->  fresh_generation
  |
  v
safety scoring
  |
  +-- safe exact or semantic match ----> return_cached
  +-- localized visual change --------> surgical_edit
  +-- camera/action change -----------> camera_or_pose_change
  +-- drift or deep edit chain --------> identity_locked_regen
  +-- ambiguous ----------------------> manual_review
```

## Design Principles

- Reuse is a product decision, not just a vector similarity decision.
- Similarity should be gated by continuity metadata.
- A router should produce an explanation a human reviewer can reject.
- Edit chains need depth limits because small edits accumulate drift.
- Public demos should use synthetic fixtures rather than private creative or
  production assets.

## Production Analogs

A real system might replace this lab's simple scoring with:

- multimodal embeddings
- vector search
- persisted image and prompt metadata
- model-specific cost estimates
- review-state promotion and demotion
- audit logs for why reuse was allowed

Those pieces are intentionally omitted from this public lab.

