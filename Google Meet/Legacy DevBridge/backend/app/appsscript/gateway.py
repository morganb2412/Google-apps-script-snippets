from typing import Protocol

import httpx

from app.appsscript.models import AppsScriptContent, AppsScriptFile, AppsScriptProject


class AppsScriptGateway(Protocol):
    async def get_project(self, script_id: str, access_token: str) -> AppsScriptProject: ...
    async def get_content(self, script_id: str, access_token: str) -> AppsScriptContent: ...
    async def update_content(
        self, script_id: str, files: list[AppsScriptFile], access_token: str
    ) -> AppsScriptContent: ...


class HttpAppsScriptGateway:
    BASE_URL = "https://script.googleapis.com/v1/projects"

    async def get_project(self, script_id: str, access_token: str) -> AppsScriptProject:
        payload = await self._request("GET", f"{self.BASE_URL}/{script_id}", access_token)
        return AppsScriptProject.model_validate(payload)

    async def get_content(self, script_id: str, access_token: str) -> AppsScriptContent:
        payload = await self._request("GET", f"{self.BASE_URL}/{script_id}/content", access_token)
        return AppsScriptContent(script_id=script_id, files=payload.get("files", []))

    async def update_content(
        self, script_id: str, files: list[AppsScriptFile], access_token: str
    ) -> AppsScriptContent:
        payload = await self._request(
            "PUT",
            f"{self.BASE_URL}/{script_id}/content",
            access_token,
            json={"files": [file.model_dump(by_alias=True, exclude_none=True) for file in files]},
        )
        return AppsScriptContent(script_id=script_id, files=payload.get("files", []))

    @staticmethod
    async def _request(
        method: str, url: str, access_token: str, json: dict[str, object] | None = None
    ) -> dict[str, object]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(
                method,
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                json=json,
            )
            response.raise_for_status()
            result: dict[str, object] = response.json()
            return result
