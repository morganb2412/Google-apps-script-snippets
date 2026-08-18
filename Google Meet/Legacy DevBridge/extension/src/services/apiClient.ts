import type { HealthResponse } from "../types/health";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, { signal, headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("DevBridge API is unavailable");
  return response.json() as Promise<HealthResponse>;
}
