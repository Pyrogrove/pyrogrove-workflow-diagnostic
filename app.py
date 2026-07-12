"""Single-page Streamlit interface for the PyroGrove practice build."""

from __future__ import annotations

import streamlit as st

from src.pyrogrove_diagnostic.extraction import MockExtractor, MockOutputError
from src.pyrogrove_diagnostic.models import (
    CriterionOutcome,
    DataSensitivity,
    Frequency,
    PRACTICE_DISCLOSURE,
    ReviewerMode,
    UNKNOWN,
    WorkflowCase,
    WorkflowStatus,
)
from src.pyrogrove_diagnostic.recommendation import MockSolutionArchitect
from src.pyrogrove_diagnostic.report import (
    AI_SIMULATION_DISCLOSURE,
    generate_markdown_report,
)
from src.pyrogrove_diagnostic.reviewer import MockReviewer
from src.pyrogrove_diagnostic.state_machine import DiagnosticSession, InvalidTransition
from src.pyrogrove_diagnostic.synthetic_cases import (
    get_synthetic_case,
    list_synthetic_cases,
)

st.set_page_config(page_title="PyroGrove Workflow Diagnostic", layout="wide")

st.title("PyroGrove Workflow Diagnostic Agentic Service")
st.error(PRACTICE_DISCLOSURE)
st.caption(AI_SIMULATION_DISCLOSURE)
st.write(
    "A human-supervised local workflow diagnostic using deterministic qualification, "
    "simulated AI roles, one controlled revision and human release authority."
)


def _csv_to_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _init_state() -> None:
    cases = list_synthetic_cases()
    default_id = next(iter(cases))
    if "selected_case_id" not in st.session_state:
        st.session_state.selected_case_id = default_id
    if "draft_case" not in st.session_state:
        st.session_state.draft_case = get_synthetic_case(default_id)
    if "session" not in st.session_state:
        st.session_state.session = None
    if "ui_error" not in st.session_state:
        st.session_state.ui_error = None


def _load_case(case_id: str) -> None:
    st.session_state.selected_case_id = case_id
    st.session_state.draft_case = get_synthetic_case(case_id)
    st.session_state.session = None
    st.session_state.ui_error = None


def _fail_extraction(case_id: str, reason: str) -> None:
    fallback = WorkflowCase(
        case_id=case_id,
        title="Invalid adapter output",
        workflow_narrative="Adapter output did not pass schema validation.",
    )
    session = DiagnosticSession(fallback)
    session.start_discovery()
    session.fail(reason, actor="MockExtractor")
    st.session_state.session = session


_init_state()
case_titles = list_synthetic_cases()

with st.sidebar:
    st.header("Practice controls")
    selected_case_id = st.selectbox(
        "Synthetic example",
        options=list(case_titles),
        format_func=lambda item: f"{item} — {case_titles[item]}",
        index=list(case_titles).index(st.session_state.selected_case_id),
    )
    if st.button("Load selected case", use_container_width=True):
        _load_case(selected_case_id)
        st.rerun()

    invalid_stage = st.selectbox(
        "Failure simulation",
        options=["None", "Extractor output", "Architect output", "Reviewer output"],
        help="Each invalid adapter output must fail safely and disable approval.",
    )
    reviewer_mode = ReviewerMode(
        st.selectbox(
            "Reviewer test mode",
            options=[
                mode.value for mode in ReviewerMode if mode != ReviewerMode.INVALID
            ],
            index=0,
            help="HIGH_ONCE proves exactly one controlled revision. HIGH_ALWAYS proves escalation.",
        )
    )

case: WorkflowCase = st.session_state.draft_case
narrative = st.text_area(
    "Workflow narrative",
    value=case.workflow_narrative,
    height=150,
    key=f"narrative_{case.case_id}",
)

if st.button("1. Run deterministic MockExtractor", type="primary"):
    try:
        extracted = MockExtractor().extract(
            narrative,
            synthetic_case_id=st.session_state.selected_case_id,
            invalid_output=invalid_stage == "Extractor output",
        )
        st.session_state.draft_case = extracted
        st.session_state.session = None
        st.session_state.ui_error = None
    except MockOutputError as exc:
        _fail_extraction(st.session_state.selected_case_id, str(exc))
    st.rerun()

st.subheader("Structured facts requiring human confirmation")
case = st.session_state.draft_case

with st.form("facts_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input("Workflow owner", value=case.workflow_owner)
        primary_user = st.text_input("Primary user", value=case.primary_user)
        trigger = st.text_input("Trigger", value=case.trigger)
        inputs = st.text_input("Inputs (comma-separated)", value=", ".join(case.inputs))
        outputs = st.text_input(
            "Outputs (comma-separated)", value=", ".join(case.outputs)
        )
        frequency = Frequency(
            st.selectbox(
                "Frequency",
                options=[value.value for value in Frequency],
                index=list(Frequency).index(case.frequency),
            )
        )
        monthly_volume_text = st.text_input(
            "Monthly volume (blank = unknown)",
            value="" if case.monthly_volume is None else str(case.monthly_volume),
        )
    with col2:
        current_tools = st.text_input(
            "Current tools (comma-separated)", value=", ".join(case.current_tools)
        )
        consequence = st.text_area(
            "Business consequence", value=case.business_consequence
        )
        exceptions = st.text_input(
            "Known exceptions (comma-separated)", value=", ".join(case.known_exceptions)
        )
        evidence = st.text_input(
            "Sample evidence (comma-separated)", value=", ".join(case.sample_evidence)
        )
        budget_signal = CriterionOutcome(
            st.selectbox(
                "Budget signal",
                options=[value.value for value in CriterionOutcome],
                index=list(CriterionOutcome).index(case.budget_signal),
            )
        )
        timeline = st.text_input("Timeline", value=case.timeline)
        narrow_mvp_fit = CriterionOutcome(
            st.selectbox(
                "Narrow MVP fit",
                options=[value.value for value in CriterionOutcome],
                index=list(CriterionOutcome).index(case.narrow_mvp_fit),
            )
        )
        supportability = CriterionOutcome(
            st.selectbox(
                "Supportability",
                options=[value.value for value in CriterionOutcome],
                index=list(CriterionOutcome).index(case.supportability),
            )
        )
        data_sensitivity = DataSensitivity(
            st.selectbox(
                "Data sensitivity",
                options=[value.value for value in DataSensitivity],
                index=list(DataSensitivity).index(case.data_sensitivity),
            )
        )

    confirm = st.form_submit_button(
        "2. Confirm facts and run deterministic qualification"
    )

if confirm:
    try:
        volume = None if not monthly_volume_text.strip() else int(monthly_volume_text)
        updated_case = WorkflowCase.model_validate(
            {
                **case.model_dump(),
                "workflow_narrative": narrative,
                "workflow_owner": owner or UNKNOWN,
                "primary_user": primary_user or UNKNOWN,
                "trigger": trigger or UNKNOWN,
                "inputs": _csv_to_list(inputs),
                "outputs": _csv_to_list(outputs),
                "frequency": frequency,
                "monthly_volume": volume,
                "current_tools": _csv_to_list(current_tools),
                "business_consequence": consequence or UNKNOWN,
                "known_exceptions": _csv_to_list(exceptions),
                "sample_evidence": _csv_to_list(evidence),
                "budget_signal": budget_signal,
                "timeline": timeline or UNKNOWN,
                "narrow_mvp_fit": narrow_mvp_fit,
                "supportability": supportability,
                "data_sensitivity": data_sensitivity,
                "status": WorkflowStatus.NEW,
            }
        )
        session = DiagnosticSession(updated_case)
        session.start_discovery()
        session.confirm_and_qualify()
        st.session_state.draft_case = updated_case
        st.session_state.session = session
        st.session_state.ui_error = None
    except (ValueError, InvalidTransition) as exc:
        st.session_state.ui_error = str(exc)
    st.rerun()

session: DiagnosticSession | None = st.session_state.session
if st.session_state.ui_error:
    st.error(st.session_state.ui_error)

if session is not None:
    st.divider()
    st.subheader("Controlled workflow result")
    metrics = st.columns(4)
    metrics[0].metric("State", session.status.value)
    metrics[1].metric(
        "Qualification score",
        "—" if session.qualification is None else f"{session.qualification.score}/10",
    )
    metrics[2].metric(
        "Decision",
        "—" if session.qualification is None else session.qualification.decision.value,
    )
    metrics[3].metric("Automated revisions", f"{session.revision_count}/1")

    if session.status == WorkflowStatus.NEEDS_CLARIFICATION:
        st.warning(
            session.clarification_question
            or "One material fact requires clarification."
        )
    elif session.status == WorkflowStatus.NOT_QUALIFIED:
        st.warning(
            "NOT_QUALIFIED — route is NO_BUILD. No architecture commitment is created."
        )
    elif session.status == WorkflowStatus.FAILED:
        st.error(f"Failed safely: {session.failure_reason}")
    elif session.qualification is not None:
        for name, result in session.qualification.criteria.items():
            st.markdown(f"{name}: {result.value}")

    if session.status in {
        WorkflowStatus.ARCHITECTURE_DRAFT,
        WorkflowStatus.DIAGNOSTIC_ONLY,
    }:
        if st.button("3. Generate recommendation and run independent Reviewer"):
            try:
                session.draft_recommendation(
                    MockSolutionArchitect(),
                    invalid_output=invalid_stage == "Architect output",
                )
                if session.status != WorkflowStatus.FAILED:
                    mode = (
                        ReviewerMode.INVALID
                        if invalid_stage == "Reviewer output"
                        else reviewer_mode
                    )
                    session.run_review(MockReviewer(), mode=mode)
            except InvalidTransition as exc:
                st.session_state.ui_error = str(exc)
            st.rerun()

    if session.recommendation is not None:
        st.subheader("Recommendation")
        st.write(f"**Route:** {session.recommendation.recommended_route.value}")
        st.write(session.recommendation.route_rationale)
        st.write("**Deterministic steps**")
        for step in session.recommendation.deterministic_steps:
            st.write(f"- {step}")

    if session.findings:
        st.subheader("Reviewer findings")
        for finding in session.findings:
            st.markdown(
                f"{finding.finding_id} | {finding.severity.value} | "
                f"{finding.requirement} | {finding.resolution_status.value}"
            )

    if session.status == WorkflowStatus.REVISION_REQUIRED:
        if st.button("4. Apply the one permitted controlled revision"):
            session.revise_once()
            if session.status == WorkflowStatus.ARCHITECTURE_DRAFT:
                session.run_review(MockReviewer(), mode=reviewer_mode)
            st.rerun()

    if session.status == WorkflowStatus.READY_FOR_APPROVAL:
        st.subheader("Human authority boundary")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button(
                "5A. Approve report", type="primary", use_container_width=True
            ):
                try:
                    session.approve()
                except InvalidTransition as exc:
                    st.session_state.ui_error = str(exc)
                st.rerun()
        with col_b:
            if st.button("5B. Reject report", use_container_width=True):
                try:
                    session.reject()
                except InvalidTransition as exc:
                    st.session_state.ui_error = str(exc)
                st.rerun()

    if session.status == WorkflowStatus.APPROVED:
        report = generate_markdown_report(session)
        st.success(
            "Human approval recorded. The synthetic Markdown report is available."
        )
        st.download_button(
            "Download approved Markdown report",
            data=report,
            file_name=f"{session.case.case_id}_workflow_diagnostic_report.md",
            mime="text/markdown",
        )
    elif session.status == WorkflowStatus.REJECTED:
        st.info("Human rejection recorded. No final downloadable report is released.")
    elif session.status == WorkflowStatus.MANUAL_REVIEW:
        st.warning(
            "Human adjudication is required. No second automated revision is permitted."
        )

    st.subheader("Visible audit-event list")
    for event in session.audit.events:
        st.markdown(
            f"{event.timestamp.isoformat()} | {event.actor} | {event.action} | "
            f"{event.from_status.value} -> {event.to_status.value} | {event.notes or ''}"
        )

st.divider()
st.caption(
    "Synthetic local prototype only. No live model, MuleRun runtime authority, customer data, "
    "pricing, external sending, production hosting or deployment commitment."
)
