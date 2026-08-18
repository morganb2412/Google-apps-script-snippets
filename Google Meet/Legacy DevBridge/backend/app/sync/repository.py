from copy import deepcopy
from typing import Protocol

from app.appsscript.models import ProjectSnapshot


class SyncBaseRepository(Protocol):
    def get(self, mapping_id: str) -> ProjectSnapshot | None: ...
    def save(self, mapping_id: str, snapshot: ProjectSnapshot) -> None: ...


class InMemorySyncBaseRepository:
    def __init__(self) -> None:
        self._snapshots: dict[str, ProjectSnapshot] = {}

    def get(self, mapping_id: str) -> ProjectSnapshot | None:
        snapshot = self._snapshots.get(mapping_id)
        return deepcopy(snapshot) if snapshot else None

    def save(self, mapping_id: str, snapshot: ProjectSnapshot) -> None:
        self._snapshots[mapping_id] = deepcopy(snapshot)
