from __future__ import annotations

import pytest

from src.pyrogrove_diagnostic.models import ReviewerMode, WorkflowStatus
from src.pyrogrove_diagnostic.recommendation import MockSolutionArchitect
from src.pyrogrove_diagnostic.reviewer import MockReviewer
from src.pyrogrove_diagnostic.state_machine import DiagnosticSession, InvalidTransition
from src.pyrogrove_diagnostic.synthetic_cases import get_synthetic_case


def qualified_session() -> DiagnosticSession:
    session = DiagnosticSession(get_synthetic_case("CASE-01"))
    session.start_discovery()
    session.confirm_and_qualify()
    session.draft_recommendation(MockSolutionArchitect())
    return session


def ready_session(mode: ReviewerMode = ReviewerMode.NORMAL) -> DiagnosticSession:
    session = qualified_session()
    session.run_review(MockReviewer(), mode=mode)
    return session


def test_high_once_triggers_exactly_one_revision_then_ready_for_approval() -> None:
    session = ready_session(ReviewerMode.HIGH_ONCE)
    assert session.status == WorkflowStatus.REVISION_REQUIRED

    session.revise_once()
    session.run_review(MockReviewer(), mode=ReviewerMode.HIGH_ONCE)

    assert session.revision_count == 1
    assert session.status == WorkflowStatus.READY_FOR_APPROVAL
    assert any(
        "manual fallback" in step.casefold()
        for step in session.recommendation.deterministic_steps
    )


def test_persistent_high_after_one_revision_requires_human_adjudication() -> None:
    session = ready_session(ReviewerMode.HIGH_ALWAYS)
    session.revise_once()
    session.run_review(MockReviewer(), mode=ReviewerMode.HIGH_ALWAYS)

    assert session.revision_count == 1
    assert session.status == WorkflowStatus.MANUAL_REVIEW
    assert not session.can_approve


def test_approval_cannot_be_bypassed() -> None:
    session = qualified_session()

    with pytest.raises(InvalidTransition, match="cannot be bypassed"):
        session.approve()


def test_human_approve_and_reject_write_audit_events() -> None:
    approved = ready_session()
    approved.approve()
    assert approved.status == WorkflowStatus.APPROVED
    assert approved.audit.events[-1].action == "APPROVE_REPORT"

    rejected = ready_session()
    rejected.reject("Not suitable")
    assert rejected.status == WorkflowStatus.REJECTED
    assert rejected.audit.events[-1].action == "REJECT_REPORT"
