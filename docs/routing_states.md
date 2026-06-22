# Routing States

## `return_cached`

Used when a prior accepted panel matches the request closely and continuity
metadata also matches. This is the only route that directly reuses a previous
result.

## `surgical_edit`

Used when the panel is fundamentally the same but a localized detail changed:
prop, wardrobe, lighting, expression, or small style tag.

## `camera_or_pose_change`

Used when the content is related but camera, framing, action, or pose changed
enough that direct reuse would be misleading.

## `identity_locked_regen`

Used when the prior panel provides useful context but direct reuse is unsafe,
especially after repeated edits. A production system would pass canonical
identity references while regenerating the scene.

## `fresh_generation`

Used when the nearest prior panel differs in core continuity dimensions such as
characters or location.

## `manual_review`

Used when the system finds a plausible candidate but cannot justify an automatic
decision. This is important for creative tools because the cost of a wrong reuse
is often human trust, not just model quality.

