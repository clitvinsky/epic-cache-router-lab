"""Continuity metrics for judging whether reuse of a prior panel is safe.

The router decides what to do; these metrics explain how much continuity risk
a matched prior panel carries. They are deliberately simple set and token
comparisons so every score is inspectable. A production system could swap in
embedding-based scores behind the same result shape.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import CacheDecision, ContinuityMetricResult, PanelRequest, PriorPanel
from .router import ROUTE_RETURN_CACHED

IDENTITY_THRESHOLD = 0.95
LOCATION_THRESHOLD = 0.90
MAX_DRIFT = 0.25

# Weighted penalty per changed continuity dimension. Set-valued dimensions are
# penalized in proportion to how much of the set changed.
DRIFT_WEIGHTS = {
    "characters": 0.30,
    "location": 0.20,
    "camera": 0.12,
    "action": 0.12,
    "props": 0.10,
    "style": 0.08,
}
EDIT_DEPTH_PENALTY = 0.04
MAX_EDIT_DEPTH_PENALTY = 0.08

REASON_NO_PRIOR_PANEL = "no_prior_panel"
REASON_IDENTITY = "identity_below_threshold"
REASON_LOCATION = "location_below_threshold"
REASON_DRIFT = "drift_above_threshold"


def score_continuity(request: PanelRequest, panel: PriorPanel | None) -> ContinuityMetricResult:
    """Score continuity between a request and its matched prior panel."""
    if panel is None:
        return ContinuityMetricResult(
            request_id=request.request_id,
            identity_score=0.0,
            prop_score=0.0,
            location_score=0.0,
            prompt_score=0.0,
            drift_score=1.0,
            passed=False,
            failure_reasons=(REASON_NO_PRIOR_PANEL,),
        )

    identity = _overlap(request.characters, panel.characters)
    props = _overlap(request.props, panel.props)
    location = 1.0 if _normalized(request.location) == _normalized(panel.location) else 0.0
    prompt = _jaccard(_tokens(request.prompt), _tokens(panel.prompt))
    drift = _drift_score(request, panel, identity, props, location)

    failures = _failure_reasons(identity, location, drift)
    return ContinuityMetricResult(
        request_id=request.request_id,
        identity_score=identity,
        prop_score=props,
        location_score=location,
        prompt_score=prompt,
        drift_score=drift,
        passed=not failures,
        failure_reasons=failures,
    )


def is_unsafe_reuse(decision: CacheDecision, result: ContinuityMetricResult) -> bool:
    """Direct reuse is unsafe when the continuity gates fail for that request."""
    return decision.route == ROUTE_RETURN_CACHED and not result.passed


def _drift_score(
    request: PanelRequest,
    panel: PriorPanel,
    identity: float,
    props: float,
    location: float,
) -> float:
    style = _overlap(request.continuity_tags, panel.continuity_tags)
    drift = (
        DRIFT_WEIGHTS["characters"] * (1.0 - identity)
        + DRIFT_WEIGHTS["location"] * (1.0 - location)
        + DRIFT_WEIGHTS["camera"] * (0.0 if request.camera == panel.camera else 1.0)
        + DRIFT_WEIGHTS["action"] * (0.0 if request.action == panel.action else 1.0)
        + DRIFT_WEIGHTS["props"] * (1.0 - props)
        + DRIFT_WEIGHTS["style"] * (1.0 - style)
        + min(panel.edit_depth * EDIT_DEPTH_PENALTY, MAX_EDIT_DEPTH_PENALTY)
    )
    return min(1.0, drift)


def _failure_reasons(identity: float, location: float, drift: float) -> tuple[str, ...]:
    reasons = []
    if identity < IDENTITY_THRESHOLD:
        reasons.append(REASON_IDENTITY)
    if location < LOCATION_THRESHOLD:
        reasons.append(REASON_LOCATION)
    if drift > MAX_DRIFT:
        reasons.append(REASON_DRIFT)
    return tuple(reasons)


def _normalized(value: str) -> str:
    return value.strip().lower()


def _tokens(text: str) -> set[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return {tok for tok in cleaned.split() if len(tok) > 2}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _overlap(left: Iterable[str], right: Iterable[str]) -> float:
    lset = set(left)
    rset = set(right)
    if not lset and not rset:
        return 1.0
    if not lset or not rset:
        return 0.0
    return len(lset & rset) / len(lset | rset)
