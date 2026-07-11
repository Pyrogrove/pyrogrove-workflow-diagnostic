from __future__ import annotations

import pytest

from src.pyrogrove_diagnostic.models import PRACTICE_DISCLOSURE, ReviewerMode
from src.pyrogrove_diagnostic.recommendation import MockSolutionArchitect
from src.pyrogrove_diagnostic.report import (
    AI_SIMULATION_DISCLOSURE,
    generate_markdown_report,
)
from src.pyrogrove_diagnostic.reviewer import MockReviewer
from src.pyrogrove_diagnostic.state_machine import DiagnosticSession, InvalidTransition
from src.pyrogrove_diagnostic.synthetic_cases import get_synthetic_case


def approved_session() -> DiagnosticSession:
    session = DiagnosticSession(get_synthetic_case("CASE-01"))
    session.start_discovery()
    session.confirm_and_qualify()
    session.draft_recommendation(MockSolutionArchitect())
    session.run_review(MockReviewer(), mode=ReviewerMode.NORMAL)
    session.approve()
    return session


def test_approved_report_contains_disclosures_evidence_and_audit() -> None:
    report = generate_markdown_report(approved_session())

    assert PRACTICE_DISCLOSURE in report
    assert AI_SIMULATION_DISCLOSURE in report
    assert "Deterministic qualification" in report
    assert "Human control points" in report
    assert "Audit events" in report
    assert "APPROVE_REPORT" in report


def test_unapproved_report_is_blocked() -> None:
    session = DiagnosticSession(get_synthetic_case("CASE-01"))

    with pytest.raises(InvalidTransition, match="requires human approval"):
        generate_markdown_report(session)
