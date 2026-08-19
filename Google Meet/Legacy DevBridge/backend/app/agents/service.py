from app.agents.models import AgentChatRequest, AgentChatResponse
from app.agents.provider import LLMProvider

SYSTEM_INSTRUCTION = """You are Legacy DevBridge Code Assistant for Google Apps Script.
Be concise, practical, and conversational. Analyze code using these mandatory rules:
- Use the V8 runtime and camelCase functions; public functions need useful JSDoc.
- Hard-coded credentials and secrets are prohibited; use PropertiesService for configuration.
- Highlight every appsscript.json OAuth scope change.
- Never claim code was changed. Any modification requires a visible diff, current hash check,
  policy review, explicit human approval, verification, and an audit event.
- Never recommend bypassing protected branches or direct production pushes.
If project source was not supplied, say what context you still need rather than inventing it.
"""


class AgentService:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def chat(self, request: AgentChatRequest) -> AgentChatResponse:
        project_context = (
            f"\nDetected Apps Script project ID: {request.script_id}"
            if request.script_id
            else "\nNo Apps Script project context was supplied."
        )
        message = await self.provider.generate(
            SYSTEM_INSTRUCTION,
            f"User request:\n{request.request}{project_context}",
        )
        return AgentChatResponse(
            message=message,
            provider=self.provider.name,
            model=self.provider.model,
        )
