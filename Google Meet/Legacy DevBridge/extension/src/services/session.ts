const SESSION_KEY = "devbridge_session_id";

export async function getDevBridgeSessionId(): Promise<string> {
  const stored = await chrome.storage.local.get(SESSION_KEY) as Record<string, unknown>;
  const existing = stored[SESSION_KEY];
  if (typeof existing === "string" && /^[A-Za-z0-9_-]{20,128}$/.test(existing)) return existing;

  const sessionId = crypto.randomUUID().replaceAll("-", "");
  await chrome.storage.local.set({ [SESSION_KEY]: sessionId });
  return sessionId;
}
