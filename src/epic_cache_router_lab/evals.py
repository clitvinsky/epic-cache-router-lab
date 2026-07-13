"""Fixture-based eval runner for the public cache-router lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cost_model import summarize_costs
from .execution_router import plan_all
from .models import PanelRequest, PriorPanel
from .router import CacheRouter


def load_prior_panels(path: Path) -> list[PriorPanel]:
    return [PriorPanel.from_dict(item) for item in json.loads(path.read_text())]


def load_requests(path: Path) -> list[PanelRequest]:
    return [PanelRequest.from_dict(item) for item in json.loads(path.read_text())]


def evaluate(prior_path: Path, requests_path: Path) -> dict:
    router = CacheRouter(load_prior_panels(prior_path))
    requests = load_requests(requests_path)
    decisions = [router.route(req) for req in requests]

    labeled = [d for d, r in zip(decisions, requests) if r.expected_route]
    correct = sum(1 for d, r in zip(decisions, requests) if r.expected_route == d.route)
    avoided = sum(1 for d in decisions if d.avoided_generation)
    unsafe_reuse = sum(1 for d in decisions if d.route == "return_cached" and d.risk_flags)

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
        "cost": cost.to_dict(),
        "decisions": [d.to_dict() for d in decisions],
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
