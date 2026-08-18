import type { HealthResponse } from "../types/health";
import type { ProjectContext } from "../types/project";
import type { UserSetupState } from "../types/onboarding";
import type { AgentResult, AssistantResponse, DemoWorkspace } from "../types/demo";
import { getDevBridgeSessionId } from "./session";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, { signal, headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("DevBridge API is unavailable");
  return response.json() as Promise<HealthResponse>;
}

export async function getOnboardingStatus(signal?: AbortSignal): Promise<UserSetupState> {
  return request<UserSetupState>("/onboarding/status", { signal });
}

export async function connectOnboardingProvider(provider: "google" | "github"): Promise<UserSetupState> {
  return request<UserSetupState>(`/onboarding/${provider}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "MOCK" }),
  });
}

interface GoogleOAuthStart {
  authorization_url: string;
  expires_at: string;
}

export async function startGoogleConnection(): Promise<UserSetupState> {
  const started = await request<GoogleOAuthStart>("/onboarding/google/start", {});
  await chrome.tabs.create({ url: started.authorization_url, active: true });
  const deadline = Math.min(Date.parse(started.expires_at), Date.now() + 10 * 60_000);
  while (Date.now() < deadline) {
    await new Promise((resolve) => window.setTimeout(resolve, 1500));
    const setup = await getOnboardingStatus();
    if (setup.google_connected) return setup;
  }
  throw new Error("Google connection timed out. Return to DevBridge and try again.");
}

export async function registerDetectedProject(project: ProjectContext): Promise<UserSetupState> {
  return request<UserSetupState>("/onboarding/project", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script_id: project.scriptId, name: project.name }),
  });
}

export async function selectRecommendedStandards(): Promise<UserSetupState> {
  return request<UserSetupState>("/onboarding/standards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset: "RECOMMENDED" }),
  });
}

export async function completeOnboarding(): Promise<UserSetupState> {
  return request<UserSetupState>("/onboarding/complete", { method: "POST" });
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const sessionId = await getDevBridgeSessionId();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { Accept: "application/json", "X-DevBridge-Session": sessionId, ...init.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "DevBridge could not complete this setup step.");
  }
  return response.json() as Promise<T>;
}

export const demoApi = {
  workspace: () => request<DemoWorkspace>("/demo/workspace", {}),
  connect: () => request<DemoWorkspace>("/demo/connect", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ owner: "legacy-automations", repository: "atlas-demo" }) }),
  branch: (name: string) => request<DemoWorkspace>("/demo/branches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) }),
  commit: (message: string) => request<DemoWorkspace>("/demo/commits", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message }) }),
  pullRequest: () => request<DemoWorkspace>("/demo/pull-requests", { method: "POST" }),
  agent: (mode: "plan" | "review", userRequest: string) => request<AgentResult>(`/demo/agent/${mode}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request: userRequest }) }),
  chat: (userRequest: string) => request<AssistantResponse>("/demo/assistant/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request: userRequest }) }),
  decide: (proposalId: string, approved: boolean) => request<AssistantResponse>(`/demo/assistant/${approved ? "approve" : "reject"}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ proposal_id: proposalId }) }),
};
