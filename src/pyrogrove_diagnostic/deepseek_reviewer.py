"""Bounded live DeepSeek adapter for independent recommendation review."""

from __future__ import annotations

import json
from typing import Any

import requests
from pydantic import ValidationError

from .extraction import MockOutputError
from .models import (
    DiagnosticRecommendation,
    LiveReviewDecision,
    LiveReviewResponse,
    QualificationResult,
    ResolutionStatus,
    ReviewFinding,
    ReviewerMode,
    Severity,
    WorkflowCase,
)

DEEPSEEK_ENDPOINT = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"


class _MalformedAPIResponse(ValueError):
    """Signal a malformed API response that permits the single retry."""


class DeepSeekReviewer:
    """Call DeepSeek and convert strictly validated output to existing findings."""

    role = "DeepSeekReviewer"

    def __init__(self, *, api_key: str | None, qualification: QualificationResult):
        self.api_key = api_key
        self.qualification = qualification
        self.last_result: LiveReviewResponse | None = None

    def review(
        self,
        case: WorkflowCase,
        recommendation: DiagnosticRecommendation,
        *,
        mode: ReviewerMode = ReviewerMode.LIVE_DEEPSEEK,
        revision_count: int = 0,
    ) -> list[ReviewFinding]:
        if mode != ReviewerMode.LIVE_DEEPSEEK:
            raise MockOutputError("DeepSeekReviewer requires LIVE_DEEPSEEK mode")
        if not self.api_key:
            raise MockOutputError("DEEPSEEK_API_KEY is required for live review")

        payload = {
            "model": DEEPSEEK_MODEL,
            "temperature": 0,
            "max_tokens": 1000,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {
                    "role": "user",
                    "content": self._review_context(
                        case,
                        recommendation,
                        revision_count=revision_count,
                    ),
                },
            ],
        }

        for attempt in range(2):
            attempt_payload = payload
            if attempt == 1:
                messages = [message.copy() for message in payload["messages"]]
                messages[-1]["content"] += (
                    "\n\nReturn the required JSON object now. Do not return analysis, "
                    "Markdown, or empty content."
                )
                attempt_payload = {**payload, "messages": messages}
            try:
                content = self._request_content(attempt_payload)
            except _MalformedAPIResponse as exc:
                if attempt == 0:
                    continue
                raise MockOutputError(
                    "DeepSeek returned malformed JSON after retry"
                ) from exc
            if not content.strip():
                if attempt == 0:
                    continue
                raise MockOutputError("DeepSeek returned empty content after retry")
            try:
                raw = json.loads(content)
            except json.JSONDecodeError as exc:
                if attempt == 0:
                    continue
                raise MockOutputError(
                    "DeepSeek returned malformed JSON after retry"
                ) from exc

            try:
                result = LiveReviewResponse.model_validate(raw)
            except ValidationError as exc:
                raise MockOutputError(
                    "DeepSeek reviewer output failed schema validation"
                ) from exc

            self.last_result = result
            return self._to_findings(result)

        raise MockOutputError("DeepSeek review failed safely")

    def _request_content(self, payload: dict[str, Any]) -> str:
        try:
            response = requests.post(
                DEEPSEEK_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise MockOutputError("DeepSeek HTTP request failed") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise _MalformedAPIResponse from exc
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MockOutputError(
                "DeepSeek response was missing required content"
            ) from exc
        if content is None:
            return ""
        if not isinstance(content, str):
            raise MockOutputError("DeepSeek response content must be text")
        return content

    def _review_context(
        self,
        case: WorkflowCase,
        recommendation: DiagnosticRecommendation,
        *,
        revision_count: int,
    ) -> str:
        context = {
            "confirmed_workflow_facts": case.model_dump(mode="json"),
            "qualification_result": self.qualification.model_dump(mode="json"),
            "current_architecture_recommendation": recommendation.model_dump(
                mode="json"
            ),
            "controlled_revisions_used": revision_count,
        }
        return json.dumps(context, indent=2)

    @staticmethod
    def _system_prompt() -> str:
        return """Return JSON only. Review the recommendation using these bounded rules:
- PASS only when manual fallback, recovery action and responsible human owner are explicit.
- Otherwise return REVISION_REQUIRED with HIGH severity.
- Do not change or invent workflow facts.
- Do not change deterministic qualification results.

Provide exactly this JSON structure with no extra fields:
{
  "decision": "PASS",
  "severity": "NONE",
  "finding": "No material finding.",
  "recommended_change": ""
}
"""

    @staticmethod
    def _to_findings(result: LiveReviewResponse) -> list[ReviewFinding]:
        if result.decision == LiveReviewDecision.PASS:
            return []
        return [
            ReviewFinding(
                finding_id="LIVE-RV-001",
                severity=Severity.HIGH,
                requirement=(
                    "Manual fallback, recovery action and responsible human owner "
                    "must be explicit."
                ),
                evidence=result.finding,
                business_impact=(
                    "The workflow cannot safely recover without explicit human ownership."
                ),
                recommended_correction=result.recommended_change,
                resolution_status=ResolutionStatus.OPEN,
            )
        ]
