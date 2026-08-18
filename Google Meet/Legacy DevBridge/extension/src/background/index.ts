import type { ExtensionMessage, ProjectContext } from "../types/project";

const projectByTab = new Map<number, ProjectContext>();

chrome.action.onClicked.addListener(async (tab) => {
  if (tab.windowId !== undefined) await chrome.sidePanel.open({ windowId: tab.windowId });
});

chrome.tabs.onRemoved.addListener((tabId) => projectByTab.delete(tabId));

chrome.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
  if (message.type === "DEVBRIDGE_OPEN_PANEL" && sender.tab?.windowId !== undefined) {
    void chrome.sidePanel.open({ windowId: sender.tab.windowId }).then(() => {
      const navigation: ExtensionMessage = { type: "DEVBRIDGE_NAVIGATE", section: message.section };
      return chrome.runtime.sendMessage(navigation);
    }).catch(() => undefined);
    return false;
  }
  if (message.type === "DEVBRIDGE_PROJECT_CONTEXT" && sender.tab?.id !== undefined) {
    projectByTab.set(sender.tab.id, message.payload);
    void chrome.runtime.sendMessage({ type: "DEVBRIDGE_PROJECT_CONTEXT_CHANGED", payload: message.payload } satisfies ExtensionMessage).catch(() => undefined);
    return false;
  }
  if (message.type !== "DEVBRIDGE_GET_PROJECT_CONTEXT") return false;
  void chrome.tabs.query({ active: true, currentWindow: true }).then(async ([tab]) => {
    if (!tab?.id || !tab.url?.startsWith("https://script.google.com/")) {
      sendResponse(null);
      return;
    }
    try {
      const context = await chrome.tabs.sendMessage(tab.id, message) as ProjectContext | null;
      if (context) projectByTab.set(tab.id, context);
      sendResponse(context ?? projectByTab.get(tab.id) ?? null);
    } catch {
      sendResponse(projectByTab.get(tab.id) ?? null);
    }
  });
  return true;
});
