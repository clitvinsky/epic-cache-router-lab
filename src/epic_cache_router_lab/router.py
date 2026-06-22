"""Deterministic cache router for synthetic long-form visual generation fixtures."""

from __future__ import annotations

from collections.abc import Iterable

from .models import CacheDecision, PanelRequest, PriorPanel


ROUTE_RETURN_CACHED = "return_cached"
ROUTE_SURGICAL_EDIT = "surgical_edit"
ROUTE_CAMERA_OR_POSE = "camera_or_pose_change"
ROUTE_IDENTITY_LOCKED_REGEN = "identity_locked_regen"
ROUTE_FRESH = "fresh_generation"
ROUTE_MANUAL_REVIEW = "manual_review"


class CacheRouter:
    """Explainable router for cache reuse and continuity decisions.

    This class deliberately uses simple, inspectable scoring. The point of the
    public lab is the decision contract and safety gates, not a proprietary
    embedding model.
    """

    def __init__(
        self,
        prior_panels: Iterable[PriorPanel],
        *,
        reuse_threshold: float = 0.86,
        review_threshold: float = 0.62,
        max_edit_depth: int = 1,
    ):
        self.prior_panels = tuple(p for p in prior_panels if p.accepted)
        self.reuse_threshold = reuse_threshold
        self.review_threshold = review_threshold
        self.max_edit_depth = max_edit_depth

    def route(self, request: PanelRequest) -> CacheDecision:
        candidate, similarity = self._nearest(request)
        if candidate is None:
            return CacheDecision(
                request_id=request.request_id,
                route=ROUTE_FRESH,
                matched_panel_id=None,
                similarity=0.0,
                safety_score=0.0,
                rationale="No accepted prior panel was available.",
            )

        flags = self._risk_flags(request, candidate)
        safety = self._safety_score(request, candidate, similarity, flags)
        matched = candidate.panel_id

        if "character_mismatch" in flags or "location_mismatch" in flags:
            return CacheDecision(
                request_id=request.request_id,
                route=ROUTE_FRESH,
                matched_panel_id=matched,
                similarity=similarity,
                safety_score=safety,
                rationale="Prior panel is similar, but core continuity metadata differs.",
                risk_flags=tuple(flags),
            )

        if candidate.edit_depth >= self.max_edit_depth and flags:
            return CacheDecision(
                request_id=request.request_id,
                route=ROUTE_IDENTITY_LOCKED_REGEN,
                matched_panel_id=matched,
                similarity=similarity,
                safety_score=safety,
                rationale="Prior panel is useful context, but the edit chain is already deep.",
                risk_flags=tuple(flags + ["edit_depth_limit"]),
            )

        if not flags and safety >= self.reuse_threshold:
            return CacheDecision(
                request_id=request.request_id,
                route=ROUTE_RETURN_CACHED,
                matched_panel_id=matched,
                similarity=similarity,
                safety_score=safety,
                rationale="High-similarity prior panel with matching continuity metadata.",
                avoided_generation=True,
            )

        if "camera_changed" in flags or "action_changed" in flags:
            route = ROUTE_CAMERA_OR_POSE
            rationale = "Camera or action changed enough to avoid direct reuse."
        elif "prop_changed" in flags or "style_changed" in flags:
            route = ROUTE_SURGICAL_EDIT
            rationale = "Prior panel is close, but a localized visual change is needed."
        elif safety >= self.review_threshold:
            route = ROUTE_MANUAL_REVIEW
            rationale = "Candidate is plausible but should be reviewed before reuse."
        else:
            route = ROUTE_IDENTITY_LOCKED_REGEN
            rationale = "Similarity is useful, but safety is too low for reuse."

        return CacheDecision(
            request_id=request.request_id,
            route=route,
            matched_panel_id=matched,
            similarity=similarity,
            safety_score=safety,
            rationale=rationale,
            risk_flags=tuple(flags),
            avoided_generation=route in {ROUTE_SURGICAL_EDIT, ROUTE_CAMERA_OR_POSE},
        )

    def _nearest(self, request: PanelRequest) -> tuple[PriorPanel | None, float]:
        best: PriorPanel | None = None
        best_score = -1.0
        for panel in self.prior_panels:
            score = self._similarity(request, panel)
            if score > best_score:
                best = panel
                best_score = score
        return best, max(best_score, 0.0)

    def _similarity(self, request: PanelRequest, panel: PriorPanel) -> float:
        prompt_score = _jaccard(_tokens(request.prompt), _tokens(panel.prompt))
        metadata_score = (
            0.25 * _set_match(request.characters, panel.characters)
            + 0.20 * _exact(request.location, panel.location)
            + 0.15 * _exact(request.camera, panel.camera)
            + 0.15 * _exact(request.action, panel.action)
            + 0.15 * _set_match(request.props, panel.props)
            + 0.10 * _set_match(request.continuity_tags, panel.continuity_tags)
        )
        return 0.42 * prompt_score + 0.58 * metadata_score

    def _risk_flags(self, request: PanelRequest, panel: PriorPanel) -> list[str]:
        flags: list[str] = []
        if set(request.characters) != set(panel.characters):
            flags.append("character_mismatch")
        if request.location != panel.location:
            flags.append("location_mismatch")
        if request.camera != panel.camera:
            flags.append("camera_changed")
        if request.action != panel.action:
            flags.append("action_changed")
        if set(request.props) != set(panel.props):
            flags.append("prop_changed")
        if set(request.continuity_tags) != set(panel.continuity_tags):
            flags.append("style_changed")
        return flags

    def _safety_score(
        self,
        request: PanelRequest,
        panel: PriorPanel,
        similarity: float,
        flags: list[str],
    ) -> float:
        score = similarity
        penalties = {
            "character_mismatch": 0.45,
            "location_mismatch": 0.28,
            "camera_changed": 0.16,
            "action_changed": 0.18,
            "prop_changed": 0.10,
            "style_changed": 0.08,
        }
        for flag in flags:
            score -= penalties.get(flag, 0.05)
        if panel.edit_depth >= self.max_edit_depth:
            score -= 0.08
        if not request.prompt.strip():
            score -= 0.25
        return max(0.0, min(1.0, score))


def _tokens(text: str) -> set[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return {tok for tok in cleaned.split() if len(tok) > 2}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _set_match(left: Iterable[str], right: Iterable[str]) -> float:
    lset = set(left)
    rset = set(right)
    if not lset and not rset:
        return 1.0
    if not lset or not rset:
        return 0.0
    return len(lset & rset) / len(lset | rset)


def _exact(left: str, right: str) -> float:
    return 1.0 if left == right else 0.0

