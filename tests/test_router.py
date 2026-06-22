from __future__ import annotations

import json
from pathlib import Path

from epic_cache_router_lab.models import PanelRequest, PriorPanel
from epic_cache_router_lab.router import (
    CacheRouter,
    ROUTE_FRESH,
    ROUTE_IDENTITY_LOCKED_REGEN,
    ROUTE_RETURN_CACHED,
    ROUTE_SURGICAL_EDIT,
)


ROOT = Path(__file__).resolve().parents[1]


def load_fixtures():
    prior = [
        PriorPanel.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "prior_panels.json").read_text())
    ]
    requests = [
        PanelRequest.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "requests.json").read_text())
    ]
    return prior, requests


def test_expected_fixture_routes():
    prior, requests = load_fixtures()
    router = CacheRouter(prior)
    decisions = [router.route(req) for req in requests]

    assert [d.route for d in decisions] == [
        ROUTE_RETURN_CACHED,
        ROUTE_SURGICAL_EDIT,
        ROUTE_IDENTITY_LOCKED_REGEN,
        ROUTE_RETURN_CACHED,
        ROUTE_FRESH,
    ]


def test_return_cached_has_no_risk_flags():
    prior, requests = load_fixtures()
    router = CacheRouter(prior)
    decision = router.route(requests[0])

    assert decision.route == ROUTE_RETURN_CACHED
    assert decision.risk_flags == ()
    assert decision.avoided_generation is True


def test_character_mismatch_forces_fresh_generation():
    prior, _ = load_fixtures()
    router = CacheRouter(prior)
    request = PanelRequest(
        request_id="mismatch",
        prompt="Companion stands on the rainlit bridge alone.",
        characters=("companion",),
        location="rainlit_bridge",
        camera="wide",
        action="stand_off",
        props=("glass_tower", "blue_cloak"),
        continuity_tags=("noir_palette", "wet_pavement"),
    )

    decision = router.route(request)

    assert decision.route == ROUTE_FRESH
    assert "character_mismatch" in decision.risk_flags
