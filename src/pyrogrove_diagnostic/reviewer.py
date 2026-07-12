"""Deterministic local adapter that simulates an independent Reviewer role."""

from __future__ import annotations

from pydantic import ValidationError

from .extraction import MockOutputError
from .models import (
    DiagnosticRecommendation,
    ResolutionStatus,
    ReviewFinding,
    ReviewerEnvelope,
    ReviewerMode,
    Severity,
    WorkflowCase,
)


class MockReviewer:
    role = "MockReviewer"

    def review(
        self,
        case: WorkflowCase,
        recommendation: DiagnosticRecommendation,
        *,
        mode: ReviewerMode = ReviewerMode.NORMAL,
        revision_count: int = 0,
    ) -> list[ReviewFinding]:
        if mode == ReviewerMode.INVALID:
            raw: dict[str, object] = {
                "role": self.role,
                "findings": [{"finding_id": "BROKEN", "severity": "SEVERE"}],
            }
        else:
            findings = self._deterministic_findings(
                case,
                recommendation,
                mode=mode,
                revision_count=revision_count,
            )
            raw = {
                "role": self.role,
                "findings": [finding.model_dump(mode="json") for finding in findings],
            }
        try:
            envelope = ReviewerEnvelope.model_validate(raw)
        except ValidationError as exc:
            raise MockOutputError(
                "MockReviewer output failed schema validation"
            ) from exc
        return envelope.findings

    @staticmethod
    def _deterministic_findings(
        case: WorkflowCase,
        recommendation: DiagnosticRecommendation,
        *,
        mode: ReviewerMode,
        revision_count: int,
    ) -> list[ReviewFinding]:
        _ = case
        findings: list[ReviewFinding] = []

        force_high = mode == ReviewerMode.HIGH_ALWAYS or (
            mode == ReviewerMode.HIGH_ONCE and revision_count == 0
        )
        if force_high:
            findings.append(
                ReviewFinding(
                    finding_id="RV-001",
                    severity=Severity.HIGH,
                    requirement="Manual fallback and recovery must be explicit.",
                    evidence="The controlled test mode requires a High finding on the first review.",
                    business_impact="An operator may not know how to recover when automated processing fails.",
                    recommended_correction=(
                        "Add an explicit manual fallback step to the deterministic workflow and failure modes."
                    ),
                    resolution_status=ResolutionStatus.OPEN,
                )
            )
        elif not any(
            "manual fallback" in step.casefold()
            for step in recommendation.deterministic_steps
        ):
            findings.append(
                ReviewFinding(
                    finding_id="RV-002",
                    severity=Severity.MEDIUM,
                    requirement="Recovery ownership should be visible.",
                    evidence="The recommendation does not name a manual fallback in deterministic steps.",
                    business_impact="Recovery may depend on undocumented operator knowledge.",
                    recommended_correction="Document the manual fallback before production use.",
                    resolution_status=ResolutionStatus.DEFERRED,
                )
            )
        return findings


def apply_one_revision(
    recommendation: DiagnosticRecommendation,
    findings: list[ReviewFinding],
) -> DiagnosticRecommendation:
    """Apply only the approved bounded correction for open High/Critical findings."""
    material = [
        finding
        for finding in findings
        if finding.severity in {Severity.CRITICAL, Severity.HIGH}
        and finding.resolution_status == ResolutionStatus.OPEN
    ]
    if not material:
        return recommendation

    revised = recommendation.model_copy(deep=True)
    fallback_step = (
        "If automated processing fails, stop, preserve the audit trace and return the case "
        "to the human operator for manual fallback."
    )
    if fallback_step not in revised.deterministic_steps:
        revised.deterministic_steps.append(fallback_step)
    controlled_revision_steps = [
        "If automated processing fails, stop automation and return the case to manual RFQ review.",
        (
            "Preserve the audit trail, notify the workflow owner, correct the failed input "
            "or configuration, and resume only after human approval."
        ),
        (
            "The Operations Manager is the responsible human owner for fallback, recovery "
            "and final release."
        ),
    ]
    for step in controlled_revision_steps:
        if step not in revised.deterministic_steps:
            revised.deterministic_steps.append(step)
    revised.failure_modes.append(
        "Manual fallback preserves the case and audit trace without an external commitment."
    )
    for finding in findings:
        if finding in material:
            finding.resolution_status = ResolutionStatus.RESOLVED
    return revised
