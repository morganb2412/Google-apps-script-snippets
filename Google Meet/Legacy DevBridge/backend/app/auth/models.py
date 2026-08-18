from datetime import UTC, datetime

from pydantic import BaseModel, Field


class GoogleOAuthStart(BaseModel):
    authorization_url: str
    expires_at: datetime


class GoogleTokenSet(BaseModel):
    access_token: str = Field(repr=False)
    refresh_token: str | None = Field(default=None, repr=False)
    expires_in: int = 3600
    scope: str = ""
    token_type: str = "Bearer"


class GoogleIdentity(BaseModel):
    subject: str
    email: str
    email_verified: bool
    hosted_domain: str | None = None
    display_name: str | None = None


class GoogleConnection(BaseModel):
    user_id: str
    email: str
    hosted_domain: str | None = None
    connected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OAuthCallbackResult(BaseModel):
    connected: bool
    email: str
    next_step: str = "GITHUB"
