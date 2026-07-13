from __future__ import annotations

from pathlib import Path

from epic_cache_router_lab.evals import evaluate


ROOT = Path(__file__).resolve().parents[1]


def test_eval_metrics_are_stable():
    report = evaluate(ROOT / "fixtures" / "prior_panels.json", ROOT / "fixtures" / "requests.json")

    assert report["total_requests"] == 24
    assert report["labeled_requests"] == 24
    assert report["route_accuracy"] == 1.0
    assert report["unsafe_reuse_count"] == 0
    assert len(report["decisions"]) == 24


def test_eval_report_includes_continuity_metrics():
    report = evaluate(ROOT / "fixtures" / "prior_panels.json", ROOT / "fixtures" / "requests.json")

    assert len(report["continuity"]) == report["total_requests"]
    assert 0.0 <= report["avg_drift_score"] <= 1.0

    by_request = {entry["request_id"]: entry for entry in report["continuity"]}
    for decision in report["decisions"]:
        result = by_request[decision["request_id"]]
        if decision["route"] == "return_cached":
            assert result["passed"] is True
            assert result["drift_score"] <= 0.25
        if decision["route"] == "fresh_generation":
            assert result["passed"] is False


def test_eval_report_includes_cost_accounting():
    report = evaluate(ROOT / "fixtures" / "prior_panels.json", ROOT / "fixtures" / "requests.json")

    assert sum(report["route_distribution"].values()) == report["total_requests"]
    assert 0.0 <= report["review_rate"] <= 1.0
    assert 0.0 <= report["avg_safety_score"] <= 1.0

    cost = report["cost"]
    assert cost["total_requests"] == report["total_requests"]
    assert cost["model_calls"] + cost["avoided_model_calls"] == cost["total_requests"]
    assert cost["routed_cost_units"] <= cost["baseline_cost_units"]
    assert cost["estimated_savings_ratio"] > 0.0

