import asyncio

from app.agents.models import AgentChatRequest
from app.agents.service import AgentService


class FakeProvider:
    name = "FAKE_MANAGED_AI"
    model = "test-model"

    def __init__(self) -> None:
        self.system_instruction = ""
        self.prompt = ""

    async def generate(self, system_instruction: str, prompt: str) -> str:
        self.system_instruction = system_instruction
        self.prompt = prompt
        return "I need the current Apps Script source before proposing a change."


def test_agent_uses_provider_neutral_governed_context() -> None:
    provider = FakeProvider()
    response = asyncio.run(
        AgentService(provider).chat(
            AgentChatRequest(request="Review this project", script_id="script-1234567890")
        )
    )

    assert response.mode == "LIVE"
    assert response.provider == "FAKE_MANAGED_AI"
    assert response.model == "test-model"
    assert response.proposal is None
    assert "explicit human approval" in provider.system_instruction
    assert "script-1234567890" in provider.prompt
    assert "Review this project" in provider.prompt
