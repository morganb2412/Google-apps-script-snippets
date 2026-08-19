import { useCallback, useEffect, useState } from "react";
import { demoApi } from "../services/apiClient";
import type { DemoWorkspace } from "../types/demo";

export function useDemoWorkspace() {
  const [workspace, setWorkspace] = useState<DemoWorkspace | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try { setWorkspace(await demoApi.workspace()); setError(null); }
    catch { setError("Start the local DevBridge API to use Demo Workspace."); }
  }, []);
  useEffect(() => { void demoApi.workspace().then(setWorkspace).catch(() => setError("Start the local DevBridge API to use Demo Workspace.")); }, []);
  const perform = async (operation: () => Promise<DemoWorkspace>) => {
    setBusy(true);
    try { setWorkspace(await operation()); setError(null); } catch (caught) { setError(caught instanceof Error ? caught.message : "Demo action failed."); }
    finally { setBusy(false); }
  };
  return { workspace, error, busy, load, connect: () => perform(demoApi.connect), branch: (name: string) => perform(() => demoApi.branch(name)), commit: (message: string) => perform(() => demoApi.commit(message)), pullRequest: () => perform(demoApi.pullRequest) };
}
