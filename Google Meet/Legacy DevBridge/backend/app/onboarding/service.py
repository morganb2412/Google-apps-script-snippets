from datetime import UTC, datetime

from app.onboarding.models import SetupStep, UserSetupState
from app.onboarding.repository import OnboardingRepository


class MockConnectionsDisabledError(RuntimeError):
    pass


class OnboardingPreconditionError(RuntimeError):
    pass


class OnboardingService:
    def __init__(self, repository: OnboardingRepository, allow_mock_connections: bool) -> None:
        self.repository = repository
        self.allow_mock_connections = allow_mock_connections

    def status(self, user_id: str) -> UserSetupState:
        return self._refresh(self.repository.get(user_id))

    def connect_google(self, user_id: str) -> UserSetupState:
        state = self._mock_state(user_id)
        state.google_connected = True
        return self.repository.save(self._refresh(state))

    def connect_github(self, user_id: str) -> UserSetupState:
        state = self._mock_state(user_id)
        if not state.google_connected:
            raise OnboardingPreconditionError("Connect Google before GitHub.")
        state.github_connected = True
        return self.repository.save(self._refresh(state))

    def detect_project(self, user_id: str) -> UserSetupState:
        state = self.repository.get(user_id)
        state.project_detected = True
        return self.repository.save(self._refresh(state))

    def configure_standards(self, user_id: str) -> UserSetupState:
        state = self.repository.get(user_id)
        if not state.project_detected:
            raise OnboardingPreconditionError("Detect a project before configuring standards.")
        state.standards_configured = True
        return self.repository.save(self._refresh(state))

    def complete(self, user_id: str) -> UserSetupState:
        state = self.repository.get(user_id)
        required_steps_complete = (
            state.google_connected
            and state.github_connected
            and state.project_detected
            and state.standards_configured
        )
        if not required_steps_complete:
            raise OnboardingPreconditionError("Complete the required setup steps first.")
        state.onboarding_completed = True
        return self.repository.save(self._refresh(state))

    def _mock_state(self, user_id: str) -> UserSetupState:
        if not self.allow_mock_connections:
            raise MockConnectionsDisabledError("Mock connections are disabled in this environment.")
        state = self.repository.get(user_id)
        state.connection_mode = "LOCAL_MOCK"
        return state

    @staticmethod
    def _refresh(state: UserSetupState) -> UserSetupState:
        if not state.google_connected:
            state.next_step = SetupStep.GOOGLE
        elif not state.github_connected:
            state.next_step = SetupStep.GITHUB
        elif not state.project_detected:
            state.next_step = SetupStep.PROJECT
        elif not state.standards_configured:
            state.next_step = SetupStep.STANDARDS
        elif not state.onboarding_completed:
            state.next_step = SetupStep.COMPLETE
        else:
            state.next_step = SetupStep.COMPLETE
        state.updated_at = datetime.now(UTC)
        return state
