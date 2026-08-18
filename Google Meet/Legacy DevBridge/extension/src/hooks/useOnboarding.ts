import { useCallback, useEffect, useState } from "react";
import {
  completeOnboarding,
  connectOnboardingProvider,
  getOnboardingStatus,
  registerDetectedProject,
  selectRecommendedStandards,
  startGoogleConnection,
} from "../services/apiClient";
import type { OnboardingState, UserSetupState } from "../types/onboarding";
import type { ProjectContext } from "../types/project";

export interface OnboardingActions {
  connectGoogle: () => Promise<void>;
  connectGitHub: () => Promise<void>;
  useProject: () => Promise<void>;
  configureStandards: () => Promise<void>;
  complete: () => Promise<void>;
  retry: () => Promise<void>;
}

export function useOnboarding(project: ProjectContext | null): [OnboardingState, OnboardingActions] {
  const [state, setState] = useState<OnboardingState>({ status: "loading" });

  const load = useCallback(async () => {
    try {
      const setup = await getOnboardingStatus();
      setState({ status: "ready", setup, busy: false, error: null });
    } catch {
      setState({ status: "unavailable" });
    }
  }, []);

  useEffect(() => {
    let active = true;
    void getOnboardingStatus()
      .then((setup) => {
        if (active) setState({ status: "ready", setup, busy: false, error: null });
      })
      .catch(() => {
        if (active) setState({ status: "unavailable" });
      });
    return () => { active = false; };
  }, []);

  const perform = useCallback(async (operation: () => Promise<UserSetupState>) => {
    setState((current) => current.status === "ready" ? { ...current, busy: true, error: null } : current);
    try {
      const setup = await operation();
      setState({ status: "ready", setup, busy: false, error: null });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Setup could not continue.";
      setState((current) => current.status === "ready" ? { ...current, busy: false, error: message } : current);
    }
  }, []);

  return [state, {
    connectGoogle: () => perform(import.meta.env.DEV
      ? () => connectOnboardingProvider("google")
      : startGoogleConnection),
    connectGitHub: () => perform(() => connectOnboardingProvider("github")),
    useProject: () => project ? perform(() => registerDetectedProject(project)) : Promise.resolve(),
    configureStandards: () => perform(selectRecommendedStandards),
    complete: () => perform(completeOnboarding),
    retry: load,
  }];
}
