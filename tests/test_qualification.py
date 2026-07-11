from __future__ import annotations

import pytest

from src.pyrogrove_diagnostic.models import (
    CriterionOutcome,
    QualificationDecision,
    UNKNOWN,
)
from src.pyrogrove_diagnostic.qualification import (
    QualificationBlocked,
    highest_value_clarification,
    missing_required_facts,
    qualify_case,
)
from src.pyrogrove_diagnostic.synthetic_cases import get_synthetic_case


def test_complete_case_scores_ten_and_is_mvp_candidate() -> None:
    case = get_synthetic_case("CASE-01")

    result = qualify_case(case, facts_confirmed=True)

    assert result.score == 10
    assert result.decision == QualificationDecision.MVP_CANDIDATE
    assert all(value == CriterionOutcome.YES for value in result.criteria.values())


def test_missing_owner_blocks_qualification_and_asks_one_question() -> None:
    case = get_synthetic_case("CASE-02")

    assert missing_required_facts(case)[0] == "workflow owner"
    assert (
        highest_value_clarification(case)
        == "Who is accountable for this workflow and its outcome?"
    )
    with pytest.raises(QualificationBlocked):
        qualify_case(case, facts_confirmed=True)


def test_human_confirmation_is_mandatory() -> None:
    with pytest.raises(QualificationBlocked, match="Human fact confirmation"):
        qualify_case(get_synthetic_case("CASE-01"), facts_confirmed=False)


def test_vague_ai_request_is_not_qualified_without_invented_facts() -> None:
    case = get_synthetic_case("CASE-03")

    result = qualify_case(case, facts_confirmed=True)

    assert result.decision == QualificationDecision.NOT_QUALIFIED
    assert result.score == 0
    assert case.workflow_owner == UNKNOWN
    assert result.criteria["volume"] == CriterionOutcome.UNKNOWN
