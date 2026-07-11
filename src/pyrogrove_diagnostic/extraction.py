"""Replaceable deterministic adapter that simulates structured extraction."""

from __future__ import annotations

from pydantic import ValidationError

from .models import ExtractorEnvelope, UNKNOWN, WorkflowCase
from .synthetic_cases import get_synthetic_case


class MockOutputError(ValueError):
    """Raised when a simulated role returns output that fails its schema boundary."""


class MockExtractor:
    """Loads only approved synthetic fixtures; it is not a general NLP extractor."""

    role = "MockExtractor"

    def extract(
        self,
        narrative: str,
        *,
        synthetic_case_id: str | None = None,
        invalid_output: bool = False,
    ) -> WorkflowCase:
        if invalid_output:
            raw: dict[str, object] = {
                "role": self.role,
                "case": {"case_id": 123, "unexpected": "malformed"},
            }
        elif synthetic_case_id:
            case = get_synthetic_case(synthetic_case_id)
            case.workflow_narrative = narrative.strip() or case.workflow_narrative
            raw = {"role": self.role, "case": case.model_dump(mode="json")}
        else:
            # Deliberately conservative fallback: unknown values remain unknown.
            case = WorkflowCase(
                case_id="MANUAL-INPUT",
                title="Manual workflow input",
                workflow_narrative=narrative.strip(),
                workflow_owner=UNKNOWN,
                primary_user=UNKNOWN,
                trigger=UNKNOWN,
            )
            raw = {"role": self.role, "case": case.model_dump(mode="json")}

        try:
            envelope = ExtractorEnvelope.model_validate(raw)
        except ValidationError as exc:
            raise MockOutputError(
                "MockExtractor output failed schema validation"
            ) from exc
        return envelope.case
