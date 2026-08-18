from typing import Protocol

from app.appsscript.models import ProjectSnapshot
from app.audit.models import AuditEvent
from app.audit.repository import AuditRepository
from app.sync.engine import SyncEngine
from app.sync.models import SyncApplyResult, SyncDirection, SyncPlan
from app.sync.repository import SyncBaseRepository


class SyncStatePort(Protocol):
    async def local_snapshot(self) -> ProjectSnapshot: ...
    async def remote_snapshot(self) -> ProjectSnapshot: ...
    async def apply_pull(
        self, target: ProjectSnapshot, expected_local_hash: str
    ) -> ProjectSnapshot: ...
    async def apply_push(
        self, target: ProjectSnapshot, expected_remote_hash: str
    ) -> ProjectSnapshot: ...


class SyncApprovalRequiredError(RuntimeError):
    pass


class SyncStalePlanError(RuntimeError):
    pass


class SyncVerificationError(RuntimeError):
    pass


class SyncService:
    def __init__(
        self,
        engine: SyncEngine,
        state: SyncStatePort,
        bases: SyncBaseRepository,
        audit: AuditRepository,
    ) -> None:
        self.engine = engine
        self.state = state
        self.bases = bases
        self.audit = audit
        self._plans: dict[str, SyncPlan] = {}

    async def prepare(self, mapping_id: str, direction: SyncDirection) -> SyncPlan:
        local = await self.state.local_snapshot()
        remote = await self.state.remote_snapshot()
        plan = self.engine.plan(direction, local, remote, self.bases.get(mapping_id))
        self._plans[plan.plan_id] = plan
        return plan.model_copy(deep=True)

    async def apply(
        self, actor_id: str, mapping_id: str, plan_id: str, approved: bool
    ) -> SyncApplyResult:
        if not approved:
            raise SyncApprovalRequiredError("Approve the current sync plan before applying it.")
        plan = self._plans.pop(plan_id, None)
        if plan is None:
            raise SyncStalePlanError("This synchronization plan is no longer valid.")
        local = await self.state.local_snapshot()
        remote = await self.state.remote_snapshot()
        if (
            local.project_hash != plan.expected_local_hash
            or remote.project_hash != plan.expected_remote_hash
        ):
            raise SyncStalePlanError(
                "Apps Script or GitHub changed after this plan was prepared. Review a fresh diff."
            )
        if plan.direction is SyncDirection.PULL:
            verified = await self.state.apply_pull(plan.target_snapshot, local.project_hash)
        else:
            verified = await self.state.apply_push(plan.target_snapshot, remote.project_hash)
        if verified.project_hash != plan.target_snapshot.project_hash:
            raise SyncVerificationError("The synchronization destination could not be verified.")
        final_local = await self.state.local_snapshot()
        final_remote = await self.state.remote_snapshot()
        fully_synchronized = final_local.project_hash == final_remote.project_hash
        if fully_synchronized:
            self.bases.save(mapping_id, final_local)
        self.audit.append(
            AuditEvent(
                actor_id=actor_id,
                action=f"SYNC_{plan.direction.value}",
                metadata={
                    "mapping_id": mapping_id,
                    "operations": len(plan.operations),
                    "verified_hash": verified.project_hash,
                    "fully_synchronized": fully_synchronized,
                },
            )
        )
        return SyncApplyResult(
            plan_id=plan.plan_id,
            direction=plan.direction,
            verified_destination_hash=verified.project_hash,
            fully_synchronized=fully_synchronized,
            operations_applied=len(plan.operations),
        )
