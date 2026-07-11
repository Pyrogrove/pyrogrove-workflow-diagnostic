"""Synthetic, non-client examples used by the practice build."""

from __future__ import annotations

from .models import (
    CriterionOutcome,
    DataSensitivity,
    Frequency,
    UNKNOWN,
    WorkflowCase,
)


def _case_01() -> WorkflowCase:
    return WorkflowCase(
        case_id="CASE-01",
        title="Complete RFQ and customer-enquiry workflow",
        workflow_narrative=(
            "A Singapore industrial distributor receives about 40 RFQs each week in Outlook. "
            "Sales coordinators copy details into Excel, chase missing quantity and required-date "
            "information, and prepare cases for Sales Operations review. Delays affect response time "
            "and quotation conversion. The workflow owner wants a narrow 30-day pilot using synthetic samples."
        ),
        workflow_owner="Sales Operations Manager",
        primary_user="Sales Coordinator",
        trigger="Customer RFQ or enquiry arrives in Outlook",
        inputs=["RFQ email", "attachments", "customer and product details"],
        outputs=["quote-readiness record", "clarification draft", "exception queue"],
        frequency=Frequency.WEEKLY,
        monthly_volume=160,
        current_tools=["Outlook", "Excel", "Microsoft 365"],
        business_consequence="Slow response, repeated chasing, missed information and reduced quotation conversion.",
        known_exceptions=[
            "Missing quantity",
            "Missing required date",
            "Ambiguous specification",
        ],
        sample_evidence=[
            "Three synthetic RFQ examples",
            "Current Excel tracker screenshot equivalent",
        ],
        data_sensitivity=DataSensitivity.SYNTHETIC,
        budget_signal=CriterionOutcome.YES,
        timeline="30-day pilot window",
        narrow_mvp_fit=CriterionOutcome.YES,
        supportability=CriterionOutcome.YES,
    )


def _case_02() -> WorkflowCase:
    return WorkflowCase(
        case_id="CASE-02",
        title="Incomplete service-request workflow",
        workflow_narrative=(
            "A service team receives repeated maintenance requests by email and records them in Excel, "
            "but the accountable workflow owner has not been identified."
        ),
        workflow_owner=UNKNOWN,
        primary_user="Service Coordinator",
        trigger="Maintenance request arrives by email",
        inputs=["Service request email"],
        outputs=["Service-request tracker entry"],
        frequency=Frequency.WEEKLY,
        monthly_volume=25,
        current_tools=["Outlook", "Excel"],
        business_consequence="Requests may be delayed or assigned inconsistently.",
        known_exceptions=["Missing equipment serial number"],
        sample_evidence=["Synthetic request sample"],
        data_sensitivity=DataSensitivity.SYNTHETIC,
        budget_signal=CriterionOutcome.UNKNOWN,
        timeline="Within one quarter",
        narrow_mvp_fit=CriterionOutcome.YES,
        supportability=CriterionOutcome.YES,
    )


def _case_03() -> WorkflowCase:
    return WorkflowCase(
        case_id="CASE-03",
        title="Vague AI transformation request",
        workflow_narrative="Use AI to automate my company and reduce headcount.",
        workflow_owner=UNKNOWN,
        primary_user=UNKNOWN,
        trigger=UNKNOWN,
        inputs=[],
        outputs=[],
        frequency=Frequency.UNKNOWN,
        monthly_volume=None,
        current_tools=[],
        business_consequence=UNKNOWN,
        known_exceptions=[],
        sample_evidence=[],
        data_sensitivity=DataSensitivity.SYNTHETIC,
        budget_signal=CriterionOutcome.UNKNOWN,
        timeline=UNKNOWN,
        narrow_mvp_fit=CriterionOutcome.NO,
        supportability=CriterionOutcome.UNKNOWN,
    )


SYNTHETIC_CASE_FACTORIES = {
    "CASE-01": _case_01,
    "CASE-02": _case_02,
    "CASE-03": _case_03,
}


def list_synthetic_cases() -> dict[str, str]:
    """Return case IDs and display titles without sharing mutable model instances."""
    return {
        case_id: factory().title
        for case_id, factory in SYNTHETIC_CASE_FACTORIES.items()
    }


def get_synthetic_case(case_id: str) -> WorkflowCase:
    """Return a fresh validated synthetic case."""
    try:
        return SYNTHETIC_CASE_FACTORIES[case_id]()
    except KeyError as exc:
        raise ValueError(f"Unknown synthetic case: {case_id}") from exc
