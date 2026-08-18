from copy import deepcopy
from typing import Protocol

from app.audit.models import AuditEvent


class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...
    def list_for_actor(self, actor_id: str) -> list[AuditEvent]: ...


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self._events.append(deepcopy(event))

    def list_for_actor(self, actor_id: str) -> list[AuditEvent]:
        return [deepcopy(event) for event in self._events if event.actor_id == actor_id]
