import asyncio
import hashlib

import pytest

from app.appsscript.models import ProjectFile, ProjectFileSource, ProjectSnapshot
from app.audit.repository import InMemoryAuditRepository
from app.sync.engine import SyncConflictError, SyncEngine
from app.sync.models import SyncDirection, SyncState
from app.sync.repository import InMemorySyncBaseRepository
from app.sync.service import (
    SyncApprovalRequiredError,
    SyncService,
    SyncStalePlanError,
    SyncVerificationError,
)


def snapshot(name: str, values: dict[str, str]) -> ProjectSnapshot:
    files = [
        ProjectFile(
            path=path,
            name=path,
            extension=f".{path.rsplit('.', 1)[-1]}",
            content=content,
            sha256=hashlib.sha256(content.encode()).hexdigest(),
            source=ProjectFileSource.APPS_SCRIPT if name == "local" else ProjectFileSource.GITHUB,
        )
        for path, content in sorted(values.items())
    ]
    digest = "\n".join(f"{file.path}:{file.sha256}" for file in files)
    return ProjectSnapshot(
        script_id=name,
        project_hash=hashlib.sha256(digest.encode()).hexdigest(),
        files=files,
    )


def states(comparison: object) -> dict[str, SyncState]:
    return {item.path: item.state for item in comparison.files}  # type: ignore[attr-defined]


def test_three_way_comparison_covers_every_non_conflict_state() -> None:
    base = snapshot(
        "base",
        {
            "same.gs": "same",
            "local-modified.gs": "base",
            "remote-modified.gs": "base",
            "local-deleted.gs": "base",
            "remote-deleted.gs": "base",
        },
    )
    local = snapshot(
        "local",
        {
            "same.gs": "same",
            "local-modified.gs": "local",
            "remote-modified.gs": "base",
            "remote-deleted.gs": "base",
            "local-added.gs": "new local",
        },
    )
    remote = snapshot(
        "remote",
        {
            "same.gs": "same",
            "local-modified.gs": "base",
            "remote-modified.gs": "remote",
            "local-deleted.gs": "base",
            "remote-added.gs": "new remote",
        },
    )
    result = states(SyncEngine().compare(local, remote, base))
    assert result == {
        "local-added.gs": SyncState.LOCAL_ADDED,
        "local-deleted.gs": SyncState.LOCAL_DELETED,
        "local-modified.gs": SyncState.LOCAL_MODIFIED,
        "remote-added.gs": SyncState.REMOTE_ADDED,
        "remote-deleted.gs": SyncState.REMOTE_DELETED,
        "remote-modified.gs": SyncState.REMOTE_MODIFIED,
        "same.gs": SyncState.IDENTICAL,
    }


def test_three_way_comparison_detects_modify_and_delete_conflicts() -> None:
    base = snapshot("base", {"both.gs": "base", "delete.gs": "base"})
    local = snapshot("local", {"both.gs": "local"})
    remote = snapshot("remote", {"both.gs": "remote", "delete.gs": "remote changed"})
    comparison = SyncEngine().compare(local, remote, base)
    assert comparison.has_conflicts is True
    assert states(comparison) == {
        "both.gs": SyncState.CONFLICT,
        "delete.gs": SyncState.CONFLICT,
    }
    assert "github/both.gs" in comparison.files[0].diff
    assert "appsscript/both.gs" in comparison.files[0].diff


def test_initial_comparison_never_guesses_when_same_path_differs() -> None:
    local = snapshot("local", {"Code.gs": "local"})
    remote = snapshot("remote", {"Code.gs": "remote"})
    with pytest.raises(SyncConflictError, match="Code.gs"):
        SyncEngine().plan(SyncDirection.PULL, local, remote, None)


def test_directional_plans_merge_changes_without_discarding_opposite_side() -> None:
    base = snapshot("base", {"Local.gs": "base", "Remote.gs": "base"})
    local = snapshot("local", {"Local.gs": "local change", "Remote.gs": "base"})
    remote = snapshot("remote", {"Local.gs": "base", "Remote.gs": "remote change"})
    engine = SyncEngine()
    pull = engine.plan(SyncDirection.PULL, local, remote, base)
    push = engine.plan(SyncDirection.PUSH, local, remote, base)
    assert {file.path: file.content for file in pull.target_snapshot.files} == {
        "Local.gs": "local change",
        "Remote.gs": "remote change",
    }
    assert [operation.path for operation in pull.operations] == ["Remote.gs"]
    assert {file.path: file.content for file in push.target_snapshot.files} == {
        "Local.gs": "local change",
        "Remote.gs": "remote change",
    }
    assert [operation.path for operation in push.operations] == ["Local.gs"]


class FakeSyncState:
    def __init__(self, local: ProjectSnapshot, remote: ProjectSnapshot) -> None:
        self.local = local
        self.remote = remote
        self.return_wrong_hash = False

    async def local_snapshot(self) -> ProjectSnapshot:
        return self.local.model_copy(deep=True)

    async def remote_snapshot(self) -> ProjectSnapshot:
        return self.remote.model_copy(deep=True)

    async def apply_pull(
        self, target: ProjectSnapshot, expected_local_hash: str
    ) -> ProjectSnapshot:
        assert self.local.project_hash == expected_local_hash
        self.local = target.model_copy(deep=True)
        return snapshot("wrong", {"wrong.gs": "wrong"}) if self.return_wrong_hash else self.local

    async def apply_push(
        self, target: ProjectSnapshot, expected_remote_hash: str
    ) -> ProjectSnapshot:
        assert self.remote.project_hash == expected_remote_hash
        self.remote = target.model_copy(deep=True)
        return snapshot("wrong", {"wrong.gs": "wrong"}) if self.return_wrong_hash else self.remote


def test_sync_service_requires_approval_checks_staleness_and_verifies() -> None:
    base = snapshot("base", {"Code.gs": "base"})
    state = FakeSyncState(
        snapshot("local", {"Code.gs": "base"}), snapshot("remote", {"Code.gs": "remote"})
    )
    bases = InMemorySyncBaseRepository()
    bases.save("mapping", base)
    service = SyncService(SyncEngine(), state, bases, InMemoryAuditRepository())
    plan = asyncio.run(service.prepare("mapping", SyncDirection.PULL))
    with pytest.raises(SyncApprovalRequiredError):
        asyncio.run(service.apply("actor", "mapping", plan.plan_id, approved=False))

    plan = asyncio.run(service.prepare("mapping", SyncDirection.PULL))
    state.remote = snapshot("remote", {"Code.gs": "changed after plan"})
    with pytest.raises(SyncStalePlanError, match="fresh diff"):
        asyncio.run(service.apply("actor", "mapping", plan.plan_id, approved=True))

    state.remote = snapshot("remote", {"Code.gs": "remote"})
    plan = asyncio.run(service.prepare("mapping", SyncDirection.PULL))
    state.return_wrong_hash = True
    with pytest.raises(SyncVerificationError):
        asyncio.run(service.apply("actor", "mapping", plan.plan_id, approved=True))


def test_successful_sync_updates_base_only_when_both_sides_match() -> None:
    base = snapshot("base", {"Code.gs": "base"})
    state = FakeSyncState(
        snapshot("local", {"Code.gs": "base"}), snapshot("remote", {"Code.gs": "remote"})
    )
    bases = InMemorySyncBaseRepository()
    bases.save("mapping", base)
    audit = InMemoryAuditRepository()
    service = SyncService(SyncEngine(), state, bases, audit)
    plan = asyncio.run(service.prepare("mapping", SyncDirection.PULL))
    result = asyncio.run(service.apply("actor", "mapping", plan.plan_id, approved=True))
    assert result.fully_synchronized is True
    assert result.operations_applied == 1
    assert bases.get("mapping").project_hash == state.local.project_hash  # type: ignore[union-attr]
    assert audit.list_for_actor("actor")[0].action == "SYNC_PULL"
