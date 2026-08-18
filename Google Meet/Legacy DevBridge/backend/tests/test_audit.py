from app.audit.models import AuditEvent
from app.audit.repository import InMemoryAuditRepository


def test_audit_repository_is_actor_scoped_and_copies_events() -> None:
    repository = InMemoryAuditRepository()
    event = AuditEvent(
        actor_id="session-one", action="GOOGLE_CONNECTED", metadata={"email_domain": "example.com"}
    )
    repository.append(event)
    repository.append(AuditEvent(actor_id="session-two", action="GOOGLE_CONNECTED"))

    events = repository.list_for_actor("session-one")
    assert len(events) == 1
    assert events[0].metadata == {"email_domain": "example.com"}
    events[0].metadata["token"] = "must-not-change-stored-event"
    assert "token" not in repository.list_for_actor("session-one")[0].metadata
