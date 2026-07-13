from __future__ import annotations

from pathlib import Path

from epic_cache_router_lab.evals import evaluate
from epic_cache_router_lab.report import render_report


ROOT = Path(__file__).resolve().parents[1]


def fixture_report() -> str:
    return render_report(
        evaluate(ROOT / "fixtures" / "prior_panels.json", ROOT / "fixtures" / "requests.json")
    )


def test_report_contains_all_sections():
    markdown = fixture_report()

    for heading in (
        "# Cache Router Eval Report",
        "## Summary",
        "## Cost Avoidance",
        "## Route Distribution",
        "## Per-Request Decisions",
        "## How To Read This",
    ):
        assert heading in markdown


def test_report_has_one_row_per_request():
    markdown = fixture_report()
    request_rows = [line for line in markdown.splitlines() if line.startswith("| r0")]

    assert len(request_rows) == 24


def test_report_flags_review_requests():
    markdown = fixture_report()
    review_rows = [
        line
        for line in markdown.splitlines()
        if line.startswith("| r0") and "| yes |" in line
    ]

    # Three manual_review fixtures plus three flagged identity_locked_regen chains.
    assert len(review_rows) == 6
    assert all("manual_review" in row or "identity_locked_regen" in row for row in review_rows)


def test_report_is_deterministic():
    assert fixture_report() == fixture_report()


def test_committed_sample_report_is_current():
    """The committed sample must match what the fixtures actually produce."""
    sample = (ROOT / "docs" / "sample_eval_report.md").read_text()

    assert sample == fixture_report()
