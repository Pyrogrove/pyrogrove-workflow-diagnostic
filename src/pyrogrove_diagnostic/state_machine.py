"""Controlled workflow state, reviewer loop and human approval boundary."""

from __future__ import annotations

from dataclasses import dataclass, field

from .audit import AuditTrail
from .extraction import MockOutputError
from .models import (
    ArchitectureRoute,
    DiagnosticRecommendation,
    QualificationDecision,
    QualificationResult,
    ResolutionStatus,
    ReviewFinding,
    ReviewerMode,
    Severity,
    WorkflowCase,
    WorkflowStatus,
)
from .qualification import (
    QualificationBlocked,
    highest_value_clarification,
    is_vague_ai_request,
    missing_required_facts,
    qualify_case,
)
from .recommendation import MockSolutionArchitect
from .reviewer import MockReviewer, apply_one_revision


class InvalidTransition(ValueError):
    """Raised when a caller attempts to bypass a controlled transition."""


@dataclass
class DiagnosticSession:
    case: WorkflowCase
    status: WorkflowStatus = WorkflowStatus.NEW
    facts_confirmed: bool = False
    qualification: QualificationResult | None = None
    recommendation: DiagnosticRecommendation | None = None
    findings: list[ReviewFinding] = field(default_factory=list)
    revision_count: int = 0
    clarification_question: str | None = None
    failure_reason: str | None = None
    audit: AuditTrail = field(default_factory=AuditTrail)

    def __post_init__(self) -> None:
        self.case.status = self.status

    @property
    def can_approve(self) -> bool:
        unresolved_material = any(
            finding.severity in {Severity.CRITICAL, Severity.HIGH}
            and finding.resolution_status == ResolutionStatus.OPEN
            for finding in self.findings
        )
        return (
            self.status == WorkflowStatus.READY_FOR_APPROVAL
            and self.recommendation is not None
            and not unresolved_material
            and self.failure_reason is None
        )

    def _transition(
        self,
        to_status: WorkflowStatus,
        *,
        actor: str,
        action: str,
        notes: str | None = None,
    ) -> None:
        from_status = self.status
        self.status = to_status
        self.case.status = to_status
        self.audit.record(
            case_id=self.case.case_id,
            actor=actor,
            action=action,
            from_status=from_status,
            to_status=to_status,
            notes=notes,
        )

    def start_discovery(self) -> None:
        if self.status != WorkflowStatus.NEW:
            raise InvalidTransition("Discovery can start only from NEW")
        self._transition(
            WorkflowStatus.DISCOVERY,
            actor="MockExtractor",
            action="START_DISCOVERY",
        )

    def confirm_and_qualify(self) -> None:
        if self.status not in {
            WorkflowStatus.DISCOVERY,
            WorkflowStatus.NEEDS_CLARIFICATION,
        }:
            raise InvalidTransition(
                "Facts can be confirmed only during discovery or clarification"
            )

        self.facts_confirmed = True
        self._transition(
            WorkflowStatus.HUMAN_CONFIRMATION,
            actor="Human",
            action="CONFIRM_FACTS",
        )

        if is_vague_ai_request(self.case):
            self._transition(
                WorkflowStatus.QUALIFICATION,
                actor="System",
                action="RUN_QUALIFICATION",
                notes="Vague broad request evaluated conservatively.",
            )
            self.qualification = qualify_case(self.case, facts_confirmed=True)
            self._transition(
                WorkflowStatus.NOT_QUALIFIED,
                actor="System",
                action="SET_QUALIFICATION_DECISION",
                notes="Broad AI request lacks a bounded workflow; route forced to NO_BUILD.",
            )
            return

        missing = missing_required_facts(self.case)
        if missing:
            if self.case.clarification_count >= 2:
                self._transition(
                    WorkflowStatus.MANUAL_REVIEW,
                    actor="System",
                    action="CLARIFICATION_LIMIT_REACHED",
                    notes="Maximum two clarification cycles reached.",
                )
                return
            self.case.clarification_count += 1
            self.clarification_question = highest_value_clarification(self.case)
            self._transition(
                WorkflowStatus.NEEDS_CLARIFICATION,
                actor="System",
                action="REQUEST_CLARIFICATION",
                notes=self.clarification_question,
            )
            return

        self._transition(
            WorkflowStatus.QUALIFICATION,
            actor="System",
            action="RUN_QUALIFICATION",
        )
        try:
            self.qualification = qualify_case(self.case, facts_confirmed=True)
        except QualificationBlocked as exc:
            self.fail(str(exc), actor="System")
            return

        if self.qualification.decision == QualificationDecision.NOT_QUALIFIED:
            target = WorkflowStatus.NOT_QUALIFIED
        elif self.qualification.decision == QualificationDecision.DIAGNOSTIC_ONLY:
            target = WorkflowStatus.DIAGNOSTIC_ONLY
        else:
            target = WorkflowStatus.ARCHITECTURE_DRAFT
        self._transition(
            target,
            actor="System",
            action="SET_QUALIFICATION_DECISION",
            notes=f"Score {self.qualification.score}/10.",
        )

    def draft_recommendation(
        self,
        architect: MockSolutionArchitect,
        *,
        invalid_output: bool = False,
    ) -> None:
        if self.status not in {
            WorkflowStatus.ARCHITECTURE_DRAFT,
            WorkflowStatus.DIAGNOSTIC_ONLY,
        }:
            raise InvalidTransition(
                "Recommendation is not permitted from the current state"
            )
        if self.qualification is None:
            raise InvalidTransition("Qualification is required before recommendation")
        try:
            recommendation = architect.recommend(
                self.case,
                self.qualification,
                invalid_output=invalid_output,
            )
        except (MockOutputError, ValueError) as exc:
            self.recommendation = None
            self.fail(str(exc), actor="MockSolutionArchitect")
            return
        if not isinstance(recommendation.recommended_route, ArchitectureRoute):
            self.fail("Invalid architecture route", actor="MockSolutionArchitect")
            return
        self.recommendation = recommendation
        if self.status == WorkflowStatus.DIAGNOSTIC_ONLY:
            self._transition(
                WorkflowStatus.ARCHITECTURE_DRAFT,
                actor="MockSolutionArchitect",
                action="DRAFT_DIAGNOSTIC_RECOMMENDATION",
            )
        else:
            self.audit.record(
                case_id=self.case.case_id,
                actor="MockSolutionArchitect",
                action="DRAFT_ARCHITECTURE_RECOMMENDATION",
                from_status=self.status,
                to_status=self.status,
                notes=f"Route: {recommendation.recommended_route.value}",
            )

    def run_review(self, reviewer: MockReviewer, *, mode: ReviewerMode) -> None:
        if self.status not in {
            WorkflowStatus.ARCHITECTURE_DRAFT,
            WorkflowStatus.REVIEW,
        }:
            raise InvalidTransition("Review requires an architecture draft")
        if self.recommendation is None:
            raise InvalidTransition("Review requires a recommendation")
        reviewer_actor = reviewer.role
        if self.status != WorkflowStatus.REVIEW:
            self._transition(
                WorkflowStatus.REVIEW,
                actor=reviewer_actor,
                action="START_REVIEW",
            )
        try:
            self.findings = reviewer.review(
                self.case,
                self.recommendation,
                mode=mode,
                revision_count=self.revision_count,
            )
        except MockOutputError as exc:
            self.findings = []
            self.fail(str(exc), actor=reviewer_actor)
            return

        material = [
            finding
            for finding in self.findings
            if finding.severity in {Severity.CRITICAL, Severity.HIGH}
            and finding.resolution_status == ResolutionStatus.OPEN
        ]
        if material and self.revision_count == 0:
            self._transition(
                WorkflowStatus.REVISION_REQUIRED,
                actor=reviewer_actor,
                action="RAISE_MATERIAL_FINDING",
                notes=f"{len(material)} material finding(s).",
            )
        elif material:
            for finding in material:
                finding.resolution_status = ResolutionStatus.HUMAN_ADJUDICATION
            self._transition(
                WorkflowStatus.MANUAL_REVIEW,
                actor=reviewer_actor,
                action="ESCALATE_AFTER_MAX_REVISION",
                notes="No second automated revision is permitted.",
            )
        else:
            self._transition(
                WorkflowStatus.READY_FOR_APPROVAL,
                actor=reviewer_actor,
                action="REVIEW_COMPLETE",
            )

    def revise_once(self) -> None:
        if self.status != WorkflowStatus.REVISION_REQUIRED:
            raise InvalidTransition("A revision is allowed only from REVISION_REQUIRED")
        if self.revision_count >= 1:
            self._transition(
                WorkflowStatus.MANUAL_REVIEW,
                actor="System",
                action="BLOCK_SECOND_REVISION",
            )
            return
        if self.recommendation is None:
            self.fail("No recommendation exists to revise", actor="System")
            return
        self.recommendation = apply_one_revision(self.recommendation, self.findings)
        self.revision_count += 1
        self._transition(
            WorkflowStatus.ARCHITECTURE_DRAFT,
            actor="MockSolutionArchitect",
            action="APPLY_ONE_CONTROLLED_REVISION",
            notes="Automated revision count is now 1/1.",
        )

    def approve(self) -> None:
        if not self.can_approve:
            raise InvalidTransition("Approval boundary cannot be bypassed")
        self._transition(
            WorkflowStatus.APPROVED,
            actor="Human",
            action="APPROVE_REPORT",
        )

    def reject(self, reason: str = "Human rejected the recommendation") -> None:
        if self.status != WorkflowStatus.READY_FOR_APPROVAL:
            raise InvalidTransition("Rejection is allowed only from READY_FOR_APPROVAL")
        self._transition(
            WorkflowStatus.REJECTED,
            actor="Human",
            action="REJECT_REPORT",
            notes=reason,
        )

    def fail(self, reason: str, *, actor: str) -> None:
        self.failure_reason = reason
        self.recommendation = None
        self._transition(
            WorkflowStatus.FAILED,
            actor=actor,
            action="FAIL_SAFE",
            notes=reason,
        )
