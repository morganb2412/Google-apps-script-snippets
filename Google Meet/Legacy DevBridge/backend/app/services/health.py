from app.models.health import HealthResponse


class HealthService:
    def status(self) -> HealthResponse:
        return HealthResponse()


def get_health_service() -> HealthService:
    return HealthService()
