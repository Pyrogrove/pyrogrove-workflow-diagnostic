# PyroGrove Workflow Diagnostic Report

> **PRACTICE BUILD — NOT CLAIMED AS EVENT-DAY WORK**

> AI roles are simulated with deterministic local adapters in v0.1. No live model API is used.

## Approval status

- Case: `CASE-01` — Complete RFQ and customer-enquiry workflow
- Final status: `APPROVED`
- Human approval: recorded
- Automated revisions used: `1/1`

## Problem statement

Sales Coordinator currently handles 'Complete RFQ and customer-enquiry workflow' with manual checks and exceptions, creating this consequence: Slow response, repeated chasing, missed information and reduced quotation conversion.

## Confirmed workflow facts

- Workflow owner: Sales Operations Manager
- Primary user: Sales Coordinator
- Trigger: Customer RFQ or enquiry arrives in Outlook
- Inputs: RFQ email, attachments, customer and product details
- Outputs: quote-readiness record, clarification draft, exception queue
- Frequency: WEEKLY
- Monthly volume: 160
- Current tools: Outlook, Excel, Microsoft 365
- Consequence: Slow response, repeated chasing, missed information and reduced quotation conversion.
- Exceptions: Missing quantity, Missing required date, Ambiguous specification

## Deterministic qualification

Score: **10/10**  
Decision: **MVP_CANDIDATE**

| Criterion | Result |
|---|---|
| Repeated Pain | YES |
| Frequency | YES |
| Volume | YES |
| Named Workflow Owner | YES |
| Business Impact | YES |
| Sample Evidence | YES |
| Budget Signal | YES |
| Timeline | YES |
| Narrow Mvp Fit | YES |
| Supportability | YES |

## Right-sized recommendation

- Recommended route: **M365**
- Rationale: The workflow is internal and already uses Outlook, Excel or Microsoft 365.

### Deterministic workflow steps

- Capture one workflow request in a structured record.
- Validate required fields and permitted values.
- Assign an explicit status and exception owner.
- Preserve an audit event for each consequential transition.
- If automated processing fails, stop, preserve the audit trace and return the case to the human operator for manual fallback.

### Simulated AI-assisted steps

- Simulated extraction of structured facts from the narrative.
- Simulated architecture drafting and reviewer challenge.

### Human control points

- Confirm extracted facts before qualification.
- Adjudicate any unresolved High or Critical finding.
- Approve or reject the final report before download.

### MVP scope

- One workflow and one primary user role.
- Required-field validation and deterministic qualification.
- One recommendation, one reviewer pass and at most one automated revision.
- Markdown report and visible audit evidence.

### Explicit exclusions

- No live model API, production hosting, customer authentication or multi-tenancy.
- No pricing, external sending, deployment commitment or customer commitment.
- No Hermes, RAG, MCP, n8n, FastAPI, Docker or database persistence.

### Failure modes and manual fallback

- Missing required fact routes to NEEDS_CLARIFICATION.
- Invalid adapter output routes to FAILED and disables approval.
- Persistent High finding after one revision routes to MANUAL_REVIEW.
- Manual fallback preserves the case and audit trace without an external commitment.

### Acceptance tests

- Complete case reaches READY_FOR_APPROVAL and can be approved by a human.
- Incomplete case asks exactly one highest-value clarification question.
- Vague AI request is rejected safely with NO_BUILD.
- High reviewer finding triggers no more than one automated revision.
- Every consequential state transition has an audit event.

### Assumptions

- All data is synthetic.
- The selected case represents one workflow only.
- M365 licensing and production feasibility are not validated in this practice build.

### Open questions

- Who would approve a real diagnostic budget?
- Which three sanitised examples would define actual exception patterns?

## Reviewer findings

| Finding | Severity | Resolution | Business impact |
|---|---|---|---|
| None | — | — | No reviewer finding recorded. |

## Audit events

| Timestamp | Actor | Action | From | To | Notes |
|---|---|---|---|---|---|
| 2026-07-12T03:32:28.673934+00:00 | MockExtractor | START_DISCOVERY | NEW | DISCOVERY |  |
| 2026-07-12T03:32:28.673981+00:00 | Human | CONFIRM_FACTS | DISCOVERY | HUMAN_CONFIRMATION |  |
| 2026-07-12T03:32:28.674034+00:00 | System | RUN_QUALIFICATION | HUMAN_CONFIRMATION | QUALIFICATION |  |
| 2026-07-12T03:32:28.674113+00:00 | System | SET_QUALIFICATION_DECISION | QUALIFICATION | ARCHITECTURE_DRAFT | Score 10/10. |
| 2026-07-12T03:32:32.022825+00:00 | MockSolutionArchitect | DRAFT_ARCHITECTURE_RECOMMENDATION | ARCHITECTURE_DRAFT | ARCHITECTURE_DRAFT | Route: M365 |
| 2026-07-12T03:32:32.022874+00:00 | MockReviewer | START_REVIEW | ARCHITECTURE_DRAFT | REVIEW |  |
| 2026-07-12T03:32:32.022942+00:00 | MockReviewer | RAISE_MATERIAL_FINDING | REVIEW | REVISION_REQUIRED | 1 material finding(s). |
| 2026-07-12T03:32:35.239244+00:00 | MockSolutionArchitect | APPLY_ONE_CONTROLLED_REVISION | REVISION_REQUIRED | ARCHITECTURE_DRAFT | Automated revision count is now 1/1. |
| 2026-07-12T03:32:35.239302+00:00 | MockReviewer | START_REVIEW | ARCHITECTURE_DRAFT | REVIEW |  |
| 2026-07-12T03:32:35.239367+00:00 | MockReviewer | REVIEW_COMPLETE | REVIEW | READY_FOR_APPROVAL |  |
| 2026-07-12T03:32:37.968456+00:00 | Human | APPROVE_REPORT | READY_FOR_APPROVAL | APPROVED |  |

## Practice-build limitation

This report is synthetic, local and non-production. It does not prove market demand, customer savings, production security, deployment readiness or event-day work.
