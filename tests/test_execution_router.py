from __future__ import annotations

import json
from pathlib import Path

import pytest

from epic_cache_router_lab.execution_router import (
    MODE_CACHE,
    MODE_FRESH_NOISE,
    MODE_LATENT_EDIT,
    MODE_REVIEW_ONLY,
    START_CACHED_ASSET,
    START_NOISE,
    START_NONE,
    START_PRIOR_LATENT,
    plan_all,
    plan_generation,
)
from epic_cache_router_lab.models import CacheDecision, PanelRequest, PriorPanel
from epic_cache_router_lab.router import (
    CacheRouter,
    ROUTE_FRESH,
    ROUTE_IDENTITY_LOCKED_REGEN,
    ROUTE_MANUAL_REVIEW,
    ROUTE_RETURN_CACHED,
    ROUTE_SURGICAL_EDIT,
)


ROOT = Path(__file__).resolve().parents[1]


def load_fixture_decisions():
    prior = [
        PriorPanel.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "prior_panels.json").read_text())
    ]
    requests = [
        PanelRequest.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "requests.json").read_text())
    ]
    router = CacheRouter(prior)
    return [router.route(req) for req in requests]


def make_decision(route: str, risk_flags: tuple[str, ...] = ()) -> CacheDecision:
    return CacheDecision(
        request_id="synthetic",
        route=route,
        matched_panel_id="p001",
        similarity=0.8,
        safety_score=0.7,
        rationale="synthetic decision",
        risk_flags=risk_flags,
    )


def test_return_cached_needs_no_model_call_and_zero_cost():
    plan = plan_generation(make_decision(ROUTE_RETURN_CACHED))

    assert plan.generation_mode == MODE_CACHE
    assert plan.starting_point == START_CACHED_ASSET
    assert plan.requires_model_call is False
    assert plan.requires_review is False
    assert plan.estimated_steps == 0
    assert plan.estimated_cost_units == 0.0


def test_manual_review_needs_no_model_call_and_requires_review():
    plan = plan_generation(make_decision(ROUTE_MANUAL_REVIEW))

    assert plan.generation_mode == MODE_REVIEW_ONLY
    assert plan.starting_point == START_NONE
    assert plan.requires_model_call is False
    assert plan.requires_review is True


def test_fresh_generation_starts_from_noise_at_full_cost():
    plan = plan_generation(make_decision(ROUTE_FRESH))

    assert plan.generation_mode == MODE_FRESH_NOISE
    assert plan.starting_point == START_NOISE
    assert plan.requires_model_call is True
    assert plan.estimated_cost_units == 1.0


def test_surgical_edit_starts_from_prior_latent():
    plan = plan_generation(make_decision(ROUTE_SURGICAL_EDIT))

    assert plan.generation_mode == MODE_LATENT_EDIT
    assert plan.starting_point == START_PRIOR_LATENT
    assert plan.requires_model_call is True
    assert 0.0 < plan.estimated_cost_units < 1.0


def test_identity_locked_regen_requires_review_only_with_risk_flags():
    flagged = plan_generation(
        make_decision(ROUTE_IDENTITY_LOCKED_REGEN, risk_flags=("edit_depth_limit",))
    )
    clean = plan_generation(make_decision(ROUTE_IDENTITY_LOCKED_REGEN))

    assert flagged.requires_review is True
    assert clean.requires_review is False


def test_unknown_route_raises_value_error():
    with pytest.raises(ValueError):
        plan_generation(make_decision("teleport"))


def test_plans_carry_decision_context_for_fixtures():
    decisions = load_fixture_decisions()
    plans = plan_all(decisions)

    assert len(plans) == len(decisions)
    for decision, plan in zip(decisions, plans):
        assert plan.request_id == decision.request_id
        assert plan.route == decision.route
        assert plan.matched_panel_id == decision.matched_panel_id
        assert plan.risk_flags == decision.risk_flags
        assert plan.estimated_latency_ms >= 0
