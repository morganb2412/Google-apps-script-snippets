from typing import Protocol

import httpx

from app.auth.models import GoogleIdentity, GoogleTokenSet


class GoogleOAuthProvider(Protocol):
    async def exchange_code(self, code: str, code_verifier: str) -> GoogleTokenSet: ...
    async def get_identity(self, access_token: str) -> GoogleIdentity: ...


class HttpGoogleOAuthProvider:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    async def exchange_code(self, code: str, code_verifier: str) -> GoogleTokenSet:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "code_verifier": code_verifier,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )
            response.raise_for_status()
            return GoogleTokenSet.model_validate(response.json())

    async def get_identity(self, access_token: str) -> GoogleIdentity:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            payload = response.json()
        return GoogleIdentity(
            subject=payload["sub"],
            email=payload["email"],
            email_verified=payload.get("email_verified", False),
            hosted_domain=payload.get("hd"),
            display_name=payload.get("name"),
        )
