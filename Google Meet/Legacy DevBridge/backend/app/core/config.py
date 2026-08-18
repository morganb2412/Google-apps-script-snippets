from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DEVBRIDGE_", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
    cors_origins_raw: str = "https://script.google.com"
    cors_origin_regex: str = r"^chrome-extension://[a-p]{32}$"
    google_oauth_enabled: bool = False
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://127.0.0.1:8000/api/v1/onboarding/google/callback"
    google_allowed_domains_raw: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]

    @property
    def google_allowed_domains(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.google_allowed_domains_raw.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
