"""Typed domain models for the deterministic practice build."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PRACTICE_DISCLOSURE = "PRACTICE BUILD — NOT CLAIMED AS EVENT-DAY WORK"
UNKNOWN = "UNKNOWN"


class WorkflowStatus(StrEnum):
    NEW = "NEW"
    DISCOVERY = "DISCOVERY"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    HUMAN_CONFIRMATION = "HUMAN_CONFIRMATION"
    QUALIFICATION = "QUALIFICATION"
    NOT_QUALIFIED = "NOT_QUALIFIED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    ARCHITECTURE_DRAFT = "ARCHITECTURE_DRAFT"
    REVIEW = "REVIEW"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FAILED = "FAILED"


class Frequency(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    AD_HOC = "AD_HOC"
    UNKNOWN = "UNKNOWN"


class DataSensitivity(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"
    UNKNOWN = "UNKNOWN"


class CriterionOutcome(StrEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class QualificationDecision(StrEnum):
    MVP_CANDIDATE = "MVP_CANDIDATE"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    NOT_QUALIFIED = "NOT_QUALIFIED"


class ArchitectureRoute(StrEnum):
    M365 = "M365"
    RPA_DESKTOP = "RPA_DESKTOP"
    DATA_CODE = "DATA_CODE"
    CODED_MICROAPP = "CODED_MICROAPP"
    NO_BUILD = "NO_BUILD"


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ResolutionStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DEFERRED = "DEFERRED"
    HUMAN_ADJUDICATION = "HUMAN_ADJUDICATION"


class ReviewerMode(StrEnum):
    NORMAL = "NORMAL"
    HIGH_ONCE = "HIGH_ONCE"
    HIGH_ALWAYS = "HIGH_ALWAYS"
    INVALID = "INVALID"


class WorkflowCase(BaseModel):
    """One bounded workflow diagnostic case."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    case_id: str
    title: str
    workflow_narrative: str
    workflow_owner: str = UNKNOWN
    primary_user: str = UNKNOWN
    trigger: str = UNKNOWN
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    frequency: Frequency = Frequency.UNKNOWN
    monthly_volume: int | None = Field(default=None, ge=0)
    current_tools: list[str] = Field(default_factory=list)
    business_consequence: str = UNKNOWN
    known_exceptions: list[str] = Field(default_factory=list)
    sample_evidence: list[str] = Field(default_factory=list)
    data_sensitivity: DataSensitivity = DataSensitivity.SYNTHETIC
    budget_signal: CriterionOutcome = CriterionOutcome.UNKNOWN
    timeline: str = UNKNOWN
    narrow_mvp_fit: CriterionOutcome = CriterionOutcome.UNKNOWN
    supportability: CriterionOutcome = CriterionOutcome.UNKNOWN
    status: WorkflowStatus = WorkflowStatus.NEW
    clarification_count: int = Field(default=0, ge=0, le=2)

    @field_validator(
        "workflow_owner",
        "primary_user",
        "trigger",
        "business_consequence",
        "timeline",
        mode="before",
    )
    @classmethod
    def normalise_blank_text(cls, value: object) -> str:
        if value is None or not str(value).strip():
            return UNKNOWN
        return str(value).strip()

    @field_validator(
        "inputs", "outputs", "current_tools", "known_exceptions", "sample_evidence"
    )
    @classmethod
    def remove_blank_items(cls, values: list[str]) -> list[str]:
        return [str(item).strip() for item in values if str(item).strip()]


class QualificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    criteria: dict[str, CriterionOutcome]
    score: int = Field(ge=0, le=10)
    decision: QualificationDecision
    missing_evidence: list[str] = Field(default_factory=list)
    explanation: str

    @model_validator(mode="after")
    def score_matches_yes_count(self) -> "QualificationResult":
        yes_count = sum(
            value == CriterionOutcome.YES for value in self.criteria.values()
        )
        if len(self.criteria) != 10:
            raise ValueError("Qualification must contain exactly ten criteria")
        if self.score != yes_count:
            raise ValueError("Score must equal the number of YES criteria")
        expected = (
            QualificationDecision.MVP_CANDIDATE
            if self.score >= 8
            else QualificationDecision.DIAGNOSTIC_ONLY
            if self.score >= 5
            else QualificationDecision.NOT_QUALIFIED
        )
        if self.decision != expected:
            raise ValueError("Decision does not match deterministic score band")
        return self


class DiagnosticRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    problem_statement: str
    target_user: str
    recommended_route: ArchitectureRoute
    route_rationale: str
    deterministic_steps: list[str]
    ai_assisted_steps: list[str]
    human_control_points: list[str]
    mvp_scope: list[str]
    explicit_exclusions: list[str]
    failure_modes: list[str]
    acceptance_tests: list[str]
    assumptions: list[str]
    open_questions: list[str]


class ReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    finding_id: str
    severity: Severity
    requirement: str
    evidence: str
    business_impact: str
    recommended_correction: str
    resolution_status: ResolutionStatus = ResolutionStatus.OPEN


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    case_id: str
    actor: str
    action: str
    from_status: WorkflowStatus
    to_status: WorkflowStatus
    timestamp: datetime
    notes: str | None = None


class ExtractorEnvelope(BaseModel):
    """Schema boundary for deterministic extractor output."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["MockExtractor"]
    case: WorkflowCase


class RecommendationEnvelope(BaseModel):
    """Schema boundary for deterministic architect output."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["MockSolutionArchitect"]
    recommendation: DiagnosticRecommendation


class ReviewerEnvelope(BaseModel):
    """Schema boundary for deterministic reviewer output."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["MockReviewer"]
    findings: list[ReviewFinding]
