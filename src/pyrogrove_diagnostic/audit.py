"""In-memory audit-event recording for consequential state transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from .models import AuditEvent, WorkflowStatus


class AuditTrail:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def record(
        self,
        *,
        case_id: str,
        actor: str,
        action: str,
        from_status: WorkflowStatus,
        to_status: WorkflowStatus,
        notes: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=f"AUD-{uuid4().hex[:10].upper()}",
            case_id=case_id,
            actor=actor,
            action=action,
            from_status=from_status,
            to_status=to_status,
            timestamp=datetime.now(UTC),
            notes=notes,
        )
        self._events.append(event)
        return event
