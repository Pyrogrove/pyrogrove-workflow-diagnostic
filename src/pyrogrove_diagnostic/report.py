"""Human-approved Markdown report generation."""

from __future__ import annotations

from .models import PRACTICE_DISCLOSURE, WorkflowStatus
from .state_machine import DiagnosticSession, InvalidTransition

AI_SIMULATION_DISCLOSURE = (
    "AI roles are simulated with deterministic local adapters in v0.1. "
    "No live model API is used."
)


def generate_markdown_report(session: DiagnosticSession) -> str:
    if session.status != WorkflowStatus.APPROVED:
        raise InvalidTransition("A downloadable final report requires human approval")
    if session.qualification is None or session.recommendation is None:
        raise InvalidTransition("Approved report is missing required evidence")

    case = session.case
    qualification = session.qualification
    recommendation = session.recommendation

    criteria_rows = "\n".join(
        f"| {name.replace('_', ' ').title()} | {value.value} |"
        for name, value in qualification.criteria.items()
    )
    finding_rows = (
        "\n".join(
            "| {id} | {severity} | {status} | {impact} |".format(
                id=finding.finding_id,
                severity=finding.severity.value,
                status=finding.resolution_status.value,
                impact=finding.business_impact.replace("|", "/"),
            )
            for finding in session.findings
        )
        or "| None | — | — | No reviewer finding recorded. |"
    )
    audit_rows = "\n".join(
        "| {timestamp} | {actor} | {action} | {from_status} | {to_status} | {notes} |".format(
            timestamp=event.timestamp.isoformat(),
            actor=event.actor,
            action=event.action,
            from_status=event.from_status.value,
            to_status=event.to_status.value,
            notes=(event.notes or "").replace("|", "/"),
        )
        for event in session.audit.events
    )

    return f"""# PyroGrove Workflow Diagnostic Report

> **{PRACTICE_DISCLOSURE}**

> {AI_SIMULATION_DISCLOSURE}

## Approval status

- Case: `{case.case_id}` — {case.title}
- Final status: `{session.status.value}`
- Human approval: recorded
- Automated revisions used: `{session.revision_count}/1`

## Problem statement

{recommendation.problem_statement}

## Confirmed workflow facts

- Workflow owner: {case.workflow_owner}
- Primary user: {case.primary_user}
- Trigger: {case.trigger}
- Inputs: {", ".join(case.inputs)}
- Outputs: {", ".join(case.outputs)}
- Frequency: {case.frequency.value}
- Monthly volume: {case.monthly_volume if case.monthly_volume is not None else "UNKNOWN"}
- Current tools: {", ".join(case.current_tools)}
- Consequence: {case.business_consequence}
- Exceptions: {", ".join(case.known_exceptions)}

## Deterministic qualification

Score: **{qualification.score}/10**  
Decision: **{qualification.decision.value}**

| Criterion | Result |
|---|---|
{criteria_rows}

## Right-sized recommendation

- Recommended route: **{recommendation.recommended_route.value}**
- Rationale: {recommendation.route_rationale}

### Deterministic workflow steps

{_bullets(recommendation.deterministic_steps)}

### Simulated AI-assisted steps

{_bullets(recommendation.ai_assisted_steps)}

### Human control points

{_bullets(recommendation.human_control_points)}

### MVP scope

{_bullets(recommendation.mvp_scope)}

### Explicit exclusions

{_bullets(recommendation.explicit_exclusions)}

### Failure modes and manual fallback

{_bullets(recommendation.failure_modes)}

### Acceptance tests

{_bullets(recommendation.acceptance_tests)}

### Assumptions

{_bullets(recommendation.assumptions)}

### Open questions

{_bullets(recommendation.open_questions)}

## Reviewer findings

| Finding | Severity | Resolution | Business impact |
|---|---|---|---|
{finding_rows}

## Audit events

| Timestamp | Actor | Action | From | To | Notes |
|---|---|---|---|---|---|
{audit_rows}

## Practice-build limitation

This report is synthetic, local and non-production. It does not prove market demand, customer savings, production security, deployment readiness or event-day work.
"""


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None"
