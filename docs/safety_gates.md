# Safety Gates

The lab uses simple gates that mirror the kinds of checks a production creative
system needs before reusing or editing a prior generation.

## Character Gate

If the requested character set does not match the prior panel, the router avoids
reuse. Character mismatch is a high-risk failure mode because it can silently
contaminate canon.

## Location Gate

Location mismatch usually means the visual context is not reusable. The router
routes these cases to `fresh_generation`.

## Camera And Action Gate

Camera or action changes can preserve subject matter while invalidating the
image. These usually route to `camera_or_pose_change`.

## Prop And Style Gate

Prop, wardrobe, or style changes are often localized. These route to
`surgical_edit` when the rest of the continuity metadata matches.

## Edit-Depth Gate

Repeated small edits accumulate drift. The lab forces deeper edit chains toward
`identity_locked_regen` rather than continuing to patch the same image.

## Human Review

The router should not pretend all uncertainty is automatable. The
`manual_review` route is a first-class result.

