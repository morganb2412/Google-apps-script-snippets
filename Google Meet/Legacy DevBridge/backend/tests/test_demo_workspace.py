import pytest

from app.demo.models import SyncState
from app.demo.service import DemoWorkspaceService


def test_demo_workspace_exercises_source_control_flow() -> None:
    service = DemoWorkspaceService()
    workspace = service.connect("legacy-automations", "atlas-demo")
    assert workspace.connected is True
    assert workspace.repository == "legacy-automations/atlas-demo"
    assert {change.state for change in workspace.changes} == {
        SyncState.CONFLICT,
        SyncState.REMOTE_ADDED,
    }
    assert service.create_branch("feature/approval-workflow").branch == "feature/approval-workflow"
    assert service.commit("feat: improve approvals").latest_commit == "feat: improve approvals"
    assert service.create_pull_request().pull_request_url == (
        "https://github.com/legacy-automations/atlas-demo/pull/1"
    )


def test_demo_agent_reports_no_oauth_changes() -> None:
    result = DemoWorkspaceService().plan("Add Finance approval")
    assert result.mode == "DEMO"
    assert result.oauth_changes == []
    assert "ApprovalService.gs" in result.files_affected


def test_code_assistant_requires_proposal_decision() -> None:
    service = DemoWorkspaceService()
    response = service.chat("Analyze standards and fix the hard-coded email")
    assert response.proposal is not None
    assert response.proposal.status == "PENDING_APPROVAL"
    assert response.proposal.original_hash
    approved = service.decide_proposal(approved=True)
    assert approved.proposal is not None
    assert approved.proposal.status == "APPLIED_DEMO"
    assert service.get().applied_proposal == "demo-fix-001"
    assert "does not write to an external" in approved.message
    assert service.get().audit_events[-1] == "Code Assistant change approved and applied"


def test_demo_source_control_sequence_fails_closed() -> None:
    service = DemoWorkspaceService()
    with pytest.raises(ValueError, match="Connect a repository"):
        service.create_branch("feature/safe")
    service.connect("legacy-automations", "atlas-demo")
    with pytest.raises(ValueError, match="main are prohibited"):
        service.commit("feat: unsafe direct commit")
    service.create_branch("feature/safe")
    with pytest.raises(ValueError, match="Commit the approved changes"):
        service.create_pull_request()
