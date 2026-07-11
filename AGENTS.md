# Repository Agent Instructions

## Authority

Chee is the product owner, business-rule approver, spending authority, release authority, publication authority, and external-communication authority.

Agents may implement, test, review, and recommend within approved scope.

Agents may not:

- change deterministic qualification rules;
- change score bands or permitted routes;
- bypass human confirmation or approval;
- weaken acceptance tests;
- invent evidence;
- price, send externally, publish, deploy, or make customer commitments;
- claim production readiness;
- introduce excluded architecture or paid tools without approval.

## Source priority

1. Chee's current explicit instruction.
2. `docs/workflow-build-brief.md`.
3. `docs/acceptance-tests.md`.
4. `PROJECT_RULES.md`.
5. `docs/architecture.md`.
6. Existing implementation.
7. Agent assumptions.

When sources conflict, report the conflict. Do not silently blend them.

## Current command gate

At this baseline, do not implement project-specific application logic.

Implementation begins only after:

```text
START PRACTICE BUILD
```

## Completion response

For every build step return:

- files changed;
- commands run;
- expected output;
- actual result;
- tests added;
- test result;
- evidence saved;
- assumptions;
- deviations;
- limitations;
- next decision required.

Do not claim completion without executable evidence.
