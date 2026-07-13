"""Typed data models for the public cache-router lab."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PriorPanel:
    """Metadata for a previously generated panel.

    The public lab stores metadata only, not generated images. A production
    system could attach image paths, embeddings, provider traces, and review
    state behind the same shape.
    """

    panel_id: str
    prompt: str
    characters: tuple[str, ...]
    location: str
    camera: str
    action: str
    props: tuple[str, ...] = ()
    continuity_tags: tuple[str, ...] = ()
    accepted: bool = True
    edit_depth: int = 0

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PriorPanel":
        return cls(
            panel_id=str(raw["panel_id"]),
            prompt=str(raw["prompt"]),
            characters=tuple(raw.get("characters", ())),
            location=str(raw.get("location", "")),
            camera=str(raw.get("camera", "")),
            action=str(raw.get("action", "")),
            props=tuple(raw.get("props", ())),
            continuity_tags=tuple(raw.get("continuity_tags", ())),
            accepted=bool(raw.get("accepted", True)),
            edit_depth=int(raw.get("edit_depth", 0)),
        )


@dataclass(frozen=True)
class PanelRequest:
    """Incoming generation or edit request."""

    request_id: str
    prompt: str
    characters: tuple[str, ...]
    location: str
    camera: str
    action: str
    props: tuple[str, ...] = ()
    continuity_tags: tuple[str, ...] = ()
    expected_route: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PanelRequest":
        return cls(
            request_id=str(raw["request_id"]),
            prompt=str(raw["prompt"]),
            characters=tuple(raw.get("characters", ())),
            location=str(raw.get("location", "")),
            camera=str(raw.get("camera", "")),
            action=str(raw.get("action", "")),
            props=tuple(raw.get("props", ())),
            continuity_tags=tuple(raw.get("continuity_tags", ())),
            expected_route=raw.get("expected_route"),
        )


@dataclass(frozen=True)
class GenerationPlan:
    """Diffusion-aware execution plan derived from a routing decision.

    Cost and latency values are normalized planning estimates, not vendor
    pricing or measured model timings.
    """

    request_id: str
    route: str
    generation_mode: str
    starting_point: str
    matched_panel_id: str | None
    requires_model_call: bool
    requires_review: bool
    estimated_steps: int
    estimated_cost_units: float
    estimated_latency_ms: int
    risk_flags: tuple[str, ...] = field(default_factory=tuple)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "route": self.route,
            "generation_mode": self.generation_mode,
            "starting_point": self.starting_point,
            "matched_panel_id": self.matched_panel_id,
            "requires_model_call": self.requires_model_call,
            "requires_review": self.requires_review,
            "estimated_steps": self.estimated_steps,
            "estimated_cost_units": round(self.estimated_cost_units, 3),
            "estimated_latency_ms": self.estimated_latency_ms,
            "risk_flags": list(self.risk_flags),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class CacheDecision:
    """Explainable router output."""

    request_id: str
    route: str
    matched_panel_id: str | None
    similarity: float
    safety_score: float
    rationale: str
    risk_flags: tuple[str, ...] = field(default_factory=tuple)
    avoided_generation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "route": self.route,
            "matched_panel_id": self.matched_panel_id,
            "similarity": round(self.similarity, 3),
            "safety_score": round(self.safety_score, 3),
            "rationale": self.rationale,
            "risk_flags": list(self.risk_flags),
            "avoided_generation": self.avoided_generation,
            "metadata": self.metadata,
        }

