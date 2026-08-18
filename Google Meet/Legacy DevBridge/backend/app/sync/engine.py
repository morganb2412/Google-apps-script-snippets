from difflib import unified_diff

from app.appsscript.models import ProjectFile, ProjectSnapshot
from app.sync.models import (
    FileComparison,
    ProjectComparison,
    SyncDirection,
    SyncOperation,
    SyncOperationType,
    SyncPlan,
    SyncState,
)


class SyncConflictError(RuntimeError):
    pass


class SyncEngine:
    def compare(
        self,
        local: ProjectSnapshot,
        remote: ProjectSnapshot,
        base: ProjectSnapshot | None,
    ) -> ProjectComparison:
        local_files = {file.path: file for file in local.files}
        remote_files = {file.path: file for file in remote.files}
        base_files = {file.path: file for file in base.files} if base else {}
        paths = sorted(set(local_files) | set(remote_files) | set(base_files))
        files = [
            self._compare_file(
                path,
                local_files.get(path),
                remote_files.get(path),
                base_files.get(path),
                base is not None,
            )
            for path in paths
        ]
        return ProjectComparison(
            local_hash=local.project_hash,
            remote_hash=remote.project_hash,
            base_hash=base.project_hash if base else None,
            files=files,
            has_conflicts=any(file.state is SyncState.CONFLICT for file in files),
        )

    def plan(
        self,
        direction: SyncDirection,
        local: ProjectSnapshot,
        remote: ProjectSnapshot,
        base: ProjectSnapshot | None,
    ) -> SyncPlan:
        comparison = self.compare(local, remote, base)
        if comparison.has_conflicts:
            conflicts = ", ".join(
                file.path for file in comparison.files if file.state is SyncState.CONFLICT
            )
            raise SyncConflictError(f"Resolve conflicts before synchronization: {conflicts}")

        source_states = (
            {SyncState.REMOTE_MODIFIED, SyncState.REMOTE_ADDED, SyncState.REMOTE_DELETED}
            if direction is SyncDirection.PULL
            else {SyncState.LOCAL_MODIFIED, SyncState.LOCAL_ADDED, SyncState.LOCAL_DELETED}
        )
        source = {
            file.path: file
            for file in (remote.files if direction is SyncDirection.PULL else local.files)
        }
        destination = {
            file.path: file.model_copy(deep=True)
            for file in (local.files if direction is SyncDirection.PULL else remote.files)
        }
        operations: list[SyncOperation] = []
        for change in comparison.files:
            if change.state not in source_states:
                continue
            source_file = source.get(change.path)
            if source_file is None:
                destination.pop(change.path, None)
                operation = SyncOperationType.DELETE
            else:
                destination[change.path] = source_file.model_copy(deep=True)
                operation = SyncOperationType.WRITE
            operations.append(
                SyncOperation(
                    path=change.path,
                    operation=operation,
                    state=change.state,
                    diff=change.diff,
                )
            )
        target = self._snapshot(
            local.script_id if direction is SyncDirection.PULL else remote.script_id,
            list(destination.values()),
        )
        return SyncPlan(
            direction=direction,
            expected_local_hash=local.project_hash,
            expected_remote_hash=remote.project_hash,
            target_snapshot=target,
            operations=operations,
        )

    def _compare_file(
        self,
        path: str,
        local: ProjectFile | None,
        remote: ProjectFile | None,
        base: ProjectFile | None,
        has_base: bool,
    ) -> FileComparison:
        local_hash = local.sha256 if local else None
        remote_hash = remote.sha256 if remote else None
        base_hash = base.sha256 if base else None
        if local_hash == remote_hash:
            state = SyncState.IDENTICAL
        elif not has_base:
            if local is None:
                state = SyncState.REMOTE_ADDED
            elif remote is None:
                state = SyncState.LOCAL_ADDED
            else:
                state = SyncState.CONFLICT
        elif base is None:
            state = (
                SyncState.LOCAL_ADDED
                if remote is None
                else (SyncState.REMOTE_ADDED if local is None else SyncState.CONFLICT)
            )
        elif local is None:
            state = SyncState.LOCAL_DELETED if remote_hash == base_hash else SyncState.CONFLICT
        elif remote is None:
            state = SyncState.REMOTE_DELETED if local_hash == base_hash else SyncState.CONFLICT
        else:
            local_changed = local_hash != base_hash
            remote_changed = remote_hash != base_hash
            if local_changed and remote_changed:
                state = SyncState.CONFLICT
            elif local_changed:
                state = SyncState.LOCAL_MODIFIED
            elif remote_changed:
                state = SyncState.REMOTE_MODIFIED
            else:
                state = SyncState.CONFLICT
        return FileComparison(
            path=path,
            state=state,
            local_sha256=local_hash,
            remote_sha256=remote_hash,
            base_sha256=base_hash,
            diff=self._diff(path, local, remote),
        )

    @staticmethod
    def _diff(path: str, local: ProjectFile | None, remote: ProjectFile | None) -> str:
        return "".join(
            unified_diff(
                (remote.content if remote else "").splitlines(keepends=True),
                (local.content if local else "").splitlines(keepends=True),
                fromfile=f"github/{path}",
                tofile=f"appsscript/{path}",
            )
        )

    @staticmethod
    def _snapshot(script_id: str, files: list[ProjectFile]) -> ProjectSnapshot:
        import hashlib

        ordered = sorted(files, key=lambda file: file.path)
        digest_input = "\n".join(f"{file.path}:{file.sha256}" for file in ordered)
        project_hash = hashlib.sha256(digest_input.encode()).hexdigest()
        return ProjectSnapshot(script_id=script_id, project_hash=project_hash, files=ordered)
