"""Maps cache-routing decisions to diffusion-aware generation execution plans.

The routing layer answers "what should happen." This module answers "what
would execute": generation mode, starting point, estimated denoising steps,
and normalized cost. All estimates are synthetic planning values so the lab
stays dependency-free and deterministic.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .models import CacheDecision, GenerationPlan
from .router import (
    ROUTE_CAMERA_OR_POSE,
    ROUTE_FRESH,
    ROUTE_IDENTITY_LOCKED_REGEN,
    ROUTE_MANUAL_REVIEW,
    ROUTE_RETURN_CACHED,
    ROUTE_SURGICAL_EDIT,
)

MODE_CACHE = "cache"
MODE_LATENT_EDIT = "latent_edit"
MODE_IMG2IMG = "img2img"
MODE_IDENTITY_LOCKED = "identity_locked"
MODE_FRESH_NOISE = "fresh_noise"
MODE_REVIEW_ONLY = "review_only"

START_CACHED_ASSET = "cached_asset"
START_PRIOR_LATENT = "prior_latent"
START_REFERENCE_IMAGE = "reference_image"
START_NOISE = "noise"
START_NONE = "none"

# Synthetic timing model: fixed lookup overhead plus a per-step denoising cost.
BASE_OVERHEAD_MS = 40
STEP_LATENCY_MS = 95


@dataclass(frozen=True)
class RouteProfile:
    """Execution characteristics of one routing state."""

    generation_mode: str
    starting_point: str
    requires_model_call: bool
    estimated_steps: int
    estimated_cost_units: float


ROUTE_PROFILES: dict[str, RouteProfile] = {
    ROUTE_RETURN_CACHED: RouteProfile(MODE_CACHE, START_CACHED_ASSET, False, 0, 0.0),
    ROUTE_SURGICAL_EDIT: RouteProfile(MODE_LATENT_EDIT, START_PRIOR_LATENT, True, 12, 0.35),
    ROUTE_CAMERA_OR_POSE: RouteProfile(MODE_IMG2IMG, START_REFERENCE_IMAGE, True, 20, 0.65),
    ROUTE_IDENTITY_LOCKED_REGEN: RouteProfile(
        MODE_IDENTITY_LOCKED, START_REFERENCE_IMAGE, True, 26, 0.85
    ),
    ROUTE_FRESH: RouteProfile(MODE_FRESH_NOISE, START_NOISE, True, 30, 1.0),
    ROUTE_MANUAL_REVIEW: RouteProfile(MODE_REVIEW_ONLY, START_NONE, False, 0, 0.1),
}


def plan_generation(decision: CacheDecision) -> GenerationPlan:
    """Convert one routing decision into an executable generation plan."""
    profile = ROUTE_PROFILES.get(decision.route)
    if profile is None:
        raise ValueError(f"Unknown route: {decision.route!r}")

    return GenerationPlan(
        request_id=decision.request_id,
        route=decision.route,
        generation_mode=profile.generation_mode,
        starting_point=profile.starting_point,
        matched_panel_id=decision.matched_panel_id,
        requires_model_call=profile.requires_model_call,
        requires_review=_requires_review(decision),
        estimated_steps=profile.estimated_steps,
        estimated_cost_units=profile.estimated_cost_units,
        estimated_latency_ms=_estimated_latency_ms(profile),
        risk_flags=decision.risk_flags,
        rationale=decision.rationale,
    )


def plan_all(decisions: Iterable[CacheDecision]) -> tuple[GenerationPlan, ...]:
    return tuple(plan_generation(decision) for decision in decisions)


def _requires_review(decision: CacheDecision) -> bool:
    if decision.route == ROUTE_MANUAL_REVIEW:
        return True
    if decision.route == ROUTE_IDENTITY_LOCKED_REGEN and decision.risk_flags:
        return True
    return False


def _estimated_latency_ms(profile: RouteProfile) -> int:
    return BASE_OVERHEAD_MS + profile.estimated_steps * STEP_LATENCY_MS
