import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import type { OnboardingActions } from "../hooks/useOnboarding";
import { OnboardingWizard } from "./OnboardingWizard";

const actions: OnboardingActions = {
  connectGoogle: vi.fn(async () => undefined),
  connectGitHub: vi.fn(async () => undefined),
  useProject: vi.fn(async () => undefined),
  configureStandards: vi.fn(async () => undefined),
  complete: vi.fn(async () => undefined),
  retry: vi.fn(async () => undefined),
};

test("starts with an explicitly labeled local Google mock", () => {
  render(<OnboardingWizard project={null} actions={actions} state={{ status: "ready", busy: false, error: null, setup: {
    user_id: "local-developer", google_connected: false, github_connected: false, organization_created: false,
    project_detected: false, project_connected: false, repository_connected: false, standards_configured: false,
    ai_ready: false, onboarding_completed: false, next_step: "GOOGLE", updated_at: "2026-08-18T00:00:00Z",
    connection_mode: "UNCONFIGURED",
  } }} />);
  expect(screen.getByText("GUIDED SETUP · LOCAL MOCK")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Connect Google (local mock)" }));
  expect(actions.connectGoogle).toHaveBeenCalled();
});
