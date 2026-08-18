export type SetupStep = "GOOGLE" | "GITHUB" | "PROJECT" | "REPOSITORY" | "STANDARDS" | "COMPLETE";

export interface UserSetupState {
  user_id: string;
  google_connected: boolean;
  github_connected: boolean;
  organization_created: boolean;
  project_detected: boolean;
  project_connected: boolean;
  repository_connected: boolean;
  standards_configured: boolean;
  ai_ready: boolean;
  onboarding_completed: boolean;
  next_step: SetupStep;
  updated_at: string;
  connection_mode: string;
}

export type OnboardingState =
  | { status: "loading" }
  | { status: "ready"; setup: UserSetupState; busy: boolean; error: string | null }
  | { status: "unavailable" };
