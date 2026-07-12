# PyroGrove Workflow Diagnostic Agentic Service

A live bounded Agentic Service that helps a small business decide whether a workflow should be automated before committing time and money to implementation.

## Live Demo

https://pyrogrove-workflow-diagnostic-v2.streamlit.app

## Business Problem

Small businesses often begin automation projects with incomplete workflow facts, unclear ownership, weak fallback planning and no objective qualification criteria.

This creates three common risks:

- automating the wrong process;
- selecting an unnecessarily complex technology;
- releasing a recommendation without adequate human control.

PyroGrove converts a workflow narrative into a structured, reviewed and auditable diagnostic.

## How the Service Works

```text
SME workflow narrative
        |
        v
Deterministic fact extraction
        |
        v
Human fact confirmation
        |
        v
Ten-criterion qualification tool
        |
        v
Deterministic solution recommendation
        |
        v
Live DeepSeek independent review
        |
        v
Strict Pydantic validation
        |
        +-------------------------------+
        |                               |
        | PASS                          | REVISION_REQUIRED / HIGH
        v                               v
READY_FOR_APPROVAL              One controlled revision
        |                               |
        |                               v
        |                       Second live review
        |                               |
        |                 +-------------+-------------+
        |                 |                           |
        |                 | PASS                      | HIGH again
        |                 v                           v
        |          READY_FOR_APPROVAL        HUMAN_ADJUDICATION
        |                                             |
        +----------------------+----------------------+
                               |
                               v
                       Human approval/rejection
                               |
                               v
                  Markdown report + visible audit trail
```

## Live Agentic Element

`LIVE_DEEPSEEK` mode uses DeepSeek V4 Flash as a bounded independent reviewer.

The live reviewer receives:

- confirmed workflow facts;
- the deterministic qualification result;
- the proposed architecture recommendation;
- the number of controlled revisions already used.

It must return a strict JSON object:

```json
{
  "decision": "PASS or REVISION_REQUIRED",
  "severity": "NONE or HIGH",
  "finding": "string",
  "recommended_change": "string"
}
```

The response is validated with Pydantic before it can affect workflow state.

```text
PASS
-> READY_FOR_APPROVAL

REVISION_REQUIRED + no revision used
-> REVISION_REQUIRED
-> one controlled correction

REVISION_REQUIRED + revision already used
-> HUMAN_ADJUDICATION

API / timeout / JSON / schema failure
-> FAILED
-> approval blocked
```

There is no silent fallback to the mock reviewer in live mode.

## Why This Is Agentic

The live model does more than generate text.

It:

1. receives the current workflow context;
2. independently evaluates the recommendation;
3. returns a constrained decision;
4. has that output validated;
5. determines the next workflow route;
6. can trigger revision, approval readiness or fail-safe escalation.

Human approval remains mandatory before release.

## Roles and Authority

| Role or tool | Implementation | Function | Authority limit |
|---|---|---|---|
| MockExtractor | Deterministic Python adapter | Structures synthetic workflow facts | Cannot confirm facts |
| Human operator | Human | Confirms workflow facts | Final authority over facts |
| Qualification tool | Deterministic Python | Applies ten frozen criteria | Cannot alter criteria |
| MockSolutionArchitect | Deterministic Python adapter | Proposes route and MVP scope | Cannot approve release |
| DeepSeekReviewer | Live DeepSeek V4 Flash API | Independently reviews the recommendation | Cannot change qualification results |
| State machine | Deterministic Python | Enforces routing and revision limits | Cannot bypass human approval |
| Human approver | Human | Approves or rejects release | Final release authority |

## Demonstrated SME Scenario

A Singapore industrial distributor receives approximately 40 RFQs each week.

Some requests arrive with missing quantities, unclear required dates or ambiguous specifications. Before investing in automation, the business needs to determine:

- whether the pain is recurring and measurable;
- whether the workflow rules are stable;
- who owns exceptions and recovery;
- whether M365, RPA, a coded micro-application or no build is appropriate;
- whether the recommendation includes a safe manual fallback.

In the recommended case, the first DeepSeek review identifies that fallback, recovery and responsible human ownership are not explicit.

The service then:

```text
DeepSeek finding
        |
        v
REVISION_REQUIRED
        |
        v
One controlled correction
        |
        v
Second live DeepSeek review
        |
        v
PASS
        |
        v
Human approval
        |
        v
Auditable Markdown report
```

## Authoritative Controls

- Only `YES` scores one point across the ten frozen criteria.
- `8–10 = MVP_CANDIDATE`.
- `5–7 = DIAGNOSTIC_ONLY`.
- `0–4 = NOT_QUALIFIED`.
- Allowed routes are `M365`, `RPA_DESKTOP`, `DATA_CODE`, `CODED_MICROAPP` and `NO_BUILD`.
- The live reviewer cannot change qualification results.
- A material finding permits at most one automated revision.
- A persistent finding requires human adjudication.
- Missing API credentials, HTTP errors, empty content, malformed JSON and schema failures block approval.
- Human approval cannot be bypassed.
- Every consequential transition creates an audit event.

## Verified Build

```text
Automated tests:
36 passed

Ruff lint:
passed

Ruff format:
passed

Public deployment:
verified

Public live review:
verified

Audit actor:
DeepSeekReviewer

Approved report download:
verified
```

## Key Files

```text
app.py
src/pyrogrove_diagnostic/
    models.py
    extraction.py
    qualification.py
    recommendation.py
    reviewer.py
    deepseek_reviewer.py
    state_machine.py
    audit.py
    report.py
tests/
    test_qualification.py
    test_state_machine.py
    test_deepseek_reviewer.py
    test_report.py
    test_acceptance.py
```

## Run Locally on Windows

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
$env:DEEPSEEK_API_KEY = "your-key"
python -m pytest -q
python -m ruff check app.py src tests
python -m ruff format --check app.py src tests
python -m streamlit run app.py
```

Never commit an API key to the repository.

## Build Disclosure

The deterministic workflow foundation was completed as a disclosed practice build before the event.

Event-day work added and verified:

- the live DeepSeek reviewer;
- strict Pydantic validation;
- model-controlled workflow routing;
- bounded retry and fail-safe behaviour;
- one controlled revision;
- public Streamlit v2 deployment;
- visible `DeepSeekReviewer` audit evidence;
- downloadable report generation.

## Scope and Limitations

This is a synthetic hackathon prototype.

It is not evidence of:

- production customer deployment;
- market validation;
- autonomous consulting authority;
- production security certification;
- guaranteed savings;
- unattended external-system actions.

The Extractor and Solution Architect remain deterministic adapters. DeepSeek is used only for the bounded independent-review role. Deterministic qualification and human release approval remain authoritative.
