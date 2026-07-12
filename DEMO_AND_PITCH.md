# Hackathon Demo and Pitch

## 90-Second Demo Route

1. Open the public application:
   https://pyrogrove-workflow-diagnostic.streamlit.app

2. Point to:
   - How the Agentic Service Works
   - Roles, Tools and Authority
   - Human authority and bounded revision controls

3. Select:
   - Synthetic example: CASE-01
   - Failure simulation: None
   - Reviewer test mode: HIGH_ONCE

4. Click:
   - Load selected case
   - Run deterministic MockExtractor
   - Confirm facts and run deterministic qualification
   - Generate recommendation
   - Run reviewer

5. Explain:
   The reviewer raises one material finding, so the workflow enters REVISION_REQUIRED.

6. Click:
   - Apply one controlled revision
   - Run reviewer again
   - Approve

7. Show:
   - APPROVED state
   - Qualification score 10/10
   - MVP_CANDIDATE decision
   - Revisions 1/1
   - Visible audit-event list
   - Download approved Markdown report

8. Final line:
   This prototype demonstrates controlled agentic execution: specialised roles collaborate, deterministic rules remain authoritative, and a human retains final release authority.

## Three-Minute Pitch

SMEs often start automation projects too early. They may have a vague pain, incomplete facts, no clear workflow owner and no agreed success criteria. The result is wasted implementation effort, uncontrolled scope and unsuitable technology choices.

PyroGrove Workflow Diagnostic Agentic Service converts one workflow narrative into a structured and controlled diagnostic.

The service first uses an Extractor role to structure the workflow facts. A human must confirm those facts before the process can continue. A deterministic ten-criterion qualification tool then decides whether the workflow is an MVP candidate, diagnostic-only case or no-build case.

For a qualified workflow, a Solution Architect role proposes the right-sized route and MVP scope. An independent Reviewer role challenges the recommendation. The service permits a maximum of one controlled revision. If the finding remains unresolved, the workflow stops for human adjudication rather than continuing autonomously.

The final recommendation cannot be released until a human approves it. Every consequential transition is recorded in a visible audit trail, and the approved result can be downloaded as a Markdown diagnostic report.

The agentic value is not uncontrolled autonomy. It is role separation, shared state, conditional routing, deterministic tool execution, bounded revision and human authority.

The current public prototype uses deterministic local role adapters rather than a live model API. This is deliberate disclosure. It proves the workflow controls, failure paths, review loop and release boundary without claiming production autonomy.

The commercial direction is a one-person consultant packaging workflow-diagnostic expertise into a repeatable service. AI can later replace selected role adapters, but the deterministic qualification rules and human approval boundary remain unchanged.
