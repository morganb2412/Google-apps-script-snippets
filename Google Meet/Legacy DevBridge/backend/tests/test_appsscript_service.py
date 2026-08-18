import asyncio

import pytest

from app.appsscript.models import (
    AppsScriptContent,
    AppsScriptFile,
    AppsScriptFileType,
    AppsScriptProject,
    SafeUpdateRequest,
)
from app.appsscript.normalization import create_snapshot, manifest_scopes, normalize_file
from app.appsscript.service import (
    AppsScriptApprovalRequiredError,
    AppsScriptService,
    AppsScriptStaleWriteError,
)
from app.audit.repository import InMemoryAuditRepository


class FakeAppsScriptGateway:
    def __init__(self, content: AppsScriptContent) -> None:
        self.content = content.model_copy(deep=True)
        self.update_calls = 0

    async def get_project(self, script_id: str, access_token: str) -> AppsScriptProject:
        return AppsScriptProject(scriptId=script_id, title="ATLAS")

    async def get_content(self, script_id: str, access_token: str) -> AppsScriptContent:
        return self.content.model_copy(deep=True)

    async def update_content(
        self, script_id: str, files: list[AppsScriptFile], access_token: str
    ) -> AppsScriptContent:
        self.update_calls += 1
        self.content = AppsScriptContent(script_id=script_id, files=files)
        return self.content.model_copy(deep=True)


def content(source: str = "function run() {}") -> AppsScriptContent:
    return AppsScriptContent(
        script_id="script-123",
        files=[
            AppsScriptFile(name="Code", type=AppsScriptFileType.SERVER_JS, source=source),
            AppsScriptFile(
                name="appsscript",
                type=AppsScriptFileType.JSON,
                source='{"runtimeVersion":"V8","oauthScopes":[]}',
            ),
        ],
    )


def test_normalizes_line_endings_and_hashes_deterministically() -> None:
    normalized = normalize_file(
        AppsScriptFile(name="Code", type=AppsScriptFileType.SERVER_JS, source="a\r\nb\r")
    )
    assert normalized.path == "Code.gs"
    assert normalized.content == "a\nb\n"
    assert len(normalized.sha256) == 64
    assert create_snapshot(content()).project_hash == create_snapshot(content()).project_hash


def test_manifest_scope_parser_validates_scope_shape() -> None:
    files = [
        AppsScriptFile(
            name="appsscript",
            type=AppsScriptFileType.JSON,
            source='{"oauthScopes":["scope.one"]}',
        )
    ]
    assert manifest_scopes(files) == {"scope.one"}


def test_safe_update_rejects_unapproved_and_stale_writes() -> None:
    gateway = FakeAppsScriptGateway(content())
    service = AppsScriptService(gateway, InMemoryAuditRepository())
    files = content("function run() { return true; }").files

    with pytest.raises(AppsScriptApprovalRequiredError):
        asyncio.run(
            service.safe_update(
                "actor",
                "script-123",
                SafeUpdateRequest(expected_project_hash="0" * 64, files=files),
                "token",
            )
        )
    with pytest.raises(AppsScriptStaleWriteError):
        asyncio.run(
            service.safe_update(
                "actor",
                "script-123",
                SafeUpdateRequest(expected_project_hash="0" * 64, approved=True, files=files),
                "token",
            )
        )
    assert gateway.update_calls == 0


def test_safe_update_verifies_state_and_audits_without_tokens() -> None:
    current = content()
    gateway = FakeAppsScriptGateway(current)
    audit = InMemoryAuditRepository()
    service = AppsScriptService(gateway, audit)
    updated_files = content("function run() { return true; }").files
    result = asyncio.run(
        service.safe_update(
            "actor",
            "script-123",
            SafeUpdateRequest(
                expected_project_hash=create_snapshot(current).project_hash,
                approved=True,
                files=updated_files,
            ),
            "secret-access-token",
        )
    )
    assert gateway.update_calls == 1
    assert result.verified_hash == create_snapshot(gateway.content).project_hash
    event = audit.list_for_actor("actor")[0]
    assert event.action == "APPS_SCRIPT_WRITE"
    assert "token" not in str(event.model_dump()).lower()


def test_safe_update_requires_separate_oauth_scope_approval() -> None:
    current = content()
    gateway = FakeAppsScriptGateway(current)
    service = AppsScriptService(gateway, InMemoryAuditRepository())
    changed = content().files
    changed[1].source = '{"oauthScopes":["https://www.googleapis.com/auth/drive"]}'

    with pytest.raises(AppsScriptApprovalRequiredError, match="OAuth scopes"):
        asyncio.run(
            service.safe_update(
                "actor",
                "script-123",
                SafeUpdateRequest(
                    expected_project_hash=create_snapshot(current).project_hash,
                    approved=True,
                    files=changed,
                ),
                "token",
            )
        )
    assert gateway.update_calls == 0
