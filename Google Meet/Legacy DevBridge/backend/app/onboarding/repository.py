from copy import deepcopy
from typing import Protocol

from app.onboarding.models import UserSetupState


class OnboardingRepository(Protocol):
    def get(self, user_id: str) -> UserSetupState: ...
    def save(self, state: UserSetupState) -> UserSetupState: ...


class InMemoryOnboardingRepository:
    def __init__(self) -> None:
        self._states: dict[str, UserSetupState] = {}

    def get(self, user_id: str) -> UserSetupState:
        return deepcopy(self._states.get(user_id, UserSetupState(user_id=user_id)))

    def save(self, state: UserSetupState) -> UserSetupState:
        self._states[state.user_id] = deepcopy(state)
        return deepcopy(state)

    def clear(self) -> None:
        self._states.clear()
