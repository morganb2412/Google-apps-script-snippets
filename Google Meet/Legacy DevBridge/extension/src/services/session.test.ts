import { beforeEach, expect, test, vi } from "vitest";
import { getDevBridgeSessionId } from "./session";

const get = vi.fn();
const set = vi.fn();

beforeEach(() => {
  get.mockReset();
  set.mockReset();
  vi.stubGlobal("chrome", { storage: { local: { get, set } } });
});

test("reuses an existing opaque extension session", async () => {
  get.mockResolvedValue({ devbridge_session_id: "existing_session_1234567890" });
  expect(await getDevBridgeSessionId()).toBe("existing_session_1234567890");
  expect(set).not.toHaveBeenCalled();
});

test("creates and stores a session without credentials", async () => {
  get.mockResolvedValue({});
  const sessionId = await getDevBridgeSessionId();
  expect(sessionId).toMatch(/^[a-f0-9]{32}$/);
  expect(set).toHaveBeenCalledWith({ devbridge_session_id: sessionId });
});
