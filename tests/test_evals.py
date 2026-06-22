from __future__ import annotations

from pathlib import Path

from epic_cache_router_lab.evals import evaluate


ROOT = Path(__file__).resolve().parents[1]


def test_eval_metrics_are_stable():
    report = evaluate(ROOT / "fixtures" / "prior_panels.json", ROOT / "fixtures" / "requests.json")

    assert report["total_requests"] == 5
    assert report["labeled_requests"] == 5
    assert report["route_accuracy"] == 1.0
    assert report["unsafe_reuse_count"] == 0
    assert len(report["decisions"]) == 5

