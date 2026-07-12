# PyroGrove Workflow Diagnostic Agentic Service

A live, bounded agentic service that helps an SME decide whether a workflow should be automated before committing time and money to implementation.

## Live Demo

https://pyrogrove-workflow-diagnostic-v2.streamlit.app

## Business Problem

SMEs often begin automation projects with incomplete workflow facts, unclear ownership, weak fallback planning and no objective qualification criteria.

This creates three risks:

- automating the wrong process;
- selecting an unnecessarily complex technology;
- releasing a recommendation without adequate human control.

PyroGrove converts a workflow narrative into a structured, reviewed and auditable diagnostic.

## How the Service Works

```text
SME workflow narrative
-> deterministic fact extraction
-> human fact confirmation
-> ten-criterion qualification tool
-> deterministic solution recommendation
-> live DeepSeek independent review
-> Pydantic validation
-> conditional workflow routing
-> maximum one controlled revision
-> second live review
-> human release approval
-> downloadable report and audit trail
