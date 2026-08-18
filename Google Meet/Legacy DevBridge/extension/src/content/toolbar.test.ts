import { fireEvent } from "@testing-library/dom";
import { afterEach, expect, test, vi } from "vitest";
import { mountDevBridgeToolbar, TOOLBAR_HOST_ID } from "./toolbar";

afterEach(() => document.getElementById(TOOLBAR_HOST_ID)?.remove());

test("mounts one isolated Apps Script toolbar and opens the requested section", () => {
  const onOpen = vi.fn();
  const host = mountDevBridgeToolbar(onOpen);
  expect(mountDevBridgeToolbar(onOpen)).toBe(host);
  const shadow = host.shadowRoot;
  expect(shadow).not.toBeNull();
  const aiButton = Array.from(shadow?.querySelectorAll("button") ?? []).find((button) => button.textContent === "Code Assistant");
  expect(aiButton).toBeDefined();
  fireEvent.click(aiButton as HTMLButtonElement);
  expect(onOpen).toHaveBeenCalledWith("Code Assistant");
});
