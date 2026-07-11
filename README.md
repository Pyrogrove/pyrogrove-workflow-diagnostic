# PyroGrove Workflow Diagnostic Agentic Service

> **PRACTICE BUILD — NOT CLAIMED AS EVENT-DAY WORK**

This repository is the Saturday private-practice baseline for the BUIDL OPC Hackathon exercise.

## Current stage

`SATURDAY PREPARATION`

No project-specific application logic exists at this baseline. The application may be implemented only after Chee issues:

```text
START PRACTICE BUILD
```

## Frozen architecture

```text
LANE B — STREAMLIT CORE WITH MULERUN AUXILIARY
```

Authoritative core:

- Python
- Streamlit
- Pydantic
- plain Python state machine
- JSON or SQLite
- pytest
- Ruff
- Git/GitHub evidence

MuleRun is auxiliary only. It is not the deterministic authority, approval authority, sole source record, or only evidence store.

## Data and secrets boundary

- Synthetic data only.
- No client, personal, confidential, regulated, or production data.
- No live secrets committed to Git.
- No external API is required for v0.1.
- `.env`, Streamlit secrets, private keys, virtual environments, and runtime state are ignored.

## Spending boundary

New cash spending: `USD 0`.

## Pre-hackathon evidence

The repository baseline must be committed and tagged:

```text
pre-hackathon-baseline
```

That tag proves what existed before the project-specific practice implementation.
