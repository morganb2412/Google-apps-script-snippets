import { useEffect, useState } from "react";
import { getHealth } from "../services/apiClient";

export type ApiState = "checking" | "connected" | "unavailable";

export function useApiHealth(): ApiState {
  const [state, setState] = useState<ApiState>("checking");
  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal).then(() => setState("connected")).catch((error: unknown) => {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setState("unavailable");
    });
    return () => controller.abort();
  }, []);
  return state;
}
