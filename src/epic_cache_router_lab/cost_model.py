"""Cost-avoidance accounting over generation plans.

The baseline assumes every request would run a fresh generation without the
router. Savings are the gap between that baseline and the routed plan costs.
All values are normalized cost units, not vendor pricing.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .models import GenerationPlan

FRESH_GENERATION_COST_UNITS = 1.0


@dataclass(frozen=True)
class CostSummary:
    """Aggregate cost and avoided-generation metrics for a set of plans."""

    total_requests: int
    model_calls: int
    avoided_model_calls: int
    review_count: int
    baseline_cost_units: float
    routed_cost_units: float
    estimated_savings_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "model_calls": self.model_calls,
            "avoided_model_calls": self.avoided_model_calls,
            "review_count": self.review_count,
            "baseline_cost_units": round(self.baseline_cost_units, 3),
            "routed_cost_units": round(self.routed_cost_units, 3),
            "estimated_savings_ratio": round(self.estimated_savings_ratio, 3),
        }


def summarize_costs(plans: Iterable[GenerationPlan]) -> CostSummary:
    """Aggregate baseline-versus-routed cost across generation plans."""
    materialized = tuple(plans)
    total = len(materialized)
    model_calls = sum(1 for plan in materialized if plan.requires_model_call)
    review_count = sum(1 for plan in materialized if plan.requires_review)
    baseline = total * FRESH_GENERATION_COST_UNITS
    routed = sum(plan.estimated_cost_units for plan in materialized)
    savings = (baseline - routed) / baseline if baseline else 0.0

    return CostSummary(
        total_requests=total,
        model_calls=model_calls,
        avoided_model_calls=total - model_calls,
        review_count=review_count,
        baseline_cost_units=baseline,
        routed_cost_units=routed,
        estimated_savings_ratio=savings,
    )
