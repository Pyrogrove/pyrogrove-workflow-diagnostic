"""Tests for the bounded live DeepSeek reviewer adapter."""

from __future__ import annotations

import json
from unittest.mock import Mock

import pytest
import requests

from src.pyrogrove_diagnostic import deepseek_reviewer
from src.pyrogrove_diagnostic.deepseek_reviewer import (
    DEEPSEEK_ENDPOINT,
    DEEPSEEK_MODEL,
    DeepSeekReviewer,
)
from src.pyrogrove_diagnostic.models import (
    LiveReviewDecision,
    LiveReviewResponse,
    ReviewerMode,
    WorkflowStatus,
)
from src.pyrogrove_diagnostic.recommendation import MockSolutionArchitect
from src.pyrogrove_diagnostic.reviewer import MockReviewer
from src.pyrogrove_diagnostic.state_machine import DiagnosticSession
from src.pyrogrove_diagnostic.synthetic_cases import get_synthetic_case


def test_live_reviewer_imports_shared_models_schema() -> None:
    assert deepseek_reviewer.LiveReviewDecision is LiveReviewDecision
    assert deepseek_reviewer.LiveReviewResponse is LiveReviewResponse


def _review_session() -> DiagnosticSession:
    session = DiagnosticSession(get_synthetic_case("CASE-01"))
    session.start_discovery()
    session.confirm_and_qualify()
    session.draft_recommendation(MockSolutionArchitect())
    return session


def _api_response(content: str) -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


def _reviewer(
    session: DiagnosticSession,
    api_key: str | None = "test-key",
) -> DeepSeekReviewer:
    assert session.qualification is not None
    return DeepSeekReviewer(api_key=api_key, qualification=session.qualification)


def test_valid_pass_response_routes_ready_for_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    mock_review = Mock(side_effect=AssertionError("mock fallback invoked"))
    monkeypatch.setattr(MockReviewer, "review", mock_review)
    result = {
        "decision": "PASS",
        "severity": "NONE",
        "finding": "No material finding.",
        "recommended_change": "",
    }
    post = Mock(return_value=_api_response(json.dumps(result)))
    monkeypatch.setattr(requests, "post", post)

    reviewer = _reviewer(session)
    session.run_review(reviewer, mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.READY_FOR_APPROVAL
    assert session.findings == []
    assert reviewer.last_result is not None
    assert reviewer.last_result.decision.value == "PASS"
    mock_review.assert_not_called()
    review_events = [
        event
        for event in session.audit.events
        if event.action in {"START_REVIEW", "REVIEW_COMPLETE"}
    ]
    assert [event.actor for event in review_events] == [
        "DeepSeekReviewer",
        "DeepSeekReviewer",
    ]
    post.assert_called_once()
    call = post.call_args
    assert call.args == (DEEPSEEK_ENDPOINT,)
    assert call.kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert call.kwargs["json"]["model"] == DEEPSEEK_MODEL
    assert call.kwargs["json"]["temperature"] == 0
    assert call.kwargs["json"]["max_tokens"] == 1000
    assert call.kwargs["json"]["thinking"] == {"type": "disabled"}
    assert call.kwargs["json"]["response_format"] == {"type": "json_object"}
    assert call.kwargs["timeout"] == 20
    prompt = call.kwargs["json"]["messages"][0]["content"]
    assert '"decision": "PASS"' in prompt
    assert "responsible human owner" in prompt


def test_empty_first_response_retries_once_and_valid_second_response_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    result = {
        "decision": "PASS",
        "severity": "NONE",
        "finding": "No material finding.",
        "recommended_change": "",
    }
    post = Mock(
        side_effect=[
            _api_response(""),
            _api_response(json.dumps(result)),
        ]
    )
    monkeypatch.setattr(requests, "post", post)

    reviewer = _reviewer(session)
    session.run_review(reviewer, mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.READY_FOR_APPROVAL
    assert reviewer.last_result is not None
    assert post.call_count == 2
    first_message = post.call_args_list[0].kwargs["json"]["messages"][-1]["content"]
    second_message = post.call_args_list[1].kwargs["json"]["messages"][-1]["content"]
    retry_instruction = (
        "Return the required JSON object now. Do not return analysis, Markdown, "
        "or empty content."
    )
    assert retry_instruction not in first_message
    assert second_message.endswith(retry_instruction)


def test_two_empty_responses_fail_safely_after_one_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    post = Mock(side_effect=[_api_response(""), _api_response("")])
    monkeypatch.setattr(requests, "post", post)

    session.run_review(_reviewer(session), mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.FAILED
    assert not session.can_approve
    assert post.call_count == 2
    assert "empty content after retry" in (session.failure_reason or "")


def test_valid_revision_required_response_routes_revision_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    mock_review = Mock(side_effect=AssertionError("mock fallback invoked"))
    monkeypatch.setattr(MockReviewer, "review", mock_review)
    result = {
        "decision": "REVISION_REQUIRED",
        "severity": "HIGH",
        "finding": "Responsible human owner is not explicit.",
        "recommended_change": "Name the responsible human owner.",
    }
    monkeypatch.setattr(
        requests,
        "post",
        Mock(return_value=_api_response(json.dumps(result))),
    )

    reviewer = _reviewer(session)
    session.run_review(reviewer, mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.REVISION_REQUIRED
    assert len(session.findings) == 1
    assert session.findings[0].severity.value == "HIGH"
    assert session.findings[0].recommended_correction == result["recommended_change"]
    mock_review.assert_not_called()
    assert session.audit.events[-2].actor == "DeepSeekReviewer"
    assert session.audit.events[-2].action == "START_REVIEW"
    assert session.audit.events[-1].actor == "DeepSeekReviewer"
    assert session.audit.events[-1].action == "RAISE_MATERIAL_FINDING"


def test_revision_required_after_one_revision_routes_human_adjudication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    mock_review = Mock(side_effect=AssertionError("mock fallback invoked"))
    monkeypatch.setattr(MockReviewer, "review", mock_review)
    result = {
        "decision": "REVISION_REQUIRED",
        "severity": "HIGH",
        "finding": "Responsible human owner remains unclear.",
        "recommended_change": "Name the responsible human owner.",
    }
    post = Mock(return_value=_api_response(json.dumps(result)))
    monkeypatch.setattr(requests, "post", post)

    session.run_review(_reviewer(session), mode=ReviewerMode.LIVE_DEEPSEEK)
    session.revise_once()
    session.run_review(_reviewer(session), mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.revision_count == 1
    assert session.status == WorkflowStatus.MANUAL_REVIEW
    assert session.findings[0].resolution_status.value == "HUMAN_ADJUDICATION"
    assert post.call_count == 2
    mock_review.assert_not_called()
    assert session.audit.events[-1].actor == "DeepSeekReviewer"
    assert session.audit.events[-1].action == "ESCALATE_AFTER_MAX_REVISION"


def test_missing_api_key_fails_without_http_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    post = Mock()
    monkeypatch.setattr(requests, "post", post)

    session.run_review(
        _reviewer(session, api_key=None), mode=ReviewerMode.LIVE_DEEPSEEK
    )

    assert session.status == WorkflowStatus.FAILED
    assert not session.can_approve
    assert "DEEPSEEK_API_KEY" in (session.failure_reason or "")
    post.assert_not_called()


def test_timeout_fails_safely_without_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _review_session()
    post = Mock(side_effect=requests.Timeout("timed out"))
    monkeypatch.setattr(requests, "post", post)

    session.run_review(_reviewer(session), mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.FAILED
    assert not session.can_approve
    assert post.call_count == 1


def test_malformed_json_after_one_retry_fails_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    post = Mock(
        side_effect=[
            _api_response("not JSON"),
            _api_response("still not JSON"),
        ]
    )
    monkeypatch.setattr(requests, "post", post)

    session.run_review(_reviewer(session), mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.FAILED
    assert not session.can_approve
    assert post.call_count == 2
    assert "malformed JSON after retry" in (session.failure_reason or "")


def test_extra_json_field_is_rejected_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    result = {
        "decision": "PASS",
        "severity": "NONE",
        "finding": "No material finding.",
        "recommended_change": "",
        "unexpected": "not permitted",
    }
    post = Mock(return_value=_api_response(json.dumps(result)))
    monkeypatch.setattr(requests, "post", post)

    session.run_review(_reviewer(session), mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.FAILED
    assert not session.can_approve
    assert post.call_count == 1
    assert "schema validation" in (session.failure_reason or "")


def test_live_mode_never_falls_back_to_mock_reviewer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _review_session()
    mock_review = Mock(side_effect=AssertionError("mock fallback invoked"))
    monkeypatch.setattr(MockReviewer, "review", mock_review)
    monkeypatch.setattr(
        requests,
        "post",
        Mock(side_effect=requests.ConnectionError("offline")),
    )

    session.run_review(_reviewer(session), mode=ReviewerMode.LIVE_DEEPSEEK)

    assert session.status == WorkflowStatus.FAILED
    assert not session.can_approve
    mock_review.assert_not_called()
