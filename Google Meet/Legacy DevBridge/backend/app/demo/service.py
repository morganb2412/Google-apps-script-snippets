from datetime import UTC, datetime
from difflib import unified_diff
from hashlib import sha256

from app.demo.models import (
    AgentResult,
    AssistantResponse,
    DemoChange,
    DemoFile,
    DemoWorkspace,
    ProposedFix,
    SyncState,
)

LOCAL_FILES = {
    "ApprovalService.gs": """/** Routes approval requests. */
function routeApproval(amount, requesterEmail) {
  if (amount > 10000) {
    MailApp.sendEmail('finance@example.com', 'Approval required', requesterEmail);
  }
  return { status: 'submitted', amount: amount };
}
""",
    "ConfigService.gs": """/** Returns application configuration. */
function getConfig() {
  return { approvalThreshold: 10000 };
}
""",
    "appsscript.json": '{"timeZone":"America/Chicago","runtimeVersion":"V8","oauthScopes":["https://www.googleapis.com/auth/script.send_mail"]}',
}

REMOTE_FILES = {
    "ApprovalService.gs": """/** Routes approval requests. */
function routeApproval(amount, requesterEmail) {
  const config = getConfig();
  if (amount > config.approvalThreshold) {
    notifyFinance(requesterEmail, amount);
  }
  return { status: 'submitted', amount: amount };
}
""",
    "ConfigService.gs": LOCAL_FILES["ConfigService.gs"],
    "README.md": "# ATLAS Approval Automation\n\nManaged with Legacy DevBridge.\n",
    "appsscript.json": LOCAL_FILES["appsscript.json"],
}


class DemoWorkspaceService:
    def __init__(self) -> None:
        self.workspace = DemoWorkspace()
        self.proposal_status = "PENDING_APPROVAL"

    def get(self) -> DemoWorkspace:
        self.workspace.changes = self.compare()
        self.workspace.updated_at = datetime.now(UTC)
        return self.workspace.model_copy(deep=True)

    def connect(self, owner: str, repository: str) -> DemoWorkspace:
        self.workspace.repository = f"{owner}/{repository}"
        self.workspace.connected = True
        return self.get()

    def create_branch(self, name: str) -> DemoWorkspace:
        if name not in self.workspace.branches:
            self.workspace.branches.append(name)
        self.workspace.branch = name
        return self.get()

    def commit(self, message: str) -> DemoWorkspace:
        self.workspace.latest_commit = message
        return self.get()

    def create_pull_request(self) -> DemoWorkspace:
        repo = self.workspace.repository or "legacy-automations/atlas-demo"
        self.workspace.pull_request_url = f"https://github.com/{repo}/pull/1"
        return self.get()

    def compare(self) -> list[DemoChange]:
        changes: list[DemoChange] = []
        for path in sorted(set(LOCAL_FILES) | set(REMOTE_FILES)):
            local = LOCAL_FILES.get(path)
            remote = REMOTE_FILES.get(path)
            if local == remote:
                continue
            if local is None:
                state = SyncState.REMOTE_ADDED
            elif remote is None:
                state = SyncState.LOCAL_ADDED
            else:
                state = SyncState.CONFLICT
            changes.append(DemoChange(path=path, state=state, diff=self._diff(path, local, remote)))
        return changes

    def files(self) -> list[DemoFile]:
        return [
            DemoFile(
                path=path,
                content=content,
                sha256=sha256(content.encode()).hexdigest(),
                source="APPS_SCRIPT",
            )
            for path, content in LOCAL_FILES.items()
        ]

    def plan(self, request: str) -> AgentResult:
        return AgentResult(
            title="Implementation Plan",
            summary=f"Demo analysis for: {request}",
            items=[
                "Move the finance threshold into PropertiesService-backed configuration.",
                "Route notifications through a dedicated MailService helper.",
                "Add structured validation and error handling.",
                "Add unit-style Apps Script tests and update documentation.",
            ],
            files_affected=[
                "ApprovalService.gs",
                "ConfigService.gs",
                "MailService.gs",
                "README.md",
            ],
        )

    def review(self, request: str) -> AgentResult:
        return AgentResult(
            title="Code Review",
            summary=f"3 findings for: {request}",
            items=[
                "HIGH: ApprovalService.gs hard-codes a finance email address.",
                "MEDIUM: The threshold should use PropertiesService configuration.",
                "LOW: Add structured logging around MailApp failures.",
            ],
            files_affected=["ApprovalService.gs", "ConfigService.gs"],
        )

    def chat(self, request: str) -> AssistantResponse:
        normalized = request.lower()
        findings = [
            "HIGH: Hard-coded finance@example.com violates configuration policy.",
            "MEDIUM: Approval threshold should come from PropertiesService.",
            "LOW: MailApp failures need structured logging.",
        ]
        fix_terms = ("fix", "change", "update", "implement", "refactor")
        wants_fix = any(term in normalized for term in fix_terms)
        proposal = self._proposal() if wants_fix else None
        if proposal:
            message = (
                "I analyzed the project and prepared a governed fix. Review the diff below. "
                "Nothing will be applied until you approve it, and the original file hash "
                "will be checked again."
            )
        else:
            message = (
                "I analyzed the project against the company security and coding standards. "
                "The main issue is hard-coded configuration in ApprovalService.gs. "
                "Ask me to fix it when ready."
            )
        return AssistantResponse(message=message, findings=findings, proposal=proposal)

    def decide_proposal(self, approved: bool) -> AssistantResponse:
        self.proposal_status = "APPROVED_DEMO" if approved else "REJECTED"
        action = "approved for demo" if approved else "rejected"
        return AssistantResponse(
            message=(
                f"The proposed change was {action}. No external file was modified. "
                "A live adapter would now re-read the file, verify its hash, apply the "
                "approved patch, verify, and audit."
            ),
            proposal=self._proposal(),
        )

    def _proposal(self) -> ProposedFix:
        original = LOCAL_FILES["ApprovalService.gs"]
        updated = original.replace(
            "MailApp.sendEmail('finance@example.com', 'Approval required', requesterEmail);",
            "notifyFinance(requesterEmail, amount);",
        )
        proposal = ProposedFix(
            status=self.proposal_status,
            original_hash=sha256(original.encode()).hexdigest(),
            explanation=(
                "Remove hard-coded recipient handling and route through the approved "
                "notification service."
            ),
            standards_impacted=[
                "No hard-coded configuration",
                "Use service boundaries",
                "Human approval required",
            ],
            diff=self._diff("ApprovalService.gs", updated, original),
        )
        return proposal

    @staticmethod
    def _diff(path: str, local: str | None, remote: str | None) -> str:
        return "".join(unified_diff(
            (remote or "").splitlines(keepends=True),
            (local or "").splitlines(keepends=True),
            fromfile=f"github/{path}",
            tofile=f"appsscript/{path}",
        ))
