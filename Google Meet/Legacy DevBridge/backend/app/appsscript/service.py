from app.appsscript.gateway import AppsScriptGateway
from app.appsscript.models import (
    AppsScriptProject,
    ProjectSnapshot,
    SafeUpdateRequest,
    SafeUpdateResult,
)
from app.appsscript.normalization import create_snapshot, manifest_scopes
from app.audit.models import AuditEvent
from app.audit.repository import AuditRepository


class AppsScriptApprovalRequiredError(RuntimeError):
    pass


class AppsScriptStaleWriteError(RuntimeError):
    pass


class AppsScriptVerificationError(RuntimeError):
    pass


class AppsScriptService:
    def __init__(self, gateway: AppsScriptGateway, audit_repository: AuditRepository) -> None:
        self.gateway = gateway
        self.audit_repository = audit_repository

    async def get_project(self, script_id: str, access_token: str) -> AppsScriptProject:
        return await self.gateway.get_project(script_id, access_token)

    async def get_snapshot(self, script_id: str, access_token: str) -> ProjectSnapshot:
        return create_snapshot(await self.gateway.get_content(script_id, access_token))

    async def safe_update(
        self,
        actor_id: str,
        script_id: str,
        request: SafeUpdateRequest,
        access_token: str,
    ) -> SafeUpdateResult:
        if not request.approved:
            raise AppsScriptApprovalRequiredError(
                "Approve the current diff before updating Apps Script."
            )

        current = await self.gateway.get_content(script_id, access_token)
        current_snapshot = create_snapshot(current)
        if current_snapshot.project_hash != request.expected_project_hash:
            raise AppsScriptStaleWriteError(
                "The Apps Script project changed after this update was prepared. "
                "Review a fresh diff."
            )

        added_scopes = sorted(manifest_scopes(request.files) - manifest_scopes(current.files))
        if added_scopes:
            raise AppsScriptApprovalRequiredError(
                "New OAuth scopes require a separate security approval before applying this update."
            )

        expected = create_snapshot(current.model_copy(update={"files": request.files}))
        await self.gateway.update_content(script_id, request.files, access_token)
        verified = create_snapshot(await self.gateway.get_content(script_id, access_token))
        if verified.project_hash != expected.project_hash:
            raise AppsScriptVerificationError(
                "Apps Script did not retain the approved project state."
            )

        self.audit_repository.append(
            AuditEvent(
                actor_id=actor_id,
                action="APPS_SCRIPT_WRITE",
                script_project_id=script_id,
                metadata={
                    "previous_hash": current_snapshot.project_hash,
                    "verified_hash": verified.project_hash,
                    "files_updated": len(request.files),
                },
            )
        )
        return SafeUpdateResult(
            script_id=script_id,
            previous_hash=current_snapshot.project_hash,
            verified_hash=verified.project_hash,
            files_updated=len(request.files),
        )
