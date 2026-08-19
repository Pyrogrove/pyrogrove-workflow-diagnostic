---
project_name: PyroGrove Workflow Diagnostic
repository: https://github.com/Pyrogrove/pyrogrove-workflow-diagnostic
project_type: streamlit-agentic-service
lifecycle: hackathon-prototype
stack: python, streamlit, pydantic, requests, deepseek-api
tags: workflow-automation, agentic-ai, deepseek, sme-tooling, hackathon
deployment: streamlit-community-cloud
deployment_url: https://pyrogrove-workflow-diagnostic-v2.streamlit.app
last_verified: 2026-08-19
---

## Purpose

A bounded Streamlit agentic service that helps a small business decide whether a workflow should be automated before committing time and money. It converts a workflow narrative into a structured, reviewed and auditable diagnostic: deterministic fact extraction, a ten-criterion qualification score, a deterministic solution recommendation, and a live DeepSeek independent review gate before human approval.

## Current State

Branch `event-day-live-agentic-v2` (HEAD `5d03a7b`) is a candidate retained milestone. The deterministic workflow foundation (extraction, qualification, recommendation, state machine, audit trail, Markdown report) was a disclosed pre-event practice build; the live DeepSeek reviewer, strict Pydantic validation of its output, model-controlled routing, bounded retry/fail-safe behaviour and the public v2 deployment were added and verified on event day. See [README.md](README.md) for the full architecture diagram and role/authority table, and [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) / [EVENT_DAY_DISCLOSURE.md](EVENT_DAY_DISCLOSURE.md) for disclosure detail.

## Demonstrated Capabilities

- Deterministic fact extraction and human fact confirmation.
- Ten-criterion qualification scoring into `MVP_CANDIDATE` / `DIAGNOSTIC_ONLY` / `NOT_QUALIFIED`.
- Deterministic solution recommendation across `M365`, `RPA_DESKTOP`, `DATA_CODE`, `CODED_MICROAPP`, `NO_BUILD`.
- Live DeepSeek V4 Flash independent review, returning a schema-validated PASS / REVISION_REQUIRED decision that drives workflow routing (one controlled revision, then human adjudication on a repeat finding).
- Fail-safe blocking of approval on missing API key, HTTP error, empty content, malformed JSON, or schema-validation failure.
- Human approval gate and downloadable Markdown report with visible audit trail.

## Verification

Performed 2026-08-19, in a fresh local venv (Python 3.14; requirements installed without exact pinned versions, since `pydantic==2.11.7` has no prebuilt wheel for Python 3.14 in this environment and no C build toolchain was available to compile it):

- `pytest -q` — **36 passed**, matching the count in README's "Verified Build" section.
- `ruff format --check` — **17 files already formatted, PASS**.
- `ruff check` — **FAIL (15 issues)**: import-sort (`I001`) and style nits (`SIM102`, `SIM114`, `UP037`) across `app.py` and several `src/pyrogrove_diagnostic/*.py` files. No `ruff`/`pyproject.toml` lint config is committed to the repo, and no `ruff` version is pinned in `requirements.txt`, so this could not be reproduced against whatever ruff version/config produced README's "Ruff lint: passed" claim. Treated as an **UNVERIFIED reproduction of a documented pass**, not a confirmed regression — no application code was modified to chase a clean lint run.
- Live deployment `https://pyrogrove-workflow-diagnostic-v2.streamlit.app` — reachable and resolves to the app (currently in Streamlit Community Cloud's sleep state pending a wake click); confirms the URL is a real, valid deployment.
- Secrets scan — no committed `.env`, key, credential, or literal API-key value found; all `api_key`/`Authorization` references are environment-variable reads or test fixtures using placeholder strings (e.g. `"test-key"`). `.gitignore` excludes `.env*`, `*.pem`, `*.key`, `secrets/`, `.streamlit/secrets.toml`.
- Tracked file sizes — largest tracked files are PNG evidence screenshots at ~256 KB; nothing unusually large.
- Working tree — clean at time of review; nothing untracked or staged.

## Known Limitations

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the full authoritative list. Summary: synthetic-data-only prototype; extraction supports fixed fixtures rather than general NL extraction; state/audit exist only in Streamlit session memory; no auth, multi-tenancy, database or production secret management; M365 recommendation is architectural only; not a substitute for customer discovery or ROI validation.

## Next Action

Owner (Chee) to review this pre-push gate output and approve commit/push. No code changes are pending from this verification pass.
