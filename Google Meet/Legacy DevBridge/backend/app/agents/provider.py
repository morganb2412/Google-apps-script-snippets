import asyncio
from typing import Protocol

import google.auth
import httpx
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request


class LLMProvider(Protocol):
    name: str
    model: str

    async def generate(self, system_instruction: str, prompt: str) -> str: ...


class VertexGeminiProvider:
    name = "VERTEX_AI"

    def __init__(self, project: str, location: str, model: str) -> None:
        self.project = project
        self.location = location
        self.model = model

    async def generate(self, system_instruction: str, prompt: str) -> str:
        token = await asyncio.to_thread(self._access_token)
        endpoint = (
            "https://aiplatform.googleapis.com/v1/projects/"
            f"{self.project}/locations/{self.location}/publishers/google/models/"
            f"{self.model}:generateContent"
        )
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                endpoint,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
                },
            )
            response.raise_for_status()
        payload = response.json()
        candidates = payload.get("candidates") or []
        if not candidates:
            raise RuntimeError("The managed AI provider returned no response.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError("The managed AI provider returned an empty response.")
        return text

    @staticmethod
    def _access_token() -> str:
        credentials, _ = google.auth.default(  # type: ignore[no-untyped-call]
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        typed_credentials: Credentials = credentials
        typed_credentials.refresh(Request())  # type: ignore[no-untyped-call]
        token = typed_credentials.token
        if not isinstance(token, str) or not token:
            raise RuntimeError("Managed AI credentials are unavailable.")
        return token
