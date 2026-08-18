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
