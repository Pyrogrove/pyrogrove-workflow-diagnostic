"""Deterministic local adapter that simulates the Solution Architect role."""

from __future__ import annotations

from pydantic import ValidationError

from .extraction import MockOutputError
from .models import (
    ArchitectureRoute,
    DiagnosticRecommendation,
    QualificationDecision,
    QualificationResult,
    RecommendationEnvelope,
    WorkflowCase,
)


class MockSolutionArchitect:
    role = "MockSolutionArchitect"

    def recommend(
        self,
        case: WorkflowCase,
        qualification: QualificationResult,
        *,
        invalid_output: bool = False,
    ) -> DiagnosticRecommendation:
        if qualification.decision == QualificationDecision.NOT_QUALIFIED:
            raise ValueError(
                "A NOT_QUALIFIED case cannot receive a build recommendation"
            )

        route = self._select_route(case)
        if invalid_output:
            raw: dict[str, object] = {
                "role": self.role,
                "recommendation": {
                    "problem_statement": "Malformed recommendation",
                    "target_user": case.primary_user,
                    "recommended_route": "AUTONOMOUS_AI_PLATFORM",
                },
            }
        else:
            recommendation = self._build_recommendation(case, route)
            raw = {
                "role": self.role,
                "recommendation": recommendation.model_dump(mode="json"),
            }

        try:
            envelope = RecommendationEnvelope.model_validate(raw)
        except ValidationError as exc:
            raise MockOutputError(
                "MockSolutionArchitect output failed schema validation"
            ) from exc
        return envelope.recommendation

    @staticmethod
    def _select_route(case: WorkflowCase) -> ArchitectureRoute:
        tools = " ".join(case.current_tools).casefold()
        narrative = case.workflow_narrative.casefold()
        inputs = " ".join(case.inputs).casefold()

        if any(
            token in tools
            for token in ("microsoft 365", "outlook", "sharepoint", "excel")
        ):
            if "legacy desktop" not in narrative:
                return ArchitectureRoute.M365
        if "legacy desktop" in narrative or "desktop" in tools:
            return ArchitectureRoute.RPA_DESKTOP
        if "csv" in inputs or "csv" in narrative:
            return ArchitectureRoute.DATA_CODE
        if any(
            token in narrative
            for token in ("external portal", "branded ux", "customer portal")
        ):
            return ArchitectureRoute.CODED_MICROAPP
        return ArchitectureRoute.NO_BUILD

    @staticmethod
    def _build_recommendation(
        case: WorkflowCase,
        route: ArchitectureRoute,
    ) -> DiagnosticRecommendation:
        route_rationales = {
            ArchitectureRoute.M365: "The workflow is internal and already uses Outlook, Excel or Microsoft 365.",
            ArchitectureRoute.RPA_DESKTOP: "A legacy desktop step dominates and requires controlled attended automation.",
            ArchitectureRoute.DATA_CODE: "Stable structured files make ordinary deterministic code the simplest route.",
            ArchitectureRoute.CODED_MICROAPP: "Custom external UX or portability is material to the workflow.",
            ArchitectureRoute.NO_BUILD: "The current evidence does not justify a build route.",
        }
        return DiagnosticRecommendation(
            problem_statement=(
                f"{case.primary_user} currently handles '{case.title}' with manual checks and exceptions, "
                f"creating this consequence: {case.business_consequence}"
            ),
            target_user=case.primary_user,
            recommended_route=route,
            route_rationale=route_rationales[route],
            deterministic_steps=[
                "Capture one workflow request in a structured record.",
                "Validate required fields and permitted values.",
                "Assign an explicit status and exception owner.",
                "Preserve an audit event for each consequential transition.",
            ],
            ai_assisted_steps=[
                "Simulated extraction of structured facts from the narrative.",
                "Simulated architecture drafting and reviewer challenge.",
            ],
            human_control_points=[
                "Confirm extracted facts before qualification.",
                "Adjudicate any unresolved High or Critical finding.",
                "Approve or reject the final report before download.",
            ],
            mvp_scope=[
                "One workflow and one primary user role.",
                "Required-field validation and deterministic qualification.",
                "One recommendation, one reviewer pass and at most one automated revision.",
                "Markdown report and visible audit evidence.",
            ],
            explicit_exclusions=[
                "No live model API, production hosting, customer authentication or multi-tenancy.",
                "No pricing, external sending, deployment commitment or customer commitment.",
                "No Hermes, RAG, MCP, n8n, FastAPI, Docker or database persistence.",
            ],
            failure_modes=[
                "Missing required fact routes to NEEDS_CLARIFICATION.",
                "Invalid adapter output routes to FAILED and disables approval.",
                "Persistent High finding after one revision routes to MANUAL_REVIEW.",
            ],
            acceptance_tests=[
                "Complete case reaches READY_FOR_APPROVAL and can be approved by a human.",
                "Incomplete case asks exactly one highest-value clarification question.",
                "Vague AI request is rejected safely with NO_BUILD.",
                "High reviewer finding triggers no more than one automated revision.",
                "Every consequential state transition has an audit event.",
            ],
            assumptions=[
                "All data is synthetic.",
                "The selected case represents one workflow only.",
                "M365 licensing and production feasibility are not validated in this practice build.",
            ],
            open_questions=[
                "Who would approve a real diagnostic budget?",
                "Which three sanitised examples would define actual exception patterns?",
            ],
        )
