export type SyncState = "IDENTICAL" | "LOCAL_MODIFIED" | "REMOTE_MODIFIED" | "LOCAL_ADDED" | "REMOTE_ADDED" | "LOCAL_DELETED" | "REMOTE_DELETED" | "CONFLICT";
export interface DemoChange { path: string; state: SyncState; diff: string; requires_approval: boolean }
export interface DemoWorkspace {
  mode: "DEMO"; project_name: string; script_id: string; repository: string | null; branch: string;
  branches: string[]; connected: boolean; changes: DemoChange[]; latest_commit: string | null;
  pull_request_url: string | null; updated_at: string;
  applied_proposal?: string | null; audit_events?: string[];
}
export interface AgentResult { mode: "DEMO"; title: string; summary: string; items: string[]; files_affected: string[]; oauth_changes: string[] }
export interface ProposedFix { proposal_id: string; status: string; file: string; operation: string; original_hash: string; explanation: string; standards_impacted: string[]; risk_level: string; diff: string }
export interface AssistantResponse { mode: "DEMO"; message: string; findings: string[]; proposal: ProposedFix | null }
