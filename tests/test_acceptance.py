"""Executable acceptance tests mapped to AT-001 through AT-015."""

from __future__ import annotations

import inspect

import pytest
from pydantic import ValidationError

from src.pyrogrove_diagnostic.extraction import MockExtractor, MockOutputError
from src.pyrogrove_diagnostic.models import (
    ArchitectureRoute,
    DiagnosticRecommendation,
    QualificationDecision,
    ReviewerMode,
    WorkflowStatus,
)
from src.pyrogrove_diagnostic.qualification import reconcile_advisory_score
from src.pyrogrove_diagnostic.recommendation import MockSolutionArchitect
from src.pyrogrove_diagnostic.report import generate_markdown_report
from src.pyrogrove_diagnostic.reviewer import MockReviewer
from src.pyrogrove_diagnostic.state_machine import DiagnosticSession
from src.pyrogrove_diagnostic.synthetic_cases import get_synthetic_case


def _qualified_session() -> DiagnosticSession:
    session = DiagnosticSession(get_synthetic_case("CASE-01"))
    session.start_discovery()
    session.confirm_and_qualify()
    return session


def _ready_session(mode: ReviewerMode = ReviewerMode.NORMAL) -> DiagnosticSession:
    session = _qualified_session()
    session.draft_recommendation(MockSolutionArchitect())
    session.run_review(MockReviewer(), mode=mode)
    return session


def test_at_001_complete_qualified_workflow_generates_deterministic_draft() -> None:
    session = _qualified_session()
    session.draft_recommendation(MockSolutionArchitect())

    assert session.qualification.score == 10
    assert session.status == WorkflowStatus.ARCHITECTURE_DRAFT
    assert session.recommendation.recommended_route == ArchitectureRoute.M365


def test_at_002_missing_owner_asks_one_question_and_has_no_final_score() -> None:
    session = DiagnosticSession(get_synthetic_case("CASE-02"))
    session.start_discovery()
    session.confirm_and_qualify()

    assert session.status == WorkflowStatus.NEEDS_CLARIFICATION
    assert (
        session.clarification_question
        == "Who is accountable for this workflow and its outcome?"
    )
    assert session.qualification is None


def test_at_003_two_clarification_cycles_exhausted_routes_manual_review() -> None:
    session = DiagnosticSession(get_synthetic_case("CASE-02"))
    session.start_discovery()
    session.case.clarification_count = 2
    session.confirm_and_qualify()

    assert session.status == WorkflowStatus.MANUAL_REVIEW


def test_at_004_vague_ai_request_is_no_build_and_not_qualified() -> None:
    session = DiagnosticSession(get_synthetic_case("CASE-03"))
    session.start_discovery()
    session.confirm_and_qualify()

    assert session.status == WorkflowStatus.NOT_QUALIFIED
    assert session.qualification.decision == QualificationDecision.NOT_QUALIFIED
    assert session.recommendation is None


def test_at_005_extractor_cannot_invent_or_accept_malformed_missing_volume() -> None:
    with pytest.raises(MockOutputError):
        MockExtractor().extract(
            "anything", synthetic_case_id="CASE-01", invalid_output=True
        )


def test_at_006_invalid_architecture_route_fails_schema_validation() -> None:
    valid = (
        MockSolutionArchitect()
        .recommend(
            get_synthetic_case("CASE-01"),
            _qualified_session().qualification,
        )
        .model_dump()
    )
    valid["recommended_route"] = "AUTONOMOUS_AI_PLATFORM"

    with pytest.raises(ValidationError):
        DiagnosticRecommendation.model_validate(valid)


def test_at_007_high_finding_triggers_exactly_one_revision() -> None:
    session = _ready_session(ReviewerMode.HIGH_ONCE)
    session.revise_once()
    session.run_review(MockReviewer(), mode=ReviewerMode.HIGH_ONCE)

    assert session.revision_count == 1
    assert session.status == WorkflowStatus.READY_FOR_APPROVAL


def test_at_008_persistent_high_after_revision_requires_human_adjudication() -> None:
    session = _ready_session(ReviewerMode.HIGH_ALWAYS)
    session.revise_once()
    session.run_review(MockReviewer(), mode=ReviewerMode.HIGH_ALWAYS)

    assert session.status == WorkflowStatus.MANUAL_REVIEW
    assert session.revision_count == 1


def test_at_009_invalid_model_output_fails_and_disables_approval() -> None:
    session = _qualified_session()
    session.draft_recommendation(MockSolutionArchitect(), invalid_output=True)

    assert session.status == WorkflowStatus.FAILED
    assert session.recommendation is None
    assert not session.can_approve
    assert session.audit.events[-1].action == "FAIL_SAFE"


def test_at_010_human_rejects_report_and_audit_is_written() -> None:
    session = _ready_session()
    session.reject()

    assert session.status == WorkflowStatus.REJECTED
    assert session.audit.events[-1].action == "REJECT_REPORT"


def test_at_011_human_approves_and_report_is_downloadable_text() -> None:
    session = _ready_session()
    session.approve()
    report = generate_markdown_report(session)

    assert session.status == WorkflowStatus.APPROVED
    assert report.startswith("# PyroGrove Workflow Diagnostic Report")


def test_at_012_every_consequential_transition_has_audit_evidence() -> None:
    session = _ready_session()
    session.approve()

    transitions = [
        (event.from_status, event.to_status) for event in session.audit.events
    ]
    assert (WorkflowStatus.NEW, WorkflowStatus.DISCOVERY) in transitions
    assert (WorkflowStatus.READY_FOR_APPROVAL, WorkflowStatus.APPROVED) in transitions
    assert all(event.event_id.startswith("AUD-") for event in session.audit.events)


def test_at_013_local_fallback_has_no_mulerun_runtime_dependency() -> None:
    modules = (
        MockExtractor,
        MockSolutionArchitect,
        MockReviewer,
        DiagnosticSession,
    )
    combined_source = "\n".join(
        inspect.getsource(module) for module in modules
    ).casefold()

    assert "import mulerun" not in combined_source
    assert "from mulerun" not in combined_source


def test_at_014_local_report_remains_available_without_deployed_page() -> None:
    session = _ready_session()
    session.approve()

    assert "Audit events" in generate_markdown_report(session)


def test_at_015_deterministic_score_prevails_over_advisory_contradiction() -> None:
    result = _qualified_session().qualification
    reconciled = reconcile_advisory_score(result, advisory_score=0)

    assert reconciled is result
    assert reconciled.score == 10
    assert reconciled.decision == QualificationDecision.MVP_CANDIDATE
