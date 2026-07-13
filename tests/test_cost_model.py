from __future__ import annotations

import json
from pathlib import Path

from epic_cache_router_lab.cost_model import summarize_costs
from epic_cache_router_lab.execution_router import plan_all, plan_generation
from epic_cache_router_lab.models import CacheDecision, PanelRequest, PriorPanel
from epic_cache_router_lab.router import CacheRouter, ROUTE_FRESH


ROOT = Path(__file__).resolve().parents[1]


def load_fixture_plans():
    prior = [
        PriorPanel.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "prior_panels.json").read_text())
    ]
    requests = [
        PanelRequest.from_dict(item)
        for item in json.loads((ROOT / "fixtures" / "requests.json").read_text())
    ]
    router = CacheRouter(prior)
    return plan_all(router.route(req) for req in requests)


def fresh_decision(request_id: str) -> CacheDecision:
    return CacheDecision(
        request_id=request_id,
        route=ROUTE_FRESH,
        matched_panel_id=None,
        similarity=0.0,
        safety_score=0.0,
        rationale="no prior work",
    )


def test_fixture_plans_report_savings():
    summary = summarize_costs(load_fixture_plans())

    assert summary.total_requests == 5
    assert summary.model_calls == 3
    assert summary.avoided_model_calls == 2
    assert summary.baseline_cost_units == 5.0
    assert summary.routed_cost_units < summary.baseline_cost_units
    assert summary.estimated_savings_ratio > 0.0


def test_all_fresh_generation_reports_zero_savings():
    plans = [plan_generation(fresh_decision(f"r{i}")) for i in range(3)]
    summary = summarize_costs(plans)

    assert summary.model_calls == 3
    assert summary.avoided_model_calls == 0
    assert summary.baseline_cost_units == summary.routed_cost_units
    assert summary.estimated_savings_ratio == 0.0


def test_empty_plan_set_is_safe():
    summary = summarize_costs(())

    assert summary.total_requests == 0
    assert summary.baseline_cost_units == 0.0
    assert summary.routed_cost_units == 0.0
    assert summary.estimated_savings_ratio == 0.0
