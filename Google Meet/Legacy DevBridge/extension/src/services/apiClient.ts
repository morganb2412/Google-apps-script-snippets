import type { HealthResponse } from "../types/health";
import type { ProjectContext } from "../types/project";
import type { UserSetupState } from "../types/onboarding";

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
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers: { Accept: "application/json", ...init.headers } });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "DevBridge could not complete this setup step.");
  }
  return response.json() as Promise<T>;
}
