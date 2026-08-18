import type { ExtensionMessage, ProjectContext } from "../types/project";
import { detectProjectContext } from "../utils/projectDetection";
import { mountDevBridgeToolbar } from "./toolbar";

let lastProjectKey = "";

function currentContext(): ProjectContext | null {
  return detectProjectContext(window.location.href, document.title);
}

function publishContext(): void {
  const context = currentContext();
  if (!context) return;
  const projectKey = `${context.scriptId}:${context.name ?? ""}`;
  if (projectKey === lastProjectKey) return;
  lastProjectKey = projectKey;
  const message: ExtensionMessage = { type: "DEVBRIDGE_PROJECT_CONTEXT", payload: context };
  void chrome.runtime.sendMessage(message).catch(() => undefined);
}

chrome.runtime.onMessage.addListener((message: ExtensionMessage, _sender, sendResponse) => {
  if (message.type !== "DEVBRIDGE_GET_PROJECT_CONTEXT") return false;
  sendResponse(currentContext());
  return false;
});

publishContext();
mountDevBridgeToolbar((section) => {
  const message: ExtensionMessage = { type: "DEVBRIDGE_OPEN_PANEL", section };
  void chrome.runtime.sendMessage(message).catch(() => undefined);
});
new MutationObserver(publishContext).observe(document.querySelector("title") ?? document.documentElement, {
  childList: true,
  subtree: true,
});
window.addEventListener("popstate", publishContext);
