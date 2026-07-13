"""Fixture-based eval runner for the public cache-router lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .continuity_metrics import is_unsafe_reuse, score_continuity
from .cost_model import summarize_costs
from .execution_router import plan_all
from .models import PanelRequest, PriorPanel
from .router import CacheRouter


def load_prior_panels(path: Path) -> list[PriorPanel]:
    return [PriorPanel.from_dict(item) for item in json.loads(path.read_text())]


def load_requests(path: Path) -> list[PanelRequest]:
    return [PanelRequest.from_dict(item) for item in json.loads(path.read_text())]


def evaluate(prior_path: Path, requests_path: Path) -> dict:
    prior_panels = load_prior_panels(prior_path)
    router = CacheRouter(prior_panels)
    requests = load_requests(requests_path)
    decisions = [router.route(req) for req in requests]

    panels_by_id = {panel.panel_id: panel for panel in prior_panels}
    continuity = [
        score_continuity(request, panels_by_id.get(decision.matched_panel_id or ""))
        for decision, request in zip(decisions, requests)
    ]

    labeled = [d for d, r in zip(decisions, requests) if r.expected_route]
    correct = sum(1 for d, r in zip(decisions, requests) if r.expected_route == d.route)
    avoided = sum(1 for d in decisions if d.avoided_generation)
    unsafe_reuse = sum(
        1 for decision, result in zip(decisions, continuity) if is_unsafe_reuse(decision, result)
    )
    matched_results = [
        result for decision, result in zip(decisions, continuity) if decision.matched_panel_id
    ]
    avg_drift = (
        round(sum(r.drift_score for r in matched_results) / len(matched_results), 3)
        if matched_results
        else None
    )

    plans = plan_all(decisions)
    cost = summarize_costs(plans)
    route_distribution = {
        route: sum(1 for d in decisions if d.route == route)
        for route in sorted({d.route for d in decisions})
    }
    avg_safety = (
        round(sum(d.safety_score for d in decisions) / len(decisions), 3) if decisions else None
    )

    return {
        "total_requests": len(requests),
        "labeled_requests": len(labeled),
        "route_accuracy": round(correct / len(labeled), 3) if labeled else None,
        "route_distribution": route_distribution,
        "avoided_generation_count": avoided,
        "unsafe_reuse_count": unsafe_reuse,
        "review_rate": round(cost.review_count / len(requests), 3) if requests else None,
        "avg_safety_score": avg_safety,
        "avg_drift_score": avg_drift,
        "cost": cost.to_dict(),
        "decisions": [d.to_dict() for d in decisions],
        "plans": [plan.to_dict() for plan in plans],
        "continuity": [result.to_dict() for result in continuity],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate synthetic cache-router fixtures.")
    parser.add_argument("prior_panels", type=Path)
    parser.add_argument("requests", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.prior_panels, args.requests), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
