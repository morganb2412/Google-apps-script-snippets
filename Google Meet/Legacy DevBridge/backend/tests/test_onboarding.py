import pytest

from app.onboarding.health import build_integration_health
from app.onboarding.repository import InMemoryOnboardingRepository
from app.onboarding.service import (
    MockConnectionsDisabledError,
    OnboardingPreconditionError,
    OnboardingService,
)


def test_guided_onboarding_sequence() -> None:
    service = OnboardingService(InMemoryOnboardingRepository(), allow_mock_connections=True)
    assert service.status("user-1").next_step == "GOOGLE"
    assert service.connect_google("user-1").next_step == "GITHUB"
    assert service.connect_github("user-1").next_step == "PROJECT"
    assert service.detect_project("user-1").next_step == "STANDARDS"
    assert service.configure_standards("user-1").next_step == "COMPLETE"
    completed = service.complete("user-1")
    assert completed.onboarding_completed is True
    assert build_integration_health(completed).ready is False


def test_github_requires_google_first() -> None:
    service = OnboardingService(InMemoryOnboardingRepository(), allow_mock_connections=True)
    with pytest.raises(OnboardingPreconditionError, match="Connect Google"):
        service.connect_github("user-1")


def test_production_disables_mock_connections() -> None:
    service = OnboardingService(InMemoryOnboardingRepository(), allow_mock_connections=False)
    with pytest.raises(MockConnectionsDisabledError):
        service.connect_google("user-1")
