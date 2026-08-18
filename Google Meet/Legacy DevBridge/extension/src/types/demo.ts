export interface DemoChange { path: string; state: string; diff: string; requires_approval: boolean }
export interface DemoWorkspace {
  mode: "DEMO"; project_name: string; script_id: string; repository: string | null; branch: string;
  branches: string[]; connected: boolean; changes: DemoChange[]; latest_commit: string | null;
  pull_request_url: string | null; updated_at: string;
}
export interface AgentResult { mode: "DEMO"; title: string; summary: string; items: string[]; files_affected: string[]; oauth_changes: string[] }
