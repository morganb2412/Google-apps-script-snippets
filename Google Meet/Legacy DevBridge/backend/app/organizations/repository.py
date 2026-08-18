from copy import deepcopy
from typing import Protocol

from app.organizations.models import ProjectMapping


class ProjectMappingRepository(Protocol):
    def save(self, mapping: ProjectMapping) -> ProjectMapping: ...
    def get(self, user_id: str, script_project_id: str) -> ProjectMapping | None: ...
    def list_for_user(self, user_id: str) -> list[ProjectMapping]: ...
    def delete(self, user_id: str, script_project_id: str) -> None: ...


class InMemoryProjectMappingRepository:
    """Local adapter matching the document shape expected by Firestore."""

    def __init__(self) -> None:
        self._mappings: dict[tuple[str, str], ProjectMapping] = {}

    def save(self, mapping: ProjectMapping) -> ProjectMapping:
        self._mappings[(mapping.user_id, mapping.script_project_id)] = deepcopy(mapping)
        return deepcopy(mapping)

    def get(self, user_id: str, script_project_id: str) -> ProjectMapping | None:
        mapping = self._mappings.get((user_id, script_project_id))
        return deepcopy(mapping) if mapping else None

    def list_for_user(self, user_id: str) -> list[ProjectMapping]:
        return [
            deepcopy(mapping)
            for (owner_id, _), mapping in self._mappings.items()
            if owner_id == user_id
        ]

    def delete(self, user_id: str, script_project_id: str) -> None:
        self._mappings.pop((user_id, script_project_id), None)
