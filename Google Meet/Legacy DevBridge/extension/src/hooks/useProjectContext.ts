import { useEffect, useState } from "react";
import type { ExtensionMessage, ProjectContext, ProjectContextState } from "../types/project";

export function useProjectContext(): ProjectContextState {
  const [state, setState] = useState<ProjectContextState>({ status: "loading" });
  useEffect(() => {
    const update = (project: ProjectContext | null | undefined) => {
      setState(project ? { status: "detected", project } : { status: "not-apps-script" });
    };
    const listener = (message: ExtensionMessage) => {
      if (message.type === "DEVBRIDGE_PROJECT_CONTEXT_CHANGED") update(message.payload);
    };
    chrome.runtime.onMessage.addListener(listener);
    (chrome.runtime.sendMessage({ type: "DEVBRIDGE_GET_PROJECT_CONTEXT" } satisfies ExtensionMessage) as Promise<ProjectContext | null>)
      .then(update)
      .catch(() => setState({ status: "unavailable", message: "Reload the Apps Script editor, then reopen DevBridge." }));
    return () => chrome.runtime.onMessage.removeListener(listener);
  }, []);
  return state;
}
