from __future__ import annotations

import json
from pathlib import Path

from epic_cache_router_lab.continuity_metrics import (
    IDENTITY_THRESHOLD,
    MAX_DRIFT,
    REASON_DRIFT,
    REASON_IDENTITY,
    REASON_LOCATION,
    REASON_NO_PRIOR_PANEL,
    is_unsafe_reuse,
    score_continuity,
)
from epic_cache_router_lab.models import CacheDecision, PanelRequest, PriorPanel
from epic_cache_router_lab.router import CacheRouter, ROUTE_FRESH, ROUTE_RETURN_CACHED


ROOT = Path(__file__).resolve().parents[1]

BASE_FIELDS = {
    "prompt": "Hero and companion stand on a rainlit bridge facing a glass tower.",
    "characters": ("hero", "companion"),
    "location": "rainlit_bridge",
    "camera": "wide",
    "action": "stand_off",
    "props": ("glass_tower", "blue_cloak"),
    "continuity_tags": ("noir_palette", "wet_pavement"),
}


def make_panel(**overrides) -> PriorPanel:
    return PriorPanel(panel_id="p_test", **{**BASE_FIELDS, **overrides})


def make_request(**overrides) -> PanelRequest:
    return PanelRequest(request_id="r_test", **{**BASE_FIELDS, **overrides})


def make_decision(route: str) -> CacheDecision:
    return CacheDecision(
        request_id="r_test",
        route=route,
        matched_panel_id="p_test",
        similarity=0.9,
        safety_score=0.9,
        rationale="synthetic decision",
    )


def load_fixture_pairs():
    prior = [
        PriorPanel.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "prior_panels.json").read_text())
    ]
    requests = [
        PanelRequest.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "requests.json").read_text())
    ]
    panels_by_id = {panel.panel_id: panel for panel in prior}
    router = CacheRouter(prior)
    decisions = [router.route(req) for req in requests]
    return [
        (req, decision, panels_by_id.get(decision.matched_panel_id or ""))
        for req, decision in zip(requests, decisions)
    ]


def test_identical_request_and_panel_pass_all_gates():
    result = score_continuity(make_request(), make_panel())

    assert result.identity_score == 1.0
    assert result.prop_score == 1.0
    assert result.location_score == 1.0
    assert result.prompt_score == 1.0
    assert result.drift_score == 0.0
    assert result.passed is True
    assert result.failure_reasons == ()


def test_character_change_fails_identity_gate():
    result = score_continuity(make_request(characters=("hero",)), make_panel())

    assert result.identity_score < IDENTITY_THRESHOLD
    assert REASON_IDENTITY in result.failure_reasons
    assert result.passed is False


def test_location_change_fails_location_gate():
    result = score_continuity(make_request(location="frost_canyon"), make_panel())

    assert result.location_score == 0.0
    assert REASON_LOCATION in result.failure_reasons
    assert result.passed is False


def test_small_changes_accumulate_into_drift_failure():
    result = score_continuity(
        make_request(camera="close", action="raise_flare", props=("signal_flare",)),
        make_panel(),
    )

    assert result.identity_score == 1.0
    assert result.location_score == 1.0
    assert result.drift_score > MAX_DRIFT
    assert result.failure_reasons == (REASON_DRIFT,)


def test_edit_depth_adds_capped_drift():
    request = make_request()
    shallow = score_continuity(request, make_panel(edit_depth=0))
    deep = score_continuity(request, make_panel(edit_depth=2))
    deeper = score_continuity(request, make_panel(edit_depth=5))

    assert deep.drift_score > shallow.drift_score
    assert deeper.drift_score == deep.drift_score


def test_missing_panel_fails_with_explicit_reason():
    result = score_continuity(make_request(), None)

    assert result.drift_score == 1.0
    assert result.failure_reasons == (REASON_NO_PRIOR_PANEL,)
    assert result.passed is False


def test_metrics_are_deterministic_over_fixtures():
    first = [score_continuity(req, panel) for req, _, panel in load_fixture_pairs()]
    second = [score_continuity(req, panel) for req, _, panel in load_fixture_pairs()]

    assert first == second


def test_unsafe_reuse_requires_cached_route_and_failed_gates():
    failing = score_continuity(make_request(characters=("stranger",)), make_panel())
    passing = score_continuity(make_request(), make_panel())

    assert is_unsafe_reuse(make_decision(ROUTE_RETURN_CACHED), failing) is True
    assert is_unsafe_reuse(make_decision(ROUTE_RETURN_CACHED), passing) is False
    assert is_unsafe_reuse(make_decision(ROUTE_FRESH), failing) is False


def test_fixture_cached_routes_all_pass_continuity_gates():
    for req, decision, panel in load_fixture_pairs():
        if decision.route == ROUTE_RETURN_CACHED:
            result = score_continuity(req, panel)
            assert result.passed is True, req.request_id
