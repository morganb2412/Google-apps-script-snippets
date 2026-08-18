from app.onboarding.models import IntegrationHealthItem, IntegrationHealthResponse, UserSetupState


def build_integration_health(state: UserSetupState) -> IntegrationHealthResponse:
    items = [
        _item("google", "Google Account", state.google_connected, "Connect Google"),
        _item("appsscript", "Apps Script", state.project_detected, "Open Apps Script"),
        _item("github", "GitHub", state.github_connected, "Connect GitHub"),
        _item("repository", "Repository", state.repository_connected, "Select repository"),
        _item("standards", "Company Standards", state.standards_configured, "Choose standards"),
        _item("ai", "Code Assistant", state.ai_ready, "Configure AI"),
    ]
    return IntegrationHealthResponse(
        ready=all(item.status == "READY" for item in items),
        items=items,
    )


def _item(key: str, label: str, ready: bool, action: str) -> IntegrationHealthItem:
    return IntegrationHealthItem(
        key=key,
        label=label,
        status="READY" if ready else "NEEDS_ATTENTION",
        message="Ready" if ready else f"{label} needs attention.",
        action=None if ready else action,
    )
