"""Deterministic required-fact and ten-criterion qualification rules."""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    CriterionOutcome,
    Frequency,
    QualificationDecision,
    QualificationResult,
    UNKNOWN,
    WorkflowCase,
)

REQUIRED_FACT_LABELS: tuple[tuple[str, str], ...] = (
    ("workflow_owner", "workflow owner"),
    ("primary_user", "primary user"),
    ("trigger", "trigger"),
    ("inputs", "input"),
    ("outputs", "output"),
    ("frequency", "frequency"),
    ("business_consequence", "consequence"),
    ("current_tools", "current tools"),
    ("known_exceptions", "at least one exception"),
)

CLARIFICATION_QUESTIONS: dict[str, str] = {
    "workflow owner": "Who is accountable for this workflow and its outcome?",
    "primary user": "Which role performs this workflow most often?",
    "trigger": "What exact event starts the workflow?",
    "input": "What information, file or request enters the workflow?",
    "output": "What result must the workflow produce?",
    "frequency": "How often does this workflow occur?",
    "consequence": "What measurable delay, error, service, revenue or audit impact occurs today?",
    "current tools": "Which tools are used in the current process?",
    "at least one exception": "What is the most common exception or failure case?",
}


class QualificationBlocked(ValueError):
    """Raised when deterministic qualification cannot yet proceed."""


def _is_unknown_text(value: str) -> bool:
    return not value.strip() or value.strip().upper() == UNKNOWN


def _list_missing(values: Iterable[str]) -> bool:
    return not any(
        str(value).strip() and str(value).strip().upper() != UNKNOWN for value in values
    )


def missing_required_facts(case: WorkflowCase) -> list[str]:
    """Return missing required facts in fixed business-priority order."""
    missing: list[str] = []
    for field_name, label in REQUIRED_FACT_LABELS:
        value = getattr(case, field_name)
        if isinstance(value, str) and _is_unknown_text(value):
            missing.append(label)
        elif isinstance(value, Frequency) and value == Frequency.UNKNOWN:
            missing.append(label)
        elif isinstance(value, list) and _list_missing(value):
            missing.append(label)
    return missing


def highest_value_clarification(case: WorkflowCase) -> str | None:
    """Ask exactly one deterministic clarification question."""
    missing = missing_required_facts(case)
    return CLARIFICATION_QUESTIONS[missing[0]] if missing else None


def is_vague_ai_request(case: WorkflowCase) -> bool:
    text = case.workflow_narrative.casefold()
    broad_phrases = (
        "automate my company",
        "ai transformation",
        "reduce headcount",
        "replace all staff",
        "use ai everywhere",
    )
    return any(phrase in text for phrase in broad_phrases)


def _yes_no_unknown(condition: bool | None) -> CriterionOutcome:
    if condition is None:
        return CriterionOutcome.UNKNOWN
    return CriterionOutcome.YES if condition else CriterionOutcome.NO


def qualify_case(case: WorkflowCase, *, facts_confirmed: bool) -> QualificationResult:
    """Run the fixed ten-criterion qualification without model discretion."""
    if not facts_confirmed:
        raise QualificationBlocked(
            "Human fact confirmation is required before qualification"
        )

    if is_vague_ai_request(case):
        criteria = {
            "repeated_pain": CriterionOutcome.NO,
            "frequency": CriterionOutcome.UNKNOWN,
            "volume": CriterionOutcome.UNKNOWN,
            "named_workflow_owner": CriterionOutcome.UNKNOWN,
            "business_impact": CriterionOutcome.UNKNOWN,
            "sample_evidence": CriterionOutcome.NO,
            "budget_signal": case.budget_signal,
            "timeline": CriterionOutcome.UNKNOWN,
            "narrow_mvp_fit": CriterionOutcome.NO,
            "supportability": CriterionOutcome.UNKNOWN,
        }
        return _build_result(criteria)

    missing = missing_required_facts(case)
    if missing:
        raise QualificationBlocked(f"Required facts missing: {', '.join(missing)}")

    repeated = case.frequency in {Frequency.DAILY, Frequency.WEEKLY, Frequency.MONTHLY}
    criteria = {
        "repeated_pain": _yes_no_unknown(repeated),
        "frequency": _yes_no_unknown(repeated),
        "volume": (
            CriterionOutcome.UNKNOWN
            if case.monthly_volume is None
            else _yes_no_unknown(case.monthly_volume >= 4)
        ),
        "named_workflow_owner": _yes_no_unknown(
            not _is_unknown_text(case.workflow_owner)
        ),
        "business_impact": _yes_no_unknown(
            not _is_unknown_text(case.business_consequence)
        ),
        "sample_evidence": _yes_no_unknown(not _list_missing(case.sample_evidence)),
        "budget_signal": case.budget_signal,
        "timeline": _yes_no_unknown(not _is_unknown_text(case.timeline)),
        "narrow_mvp_fit": case.narrow_mvp_fit,
        "supportability": case.supportability,
    }
    return _build_result(criteria)


def _build_result(criteria: dict[str, CriterionOutcome]) -> QualificationResult:
    score = sum(value == CriterionOutcome.YES for value in criteria.values())
    decision = (
        QualificationDecision.MVP_CANDIDATE
        if score >= 8
        else QualificationDecision.DIAGNOSTIC_ONLY
        if score >= 5
        else QualificationDecision.NOT_QUALIFIED
    )
    missing = [
        name for name, value in criteria.items() if value == CriterionOutcome.UNKNOWN
    ]
    return QualificationResult(
        criteria=criteria,
        score=score,
        decision=decision,
        missing_evidence=missing,
        explanation=(
            f"{score}/10 criteria are YES. Deterministic band: {decision.value}. "
            "This is a prototype decision aid, not market validation."
        ),
    )


def reconcile_advisory_score(
    authoritative: QualificationResult,
    advisory_score: int | None,
) -> QualificationResult:
    """Preserve the deterministic result when an advisory system disagrees."""
    _ = advisory_score
    return authoritative
