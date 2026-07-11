# PyroGrove Workflow Diagnostic Agentic Service

> **PRACTICE BUILD — NOT CLAIMED AS EVENT-DAY WORK**

A local Streamlit v0.1 that demonstrates a controlled workflow-diagnostic loop using deterministic Python rules and simulated AI roles.

## What this practice build proves

```text
workflow narrative and synthetic evidence
-> deterministic MockExtractor
-> human fact confirmation
-> required-fact gate
-> ten-criterion qualification
-> deterministic score and band
-> deterministic MockSolutionArchitect
-> independent MockReviewer
-> maximum one controlled revision
-> human approval or rejection
-> approved Markdown report
-> visible audit events
```

AI roles are simulated with deterministic local adapters in v0.1. No live model API is used.

## Authoritative controls

- Only `YES` scores one point across the ten frozen criteria.
- `8–10 = MVP_CANDIDATE`, `5–7 = DIAGNOSTIC_ONLY`, `0–4 = NOT_QUALIFIED`.
- Allowed routes are `M365`, `RPA_DESKTOP`, `DATA_CODE`, `CODED_MICROAPP`, and `NO_BUILD`.
- Missing required facts generate exactly one highest-value clarification question per cycle.
- A High or Critical finding permits at most one automated revision.
- A persistent material finding after that revision requires human adjudication.
- Approval cannot be bypassed.
- Invalid simulated-role output fails safely and disables report release.
- Every consequential state transition writes an in-memory audit event.

## Files

```text
app.py
src/pyrogrove_diagnostic/
    __init__.py
    models.py
    synthetic_cases.py
    extraction.py
    qualification.py
    state_machine.py
    recommendation.py
    reviewer.py
    audit.py
    report.py
tests/
    test_qualification.py
    test_state_machine.py
    test_report.py
    test_acceptance.py
KNOWN_LIMITATIONS.md
```

## Run on Windows PowerShell

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python -m ruff check app.py src tests
python -m ruff format --check app.py src tests
python -m streamlit run app.py
```

## Recommended demo path

1. Load `CASE-01`.
2. Run `MockExtractor`.
3. Confirm the prefilled facts.
4. Select Reviewer mode `HIGH_ONCE`.
5. Generate the recommendation and review.
6. Apply the one controlled revision.
7. Approve the report.
8. Download the Markdown report and inspect the audit list.
9. Run `CASE-02` to show one clarification question.
10. Run `CASE-03` to show safe `NO_BUILD` rejection.
11. Select an invalid-output simulation to show fail-safe handling.

## Scope boundary

This is a synthetic local practice build. It is not evidence of customer use, market validation, event-day work, production security, production deployment, savings, pricing, or autonomous consulting authority.
